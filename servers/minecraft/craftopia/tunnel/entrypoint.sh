#!/bin/sh
set -eu

runtime_key=/tmp/id_ed25519
runtime_known_hosts=/tmp/known_hosts

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

if [ -z "${SSH_TUNNEL_PRIVATE_KEY:-}" ]; then
  echo "Required variable SSH_TUNNEL_PRIVATE_KEY is empty" >&2
  exit 1
fi

if [ -z "${SSH_TUNNEL_KNOWN_HOSTS:-}" ]; then
  echo "Required variable SSH_TUNNEL_KNOWN_HOSTS is empty" >&2
  exit 1
fi

# Coolify supplies multiline runtime variables. Materialize them only in the
# container's ephemeral tmpfs with the permissions OpenSSH requires.
umask 077
printf '%s\n' "$SSH_TUNNEL_PRIVATE_KEY" > "$runtime_key"
printf '%s\n' "$SSH_TUNNEL_KNOWN_HOSTS" > "$runtime_known_hosts"
chmod 600 "$runtime_key"
chmod 600 "$runtime_known_hosts"

# Do not pass either credential into the long-running SSH process environment.
unset SSH_TUNNEL_PRIVATE_KEY SSH_TUNNEL_KNOWN_HOSTS

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
  -o UserKnownHostsFile="$runtime_known_hosts" \
  -- "$SSH_TUNNEL_HOST"
