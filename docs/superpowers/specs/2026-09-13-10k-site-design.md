# georgeai.dev → the €10K site — design spec

Date: 2026-09-13 · Branch: to be cut from `main` · Status: approved in chat, awaiting plan

## 1. Goal

Lift the live site (`/cinematic/`, the front door since 9231dd3) from "€10K hero,
€200 body" to €10K end-to-end on the eight-point checklist below, then sell that
same build as a fixed-price package on `/pricing/`, with georgeai.dev as the live
demo.

## 2. Diagnosis (2026-09-13, live, desktop 1440 + mobile 390)

| # | Checklist item | Today | Gap |
|---|---|---|---|
| 01 | Point of view, not a template | 8 | Hero is a narrative; everything below (stats → how → 15-row services → 4 AI tiles → FAQ → footer) is a template |
| 02 | Typography that does work | 6 | One family (good) but flat scale: every H2 same size, 16px body, no display moment after the hero |
| 03 | A restrained color system | 7 | Coral UI vs teal imagery — two accents without assigned roles |
| 04 | Hierarchy that breathes | 5 | ~64px between sections; services block is a directory |
| 05 | Imagery with intent | 5 | "Selected work" = generic AI stock; no real screenshot, number or client name |
| 06 | Motion that whispers | 6 | Scrub video shouts; no micro-motion below the hero |
| 07 | Mobile designed, not shrunk | 5 | Stacked desktop; 4 hero headlines with no transition on touch; services = 3 screens of list |
| 08 | The invisible expensive stuff | 7 | Good: 473 KB initial, font preload, reduced-motion, hreflang, filled Impressum, scrub disabled on touch. Missing: AVIF, immutable cache, enforced CSP, tests for the new content |

One-line verdict: the first three screens are worth €10K; the next twelve are the
€200 site in dark mode. The break is felt at second eight.

## 3. Principles

1. **Proof, not description.** Every section below the hero shows something real.
2. **One path, not a menu.** One hero service (voice agent + assistant) demoed inline; the 15 services stay on `/services/`.
3. **Nothing fake ships.** Draft case studies never reach production (same gate pattern as `apply_legal`).
4. **Repo-owned, deploy-applied.** All content lives in JSON/source dirs and is applied by `deploy.sh` layers; `site/` is never hand-edited.
5. **EN and DE mirror** (`pages/cinematic/` and `pages/cinematic/de/`) change together.

## 4. Homepage structure (EN + DE)

Replaces `stats → how → svcs → work → faq → final` under the untouched hero:

| # | Section | Content |
|---|---|---|
| 1 | Proof strip | 3 real client numbers with client names (replaces "8+ years / 40+ projects") |
| 2 | Case studies | 3 full-width, alternating 60/40 (screenshot / text). Kicker `01 / CASE`, H2 = the result metric, client name, 3 sentences: problem / system / result |
| 3 | Live demo | Voice agent + `jarvis.js` inline: "Talk to it now". `/assistant/` stays as the long page |
| 4 | Four pillars | Automation · Visibility · Web · Data — one sentence each + "see all 15 →" |
| 5 | How it works | Kept, cut to 3 steps, doubled spacing |
| 6 | FAQ | Kept |
| 7 | Final CTA | Kept + "Or buy the €10K site →" to `/pricing/#cinematic-site` |

Removed from home: the 15-service list, the 4 AI-image tiles.

### Data: `seo/case-studies.json`

```json
{ "cases": [ {
  "slug": "…", "draft": false,
  "client": "…", "logo": "…svg|null",
  "metric": "−63 %", "metric_label": {"en": "missed calls in 6 weeks", "de": "…"},
  "problem": {"en": "…", "de": "…"}, "system": {…}, "result": {…},
  "img": "cases/<slug>.jpg", "img_alt": {…}
} ] }
```

Applied by `seo/apply_cases.py` (new `apply_cases` layer in `deploy.sh`, runs after
`apply_pages`, before `apply_widget`). Renders section 1 and 2 into both language
homepages between `<!-- cases:start -->` / `<!-- cases:end -->` markers
(idempotent full replace). **Exits 2 and changes nothing** if any case has
`draft: true` and `GEORGEAI_ENV != dev`. Screenshots: `images/cases/*.{jpg,png}`
(source), emitted as AVIF + WebP + JPG into `site/cinematic/assets/cases/` by
`images/gen_cases.py` (Pillow), referenced through `<picture>`.

## 5. Typography and color

**Accent roles** (documented in `brand/palette.json` `_comment` and as a rule in
`pages/cinematic/style.css`):
- Coral `#fb5e31` = *action*: buttons, links, focus, wordmark. Never inside imagery.
- Teal = *the machine*: only in imagery (video, screenshots, mock glows) via a
  `--glow` token used exclusively on `img`/`video` overlays. Never on text or borders.

