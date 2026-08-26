#!/bin/sh
set -eu

private_key=/run/secrets/ssh_tunnel_private_key
known_hosts=/run/secrets/ssh_tunnel_known_hosts
runtime_key=/tmp/id_ed25519

for variable in \
  SSH_TUNNEL_HOST \
  SSH_TUNNEL_PORT \
  SSH_TUNNEL_USER \
  SSH_TUNNEL_BIND_ADDRESS \
  SSH_TUNNEL_REMOTE_PORT \
  SSH_TUNNEL_TARGET_HOST \
  SSH_TUNNEL_TARGET_PORT
do
  eval "value=\${$variable:-}"
  if [ -z "$value" ]; then
    echo "Required variable $variable is empty" >&2
    exit 1
  fi
done

if [ ! -s "$private_key" ]; then
  echo "SSH private-key secret is missing or empty" >&2
  exit 1
fi

if [ ! -s "$known_hosts" ]; then
  echo "SSH known-hosts secret is missing or empty" >&2
  exit 1
fi

# Compose secrets are read-only and may be too permissive for OpenSSH. Copy the
# key into the container's ephemeral tmpfs with the required permissions.
umask 077
cp "$private_key" "$runtime_key"
chmod 600 "$runtime_key"

exec ssh -N -T \
  -i "$runtime_key" \
  -l "$SSH_TUNNEL_USER" \
  -p "$SSH_TUNNEL_PORT" \
  -R "$SSH_TUNNEL_BIND_ADDRESS:$SSH_TUNNEL_REMOTE_PORT:$SSH_TUNNEL_TARGET_HOST:$SSH_TUNNEL_TARGET_PORT" \
  -o BatchMode=yes \
  -o EscapeChar=none \
  -o ExitOnForwardFailure=yes \
  -o GlobalKnownHostsFile=/dev/null \
  -o IdentitiesOnly=yes \
  -o KbdInteractiveAuthentication=no \
  -o PasswordAuthentication=no \
  -o PreferredAuthentications=publickey \
  -o ServerAliveCountMax=3 \
  -o ServerAliveInterval=30 \
  -o StrictHostKeyChecking=yes \
  -o UserKnownHostsFile="$known_hosts" \
  -- "$SSH_TUNNEL_HOST"
