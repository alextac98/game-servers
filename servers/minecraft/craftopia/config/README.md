# Tracked configuration

Place intentionally Git-managed Minecraft configuration inputs in this
directory, then mount or apply them explicitly from `docker-compose.yaml`.

Do not copy generated `/data` contents here. In particular, worlds, logs,
downloaded JARs, `whitelist.json`, and `ops.json` are runtime state and belong in
the persistent data volume.
