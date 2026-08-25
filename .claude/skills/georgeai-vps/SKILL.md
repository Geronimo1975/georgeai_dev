---
name: georgeai-vps
description: Operate the shared VPS (85.215.69.83) — containers, Traefik, Postgres, logs, tunnels. Use for any ssh/docker work on the server.
---

# VPS operations — 85.215.69.83

Access: `ssh macbook-air` (alias → `root@85.215.69.83`). Site files: `/opt/georgeai`.

## ⚠️ This VPS is SHARED infrastructure

`gethub-traefik` (Traefik v2.11 + Let's Encrypt) and `gethub-postgres` serve
**other projects besides georgeai** — the box runs 20+ containers, several of
them named `*-georgeai-*` but belonging to unrelated projects (`wp-georgeai-*`,
`booking-georgeai-*`, `orbit-georgeai`, …). Never restart, reconfigure, or
upgrade the shared services for a georgeai.dev-only problem without confirming
with George first.

**Owned by georgeai.dev** (safe to restart, both defined in
`deploy/docker-compose.yml`):

| Container | What |
|---|---|
| `georgeai-web` | nginx at the edge, serves `site/`, proxies `/api/` |
| `georgeai-app` | Django (gunicorn), not routed by Traefik — reachable only from `georgeai-web` on the shared network |

Keeping nginx at the edge is deliberate: a broken backend deploy cannot take
the site down.

## Common operations

```bash
ssh macbook-air "docker ps"                                  # what's running
ssh macbook-air "docker logs --tail 50 georgeai-web"         # nginx logs
ssh macbook-air "docker logs --tail 50 georgeai-app"         # Django logs
ssh macbook-air "docker restart georgeai-web"                # safe to restart
ssh macbook-air "docker logs --tail 50 gethub-traefik"       # routing/TLS issues
```

## Routing

Traefik labels live in `deploy/docker-compose.yml`; cert resolver `letsencrypt`,
network `gethub_gethub-network`.

- **`georgeai.dev`** (apex) is the only host that serves content.
- **`www.georgeai.dev`** is routed and on the certificate *purely so it can
  redirect* — `georgeai-www-redirect` (a `redirectregex` middleware) 308s it to
  the apex with the path preserved. If www ever answers 200 again, that
  middleware or its routers were lost, and the site is back to a duplicate
  origin. `deploy.sh` fails the deploy on exactly that.
- Plain `http://www…` costs two hops: the shared Traefik entrypoint's global
  HTTPS redirect fires *before* router middlewares, so it lands on `https://www`
  first. Not fixable from this project's labels.

nginx per-location headers: `deploy/nginx.conf`. Note `absolute_redirect off` at
the top of the server block — Traefik terminates TLS and proxies over plain
`:80`, so without it nginx builds its own trailing-slash redirects as `http://`
and every slash-less URL takes a cleartext hop.

## Local port conventions (do not collide)

| Port | Purpose |
|------|---------|
| 5433 | n8n postgres tunnel (reserved — never rebind) |
| 5434 | georgeai postgres tunnel (see georgeai-backend skill) |
