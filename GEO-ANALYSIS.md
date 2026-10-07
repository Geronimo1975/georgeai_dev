# GEO Analysis — georgeai.dev

Measured live on 2026-08-24 against `https://georgeai.dev`. Every figure below
comes from fetching the site with JavaScript disabled — i.e. what an AI crawler
actually receives.

## GEO Readiness Score: 61/100

| Criterion | Weight | Score | Verdict |
|---|---|---|---|
| Citability | 25% | 14/25 | Homepage content buried in template noise; blog strong |
| Structural readability | 20% | 13/20 | Static pages clean; homepage has 9 `<h1>` |
| Multi-modal content | 15% | 8/15 | Images + hero video; no charts, tools or calculators |
| Authority & brand signals | 20% | 11/20 | Excellent schema, near-zero off-site entity presence |
| Technical accessibility | 20% | 15/20 | Best-in-class robots/llms.txt; homepage SSR is a fallback, not real SSR |

## The finding that matters most

**The homepage ships 549 unrendered `{{ }}` template placeholders into the
crawlable HTML.** The design-tool export renders client-side from `support.js`,
and AI crawlers do not execute JavaScript, so they receive the raw skeleton.

Breakdown of the homepage as a crawler sees it:

| Region | Chars | Content |
|---|---|---|
| `<noscript>` block | 2,991 | Clean, real prose (repo-owned `seo/noscript.html`) |
| Everything outside it | 6,694 | SPA skeleton containing all 549 `{{ }}` tokens |

Five of the nine `<h1>` elements are literally `{{ t.pg.servicesTitle }}`,
`{{ detail.name }}`, `{{ about.title }}`, `{{ ct.title }}`, `{{ news.title }}`.
Only the hero lede injected by `apply_hero` is a real heading.

This is confined to `/`. The generated pages are clean:

| URL | Unrendered `{{ }}` |
|---|---|
| `/` | **549** |
| `/services/ai-chatbot/` | 0 |
| `/blog/` | 0 |
| `/pricing/` | 0 |

Two consequences. First, the good content sits inside `<noscript>`, and
extraction pipelines vary in whether they keep noscript text — relying on it is
a gamble, not a guarantee. Second, even where it is kept, it competes with 549
junk tokens, which depresses the clean-passage extraction that citation depends
on. The `seo/noscript.html` layer was the right instinct; it is currently
carrying the entire homepage on its own.

## AI crawler access — full marks

`robots.txt` explicitly allows every crawler that matters, which is unusually
thorough: GPTBot, OAI-SearchBot, ChatGPT-User, ClaudeBot, Claude-Web,
anthropic-ai, PerplexityBot, Perplexity-User, Google-Extended,
Applebot-Extended, Bytespider, CCBot. Sitemap declared. Nothing to fix.

## llms.txt — present and genuinely good

48 lines at `/llms.txt`: description, contact, languages, and all 15 services
grouped into three categories with a one-line description and stack per service.
This is above the standard of most sites that have one at all. No change needed.

## Brand mention analysis — the biggest strategic gap

Brand mentions correlate ~3x more strongly with AI citation than backlinks
(Ahrefs, Dec 2025: mentions ~0.737 for YouTube vs ~0.266 for Domain Rating).

| Platform | Presence | Note |
|---|---|---|
| GitHub | Yes | The only `sameAs` target on the site |
| LinkedIn | Not linked | Moderate correlation; easiest win |
| YouTube | Not linked | Strongest single correlation (~0.737) |
| Reddit | Not linked | Perplexity's top source (46.7% of citations) |
| Wikipedia / Wikidata | Absent | ChatGPT's top source (47.9% of citations) |

`sameAs` currently contains exactly one URL. For a business selling GEO
services, this is the most visible gap in the profile.

## Schema — strong, with two holes

Homepage carries a well-built graph: `ProfessionalService`, `Person` (with
`@id`, `jobTitle`, `worksFor`, and a rich `knowsAbout` array), `Book`, `WebSite`,
`WebPage`. Service pages carry `Service` + `ServiceChannel` + `BreadcrumbList`.
The blog post carries `BlogPosting` + `FAQPage` with `Question`/`Answer` and both
`datePublished` and `dateModified` (2026-07-02).

Holes:
1. **No `author` on the blog post.** `BlogPosting` without an author forfeits the
   E-E-A-T signal, and there is already a fully-formed `Person` node at
   `https://georgeai.dev/#george` to point at.
2. **`sameAs` has one entry** and appears only on `/`. Service and blog pages
   carry none.

## Passage-level citability

Target is self-contained 134-167 word blocks. Current state:

| Page type | Words | Assessment |
|---|---|---|
| Blog post | 1,381 | Good — 9 `<h2>`, 4 `<h3>`, FAQ schema. Closest thing to citable |
| Service pages (×15) | ~301 | Thin. Roughly two passages' worth of text total |
| Homepage (noscript) | ~470 | Enough for ~3 blocks, but competing with placeholder noise |

Service pages at 301 words are the weak layer: 15 URLs, each too thin to yield a
quotable self-contained answer.

## Platform breakdown

| Platform | Est. | Reasoning |
|---|---|---|
| Google AI Overviews | 65/100 | Static service/blog pages are clean and indexable; homepage weak |
| ChatGPT | 50/100 | No Wikipedia/Wikidata entity — its single largest citation source |
| Perplexity | 48/100 | No Reddit presence — its largest citation source |
| Bing Copilot | 60/100 | Clean static pages, sitemap present; no IndexNow |

## Top 5 highest-impact changes

1. **Server-render the homepage content, or promote the noscript block into the
   real DOM.** Removes dependence on noscript handling and kills the 549-token
   dilution in one move. Highest impact by a wide margin.
2. **Expand `sameAs`** to LinkedIn, YouTube, Reddit and any conference/podcast
   profiles, and emit it on every page rather than only `/`. Cheap; directly
   targets the strongest known correlate of AI citation.
3. **Add `author` to `BlogPosting`**, pointing at the existing
   `https://georgeai.dev/#george` node.
4. **Thicken the 15 service pages** from ~301 to 700-900 words, structured as
   134-167 word self-contained answer blocks under question-form `<h2>`s.
5. **Build off-site entity presence** — Wikidata entry, a YouTube channel, real
   Reddit participation. Slowest, but it is what moves ChatGPT and Perplexity.

## Quick wins available today

- Add `dateModified` to service pages (currently none carry dates).
- Convert service-page `<h2>`s to question form ("What does an AI chatbot do?").
- Add a 40-60 word "What is X?" definition opening each service page.
- Emit `sameAs` sitewide, not just on the homepage.

## What is already right

Worth stating plainly, because these are the parts most sites get wrong:
`robots.txt` AI-crawler policy is complete and deliberate; `llms.txt` is
well-structured and current; the schema graph uses proper `@id` cross-references;
the blog post has FAQ schema and real dates; and 21 URLs are in the sitemap with
service and blog pages fully static and placeholder-free.

The gap is not technical care — it is that the homepage never got the static
treatment the generated pages did, and that the brand has no presence off its own
domain.
