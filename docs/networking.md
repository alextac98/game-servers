# Networking

Minecraft Java Edition uses TCP port `25565`. The Compose port mapping publishes
that port directly on the Coolify host; game traffic does not pass through
Coolify's HTTP reverse proxy.

## Local network

For a LAN-only server, do not forward the Minecraft port on the router. Restrict
access with the host firewall when the machine also has a public interface.

## Internet access

Choose one ingress method:

1. Forward TCP `25565` from the router to the Coolify host.
2. Use a private overlay network such as Tailscale for known players.
3. Use a reverse tunnel when the host is behind CGNAT.

If a reverse tunnel must address the Minecraft container by service name, run it
as a sidecar in the same Compose application. Keep its private key or token in
Coolify or a host-mounted secret; never commit it.

## Internal ports

RCON uses TCP `25575` inside the application network. It is intentionally absent
from `ports:` and must not be opened on the router. Backup or management services
reach it using the Compose service hostname `minecraft`.

When adding another Minecraft instance on the same host, assign a unique host
port, for example `25566:25565`.

See [Coolify's Compose networking guidance](https://coolify.io/docs/knowledge-base/docker/compose)
for the distinction between domains, published ports, and private services.
