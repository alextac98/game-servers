# Craftopia

Craftopia is a whitelisted Forge server configured for Minecraft `26.3` with
Forge `66.0.6`. The Compose stack is intended to be deployed as a standalone
Coolify application.

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

The mod list pins FallingTree `26.3-26.3.0.2` for Minecraft `26.3`.

## Upgrading from 26.2

1. Have players disconnect and keep them off the server during the upgrade.
   In Coolify's `backups` container terminal, run `backup now`, confirm the
   archive completed in the service logs, and copy it off-host. Record the
   deployed Git commit and current Coolify version overrides.
2. Restore that backup into a separate test data volume. Start only the
   `minecraft` service using the new configuration, a separate Compose project,
   and an unused host port. Do not attach the production volume or start the
   public tunnel for this test.
3. Confirm startup reports Minecraft `26.3` and Forge `66.0.6`, then join with a
   `26.3` client. Check the world, inventories, operator commands, and FallingTree.
4. Before production deployment, set any existing Coolify `MINECRAFT_VERSION`
   override to `26.3` and any `FORGE_VERSION` override to `66.0.6`. Environment
   overrides take precedence over the defaults in Compose.
5. Deploy the updated commit with the existing production data volume. Check
   Minecraft health, mod loading, and tunnel connectivity before players return.

To roll back after the upgraded server has opened the world, stop the services,
restore the pre-upgrade backup, and restore both the previous Git commit and
Coolify version overrides. Do not open the upgraded world with Minecraft `26.2`.
See the [recovery runbook](../../../docs/disaster-recovery.md).

## Operations

Whitelist and other live administration should be performed through RCON. An
authenticated operator UI can be added later without changing the world volume
or mod-management model.

See the repository [`docs`](../../../docs/architecture.md) for networking,
deployment, and recovery guidance.
