# Game Servers

This repository is the GitOps source of truth for Minecraft servers deployed by
Coolify. Runtime data such as worlds, logs, generated server files, and backups
lives in Docker volumes and is intentionally not committed.

## Repository layout

```text
.
├── docs/
│   ├── adding-a-server.md
│   ├── architecture.md
│   ├── disaster-recovery.md
│   └── networking.md
└── servers/
    └── minecraft/
        └── craftopia/
            ├── compose.yaml
            ├── .env.example
            ├── README.md
            ├── config/
            └── mods/
```

Each directory directly below `servers/minecraft/` is an independently
deployable Coolify application.

## Workflow

1. Change a server's Compose definition, mod manifest, or tracked configuration.
2. Validate it locally with the server's `.env.example` file.
3. Review and merge the change to `main`.
4. Coolify deploys only the affected server through its configured watch path.

Start with [the architecture](docs/architecture.md), then follow
[adding a server](docs/adding-a-server.md) for the Coolify settings.
