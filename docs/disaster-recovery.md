# Disaster recovery

## What is backed up

The `backups` sidecar takes an initial archive when the stack starts. After that,
it waits for player activity and schedules at most one archive every 24 hours.
When nobody is playing, it pauses instead of repeatedly archiving an unchanged
world. It keeps at most seven local archives and removes any older than 30 days.
The interval, activity behavior, and retention are configurable through Coolify.

The backup archive volume is on the same Docker host as the world. Replicate it
off-host; otherwise a disk or host failure can destroy both the world and its
backups.

## Before a risky change

1. Confirm the last scheduled backup succeeded in the `backups` service logs.
2. Trigger an immediate backup from Coolify's terminal:

   ```sh
   backup now
   ```

3. Copy the resulting archive off-host.
4. Record the currently deployed Git commit.

## Restore procedure

1. Stop the Minecraft and backup services.
2. Preserve the current data volume instead of deleting it.
3. Mount the selected backup archive and the data volume into an
   `itzg/mc-backup` recovery container.
4. Run `restore-tar-backup` following the upstream restore documentation.
5. Start Minecraft without the backup sidecar and verify the world, player data,
   and mod compatibility.
6. Re-enable backups after verification.

Test this procedure with a disposable volume before relying on it in an outage.
The authoritative restore options are documented by
[`itzg/mc-backup`](https://github.com/itzg/docker-mc-backup).

## Repository recovery

Recreating the Compose stack from Git does not recreate the world. A complete
recovery therefore needs:

- The Git repository and desired commit.
- Coolify secrets, especially `RCON_PASSWORD`.
- An off-host world backup.
- Network/DNS records and router or tunnel configuration.
