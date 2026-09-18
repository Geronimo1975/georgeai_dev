# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Deployment pipeline + backend for **georgeai.dev**, George's portfolio/sales site. The HTML is designed and exported elsewhere (a design tool producing a `.zip`); this repo unpacks it, repairs and augments it, ships it to a VPS, and serves it. Two halves:

1. **Static pipeline** (`deploy.sh`, `site/`, `deploy/`, `seo/`, `brand/`, `pages/`) — live in production: an `nginx:1.27-alpine` container (`georgeai-web`) serving `./site` read-only, behind the shared `gethub-traefik` (Traefik v2.11, cert resolver `letsencrypt`, external network `gethub_gethub-network`) on VPS `85.215.69.83`. No build step.
2. **Django backend** (`backend/`) — serves the same export plus a session-auth API (`/api/auth/*`); intended to replace nginx. **Not currently routed in production**: `deploy/nginx.conf` has no `proxy_pass`, so `/api/auth/*` 404s on the live site and `auth.js` degrades gracefully.

## Commands

### Deploy (static site)

```bash
./deploy.sh                        # unpack newest zip in exports/ → site/ → apply layers → rsync → container → health checks
./deploy.sh exports/georgeai.zip   # specific archive
./deploy.sh --no-content           # re-apply layers to the current site/ and redeploy, without unpacking a zip
```

`exports/` is usually empty (zips are gitignored), so `--no-content` is the normal command for anything that is not a fresh design export.

Config env vars: `GEORGEAI_SSH_HOST`, `GEORGEAI_REMOTE_DIR` (default `/opt/georgeai`), `GEORGEAI_HOMEPAGE` (default `GeorgeAI.dc.html`), `GEORGEAI_TEMPLATE_DIR` (default `frontend/template`; set empty to skip mirroring).

**`GEORGEAI_SSH_HOST` default is stale.** `deploy.sh` defaults to `macbook-air`, which no longer resolves; `~/.ssh/config` defines **`macmini`** → `root@85.215.69.83`. Deploy with:

```bash
GEORGEAI_SSH_HOST=macmini ./deploy.sh --no-content
```

`README.md` and `AGENTS.md` repeat the same stale alias (and `AGENTS.md` references a non-existent `DESIGN-AGENTS.md`).

