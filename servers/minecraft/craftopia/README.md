# Craftopia

Craftopia is a whitelisted Forge server running Minecraft `26.2`. The Compose
stack is intended to be deployed as a standalone Coolify application.

## Local validation

```sh
docker compose --env-file .env.example -f compose.yaml config --quiet
```

To run locally, copy `.env.example` to `.env`, replace the RCON password, and use:

```sh
docker compose up -d
```

The local `.env`, world data, downloaded mods, and backup archives are ignored by
Git.

## Coolify

Use `/servers/minecraft/craftopia` as the base directory and `/compose.yaml` as
the Compose location. Enable repository preservation for the mounted mod list,
and set a strong `RCON_PASSWORD` in Coolify before deploying.

The server publishes TCP `25565`. RCON remains internal to the Compose network.

## Mods

Edit [`mods/modrinth.txt`](mods/modrinth.txt) and redeploy. Prefer pinned versions
for important mods. Verify loader and Minecraft compatibility before upgrading.

The manifest starts empty because the legacy Compose file did not declare any
mods.

## Operations

Whitelist and other live administration should be performed through RCON. An
authenticated operator UI can be added later without changing the world volume
or mod-management model.

See the repository [`docs`](../../../docs/architecture.md) for networking,
deployment, and recovery guidance.
