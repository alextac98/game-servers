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
`SSH_TUNNEL_KNOWN_HOSTS` secrets described in the
[remote-access runbook](../../../docs/remote-access.md).

LAN players connect to TCP `25565` on the Coolify host. Remote players connect
to `mc.alextac.com:25565`, which the VPS forwards through the `tunnel` sidecar.
RCON remains internal to the Compose network. Docker restarts the tunnel after a
failed SSH session; persistent failures are visible in the service logs.

## Mods

Edit [`mods/modrinth.txt`](mods/modrinth.txt) and redeploy. Prefer pinned versions
for important mods. Verify loader and Minecraft compatibility before upgrading.

The initial manifest installs FallingTree from a pinned Modrinth release.

## Operations

Whitelist and other live administration should be performed through RCON. An
authenticated operator UI can be added later without changing the world volume
or mod-management model.

See the repository [`docs`](../../../docs/architecture.md) for networking,
deployment, and recovery guidance.
