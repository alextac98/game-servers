#!/usr/bin/env python3
"""Remove only root/fml/Registries from gzip NBT. Python 3, no dependencies.

For vanilla-content worlds such as Craftopia with only FallingTree.
Stop Minecraft first. Defaults to a dry run; pass --apply to write.
"""

import argparse
import fcntl
import gzip
import os
from pathlib import Path
import shutil
import struct
import sys
import tempfile
from datetime import datetime, timezone


class NBT:
    def __init__(self, data):
        self.data = data
        self.pos = 0
        self.matches = []

    def take(self, size):
        if size < 0 or self.pos + size > len(self.data):
            raise ValueError("Invalid or truncated NBT")
        result = self.data[self.pos:self.pos + size]
        self.pos += size
        return result

    def number(self, fmt):
        return struct.unpack(fmt, self.take(struct.calcsize(fmt)))[0]

    def string(self):
        # Keep names as raw bytes: Java NBT strings use modified UTF-8.
        return self.take(self.number(">H"))

    def payload(self, tag, path, depth=0):
        if depth > 128:
            raise ValueError("NBT nesting exceeds safety limit")
        fixed = {1: 1, 2: 2, 3: 4, 4: 8, 5: 4, 6: 8}
        if tag in fixed:
            self.take(fixed[tag])
        elif tag in (7, 11, 12):
            count = self.number(">i")
            self.take(count * {7: 1, 11: 4, 12: 8}[tag])
        elif tag == 8:
            self.string()
        elif tag == 9:
            child = self.number(">B")
            count = self.number(">i")
            if count < 0 or count > len(self.data) or child > 12 or (child == 0 and count):
                raise ValueError("Invalid NBT list")
            for _ in range(count):
                self.payload(child, path + (None,), depth + 1)
        elif tag == 10:
            names = set()
            while True:
                start = self.pos
                child = self.number(">B")
                if child == 0:
                    break
                name = self.string()
                if name in names:
                    raise ValueError("Duplicate compound keys; refusing ambiguous edit")
                names.add(name)
                child_path = path + (name,)
                self.payload(child, child_path, depth + 1)
                if child_path == (b"fml", b"Registries"):
                    if child != 10:
                        raise ValueError("fml/Registries is not a compound")
                    self.matches.append((start, self.pos))
        else:
            raise ValueError("Unknown NBT tag: %s" % tag)

    def parse(self):
        if self.number(">B") != 10:
            raise ValueError("Expected an NBT compound root")
        self.string()
        self.payload(10, ())
        if self.pos != len(self.data):
            raise ValueError("Unexpected bytes after NBT root")
        return self.matches


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", default="/data/world/level.dat")
    parser.add_argument("--apply", action="store_true", help="back up and write the repair")
    args = parser.parse_args()
    path = Path(args.file).resolve(strict=True)

    # Java's world lock uses POSIX record locks on Linux, as does lockf.
    # Hold it through the edit to prevent Minecraft opening this world midway.
    with path.with_name("session.lock").open("r+b") as lock:
        try:
            fcntl.lockf(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise ValueError("World is in use. Stop Minecraft before running this script.")
        original = path.read_bytes()
        data = gzip.decompress(original)
        matches = NBT(data).parse()
        if not matches:
            print("No root/fml/Registries compound found. Nothing changed.")
            return
        start, end = matches[0]
        repaired = data[:start] + data[end:]
        if NBT(repaired).parse():
            raise ValueError("Repair verification failed")
        print("Would remove only root/fml/Registries (%s uncompressed bytes)." % (end - start))
        if not args.apply:
            print("Dry run: nothing changed. Add --apply to back up and write.")
            return

        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
        backup = path.with_name(path.name + ".before-registry-reset-" + stamp)
        with backup.open("xb") as output:
            output.write(original)
            output.flush()
            os.fsync(output.fileno())
        shutil.copystat(path, backup)
        if backup.read_bytes() != original:
            raise ValueError("Backup verification failed")

        stat = path.stat()
        temp = None
        try:
            with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".level.dat-repair-", delete=False) as output:
                temp = Path(output.name)
                os.fchmod(output.fileno(), stat.st_mode & 0o7777)
                current = os.fstat(output.fileno())
                if (current.st_uid, current.st_gid) != (stat.st_uid, stat.st_gid):
                    os.fchown(output.fileno(), stat.st_uid, stat.st_gid)
                output.write(gzip.compress(repaired))
                output.flush()
                os.fsync(output.fileno())
            if gzip.decompress(temp.read_bytes()) != repaired:
                raise ValueError("Written NBT verification failed")
            if path.read_bytes() != original:
                raise ValueError("level.dat changed during repair; refusing to overwrite")
            os.replace(temp, path)
            temp = None
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
        finally:
            if temp is not None:
                temp.unlink(missing_ok=True)
        print("Repaired:", path)
        print("Backup:", backup)
        print("Start Forge, then verify vanilla login, inventories, and entities.")


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, EOFError, struct.error) as error:
        sys.exit("ERROR: " + str(error))
