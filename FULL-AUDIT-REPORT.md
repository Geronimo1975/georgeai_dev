# Full SEO Audit — georgeai.dev

Crawled live on **2026-08-26** (21 URLs from `sitemap.xml`, 100 % of the sitemap).
Raw HTML via `curl` (what crawlers see) + a headless Chromium render (what users see).
Lab measurements only — no CrUX/GSC/GA4 credentials and no backlink API were configured,
so field data and off-site authority are estimated, not measured.

## Executive summary

**SEO Health Score: 70 / 100**

| Category | Weight | Score |
|---|---|---|
| Technical SEO | 22 % | 80 |
| Content quality | 23 % | 58 |
| On-page SEO | 20 % | 72 |
| Schema / structured data | 10 % | 92 |
| Performance (CWV, lab) | 10 % | 62 |
| AI search readiness | 10 % | 65 |
| Images | 5 % | 45 |

**Business type:** B2B professional services / solo consultancy (AI automation + custom
software), Germany-based, worldwide delivery, remote — *not* a local brick-and-mortar
business, so GBP/maps signals were not audited.

### Top 5 critical issues
1. **The homepage ships 535 unrendered `{{ }}` placeholders and 10 `<h1>` elements** in the crawlable HTML. After JS it renders 2 `<h1>` and clean copy — but Googlebot's first pass and every AI crawler get the skeleton.
2. **7.8 MB homepage weight**, of which 5.7 MB is three unoptimised PNGs (`concept_smart_home.png` 2.3 MB, `SEO_AI.png` 1.7 MB, `medical_ai.png` 1.7 MB) at ~1376×768. On a real mobile connection this is the difference between a fast site and a slow one.
3. **All 15 service pages are thin** — 140 words on average, identical block structure ("What's included / How it works / Outcome / Stack"). They are template stubs competing for commercial keywords.
4. **No `hreflang` anywhere**, although the site serves 5 languages (en/de/fr/ro/ar) and `knowsLanguage` in the schema advertises them. Every language variant lives behind client-side switching at the same URL, so only English is indexable.
5. **No crawlable Impressum / About / Contact URL.** `/impressum`, `/about`, `/contact` all 404; legal text exists only inside the SPA. That is both an E-E-A-T gap and a § 5 DDG exposure ahead of the Stripe go-live.

### Top 5 quick wins
1. Convert the three hero PNGs to AVIF/WebP at display size → ~5.5 MB saved, one afternoon of work.
2. Fix the `{{ detail.img }}` 404 — a literal `https://georgeai.dev/%7B%7B%20detail.img%20%7D%7D` image request fires on every page load.
3. Give service pages real titles: `Automation — GeorgeAI` (21 chars) wastes the whole SERP line. 13 of 21 titles are under 30 characters.
4. Cross-link the 15 service pages to each other and to the 2 blog posts — each service page currently exposes only 5 internal links (home, services, blog, pricing, self).
5. Publish `/impressum/`, `/about/` and `/contact/` as static pages through the existing `pages/` deploy layer.

## Technical SEO — 80/100

Strong fundamentals; the weaknesses are all rendering- and internationalisation-shaped.

**Passing**
- HTTPS enforced; `http://` → `https://` and `www.` → apex both 301 in one hop.
- HSTS `max-age=31536000; includeSubDomains`, `X-Content-Type-Options`, `Referrer-Policy: strict-origin-when-cross-origin`, `X-Frame-Options`, `Permissions-Policy` all present.
- gzip on HTML, JS and CSS (homepage 154 KB → 47.7 KB).
- Correct 404 for unknown paths; trailing-slash normalisation 301s.
- Self-referencing canonical on all 21 URLs, `lang="en"` on all.
- `robots.txt` explicitly allows GPTBot, OAI-SearchBot, ClaudeBot, PerplexityBot, Google-Extended, Applebot-Extended, CCBot — best practice for a business selling GEO.
- `sitemap.xml` valid, 21 URLs, all 200, all in the sitemap are linked.

**Failing / at risk**
- **JS-dependent homepage.** Raw HTML = SPA skeleton + a 4.4 KB `<noscript>` block. Rendered text is 5.3 KB. Google will render it eventually; ChatGPT, Perplexity and Claude crawlers will not.
- **No `hreflang`.** 5 languages, one URL, zero annotations.
- **`sitemap.xml` gives every URL the same `lastmod`** (2026-08-26) including two blog posts written earlier — the signal is noise.
- **CSP is still report-only.** `unsafe-eval` + `unsafe-inline` are required by the export today; not a ranking factor, but it is a stated intention that has not shipped.
- No `/security.txt`, no `/humans.txt` (cosmetic).

## Content quality — 58/100

**The blog is genuinely good.** Both posts (1,220 and 1,023 words) lead with a sourced
statistic in the meta description, carry `BlogPosting` + `FAQPage` schema, 9 `<h2>`s
each, and cite external sources (Ahrefs, US Chamber). This is citation-ready content.

**Everything else is thin.**

| Page group | Count | Avg words | Verdict |
|---|---|---|---|
| Blog posts | 2 | 1,122 | Strong |
| Homepage (rendered) | 1 | 1,468 raw / ~800 real | Diluted by template noise |
| Pricing | 1 | 585 | Adequate |
| Service pages | 15 | **140** | **Thin — below any useful threshold** |
| Hub pages (`/services/`, `/blog/`) | 2 | 178 | Acceptable for hubs |

The 15 service pages share one template with four fixed headings and roughly 100 words
of unique copy each. They will not rank for "n8n automation agency" or "AI phone agent
Germany" at that depth, and they give AI engines almost nothing quotable.

