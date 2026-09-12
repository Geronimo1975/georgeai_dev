# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repo is

Deployment pipeline + backend for **georgeai.dev**, George's portfolio site. The site's HTML is designed/exported elsewhere (a design tool producing a `.zip`); this repo unpacks it, ships it to a VPS, and serves it. It has two halves:

1. **Static pipeline** (`deploy.sh`, `site/`, `deploy/`) — currently live in production: nginx container behind the shared `gethub-traefik` (Traefik v2.11, Let's Encrypt) on VPS `85.215.69.83`.
2. **Django backend** (`backend/`) — serves the same export plus a session-auth API (`/api/auth/*`); intended to replace nginx (gunicorn is in requirements for that).

Bolted onto the static half is a **payments/monitoring layer**: a repo-owned `/pricing/`
page of Stripe Payment Links, an n8n workflow that turns checkouts into orders, and
stdlib-only health checks (`tests/`, `cron/`, GitHub Actions) that guard that chain.

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

### Payments-pipeline checks (`tests/`, `cron/`)

Stdlib-only, read-only/side-effect-free health checks over the whole order chain
(live `/pricing/` page → Stripe Payment Links → n8n `stripe-orders` workflow +
`orders` data table). No pytest/deps required; `pytest tests/ -v` also works.

```bash
python3 tests/test_payments_pipeline.py     # standalone, exit 0/1 — what cron runs
./cron/check_payments.sh                    # same + logging to cron/logs/ (gitignored)
GEORGEAI_STRIPE_MODE=live python3 tests/test_payments_pipeline.py   # after go-live
```

Secrets (`STRIPE_TOKEN`, `N8N_API_KEY`) are read from the **repo-root `.env`**
(not `backend/.env`) and never printed. `EXPECTED_STRIPE_MODE` defaults to `test` —
the suite fails on purpose if the site is switched to live links without flipping it.
See `cron/README.md` for the crontab install and the pattern for adding a new suite.

### CI (`.github/workflows/`)

- `backend-ci.yml` — on push/PR touching `backend/**`: `pip-audit` + `migrate` +
  `python manage.py test accounts` against a Postgres 16 service container.
- `payments-pipeline.yml` — runs `tests/test_payments_pipeline.py` every 6h against
  **production**; needs the `STRIPE_TOKEN` / `N8N_API_KEY` repo secrets.

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
Everything the export itself does *not* contain is layered back on at deploy time, from
repo-owned source dirs, so it **survives every re-export**. All layers are idempotent and
all of them run even with `--no-content`:

| Layer | Source | What it does |
|---|---|---|
| `apply_assets` | `backend/assets/` | copies `auth.js` + `audit.js` into `site/`, injects `<script src="/auth.js" defer>` and `/audit.js` into `index.html` |
| `apply_seo` | `seo/` | see below |
| `apply_copy` | `seo/apply_content.py` + `seo/hero.json`, `seo/testimonials.json` | the export hard-codes marketing copy inside the design-tool HTML (hero strings in the `T()` table, testimonials in `services-data.js`), so a re-export silently reverts positioning or compliance work. The JSON is the source of truth and is re-applied here. Full replace, never an append — edit the JSON, never `site/` |
| `apply_legal` | `seo/apply_legal.py` + `seo/legal.json` | the export's `legal-data.js` carries `[bracketed]` Impressum placeholders (street, ZIP, VAT) and cites § 5 TMG, repealed by the DDG in 2024. Re-applies the real identity in all 5 languages. **Exits 2 and changes nothing while `seo/legal.json` is unfilled** — a placeholder Impressum is a § 5 DDG defect and blocks the Stripe go-live |
| `apply_brand` | `brand/apply_brand.py` | rewrites the export's hard-coded coral `#cc785c` into theme-aware WCAG-AA accents (`--accent` / `--accentBtn`), mutes decorative accents |
| `apply_images` | `images/apply_images.py` + `images/mock/` | the export leaves empty placeholder slots (diagonal-hatch `[ label ]` divs). Copies the committed on-brand SVG mockups into `site/assets/mock/` and rewrites the placeholders to `<img>`: the About portrait (`about.svg`), the 3 News cards (`news-{{ $index }}.svg`), and all 15 service-detail views (adds `img:` to `svcMeta`, binds `{{ detail.img }}`). Regenerate the SVGs with `python3 images/gen_mockups.py` after a palette change |
| `apply_pages` | `pages/` | copies repo-owned static pages (currently `pages/pricing/`) verbatim into `site/` |
| `apply_prune` | — | deletes junk the export ships into the web root: `uploads/` (carries `Resume EN.pdf` with a home address, a 17 MB unused video), `screenshots/` (62 design-tool QA captures), the `Portfolio.dc.html` / `Studio Site.dc.html` fictional-persona pages, the stale `GeorgeAI - Portfolio.html` snapshot, and `assets/hero.mp4` (replaced by `apply_hero`'s re-encode). Deliberately a **denylist**: a wrong allowlist takes the site down, an incomplete denylist only leaves junk. Warns about unrecognised new entries instead of deleting them |
| `apply_media` | — | remuxes export mp4s with `ffmpeg -c copy -movflags +faststart` (the design tool writes `moov` after `mdat`, so the hero video stalls until fully downloaded); skips already-faststarted files |
| `apply_hero` | `hero/` | copies `hero-motion.{css,js}` + `hero-cinema.{css,js}` into `site/` and injects the hero lede and cinema stage into `index.html` — autoplay, entrance choreography, pointer parallax, video backdrop. Kept out of the export because it has no classes and re-renders the hero subtree, so the JS hooks it by structure. Also swaps in `hero/assets/hero.mp4`, a 1280p re-encode at a quarter the export's 7.2 MB (runs after `apply_media`, so it wins). Idempotent per asset via the `hero:motion` / `hero-cinema` markers |
| `apply_widget` | `seo/inject_widget.py` + `backend/assets/audit.js` | injects the free-visibility-check lead widget — the only thing on the site that turns an anonymous visitor into a name. Runs **last**, so it also covers the service and blog pages generated by `apply_seo` and the static pages copied by `apply_pages` (20 pages at last deploy), not just the homepage. Skips a page that already has it |

The **SEO layer** injects `seo/head.html` (title/meta/OG/JSON-LD, marker `seo:head`) before `</head>`, a crawlable footer link block (marker `seo:footer`) before `</body>`, sets `lang="en"` on `<html>`, and copies `robots.txt`, `sitemap.xml`, `llms.txt`, `favicon.svg`, `responsive.css` into `site/`. Edit SEO in `seo/`, never in `site/`.
- It then runs `seo/generate_service_pages.py`, which generates **static crawlable pages** — `/services/` hub + one page per service from `georgeai_services.json`, plus `/blog/` from the HTML-fragment posts in `blog/` (meta in a `<!--meta {json} -->` header: title, description, date, tags, faq) — and regenerates `sitemap.xml` with all URLs. Service names in the JSON must stay in sync with the design-tool export.
- `site/` and `frontend/template/` are **wiped and regenerated on every deploy** — never hand-edit files there; changes belong in the design tool, `deploy.sh`, or `backend/assets/`.

#### Recovering `site/` (it is untracked build output)

Both dirs are **gitignored** — they are build output, and they reach the VPS by
rsync from the working tree, never via git. That means the working copy can be
the only copy, so treat `git clean -xfd` as destructive here.

Rebuild in this order:

1. **From an export** (correct path): drop the newest design-tool `.zip` in
   `exports/` and run `./deploy.sh`. It picks the newest by mtime
   (`ls -t exports/*.zip | head -1`).
2. **From git history** (fallback when no export exists):

   ```bash
   git restore --source=7f47afa --worktree -- site frontend/template
   ./deploy.sh --no-content     # re-applies every layer; all layers are idempotent
   ```

   `7f47afa` is the last commit that tracked these dirs, from just before they
   were untracked. Any commit at or before it works; `git log --oneline -- site`
   finds others. `--worktree` restores the files without re-staging them.

**Do not seed `exports/` from `~/Downloads`.** The `GeorgeAI.dev*.zip` files
there are from June 2026 and predate what is live — their `support.js` and
`services-data.js` are ~4 KB and ~18 KB smaller than the deployed copies, and no
layer touches those two files, so the gap is export age. A bare `./deploy.sh`
would unpack one and silently roll production back. Verify any candidate export
by comparing those two files against `site/` before deploying it.

### Django backend (`backend/`)

- **Serving the export:** `backend/backend/views.py:serve_frontend` is a catch-all (last URL pattern) that maps any path to a file in `frontend/template/` and returns it **verbatim as a `FileResponse` — never through the Django template engine**. The exported HTML uses `{{ }}` placeholders rendered client-side by `support.js`, which collide with Django template syntax. Keep it that way.
- **Auth:** `accounts` app with a custom email-based `User` (`AUTH_USER_MODEL = accounts.User`, no username). DRF with **SessionAuthentication only** (JSON renderer only) at `/api/auth/{signup,login,logout,me}`. `serve_frontend` is decorated with `@ensure_csrf_cookie` so the SPA always gets a readable `csrftoken` that `auth.js` echoes back as `X-CSRFToken` — hence `CSRF_COOKIE_HTTPONLY = False` is intentional.
- **auth.js bridge** (`backend/assets/auth.js`): hooks the export's signin/signup modal *by structure* (input type + position, event delegation) because the export's form fields have no ids and are regenerated every deploy. It degrades gracefully when `/api/auth/*` is absent (the current nginx-only production).
- **Config:** everything via `backend/.env` (django-environ); no secrets in source. Settings live in `backend/backend/settings.py`.

### Other files

- `DESIGN-claude.md` — describes the **design-tool export's** system (warm cream canvas, serif display, coral `#cc785c`). None of that is live. The live palette is corporate B2B — near-black canvas `#02060a`, accent `#fb5e31` (dark) / `#b23c0a` (light), near-black `#02060a` button labels, single-family Plus Jakarta Sans — and its **source of truth is `brand/palette.json`**, applied by `brand/apply_brand.py` at deploy time. See the "Production override" note at the top of the `DESIGN-claude.md` body. Reference it for any UI/styling work. For UI/UX work on this repo, always invoke the `ui-ux-pro-max` skill alongside it — it takes precedence on style/palette/typography decisions specific to this site, and `ui-ux-pro-max` fills in broader UX/component/accessibility guidance.
- `deploy/docker-compose.yml` + `deploy/nginx.conf` — the production nginx service, Traefik routing labels, and per-location headers. The compose file joins the external `gethub_gethub-network`. `nginx.conf` ships a `Content-Security-Policy-Report-Only` header (not yet enforced) — `unsafe-eval`/`unsafe-inline` are required because `support.js` runs Babel-transpiled JSX via `new Function(...)` for the generated-page feature and the design-tool export emits ~490 inline `style=""` attributes. To flip to enforced: check browser DevTools console on the live site for `Content-Security-Policy-Report-Only` violation reports across the homepage, a service page, `/blog/`, `/pricing/`, and any page using the generated-page/React feature; once clean, rename the header to `Content-Security-Policy` in all three `nginx.conf` `location` blocks.
- `Media/`, `georgeai_services.json`, `CPQ_prompt.md` — content assets/source data for the site.

### Payments / lead capture

The money path is **not** in this codebase's runtime — it's Stripe Payment Links on a
static page, wired to n8n:

```
pages/pricing/index.html  ──7 buy buttons (data-product slug)──▶  Stripe Payment Link
                                                                        │ checkout.session.completed
  n8n `stripe-orders` workflow (app.n8n-studio.com) ◀─────webhook───────┘
                    └──▶ `orders` data table + confirmation email
```

- Each Payment Link and product carries `metadata.data_product = <slug>`; that's how n8n
  maps an event back to a product. IDs/URLs/prices: `docs/stripe-payment-links.md`;
  workflow export: `docs/n8n-stripe-orders.json`.
- **Still Stripe TEST mode** (`acct_1TIuuYEffkWmXH1r`, get-hub Sandbox). Go-live means:
  recreate the links in live mode, swap the URLs in `pages/pricing/index.html`, redeploy,
  and set `GEORGEAI_STRIPE_MODE=live` in the crontab.
- Prices live in three places that must stay in sync: `pages/pricing/index.html`, Stripe,
  and the `CATALOG` dict in `tests/test_payments_pipeline.py` — the test suite exists to
  catch exactly that drift, so update it alongside any price change.
- `backend/assets/audit.js` — the free-visibility-audit floating CTA + lead modal. Posts to
  an n8n webhook that audits the submitted URL and emails a report.
- n8n work for this project goes to **`app.n8n-studio.com`** (George's own VPS), not
  `n8n.rotocon.world` — see the `georgeai-n8n` skill.

### Project skills

`.claude/skills/` holds task-scoped playbooks that go deeper than this file — prefer them
over rediscovering: `georgeai-deploy`, `georgeai-backend`, `georgeai-seo`, `georgeai-vps`,
`georgeai-n8n`.
