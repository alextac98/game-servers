# Networking

Minecraft Java Edition uses TCP port `25565`. The Compose port mapping publishes
that port directly on the Coolify host; game traffic does not pass through
Coolify's HTTP reverse proxy.

## Local network

For a LAN-only server, do not forward the Minecraft port on the router. Restrict
access with the host firewall when the machine also has a public interface.

## Internet access

Craftopia uses an outbound reverse SSH tunnel. The `tunnel` sidecar connects to
the VPS and asks its SSH server to listen publicly on TCP `25565`; traffic is
then carried back to `minecraft:25565` on the private Compose network. This does
not require an inbound router port-forward at home.

The containerized VPS endpoint is restricted to that one remote forward, and the
sidecar pins its SSH host key. See [remote access](remote-access.md) for the VPS,
Coolify, firewall, DNS, and verification steps.

## Internal ports

RCON uses TCP `25575` inside the application network. It is intentionally absent
from `ports:` and must not be opened on the router. Backup or management services
reach it using the Compose service hostname `minecraft`.

When adding another Minecraft instance on the same host, assign a unique host
port, for example `25566:25565`.

See [Coolify's Compose networking guidance](https://coolify.io/docs/knowledge-base/docker/compose)
for the distinction between domains, published ports, and private services.