### Django backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # venv lives at backend/.venv (gitignored)
pip install -r requirements.txt
cp .env.example .env                                # then fill SECRET_KEY / DATABASE_URL
python manage.py migrate
python manage.py runserver
python manage.py test accounts                      # 6 tests in backend/accounts/tests.py
python manage.py test accounts.tests.ClassName.test_name   # single test
```

There is no linter, formatter or pre-commit config in the repo; Django's test runner is the only test tooling.

**Database:** PostgreSQL in the shared `gethub-postgres` container on the VPS — no local DB. For local dev, tunnel on port **5434** (5433 is taken by the n8n tunnel):

```bash
IP=$(ssh macmini "docker inspect -f '{{range .NetworkSettings.Networks}}{{.IPAddress}}{{end}}' gethub-postgres")
ssh -N -L 5434:$IP:5432 macmini &
# DATABASE_URL=postgres://georgeai:PASSWORD@127.0.0.1:5434/georgeai
```

## Architecture

### The layer model — the thing to understand first

`site/` is **generated output, never a source**. It is wiped and rebuilt from the export on every full deploy. The repo's real work is eight small, **idempotent** layers that `deploy.sh` re-applies in this fixed order on *every* deploy, including `--no-content`:

| Order | Layer | Source of truth | Owns |
|---|---|---|---|
| 1 | `apply_assets` | `backend/assets/` | `auth.js`, `audit.js` — JS kept out of the export so it survives re-exports |
| 2 | `apply_seo` | `seo/` | copies `robots.txt`/`sitemap.xml`/`llms.txt`/icons/`responsive.css`; injects `seo/head.html` (marker `seo:head`) and `seo/noscript.html`; adds the crawlable footer block (`seo:footer`); then runs `seo/generate_service_pages.py` |
| 3 | `apply_copy` | `seo/*.json` + `seo/apply_content.py` | marketing copy and structural repairs inside the export (hero, testimonials, Impressum, contact page, portfolio links, brand mark) |
| 4 | `apply_brand` | `brand/apply_brand.py` | the entire accent palette |
| 5 | `apply_pages` | `pages/` | hand-written static pages copied in verbatim (currently `/pricing/`) |
| 6 | `apply_prune` | `deploy.sh` (denylist) | deletes export junk — `Portfolio.dc.html`, `Studio Site.dc.html`, `GeorgeAI - Portfolio.html`, `.thumbnail`. Deliberately a denylist, not an allowlist, plus an "unexpected files" warning |
| 7 | `apply_media` | `deploy.sh` | remuxes exported mp4s with `+faststart` (the export puts `moov` after `mdat`, so the hero video stutters on first load) |
| 8 | `apply_widget` | `seo/inject_widget.py` | lead-capture widget on every page — runs last so it also covers generated and copied pages |

**The rule this implies:** never hand-edit `site/` or `frontend/template/`. To change something, find the layer that owns it. If no layer owns it yet, add a patcher to the right layer — that is how everything here survives a re-export. Each patcher raises loudly (`PatchError`) when the export changes shape, rather than silently no-op'ing.

### The `index.html` trap

The served homepage is `site/index.html`, which `deploy.sh` creates by **copying** `$GEORGEAI_HOMEPAGE` (`GeorgeAI.dc.html`) — but only `if [ ! -f site/index.html ]`, i.e. only after a full export unpack wipes `site/`.

Consequences, both of which have caused real drift:

- Editing `site/GeorgeAI.dc.html` does **not** reach the served homepage on a `--no-content` deploy. `index.html` stays as it was.
- Editing either file is lost entirely on the next full export.

So homepage changes belong in `seo/apply_content.py` (or `brand/apply_brand.py` for colour), which run on both files on every deploy. Verify against `site/index.html`, not `GeorgeAI.dc.html`.

### Export quirks

- The export ships **no `index.html`**. The real homepage is `GeorgeAI.dc.html`, which renders client-side from `support.js` + `services-data.js` (both refreshed every export). `GeorgeAI - Portfolio.html` is a stale one-off "Bundled Page" snapshot — never use it as the homepage.
- The export hard-codes marketing copy in a `T()` translation table (5 languages: en, de, fr, ro, ar) and testimonials in `services-data.js`, so a re-export reverts positioning and compliance work. Hence layer 3.
- Fonts are vendored in `seo/vendor/` and served from `/assets/fonts.css` specifically so no visitor IP reaches `fonts.googleapis.com`/`fonts.gstatic.com`. Keep it that way — don't add a Google Fonts `<link>`.

### Generated static pages

`seo/generate_service_pages.py` builds real crawlable URLs (English only; the SPA handles i18n at runtime) and regenerates `sitemap.xml` with every URL:

- `/services/` hub + one page per service from `georgeai_services.json`
- `/work/` hub + one page per project from `georgeai_work.json`, cross-linked to the matching service page
- `/blog/` from HTML fragments in `blog/` (metadata in a leading `<!--meta {json} -->` header: title, description, date, tags, faq)

Service and project names in those JSON files must stay in sync with the design-tool export. Slugs come from `slugify()`; `seo/apply_content.py` hard-codes the same slug lists to wire the homepage to `/work/<slug>/`, so changing a name means changing both.

### Brand palette

Owned entirely by `brand/apply_brand.py`, which rewrites the export's hard-coded Anthropic coral `#cc785c`. Change the shade there — never in `site/`. It is a deliberate **two-tier** system, because one shade cannot be both vivid and legible:

- `ACCENT_NEON` `#ff5c39` — the brand voltage: large surfaces, CTA band, logo, hero beams, dark-theme text. 5.84:1 on the dark canvas, 6.01:1 under ink labels. **Fails** for small text on cream (2.91:1) and under white labels (3.07:1).
- `ACCENT_TEXT` `#df2700` — the darkened companion for exactly those two cases: small text on cream (4.50:1) and button fills under white labels (4.74:1).

So: white text never goes on the neon (use ink `#141413`, or switch the fill to the companion). The logo follows the same split — `seo/logo-mark.png` (neon) on dark surfaces, `seo/logo-mark-ink.png` (companion) on cream, with the SPA header swapping via a `markSrc` value injected into the render context.

### Django backend (`backend/`)

- **Serving the export:** `backend/backend/views.py:serve_frontend` is a catch-all (last URL pattern) mapping any path to a file in `frontend/template/`, returned **verbatim as a `FileResponse` — never through the Django template engine**. The exported HTML uses `{{ }}` placeholders rendered client-side by `support.js`, which collide with Django template syntax. Keep it that way.
- **Auth:** `accounts` app with a custom email-based `User` (`AUTH_USER_MODEL = accounts.User`, no username). DRF with **SessionAuthentication only** (JSON renderer only) at `/api/auth/{signup,login,logout,me}`. `serve_frontend` is decorated with `@ensure_csrf_cookie` so the SPA always gets a readable `csrftoken` that `auth.js` echoes back as `X-CSRFToken` — hence `CSRF_COOKIE_HTTPONLY = False` is intentional.
- **auth.js bridge** (`backend/assets/auth.js`): hooks the export's signin/signup modal *by structure* (input type + position, event delegation), because the export's form fields have no ids and are regenerated every deploy.
- **Config:** everything via `backend/.env` (django-environ); no secrets in source. Settings in `backend/backend/settings.py`.

### Design and product context

- `DESIGN.md` — **ground truth** for implementation: the exact tokens shipped in the export (both themes, real fonts Newsreader/Inter/JetBrains Mono, breakpoints `isMobile` <860px and `isNarrow` <560px, component inventory).
- `DESIGN-claude.md` — the Claude.com system this identity was adapted from. Aesthetic reference only; its fonts (Copernicus/StyreneB) and token values are **not** what ships.
- `PRODUCT.md` — register, users, positioning, anti-references, accessibility target (WCAG AA).

For UI/UX work, reference `DESIGN.md` first; the project also asks for the `ui-ux-pro-max` skill alongside it when that skill is available.

### Other files

- `deploy/docker-compose.yml` + `deploy/nginx.conf` — the nginx service, Traefik routing labels, per-location headers. Compose defines **only** `georgeai-web`, and `deploy.sh` runs `docker compose up -d --remove-orphans`, so any container on the VPS not in that file gets removed on deploy.
- `nginx.conf` ships `Content-Security-Policy-Report-Only` (not enforced). `unsafe-eval`/`unsafe-inline` are required because `support.js` runs Babel-transpiled JSX via `new Function(...)` and the export emits ~490 inline `style=""` attributes. To enforce: check DevTools for report-only violations across the homepage, a service page, `/blog/`, `/pricing/` and any generated-page/React feature, then rename the header in all three `location` blocks.
- `Media/`, `georgeai_services.json`, `georgeai_work.json`, `CPQ_prompt.md` — content assets and source data.

## Operational notes

**When `ssh`/`rsync` to the VPS fails with `Connection closed by 85.215.69.83 port 22`,** it is almost certainly not your key or a ban on your IP. The host is under continuous SSH brute-force scanning; `sshd` drops *new unauthenticated* connections at random once its `MaxStartups` queue fills, and a deploy opens ~7 ssh/rsync invocations. Mitigations already in place:

- `~/.ssh/config` enables `ControlMaster`/`ControlPersist` for `macmini`, so a whole deploy reuses one authenticated connection and only the first has to win the race.
- `deploy.sh` retries that first connection 5 times. `ssh`'s own `ConnectionAttempts` does *not* help, because the TCP connection is accepted and then closed.
- `fail2ban` on the VPS bans the sources (jail `ssh`). It was dead for two weeks because the `plesk-horde` jail pointed at a missing logpath, and fail2ban refuses to start if any enabled jail's log is absent — check `systemctl is-active fail2ban` and `fail2ban-client status ssh` before blaming anything else.

Still open on the VPS: `PasswordAuthentication` is `yes` (root is key-only, so root cannot be brute-forced, but the volume persists), and a staged-but-unapplied `/etc/ssh/sshd_config.d/10-maxstartups.conf` raising `MaxStartups` to `30:50:200` awaits an `sshd -t && systemctl reload ssh`.
