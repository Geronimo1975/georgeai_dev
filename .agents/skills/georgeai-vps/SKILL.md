---
name: georgeai-vps
description: Operate the shared VPS (85.215.69.83) — containers, Traefik, Postgres, logs, tunnels. Use for any ssh/docker work on the server.
---

# VPS operations — 85.215.69.83

Access: `ssh macbook-air` (alias → `root@85.215.69.83`). Site files: `/opt/georgeai`.

## ⚠️ This VPS is SHARED infrastructure

`gethub-traefik` (Traefik v2.11 + Let's Encrypt) and `gethub-postgres` serve
**other projects besides georgeai**. Never restart, reconfigure, or upgrade them
for a georgeai-only problem without confirming with George first. The only
container owned by this project is `georgeai-web`.

## Common operations

```bash
ssh macbook-air "docker ps"                                  # what's running
ssh macbook-air "docker logs --tail 50 georgeai-web"         # nginx logs
ssh macbook-air "docker restart georgeai-web"                # safe to restart
ssh macbook-air "docker logs --tail 50 gethub-traefik"       # routing/TLS issues
```

Routing: Traefik labels live in `deploy/docker-compose.yml`
(hosts `georgeai.dev` + `www.georgeai.dev`, cert resolver `letsencrypt`,
network `gethub_gethub-network`). nginx per-location headers: `deploy/nginx.conf`.

## Local port conventions (do not collide)

| Port | Purpose |
|------|---------|
| 5433 | n8n postgres tunnel (reserved — never rebind) |
| 5434 | georgeai postgres tunnel (see georgeai-backend skill) |