**Scale** (Plus Jakarta Sans only):

| Role | Size | Use |
|---|---|---|
| Metric | `clamp(56px, 8vw, 104px)` 800, `tabular-nums`, −0.03em | case-study number |
| H2 | `clamp(36px, 4.5vw, 60px)` 700, −0.02em | section titles |
| H3 | 24px / 1.25 | client, pillar |
| Body | 17px / 1.6, `max-width: 62ch` | all copy |
| Kicker | mono 12px, .18em tracking, uppercase, muted | `01 / CASE` |

Rhythm: `--space-section: clamp(96px, 12vw, 176px)`; each case study `min-height: 80vh`.

**Motion:** metric counts 0→value once on viewport entry (900 ms ease-out);
screenshot hover `scale(1.02)` 300 ms; `@view-transition { navigation: auto }` for
cinematic pages. All gated by `prefers-reduced-motion`.

## 6. Mobile (≤ 720px / coarse pointer)

- Hero: poster + 3 s `hero-loop.mp4` (~800 KB, ffmpeg cut of the scrub, `autoplay muted loop playsinline`), one H1 + sub instead of four headlines.
- Case studies: image on top (4:3, `object-fit: cover`), metric overlaid in a corner, text below. No alternation.
- Pillars: horizontal `scroll-snap-type: x mandatory`, cards 80vw.
- Sticky bottom CTA bar (56px): "Free audit" + phone; shown after the hero leaves the viewport, hidden while the final CTA is visible (`IntersectionObserver`). One button.
- Jarvis input `position: sticky; bottom: 0` inside its section.

## 7. The invisible expensive stuff

| Item | Change |
|---|---|
| Images | AVIF/WebP + JPG fallback for hero stills and case screenshots (`images/gen_cases.py`) |
| Cache | `Cache-Control: max-age=31536000, immutable` on `/cinematic/assets/*` in `deploy/nginx.conf` |
| CSP | Check console on home, a service page, `/blog/`, `/pricing/`, `/cinematic/`; if clean, rename `Content-Security-Policy-Report-Only` → `Content-Security-Policy` in all three location blocks |
| Scrub video | `preload="metadata"` set only after `load` + `requestIdleCallback`, desktop only |
| Targets | Lighthouse mobile ≥ 90 perf / 100 a11y / 100 SEO; measured before and after, numbers recorded in the plan |
| Test | `tests/test_cinematic.py` (stdlib): every `<img>` has alt; every case has `metric` + `client`; no `draft` in production; mobile home initial weight < 600 KB |

## 8. The €10K package on `/pricing/`

Card `id="cinematic-site"`, slug `cinematic-site`:
- Name: **A Website Worth €10,000** / DE *Eine Website, die 10.000 € wert ist*.
- Price line: €10,000 one-time. Button: **Reserve a slot — €2,500 deposit** (Stripe Payment Link, `metadata.data_product = cinematic-site`); balance invoiced at milestones.
- Promise: "The site you are on right now. Built for you, on your story."
- Includes: the eight checklist items phrased as deliverables (cinematic hero with you in frame · 3 case studies with numbers · live demo of your product · one color system · mobile designed separately · Lighthouse ≥ 90/100/100 · GDPR + Impressum + CSP · 5 languages optional).
- Live in: 4–6 weeks. Aud line: "Want to see what €200 looks like next to this? → #compare".
- New section **The €10K Checklist** (`#compare`): 3 columns Taste / Substance / Felt quality × rows *€200 site / this site*; each row links to the homepage section that demonstrates it.
- Keep in sync: `CATALOG["cinematic-site"] = {"one_time": 250000, "monthly": None}` in `tests/test_payments_pipeline.py`; JSON-LD `Offer`; `docs/stripe-payment-links.md`; n8n `stripe-orders` mapping (confirmation email says "next: 30-min call").

## 9. `docs/10K-PLAN.md`

1. Today's diagnosis (table above + before screenshots).
2. Execution order — 7 phases, one PR each, each with a measurable "done when":
   proof data → typography/accent → case studies → inline demo → mobile → invisible → pricing tier.
3. What George must supply (blocks phase 3): per client — screenshot, one number with its period, written consent for name/logo. Includes a 5-line consent email template.
4. Sales script: showing the checklist to a prospect in 3 minutes with georgeai.dev open.
5. Lighthouse before/after as proof.

## 10. Out of scope

Regenerating the hero video; changing the classic site (`GeorgeAI.dc.html`); new
languages beyond EN/DE for the cinematic pages; Stripe live-mode migration of the
existing seven packages.
