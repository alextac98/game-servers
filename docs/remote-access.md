# Remote access through the VPS

Craftopia's `tunnel` service makes an outbound SSH connection to the VPS. The
VPS listens on public TCP `25565` and carries that traffic through the tunnel to
`minecraft:25565`. LAN users continue connecting directly to the Coolify host.

The VPS endpoint is a dedicated LinuxServer OpenSSH container. The examples use
the existing address `mc.alextac.com`, SSH port `25522`, and the descriptive
container account `minecraft-tunnel`.

## 1. Create a dedicated key

Generate this key on a trusted workstation, not in the repository:

```sh
ssh-keygen -t ed25519 -a 100 \
  -f craftopia_tunnel \
  -C craftopia-reverse-tunnel
```

Do not reuse a personal login key. Keep `craftopia_tunnel` private and use the
contents of `craftopia_tunnel.pub` in the next step.

## 2. Deploy the containerized VPS endpoint

Use the versioned application in [`docs/vps-tunnel`](vps-tunnel/). It updates the
old LinuxServer OpenSSH 9.9 image to the pinned 10.3 release, keeps password and
sudo access disabled, and loads the forwarding policy from `sshd_config.d`.

On the VPS, copy `.env.example` to `.env`. Set
`SSH_TUNNEL_AUTHORIZED_KEY` to the new public key with this exact prefix:

```text
restrict,port-forwarding,permitlisten="0.0.0.0:25565",command="/bin/false" ssh-ed25519 PUBLIC_KEY craftopia-reverse-tunnel
```

Then validate and deploy:

```sh
cd docs/vps-tunnel
docker compose config --quiet
docker compose pull
docker compose up -d
```

The Compose file publishes host TCP `25522` to the container's SSH port `2222`
and host TCP `25565` to the reverse listener on the same container port. The
tracked SSH fragment permits remote forwarding only, limits the listener to
`0.0.0.0:25565`, disables Unix-socket and network-device tunnels, prevents SSH
sessions, and forces any requested command to `/bin/false`.

### Migrating the old container

Preserve the old `./config` directory when changing the image or Compose file.
It contains the VPS endpoint's SSH host keys; losing it changes the fingerprint
and correctly causes the Coolify tunnel to reject the server.

The LinuxServer initialization process appends `PUBLIC_KEY` to persistent
`config/.ssh/authorized_keys`; removing the environment variable does not remove
an old key. If reusing the old key, replace its unrestricted line with the line
above. If rotating, deploy and verify the new restricted key, then explicitly
remove the old line. Do not leave an unrestricted copy of the same key in the
file.

The old and new containers cannot both publish ports `25522` and `25565`.
Validate the new model first, stop the old Compose application, and then start
this one. Confirm the effective server policy after startup:

```sh
docker compose exec openssh-server \
  sshd -T -C user=minecraft-tunnel,host=localhost,addr=127.0.0.1 \
  -f /config/sshd/sshd_config \
  | grep -E '^(allowtcpforwarding|allowstreamlocalforwarding|gatewayports|permitlisten|maxsessions|forcecommand)'
```

The expected values are remote-only TCP forwarding, `clientspecified` gateway
ports, disabled stream-local forwarding, `0.0.0.0:25565` as the only permitted
listener, zero SSH sessions, and `/bin/false` as the forced command.

## 3. Open only the required ports

Allow inbound TCP `25522` and `25565` in both the VPS host firewall and any
provider firewall. Port `25522` carries the authenticated SSH tunnel; restrict
it to the home connection's public IP when that address is stable. Port `25565`
is the public Minecraft endpoint. Do not expose RCON port `25575`. Stop the
legacy container first if it is still occupying either required port.

Point the `A` record for `mc.alextac.com` at the VPS. Add an `AAAA` record only
if the VPS has working IPv6 and the firewall permits the same game port.

## 4. Verify and pin the VPS host key

From the repository root on the VPS, record the container's trusted ED25519
host-key fingerprint:

```sh
cd docs/vps-tunnel
docker compose exec openssh-server \
  ssh-keygen -lf /config/ssh_host_keys/ssh_host_ed25519_key.pub
```

From a trusted workstation, retrieve the advertised key:

```sh
ssh-keyscan -p 25522 -t ed25519 mc.alextac.com > craftopia_known_hosts
ssh-keygen -lf craftopia_known_hosts
```

Compare the fingerprints. Continue only when they match. The saved line should
start with `[mc.alextac.com]:25522`; this complete verified line becomes the
`SSH_TUNNEL_KNOWN_HOSTS` secret. `ssh-keyscan` alone does not authenticate a
server, which is why the out-of-band fingerprint comparison matters.

## 5. Configure Coolify

Add these environment variables to the Craftopia application:

| Variable | Value |
| --- | --- |
| `SSH_TUNNEL_HOST` | `mc.alextac.com` |
| `SSH_TUNNEL_PORT` | `25522` |
| `SSH_TUNNEL_USER` | `minecraft-tunnel` |
| `SSH_TUNNEL_BIND_ADDRESS` | `0.0.0.0` |
| `SSH_TUNNEL_REMOTE_PORT` | `25565` |
| `SSH_TUNNEL_PRIVATE_KEY` | Complete multiline contents of `craftopia_tunnel` |
| `SSH_TUNNEL_KNOWN_HOSTS` | Complete verified line from `craftopia_known_hosts` |

Mark the two credential values as runtime-only secrets. Add them manually in
Coolify's developer view if it does not automatically discover variables used
only as top-level Compose secret sources. The Compose model mounts them as
read-only files under `/run/secrets`; they are not placed in the sidecar's
environment.

## 6. Deploy and verify

After deploying, confirm:

1. The `minecraft` service is healthy and the `tunnel` service remains running.
2. Tunnel logs contain no host-key, authentication, or remote-forward errors.
3. `docker compose exec openssh-server ss -ltnp` on the VPS shows a listener on
   `0.0.0.0:25565`.
4. A device outside the home network can join `mc.alextac.com:25565`.
5. A LAN device can still join the Coolify host's local address on port `25565`.

The SSH keepalive detects a dead connection in about 90 seconds, exits, and lets
Docker's restart policy reconnect. Add an external TCP check for
`mc.alextac.com:25565` if remote availability matters.

Because traffic reaches Minecraft through one SSH connection, IP-based bans and
logs may identify the tunnel path rather than each remote player's original IP.
Use Minecraft's account whitelist as the primary access control.

## Rotation and failure behavior

To rotate the client key without downtime, add a second restricted public key on
the VPS, update `SSH_TUNNEL_PRIVATE_KEY` in Coolify, redeploy and verify, then
remove the old public key. If the VPS host key legitimately changes, the tunnel
fails closed; verify the new fingerprint out of band before updating
`SSH_TUNNEL_KNOWN_HOSTS`.

## References

- [OpenSSH `sshd_config`](https://man.openbsd.org/sshd_config)
- [OpenSSH `authorized_keys`](https://man.openbsd.org/sshd#AUTHORIZED_KEYS_FILE_FORMAT)
- [Docker Compose secrets](https://docs.docker.com/compose/how-tos/use-secrets/)
- [Coolify Docker Compose](https://coolify.io/docs/knowledge-base/docker/compose)
- [LinuxServer OpenSSH container](https://github.com/linuxserver/docker-openssh-server)
