# Craftopia

Craftopia is a whitelisted Forge server running Minecraft `26.2`. The Compose
stack is intended to be deployed as a standalone Coolify application.

## Local validation

```sh
docker compose --env-file .env.example -f docker-compose.yaml config --quiet
```

To run locally, copy `.env.example` to `.env`, replace both the RCON and web UI
passwords, and use:

```sh
docker compose up -d minecraft backups rcon-web console
```

That command leaves the public tunnel disabled. Start the full stack only after
replacing the placeholder SSH secrets with the verified VPS credentials.

The local `.env`, world data, downloaded mods, and backup archives are ignored by
Git.

## Coolify

Use `/servers/minecraft/craftopia` as the base directory and
`/docker-compose.yaml` as the Compose location. Set a strong `RCON_PASSWORD` in
Coolify before deploying. Set a separate strong `RCON_WEB_PASSWORD` for the web
UI login, and optionally set `RCON_WEB_USERNAME` (default: `admin`). Keep passwords
runtime-only with Build Variable disabled. Also add the multiline `SSH_TUNNEL_PRIVATE_KEY` and
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

Use the `rcon-web` browser console for whitelist and other live administration.
Coolify continues to own deployments, container restarts, and container logs;
Git owns mod lists and deployment configuration.

### Browser administration

The [RCON Web Admin container](https://github.com/itzg/docker-rcon-web-admin)
connects to `minecraft:25575` on the private Compose network. It needs no world
volume or Docker socket access. Its database and dashboard settings persist in
`craftopia-rcon-web`; keep that volume across redeploys. The configured username,
password, and Minecraft connection are reapplied from environment variables on
startup, so change those values in Coolify rather than only in the UI.

The `console` proxy combines the page and WebSocket on one endpoint:
`https://console.mc.alextac.com` serves the UI and
`wss://console.mc.alextac.com/ws` carries console commands. The underlying
`rcon-web` ports are internal to Docker.

In Coolify:

1. Assign `https://console.mc.alextac.com:8080` to the **console** service's
   Domains field. The `:8080` selects the internal proxy port; open the site
   without that suffix. Do not assign a domain to `rcon-web`.
2. Point DNS for `console.mc.alextac.com` to an address that reaches the Coolify
   HTTPS proxy and let Coolify provision a certificate for that exact hostname.
   The existing game-only VPS tunnel does not forward web traffic; pointing DNS
   at that VPS alone is insufficient.
3. Set `RCON_WEB_PASSWORD` and deploy. The default
   `RCON_WEB_WEBSOCKET_URL_SSL` is `wss://console.mc.alextac.com/ws`. If an earlier
   deployment set it to a different domain, update the saved Coolify variable.
4. Open <https://console.mc.alextac.com>, log in with
   `RCON_WEB_USERNAME` / `RCON_WEB_PASSWORD`, select Craftopia, and add a Console
   widget. Run Minecraft commands without the `rcon-cli` prefix:

   ```text
   whitelist list
   whitelist add YOUR_JAVA_PROFILE_NAME
   list
   ```

The image uses an older Node.js runtime. Keep access restricted through a VPN
or an authentication gateway covering both the page and `/ws`.

For local access without DNS or HTTPS, the proxy also binds to the Docker host's
loopback port 4326. Forward that single port from your computer:

```sh
ssh -N -o ExitOnForwardFailure=yes \
  -L 4326:127.0.0.1:4326 \
  YOUR_SSH_USER@YOUR_COOLIFY_HOST
```

Use your normal SSH account on the Docker/Coolify host, not the restricted VPS
`minecraft-tunnel` account. Open <http://localhost:4326>; the default non-TLS
WebSocket URL is `ws://localhost:4326/ws`.

For direct access over a trusted LAN or VPN, set `RCON_WEB_BIND_ADDRESS` to the
Docker host's LAN/VPN IP and `RCON_WEB_WEBSOCKET_URL=ws://THAT_IP:4326/ws`, then
redeploy. Both connections use `http://THAT_IP:4326` and its WebSocket equivalent;
no port 4327 forwarding is needed.

If the page loads but the console stays disconnected, check browser access to
the WebSocket endpoint first, then check the `rcon-web` logs and that its RCON
password matches Minecraft. Verify persistence by redeploying and confirming
the dashboard and `whitelist list` output are retained.

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
