---
name: georgeai-deploy
description: Deploy georgeai.dev to the VPS. Use when the user asks to deploy, redeploy, ship the site, publish a new export, or when a new .zip lands in exports/.
---

# Deploying georgeai.dev

Everything goes through `deploy.sh` — never rsync or edit `site/` by hand.

```bash
./deploy.sh                        # newest zip in exports/ → site/ → VPS → restart → health checks
./deploy.sh exports/georgeai.zip   # specific archive
./deploy.sh --no-content           # redeploy current site/ (still re-applies SEO layer)
```

Config env vars (defaults in parentheses): `GEORGEAI_SSH_HOST` (`macbook-air`),
`GEORGEAI_REMOTE_DIR` (`/opt/georgeai`), `GEORGEAI_HOMEPAGE` (`GeorgeAI.dc.html`),
`GEORGEAI_TEMPLATE_DIR` (`frontend/template`, empty = skip mirroring).

## Hard rules

- **Never** use `GeorgeAI - Portfolio.html` as homepage — it is a stale one-off
  snapshot. The real homepage is `GeorgeAI.dc.html` (renders client-side from
  `support.js` + `services-data.js`).
- `site/` and `frontend/template/` are **wiped every deploy**. Changes belong in
  the design tool, `deploy.sh`, `seo/`, or `backend/assets/`.
- `auth.js` is injected by deploy.sh from `backend/assets/` — it is not part of
  the export and must survive re-exports.
- SEO edits go in `seo/` (see the georgeai-seo skill), never in `site/`.

## Verify after deploy

deploy.sh runs health checks itself; to double-check:

```bash
curl -sI https://georgeai.dev | head -5
ssh macbook-air "docker logs --tail 20 georgeai-web"
```
