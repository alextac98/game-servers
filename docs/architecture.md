# Architecture

## Control planes

The repository, Coolify, and Minecraft each own a different kind of state:

| Owner | Responsibilities |
| --- | --- |
| Git | Container versions, Minecraft version and loader, mod manifests, declarative settings, backup policy, and documentation |
| Coolify | Deployment, secret values, domains, environment overrides, and application lifecycle |
| Docker volumes | Worlds, generated files, whitelist and operator state, logs, and backup archives |
| Minecraft/RCON | Runtime actions such as whitelist, kick, ban, save, and announcements |

Keeping these responsibilities separate makes Git rollbacks safe without trying
to store changing world data in the repository.

## Deployment unit

Every `servers/minecraft/<instance>/compose.yaml` is a standalone Coolify
application. A change to one instance should not restart another instance.
Coolify supplies the private network for the services in an application, so the
Compose definitions do not create custom networks or fixed container names.

The current Craftopia stack contains:

- `minecraft`: the Java Edition server.
- `backups`: a sidecar that coordinates `save-off`, `save-all`, and `save-on`
  over the private RCON connection before archiving the data volume.

RCON port `25575` is never published to the host. A future operator UI should be
added to the same Compose stack and connect to the `minecraft` service over the
private Coolify network.

## Persistent data

The Minecraft data and backup archives use separate named volumes. Coolify adds
the resource identifier to Compose volume names, preventing instances from
overlapping. Deleting or renaming a volume in Compose is a data migration and
must be preceded by a verified backup.

Backups stored on the same host protect against a broken world or bad deployment,
not host loss. Copy backup archives to another machine or object-storage target.

## Mods

Small curated mod sets use a tracked Modrinth listing file. The Minecraft image
downloads compatible artifacts during startup and removes artifacts deleted from
the manifest. Pin a project version when reproducibility matters:

```text
fabric-api
lithium:0.15.0
spark?
```

Use Packwiz instead when Craftopia needs a distributable client and server
modpack. Do not commit downloaded JAR files.

## Secrets

Compose declares `RCON_PASSWORD` as required. Store it in Coolify and use the
same value for the Minecraft and backup services. Never put real credentials in
`.env.example`, Compose, or documentation.

## Upstream references

- [Coolify Docker Compose](https://coolify.io/docs/knowledge-base/docker/compose)
- [itzg Minecraft server](https://github.com/itzg/docker-minecraft-server)
- [Modrinth project lists](https://github.com/itzg/docker-minecraft-server/blob/master/docs/mods-and-plugins/modrinth.md)
- [Minecraft backup sidecar](https://github.com/itzg/docker-mc-backup)
