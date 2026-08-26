# Adding a Minecraft server

## Create the instance

1. Copy an existing directory under `servers/minecraft/` to a new, descriptive
   instance name.
2. Change its named volumes, server name, port, and other defaults. Volume names
   must be unique and should not be changed after the first deployment.
3. Replace the inline `MODRINTH_PROJECTS` list and document any instance-specific
   operating notes.
4. Validate the Compose model:

   ```sh
   docker compose \
     --env-file servers/minecraft/<instance>/.env.example \
     -f servers/minecraft/<instance>/docker-compose.yaml \
     config --quiet
   ```

5. Commit the new instance and push it to the Git provider connected to Coolify.

## Create the Coolify application

Create a Git-based application using the Docker Compose build pack and configure:

| Setting | Value |
| --- | --- |
| Branch | `main` |
| Base directory | `/servers/minecraft/<instance>` |
| Docker Compose location | `/docker-compose.yaml` |
| Watch path | `servers/minecraft/<instance>/**` |
| Preserve repository during deployment | Not required |

The Modrinth project list is a multiline value in Compose. Keeping it inline
avoids repository-relative bind mounts, which do not share the same filesystem
namespace as Coolify's deployment helper container.

Set `RCON_PASSWORD`, `SSH_TUNNEL_PRIVATE_KEY`, and `SSH_TUNNEL_KNOWN_HOSTS` in
Coolify before the first deployment. The private key is multiline; both SSH
values and the RCON password are runtime-only variables. Disable their Build
Variable setting so they are never passed to the image build. The tunnel copies
its SSH values into a private tmpfs before starting SSH. Review all other
variables detected from Compose and override only values that should differ from
the Git defaults.

Complete the VPS endpoint, firewall, DNS, and key-verification steps in
[remote access](remote-access.md) before enabling the tunnel.

## First-deployment checks

- The `minecraft` service becomes healthy.
- The `backups` service connects to RCON and creates its initial archive.
- The `tunnel` service remains running and its logs show no forwarding or host
  key errors.
- TCP `25565` is reachable through the intended LAN and VPS paths, while RCON
  remains unreachable externally.
- The world seed, loader, version, and whitelist setting are correct.
- A backup archive can be restored before inviting players.

Do not enable auto-deploy until these checks pass for a new instance.
