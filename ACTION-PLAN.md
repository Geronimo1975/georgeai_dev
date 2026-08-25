# georgeai.dev — SEO Action Plan

> **Status 2026-08-25:** C1, H3 and H6 are **done and live** (deployed via `./deploy.sh --no-content`). Verified below.

Prioritised from the 2026-08-25 audit (score 71/100). Every fix below belongs in a **repo-owned source dir**, never in `site/` — that directory is wiped on each deploy.

---

## Critical — do first

*(nothing blocks indexing outright; the redirect defect is the closest thing)*

### ~~C1. Stop redirects downgrading to `http://`~~ ✅ DONE
`/services/crm` → `Location: http://georgeai.dev/services/crm/` → 308 back to HTTPS. Two hops, first one plaintext.
**Where:** `deploy/nginx.conf` — add `absolute_redirect off;` (or `port_in_redirect off;` + `server_name_in_redirect off;`) in the server block so nginx emits relative redirects behind Traefik's TLS termination.
**Done:** `absolute_redirect off; server_name_in_redirect off; port_in_redirect off;` in `deploy/nginx.conf`.
**Verified:** `location: /services/crm/` (relative) — 1 hop, no cleartext leg.

---

## High — within one week

### H1. Rewrite the 15 service page titles
Currently `CRM — GeorgeAI` (14 chars). Target 50–60 chars with intent + qualifier.
| Now | Proposed |
|---|---|
| `CRM — GeorgeAI` | `Custom CRM Development for SMBs — Django & n8n \| GeorgeAI` |
| `RAG — GeorgeAI` | `RAG Systems: Ground Your AI in Your Own Documents \| GeorgeAI` |
| `Automation — GeorgeAI` | `n8n Workflow Automation for Small Business \| GeorgeAI` |
| `Django — GeorgeAI` | `Django Development — Dashboards, Portals & APIs \| GeorgeAI` |
**Where:** `seo/generate_service_pages.py` + `georgeai_services.json`. **Effort:** 1–2 h.

### H2. Fix the homepage heading structure
Nine `{{ … }}` H1s and ~20 placeholder H2s reach crawlers verbatim; one H1 contains a leaked build comment.
**Fix:** demote the non-active SPA view headings from `<h1>` to `<h2>`/`<div role="heading">` in the export template handling, so exactly one H1 is served. Move the build comment outside the `<h1>`.
**Where:** `hero/` injection + `seo/apply_content.py`. **Effort:** 2–4 h. Highest-leverage GEO fix on the site.

### H3. ~~301 `www` → apex~~ ✅ DONE · `/index.html` → `/` still open
**Done:** `georgeai-www-redirect` (Traefik `redirectregex`) plus dedicated `georgeai-www` / `georgeai-www-http` routers in `deploy/docker-compose.yml`; the apex routers no longer match the www host.
**Verified:** `https://www.georgeai.dev/services/crm/` → `308 → https://georgeai.dev/services/crm/` (path preserved). `deploy.sh` now asserts this redirect instead of expecting a 200.
**Still open:** `/index.html` returns 200 as a duplicate of `/` — add an nginx `location = /index.html { return 301 /; }`.

### H4. Thicken the four revenue service pages
`automation`, `ai-phone-calls`, `ai-chatbot`, `seo-aio-geo` — 128–156 words each today. Take each to 600–900 words: a worked before/after example with real numbers, a cost/timeline block, one FAQ pair (with `FAQPage` schema), one image.
**Where:** `georgeai_services.json` schema extension + `seo/generate_service_pages.py`. **Effort:** 1 day for the four. Then repeat for the remaining 11.

### H5. Cross-link the service pages
Each of the 15 has 10 internal links and all are chrome. Add a "Related services" block (2–3 siblings) and a link to the relevant blog post.
**Where:** `seo/generate_service_pages.py` — derive siblings from the category grouping already in `georgeai_services.json`. **Effort:** 2 h.

### ~~H6. Shrink the OG image~~ ✅ DONE
**Done:** `seo/assets/og-cover.jpg` — the same artwork cropped to exactly 1200×630 at **137 KB** (13× smaller). `apply_seo` now copies `seo/assets/` into `site/assets/`, so it survives a re-export. All 21 pages repointed, plus `og:image:type/width/height/alt`.
**Note:** `SEO_AI.png` stays in the web root — the export uses it as the "AI SEO Automation System" featured-project image, so it is *not* dead weight to prune, though at 1.79 MB in-page it is worth re-encoding separately.
**Still open:** per-page OG variants (all 21 shares still look identical).

---

## Medium — within one month

### M1. Cache static assets properly
All JS/CSS ship `no-cache, must-revalidate`. Give hashed/versioned assets `public, max-age=31536000, immutable`; keep HTML at `no-cache`.
**Where:** `deploy/nginx.conf` location blocks. **Effort:** 30 min.

### M2. Add `FAQPage` schema to the homepage
The FAQ section already renders; the markup is absent. Same for `Review`/`AggregateRating` on the testimonials block.
**Where:** `seo/head.html` or a new `seo/` JSON-LD injector, sourced from `seo/testimonials.json`. **Effort:** 2 h.

### M3. Give About / Contact / News real URLs
`/about`, `/contact`, `/news` all 404 — that content is JS-only. Generate static `/about/` and `/contact/` pages (the generator already does this shape for services) with `AboutPage` / `ContactPage` schema, and link them from the footer. Directly improves E-E-A-T and AI citability.
**Where:** `seo/generate_service_pages.py` (extend) + `pages/`. **Effort:** half a day.

### M4. Self-host fonts on service and blog pages
They pull `fonts.googleapis.com` while the homepage uses `/assets/fonts.css`. Extra RTT plus a GDPR exposure for a Germany-based business (Google Fonts hotlinking has been litigated there).
**Where:** `seo/generate_service_pages.py` template head. **Effort:** 30 min.

### M5. Expose per-package `Offer` on `/pricing/`
`OfferCatalog` is present but carries no `price`/`priceCurrency`, while the page states from €299.
**Where:** `pages/pricing/index.html`. Keep in sync with Stripe and `tests/test_payments_pipeline.py`'s `CATALOG`. **Effort:** 1 h.

### M6. Measure real Core Web Vitals
No field data exists. Verify the property in Search Console, then run PSI on `/` and `/services/automation/`. Re-score Performance once there are numbers.
**Effort:** 1 h.

### M7. Decide the multilingual story
The site advertises 5 languages and ships `data-i18n`, but there is one `lang="en"` document and no `hreflang`. Either publish language URLs with proper `hreflang`, or stop advertising the languages as a site feature.
**Effort:** scoping decision first.

---

## Low — backlog

- **L1.** Trim the 98-char blog title to ~60 for SERP display.
- **L2.** Delete unused heavy images from the web root: `concept_smart_home.png` (2.37 MB), `medical_ai.png` (1.71 MB) — add to `apply_prune`'s denylist.
- **L3.** Enable brotli alongside gzip in nginx.
- **L4.** Publish more than 2 blog posts — the two that exist are good and both carry `FAQPage`; the format works.
- **L5.** Add `dateModified` to service pages so answer engines can judge freshness.
- **L6.** Before flipping CSP to enforced, note `script-src` lacks `'unsafe-inline'` while the homepage has 2 inline scripts — it will break today. Hash or nonce them first.
