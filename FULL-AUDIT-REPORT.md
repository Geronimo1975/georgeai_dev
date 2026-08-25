# georgeai.dev — Full SEO Audit

**Audited:** 2026-08-25 · **Updated 2026-08-25 after remediation:** the redirect downgrade, the www duplicate origin and the oversized OG image are fixed and live; Technical re-scores 80 → 88, Images 70 → 80, overall **71 → 73**.

**Audited:** 2026-08-25 · **Pages crawled:** 21 (complete sitemap) · **Method:** live HTTP crawl of production (nginx/1.27.5, 85.215.69.83) + inspection of the repo build layers.

---

## Executive Summary

**SEO Health Score: 71 / 100**

| Category | Weight | Score | Weighted |
|---|---|---|---|
| Technical SEO | 22% | 80 | 17.6 |
| Content Quality | 23% | 55 | 12.7 |
| On-Page SEO | 20% | 65 | 13.0 |
| Schema / Structured Data | 10% | 85 | 8.5 |
| Performance (CWV) | 10% | 75* | 7.5 |
| AI Search Readiness | 10% | 78 | 7.8 |
| Images | 5% | 70 | 3.5 |
| **Total** | | | **70.6 → 71** |

\* Lab-estimated from transfer sizes and TTFB. No Lighthouse binary and no CrUX/GSC credentials on this machine, so no field CWV data — see *Performance*.

**Business type:** B2B professional service / solo consultancy (AI automation + software), Germany-based, remote delivery EU-wide. Not a local brick-and-mortar business — `LocalBusiness`/GBP work is **not** the priority here, `ProfessionalService` + `Person` (already present) is the correct model.

### Top 5 critical / high issues
1. **15 service pages are thin content** (128–156 words each) — 71% of the indexable site is below the threshold where a page can rank for anything competitive.
2. **Trailing-slash redirects downgrade to `http://`** — `/services/crm` → `Location: http://georgeai.dev/services/crm/`, which then 308s back to HTTPS. Two hops, one of them plaintext.
3. **The homepage ships 9 unrendered `{{ … }}` H1s and ~20 placeholder H2s** to any crawler that doesn't execute JS — which is most AI answer-engine crawlers. On a site that sells GEO.
4. **About / Contact / News / Configurator have no crawlable URLs** (`/about` → 404). That content only exists as JS view-switches inside `/`.
5. **`www.georgeai.dev` serves a full 200** with identical bytes instead of redirecting to the apex.

### Top 5 quick wins
1. Fix the nginx redirect to be protocol-relative or `https://` (one line).
2. 301 `www` → apex, and `/index.html` → `/`.
3. Compress the OG image — `SEO_AI.png` is **1.79 MB**; LinkedIn and WhatsApp routinely skip previews over ~1 MB, so social shares currently render blank.
4. Add `FAQPage` schema to the homepage — the FAQ block already exists, the markup doesn't.
5. Serve the self-hosted fonts on service pages too; they currently pull Google Fonts (extra RTT, and a GDPR exposure for a Germany-based business).

---

## Technical SEO — 80/100

**Working well**
- HSTS `max-age=31536000; includeSubDomains`, `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy`, `Permissions-Policy` all present.
- `http://` → `https://` 308 at the edge.
- Canonicals correct and self-referential on all 21 pages.
- `robots.txt` clean, explicit AI-crawler allowlist, sitemap declared.
- `sitemap.xml` valid, 21 URLs, all return 200, `lastmod` current.
- gzip active on HTML/JS/CSS (homepage 154 KB → 46.5 KB).
- 404s return a real 404.