**E-E-A-T:** Experience and identity signals are present in the schema (Person, jobTitle,
`knowsAbout`, an authored book on Amazon) but almost nowhere in crawlable prose. There is
no author bio page, no case study with a named client or a number, no Impressum URL.
Off-site entity presence is a single `sameAs` to GitHub — the LinkedIn profile linked in
the page body is not in `sameAs`.

**Duplicate content:** none. All 21 titles and all 21 meta descriptions are unique.

## On-page SEO — 72/100

**Titles**
- All unique, none truncated over 60 chars except two blog posts (98 and 73 chars — both will be cut in the SERP).
- **13 of 21 titles are under 30 characters** (`CRM — GeorgeAI`, `RAG — GeorgeAI`, `Django — GeorgeAI`). No keyword modifiers, no differentiation, no reason to click.

**Meta descriptions** — all present, all unique, 128–200 chars. Two exceed 160 and will be truncated. This is the strongest on-page area.

**Headings**
- 19 of 21 pages: exactly one `<h1>`, clean `<h2>`/`<h3>` hierarchy.
- Homepage raw HTML: **10 `<h1>`**, five of them literal `{{ t.pg.servicesTitle }}` style tokens. Renders down to 2 `<h1>` — still one too many.

**Internal linking** — the weakest structural element.

| Page | Unique internal links |
|---|---|
| Homepage | 21 |
| `/services/` | 20 |
| `/pricing/` | 12 |
| Blog posts | 6–8 |
| Each service page | **5** |

The 15 service pages are a flat spoke layer with no lateral links and no links into the
blog. Link equity arrives and stops. There is no hub-and-spoke topical structure despite
having exactly the content to build one.

## Schema & structured data — 92/100

The best-executed part of the site. All JSON-LD parses without error.

- Homepage `@graph`: `ProfessionalService` + `Person` + `Book` + `WebSite` + `WebPage`, correctly `@id`-linked (`founder` → `#george`, `worksFor` → `#organization`).
- Service pages: `Service` + `BreadcrumbList` + `WebPage`.
- Blog posts: `BlogPosting` + `BreadcrumbList` + `FAQPage`.
- Hubs: `Blog`, `CollectionPage` + `ItemList`.
- Pricing: `OfferCatalog`.

**Gaps:** `sameAs` lists only GitHub and Amazon — LinkedIn, WhatsApp and any profile,
directory or publication should be added, since `sameAs` is the primary entity-resolution
signal for both Google's Knowledge Graph and LLMs. No `aggregateRate`/`Review` (nothing to
cite), no `speakable`, no `Offer` with `price` on the individual `Service` nodes even
though `/pricing/` publishes fixed prices.

## Performance — 62/100 (lab)

Measured headless Chromium, unthrottled, from a fast connection — treat as a ceiling.

| Metric | Desktop | Verdict |
|---|---|---|
| TTFB | 129 ms | Excellent |
| FCP | 296 ms | Excellent |
| LCP | 404 ms | Excellent (lab) |
| CLS | 0.00 | Excellent |
| DOMContentLoaded | 271 ms | Excellent |
| Load | 1,574 ms | Good |
| **Total transferred** | **7.8 MB / 50 requests** | **Poor** |

The server and the critical path are fast. The payload is not: 5.9 MB of images plus a
1.6 MB hero video. LCP looks great in the lab precisely because throttling is absent —
on a 4G connection the same 2.3 MB PNG becomes the LCP element and the number collapses.

Also loaded: 31 `@font-face` declarations (Amiri Arabic, Inter, Plus Jakarta Sans,
Newsreader, JetBrains Mono), with Google Fonts fetched cross-origin on the service pages
while the homepage self-hosts. Two font strategies in one site.

`cache-control: no-cache, must-revalidate` is set on HTML — correct — but the same header
applies broadly; static assets should carry a long immutable max-age.

## Images — 45/100

| Issue | Detail |
|---|---|
| Oversized PNGs | `concept_smart_home.png` 2.3 MB, `SEO_AI.png` 1.7 MB, `medical_ai.png` 1.7 MB — all ~1376×768 photographs saved as PNG |
| No modern formats | Zero AVIF/WebP; no `<picture>`, no `srcset` |
| Broken request | `GET /%7B%7B%20detail.img%20%7D%7D` → 404 on every page load (unrendered `{{ detail.img }}` binding) |
| Alt text | **All 54 rendered images have alt text** — genuinely done well |
| OG image | `og-cover.jpg` 1200×630, 138 KB — correct dimensions, could be half the size |

Converting the three PNGs to AVIF at display width is worth roughly **5.5 MB**, a ~70 %
cut in total page weight, for no visual loss.

## AI search readiness — 65/100

Consistent with the separate `GEO-ANALYSIS.md` (61/100, 2026-08-24). Two days on, the
homepage still ships 535 `{{ }}` tokens.

**Excellent:** `llms.txt` is exemplary — structured, per-service, with URLs, stack lists
and engagement tiers. `robots.txt` explicitly welcomes every AI crawler. Blog posts carry
`FAQPage` and lead with sourced statistics, which is exactly what gets quoted.

**Blocking:** AI crawlers do not execute JavaScript. For the homepage they receive a
skeleton whose only real prose is the 4.4 KB `<noscript>` block. The service pages are
static and clean, but at 140 words each there is little to extract. Off-site brand
mentions — the dominant factor in LLM recall — are near zero.

## Sitemap & architecture

Valid, complete, 21/21 URLs return 200 and none are orphaned. Structure is
home → 2 hubs → 15 service spokes + 2 posts. Missing from the architecture entirely:
about/author page, contact page, Impressum, case studies, and any lateral links between
spokes.
