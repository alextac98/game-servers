# VPS tunnel endpoint

This Compose application runs the public SSH endpoint for Craftopia's reverse
tunnel. It exposes the SSH transport on TCP `25522` and the forwarded Minecraft
listener on TCP `25565`. It does not contain the tunnel's private key.

## Deploy

1. Copy this directory to the VPS, or check out the repository there.
2. Preserve the existing `config/` directory if migrating the old container;
   it contains the SSH host identity.
3. Copy `.env.example` to `.env` and replace the public-key placeholder.
4. Validate and deploy:

   ```sh
   docker compose config --quiet
   docker compose pull
   docker compose up -d
   ```

5. Check the effective restrictions and logs:

   ```sh
   docker compose exec openssh-server \
     sshd -T -C user=minecraft-tunnel,host=localhost,addr=127.0.0.1 \
     -f /config/sshd/sshd_config \
     | grep -E '^(allowtcpforwarding|allowstreamlocalforwarding|gatewayports|permitlisten|maxsessions|forcecommand)'
   docker compose logs -f openssh-server
   ```

LinuxServer appends `PUBLIC_KEY` to the persistent
`config/.ssh/authorized_keys`; removing or replacing the environment variable
does not remove older entries. After the new key works, remove the legacy line
from that file explicitly.

See [the complete remote-access runbook](../remote-access.md) for host-key
verification, Coolify configuration, firewall rules, and end-to-end tests.