**Issues**
| Issue | Evidence | Severity |
|---|---|---|
| ~~Redirect protocol downgrade~~ | **FIXED** — `absolute_redirect off` in `deploy/nginx.conf`; now `location: /services/crm/` | ~~High~~ |
| ~~`www` not redirected~~ | **FIXED** — Traefik `georgeai-www-redirect`; now 308 → apex, path preserved | ~~High~~ |
| `/index.html` returns 200 | duplicate of `/`; canonical mitigates but doesn't remove the crawl path | Medium |
| Static assets sent `no-cache, must-revalidate` | `support.js` (58 KB), `services-data.js` (73 KB), `hero-cinema.js` (45 KB), `legal-data.js` (27 KB) all revalidate every visit | Medium |
| No brotli | only `content-encoding: gzip` offered | Low |
| CSP still report-only | `script-src` has `'unsafe-eval'` but **no** `'unsafe-inline'`, while the homepage has 2 inline scripts — flipping to enforced today would break the page | Medium |
| No `hreflang` | site advertises 5 languages and ships `data-i18n`, but there is one `lang="en"` document and no language URLs | Medium |

---

## Content Quality — 55/100

**The core problem.** 15 of 21 indexable pages are service stubs of 128–156 words. Sample (`/services/crm/`, 136 words) is: heading, one-line promise, 3 bullets "What's included", 3 bullets "How it works", one outcome line, 4 stack chips, CTA. There is no depth, no example, no pricing anchor, no client evidence, no FAQ.

- Word counts: homepage 1,460 · blog posts 1,220 and 1,023 · `/pricing/` 585 · `/services/` hub 210 · `/blog/` hub 146 · **the 15 service pages 128–156**.
- The 15 stubs share an identical template and section structure — near-duplicate skeletons distinguished only by a paragraph of copy.
- **E-E-A-T is strong where it exists**: named author with 8+ years stated, a published book (`Book` schema, Amazon link), GitHub and LinkedIn `sameAs`, phone, email, country. The blog posts cite dated sources (Ahrefs 2025, US Chamber). This is genuinely above average — it just isn't present on the 15 pages that need it.
- `/blog/` has only 2 posts. Both are good. That's the whole content programme.

**Recommendation:** service pages need to reach 600–900 words with a worked example, a "what this costs / how long" block, one FAQ pair, and links to the 2–3 sibling services and the relevant blog post. Prioritise the four that map to actual revenue: `automation`, `ai-phone-calls`, `ai-chatbot`, `seo-aio-geo`.

---

## On-Page SEO — 65/100

**Titles**
- Homepage (57), `/services/` (65), blog posts (98 and 73) — good, keyword-bearing.
- **The 15 service titles are bare labels**: `CRM — GeorgeAI` (14 chars), `RAG — GeorgeAI` (14), `Django — GeorgeAI` (17), `Automation — GeorgeAI` (21). None carry an intent qualifier or a location. Nobody searches "CRM"; they search "custom CRM development Germany". 40–50 characters of title real estate are being thrown away on every one.
- The 98-char blog title will truncate in SERPs (~60 char display limit).

**Meta descriptions** — consistently 128–200 chars, written, distinct, benefit-first. This is the strongest on-page dimension. `/pricing/` at 200 chars will truncate slightly.

**Headings**
- Service pages, blog posts, `/pricing/`, hubs: clean single-H1, sane H2 nesting.
- **Homepage: 14 `<h1>` elements.** One is real ("The enquiry you miss on a Saturday still ends up in your calendar."); nine are unrendered SPA placeholders (`{{ t.hero.title }}`, `{{ about.title }}`, `{{ ct.title }}`, `{{ news.title }}`, `{{ cfg.title }}`, `{{ legalCur.title }}`, …); one contains a leaked HTML build comment as heading text. 521 `{{ }}` tokens total in the served HTML.
- Homepage H3 count is 16 with no H4s — flat.

**Internal linking**
- Every service page carries exactly 10 internal links, and they are all navigation: `/`, `/services/`, `/pricing/`, `/blog/`. **Zero contextual links between sibling services, and zero links from services to the blog posts that support them.** The 15 pages form 15 disconnected leaves.
- The homepage links all 15 services (good) but nothing links *back* laterally.
- `/blog/` hub: 9 internal links for 2 posts.

---

## Schema & Structured Data — 85/100

Strongest area. All JSON-LD parses without error.

| Page type | Types present |
|---|---|
| Homepage | `ProfessionalService`, `Person`, `Book`, `WebSite`, `WebPage` |
| `/services/` | `CollectionPage`, `ItemList`, `BreadcrumbList` |
| Service pages (15) | `Service`, `BreadcrumbList`, `WebPage` |
| `/blog/` | `Blog`, `BreadcrumbList` |
| Blog posts (2) | `BlogPosting`, `BreadcrumbList`, `FAQPage` |
| `/pricing/` | `WebPage`, `OfferCatalog` |

