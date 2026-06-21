# georgeai.dev

Production deployment pipeline for **George Sebastian Cucuiet's** portfolio
(`georgeai.dev`). You design/export HTML elsewhere; this project unpacks the
export, ships it to the VPS, and serves it live behind Traefik with automatic
TLS.

## How it works

```
  design tool ──export.zip──▶  ./exports/  ──./deploy.sh──▶  ./site/  ──rsync──▶  VPS:/opt/georgeai
                                                                                       │
                                              nginx container (georgeai-web)  ◀────────┘
                                                       │
                                              Traefik (TLS, Let's Encrypt)
                                                       │
                                          https://georgeai.dev
```

- **Static hosting:** `nginx:1.27-alpine` serving `./site` (bind-mounted, read-only).
- **Edge / TLS:** existing `gethub-traefik` (Traefik v2.11) on network `gethub_gethub-network`, cert resolver `letsencrypt`.
- **No build step** — the design export is plain HTML/CSS/JS.

## Deploy

```bash
# 1. export your site from the design tool as a .zip
# 2. drop it in ./exports/
# 3. publish:
./deploy.sh
```

Other forms:

```bash
./deploy.sh exports/georgeai.zip   # specific archive
./deploy.sh --no-content           # redeploy current ./site (e.g. after editing the placeholder)
./deploy.sh --help
```

The script: unpacks the newest zip into `./site` (flattening a single wrapper
folder if present) → `rsync` to the VPS → `docker compose up -d` + restart →
health-checks the live URLs.

## Layout

| Path | Purpose |
|------|---------|
| `deploy.sh` | the deployment pipeline (run locally) |
| `site/` | live web root — placeholder now, overwritten by each export |
| `exports/` | drop zone for design-tool `.zip` exports (zips are git-ignored) |
| `deploy/docker-compose.yml` | nginx service + Traefik routing labels |
| `deploy/nginx.conf` | gzip, caching, security headers, `/healthz` |
| `DESIGN-claude.md` | the warm Claude.com design system (cream / coral / dark) |

## Domains

| URL | Status |
|-----|--------|
| `https://georgeai.dev` / `www` | **activates automatically** once the registrar A record points `@` and `www` → `85.215.69.83` |

Until the `georgeai.dev` A record is changed (currently parked at `2.57.91.91`), Let's Encrypt cannot issue its certificate. To test locally before the DNS change propagates, you can map `georgeai.dev` and `www.georgeai.dev` to `85.215.69.83` in your local `/etc/hosts` file.

## Config

| Env var | Default | Notes |
|---------|---------|-------|
| `GEORGEAI_SSH_HOST` | `macbook-air` | ssh alias → `root@85.215.69.83` |
| `GEORGEAI_REMOTE_DIR` | `/opt/georgeai` | project dir on the VPS |
