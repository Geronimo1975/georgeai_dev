# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Deployment pipeline + backend for **georgeai.dev**, George's portfolio site. The site's HTML is designed/exported elsewhere (a design tool producing a `.zip`); this repo unpacks it, ships it to a VPS, and serves it. It has two halves:

1. **Static pipeline** (`deploy.sh`, `site/`, `deploy/`) — currently live in production: nginx container behind the shared `gethub-traefik` (Traefik v2.11, Let's Encrypt) on VPS `85.215.69.83`.
2. **Django backend** (`backend/`) — serves the same export plus a session-auth API (`/api/auth/*`); intended to replace nginx (gunicorn is in requirements for that).

## Commands

### Deploy (static site)

```bash
./deploy.sh                        # unpack newest zip in exports/ → site/ → rsync to VPS → restart container → health checks
./deploy.sh exports/georgeai.zip   # specific archive
./deploy.sh --no-content           # redeploy current site/ without unpacking
```

Config env vars: `GEORGEAI_SSH_HOST` (default `macbook-air`, an ssh alias → `root@85.215.69.83`), `GEORGEAI_REMOTE_DIR` (default `/opt/georgeai`), `GEORGEAI_HOMEPAGE` (default `GeorgeAI.dc.html`), `GEORGEAI_TEMPLATE_DIR` (default `frontend/template`; set empty to skip mirroring).

### Django backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # venv lives at backend/.venv (gitignored)
pip install -r requirements.txt
cp .env.example .env                                # then fill SECRET_KEY / DATABASE_URL
python manage.py migrate
python manage.py runserver
python manage.py test accounts                      # run tests (single test: accounts.tests.ClassName.test_name)
```

**Database:** PostgreSQL in the shared `gethub-postgres` container on the VPS — no local DB. For local dev, tunnel on port **5434** (5433 is taken by the n8n tunnel):

```bash
IP=$(ssh macbook-air "docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' gethub-postgres")
ssh -N -L 5434:$IP:5432 macbook-air &
# DATABASE_URL=postgres://georgeai:PASSWORD@127.0.0.1:5434/georgeai
```

## Architecture

### Content flow

```
design tool export.zip → exports/ → deploy.sh → site/ (live web root)
                                              ↘ frontend/template/ (mirror for Django)
site/ → rsync → VPS:/opt/georgeai → nginx (georgeai-web) → Traefik → https://georgeai.dev
```

`deploy.sh` does non-obvious work during unpack — read it before changing anything about content handling:

- The export ships **no `index.html`**. The real homepage is `GeorgeAI.dc.html` (renders client-side from `support.js` + `services-data.js`, both refreshed every export). `GeorgeAI - Portfolio.html` is a **stale one-off "Bundled Page" snapshot** — never use it as the homepage.
- It injects `<script src="/auth.js" defer>` into `index.html` (idempotent). `auth.js` lives in `backend/assets/`, *not* in the export, so it survives re-exports.
- It applies the **SEO layer** from `seo/` (idempotent, runs even with `--no-content`): injects `seo/head.html` (title/meta/OG/JSON-LD, marker `seo:head`) before `</head>`, a crawlable footer link block (marker `seo:footer`) before `</body>`, sets `lang="en"` on `<html>`, and copies `robots.txt`, `sitemap.xml`, `llms.txt`, `favicon.svg` into `site/`. Edit SEO in `seo/`, never in `site/`.
- It then runs `seo/generate_service_pages.py`, which generates **static crawlable pages** — `/services/` hub + one page per service from `georgeai_services.json`, plus `/blog/` from the HTML-fragment posts in `blog/` (meta in a `<!--meta {json} -->` header: title, description, date, tags, faq) — and regenerates `sitemap.xml` with all URLs. Service names in the JSON must stay in sync with the design-tool export.
- `site/` and `frontend/template/` are **wiped and regenerated on every deploy** — never hand-edit files there; changes belong in the design tool, `deploy.sh`, or `backend/assets/`.

### Django backend (`backend/`)

- **Serving the export:** `backend/backend/views.py:serve_frontend` is a catch-all (last URL pattern) that maps any path to a file in `frontend/template/` and returns it **verbatim as a `FileResponse` — never through the Django template engine**. The exported HTML uses `{{ }}` placeholders rendered client-side by `support.js`, which collide with Django template syntax. Keep it that way.
- **Auth:** `accounts` app with a custom email-based `User` (`AUTH_USER_MODEL = accounts.User`, no username). DRF with **SessionAuthentication only** (JSON renderer only) at `/api/auth/{signup,login,logout,me}`. `serve_frontend` is decorated with `@ensure_csrf_cookie` so the SPA always gets a readable `csrftoken` that `auth.js` echoes back as `X-CSRFToken` — hence `CSRF_COOKIE_HTTPONLY = False` is intentional.
- **auth.js bridge** (`backend/assets/auth.js`): hooks the export's signin/signup modal *by structure* (input type + position, event delegation) because the export's form fields have no ids and are regenerated every deploy. It degrades gracefully when `/api/auth/*` is absent (the current nginx-only production).
- **Config:** everything via `backend/.env` (django-environ); no secrets in source. Settings live in `backend/backend/settings.py`.

### Other files

- `DESIGN-claude.md` — the site's design system (warm cream/coral/dark palette, `#cc785c` primary, serif display type). Reference it for any UI/styling work. For UI/UX work on this repo, always invoke the `ui-ux-pro-max` skill alongside it — it takes precedence on style/palette/typography decisions specific to this site, and `ui-ux-pro-max` fills in broader UX/component/accessibility guidance.
- `deploy/docker-compose.yml` + `deploy/nginx.conf` — the production nginx service, Traefik routing labels, and per-location headers. The compose file joins the external `gethub_gethub-network`. `nginx.conf` ships a `Content-Security-Policy-Report-Only` header (not yet enforced) — `unsafe-eval`/`unsafe-inline` are required because `support.js` runs Babel-transpiled JSX via `new Function(...)` for the generated-page feature and the design-tool export emits ~490 inline `style=""` attributes. To flip to enforced: check browser DevTools console on the live site for `Content-Security-Policy-Report-Only` violation reports across the homepage, a service page, `/blog/`, `/pricing/`, and any page using the generated-page/React feature; once clean, rename the header to `Content-Security-Policy` in all three `nginx.conf` `location` blocks.
- `Media/`, `georgeai_services.json`, `CPQ_prompt.md` — content assets/source data for the site.