**Gaps**
- Homepage renders a visible FAQ section (`{{ faqT.title }}`) with **no `FAQPage` markup** — a free rich-result and AI-citation surface left on the table.
- Homepage has visible testimonials with no `Review` / `AggregateRating`.
- `Service` entities don't carry `offers` / `areaServed` / `provider` linking back to the `ProfessionalService` node.
- `OfferCatalog` on `/pricing/` doesn't expose per-package `Offer` with `price` + `priceCurrency`, though the page states prices from €299.

---

## Performance — 75/100 (lab-estimated, no field data)

| Metric | Observed |
|---|---|
| TTFB (apex) | 247 ms |
| TTFB (service pages) | 86–194 ms |
| Homepage HTML | 154 KB raw / 46.5 KB gzipped |
| JS payload (homepage) | ~255 KB raw / ~100 KB gzipped across 6 files |
| `hero.mp4` | 1.67 MB, faststarted, cached 7 days |
| Third-party requests | Google Fonts (service/blog pages only) |

**Notes**
- Server response is genuinely fast; the risk sits in the client.
- The heaviest single JS file is `services-data.js` (73 KB) which is data, not code, and is fetched on every page load of the SPA.
- `no-cache, must-revalidate` on all JS/CSS forces a conditional request per asset per navigation — the single cheapest performance fix available.
- Hero video is not referenced in the HTML (injected by `hero-cinema.js`), so it can't be preloaded and won't be the LCP element — but it also means LCP waits on JS.
- **Not measured:** LCP / INP / CLS. No Lighthouse binary, no CrUX or GSC credentials configured. To get real numbers, run PageSpeed Insights on `/` and `/services/automation/`, or verify the property in Search Console.

---

## Images — 70/100

- **Alt text: 100% coverage.** Every `<img>` on every crawled page has a non-empty `alt`. `loading="lazy"` and `decoding="async"` throughout. That's better than most sites this size.
- Only 3 `<img>` on the homepage (about portrait + two templated slots); **service pages and blog posts contain zero images**. Text-only service pages under 160 words are a weak signal both to Google and to answer engines.
- ~~**OG image is 1.79 MB**~~ **FIXED** — now `/assets/og-cover.jpg`, 1200×630 at 137 KB, served from repo-owned `seo/assets/`. Remaining: it is still the *same* image on all 21 pages, so every share looks identical.
- Unused heavyweights sitting in the web root: `concept_smart_home.png` 2.37 MB, `medical_ai.png` 1.71 MB.

---

## AI Search Readiness (GEO) — 78/100

**Strong**
- `llms.txt` is genuinely well built — summary, all 15 services with one-line descriptions and stacks, blog, engagement tiers, publications, contact. This is a model example.
- Every major AI crawler explicitly allowed: GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, anthropic-ai, PerplexityBot, Google-Extended, Applebot-Extended, CCBot, Bytespider.
- Blog posts carry `FAQPage` + dated, attributed statistics — the exact passage shape answer engines quote.
- Entity signals are clean: `Person` + `Book` + `sameAs` gives a real author to attach citations to.

**Weak**
- **Answer engines mostly don't run JS.** They fetch `/` and receive 521 `{{ }}` tokens, nine placeholder H1s, and no About/Contact/News content. 1,249 words *are* server-rendered (hero, about, services list), so it isn't a blank page — but the structure a citation engine parses is polluted.
- The 15 service pages are the site's most quotable surfaces and each offers ~140 words with no statistics, no dates, no named examples. There is nothing to cite.
- No `dateModified` visible on service pages.

---

## Crawl Coverage

All 21 sitemap URLs: **HTTP 200**, no redirect chains, no orphans within the sitemap, no `noindex`. Crawl was complete — the site is well under the 500-page cap. Pages reachable only via JS view-switching (`about`, `contact`, `news`, `configurator`, `legal`) are outside the crawl by construction, since they have no URLs.
