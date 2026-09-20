# Craftopia

Craftopia is a whitelisted Forge server running Minecraft `26.2`. The Compose
stack is intended to be deployed as a standalone Coolify application.

## Local validation

```sh
docker compose --env-file .env.example -f docker-compose.yaml config --quiet
```

To run locally, copy `.env.example` to `.env`, replace the RCON password, and use:

```sh
docker compose up -d minecraft backups
```

That command leaves the public tunnel disabled. Start the full stack only after
replacing the placeholder SSH secrets with the verified VPS credentials.

The local `.env`, world data, downloaded mods, and backup archives are ignored by
Git.

## Coolify

Use `/servers/minecraft/craftopia` as the base directory and
`/docker-compose.yaml` as the Compose location. Set a strong `RCON_PASSWORD` in
Coolify before deploying. Also add the multiline `SSH_TUNNEL_PRIVATE_KEY` and
verified `SSH_TUNNEL_KNOWN_HOSTS` value described in the
[remote-access runbook](../../../docs/remote-access.md).

LAN players connect to TCP `25565` on the Coolify host. Remote players connect
to `mc.alextac.com:25565`, which the VPS forwards through the `tunnel` sidecar.
RCON remains internal to the Compose network. Docker restarts the tunnel after a
failed SSH session; persistent failures are visible in the service logs.

## Mods

Edit the multiline `MODRINTH_PROJECTS` value in `docker-compose.yaml` and
redeploy. Prefer pinned versions for important mods. Verify loader and Minecraft
compatibility before upgrading.

The initial list installs FallingTree from a pinned Modrinth release.

## Operations

Whitelist and other live administration should be performed through RCON. An
authenticated operator UI can be added later without changing the world volume
or mod-management model.

### Restore allowlist access

If Minecraft reports "You are not white-listed on this server", open Coolify's
terminal for the **minecraft** container and run:

```sh
rcon-cli whitelist list
rcon-cli whitelist add YOUR_JAVA_PROFILE_NAME
rcon-cli whitelist list
```

Replace `YOUR_JAVA_PROFILE_NAME` with your Minecraft Java profile name, which
can differ from your Xbox gamertag. Repeat the add command for each missing
player. Changes take effect immediately and are saved by Minecraft; no restart
or `whitelist reload` is needed. Keep the whitelist enabled.

### Preserve the allowlist across deployments

Minecraft saves membership in `/data/whitelist.json`. The existing
`craftopia-data:/data` named-volume mount persists that file along with the world.
`EXISTING_WHITELIST_FILE: "SKIP"` tells the image's startup scripts to leave an
existing allowlist alone, so RCON remains the source of membership changes. See
the [upstream whitelist options](https://docker-minecraft-server.readthedocs.io/en/latest/configuration/server-properties/#whitelist-players).

Deploy this Compose change through the existing Coolify application. Keep the
same data volume and application resource; do not rename or delete the volume
or run `docker compose down -v`. This setting preserves an existing list but
cannot recover entries already lost, so add missing players using RCON above.

If membership disappears again:

1. Before and after redeploying, run `rcon-cli whitelist list` and
   `cat /data/whitelist.json` in the Minecraft container terminal.
2. In Coolify, check the deployed container's environment for `WHITELIST`,
   `WHITELIST_FILE`, `OVERRIDE_WHITELIST`, and `EXISTING_WHITELIST_FILE` overrides.
   Remove conflicting startup-managed membership settings and ensure the
   deployed value of `EXISTING_WHITELIST_FILE` is `SKIP`.
3. On the Docker host, compare the actual volume mounted at `/data` before and
   after deployment (replace `CONTAINER_ID` with the Minecraft container ID):

   ```sh
   docker inspect CONTAINER_ID --format '{{range .Mounts}}{{if eq .Destination "/data"}}{{.Name}} -> {{.Destination}}{{end}}{{end}}'
   ```

   If the volume changed, reconnect the original volume while the server is
   stopped, or follow the [recovery procedure](../../../docs/disaster-recovery.md).
   A reset world also points to a different or empty data volume. Preserve both
   volumes until recovery is verified.

See the repository [`docs`](../../../docs/architecture.md) for networking,
deployment, and recovery guidance.
