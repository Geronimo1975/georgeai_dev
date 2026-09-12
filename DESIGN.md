---
version: 1.0
name: GeorgeAI-dev
description: A warm cream/coral editorial interface for georgeai.dev, George's AI-services portfolio site, adapted from Claude.com's visual language (per DESIGN-claude.md) and verified against the live export (site/GeorgeAI.dc.html). Supports a light theme (tinted cream canvas) and a dark theme (near-black warm surface) via a header toggle. Serif display (Newsreader) pairs with Inter body copy and JetBrains Mono for eyebrow labels/metadata; RTL support swaps in Amiri/Noto Sans Arabic. This file reflects the actual tokens shipped in the export; treat DESIGN-claude.md as the aesthetic reference it was adapted from, this file as ground truth for implementation.
---

## Overview

georgeai.dev sells AI voice-agent and website-assistant pilots to German SMB owners (trades, clinics, service firms). It deliberately borrows Claude.com's warm-editorial identity — tinted cream canvas, coral CTAs, serif display type — as counter-positioning against the cold blue/slate look of most AI-tool marketing sites. Unlike the Claude.com reference, this site ships **two full themes** (light/dark, user-toggleable) and swaps its entire type system for **open, self-hostable fonts** (no Copernicus/StyreneB license): Newsreader serif for display, Inter for body, JetBrains Mono for uppercase eyebrows and metadata.

**Key characteristics:**
- Light theme: warm cream canvas (`#faf9f5`) with warm-black ink (`#141413`). Dark theme: near-black warm surface (`#181715`) with cream-tinted ink (`#faf9f5`) — the two themes are inversions of the same warm palette, not a generic light/dark pair.
- Neon coral-orange accent. Two tiers, both WCAG AA: **`#ff5c39`** is the brand voltage — large surfaces, the CTA band, the logo and dark-theme text (5.84:1 on the dark canvas, 6.01:1 under ink labels). It is NOT usable for small text on cream (2.91:1) or under white labels (3.07:1); **`#df2700`** is the darkened companion that covers exactly those two cases (4.50:1 on cream, 4.74:1 under white).
- Serif display via **Newsreader** (weight 400, negative letter-spacing), body/UI via **Inter**, uppercase eyebrow labels and metadata via **JetBrains Mono**. RTL (Arabic) swaps Newsreader → Amiri.
- The GeorgeAI "Ai" monogram follows the same two-tier rule as the accent: `seo/logo-mark.png` (neon `#ff5c39`) on dark surfaces, `seo/logo-mark-ink.png` (companion `#df2700`) on cream, where neon washes out. The footer and auth modal are dark in both themes so they are pinned to neon; the header swaps via `markSrc` in the render context; the static pages are always cream so they use the companion. The favicon tile is dark, so it stays neon. It is swapped in by `seo/apply_content.py:brand_mark()`; the export's own 8-point polygon survives only as 7px bullets and 18px success glyphs.
- Fonts are self-hosted (`site/assets/fonts.css`, `site/assets/fonts/*.woff2`) — deliberately no `fonts.googleapis.com`/`fonts.gstatic.com` requests, so no visitor IP reaches Google. Preserve this when adding type.
- Two breakpoints drive the whole layout: `isMobile` (`vw < 860`) and `isNarrow` (`vw < 560`, nested inside mobile for hero title sizing). There is no separate tablet breakpoint.

## Colors

Both themes are runtime CSS custom properties (`--ink`, `--accent`, etc.), swapped by a header toggle. Values below are exact, from `site/GeorgeAI.dc.html`'s `themes` object.

| Token | Light | Dark | Use |
|---|---|---|---|
| `--canvas` | `#faf9f5` | `#181715` | Page floor |
| `--surface` | `#f5f0e8` | `#1f1e1b` | Section band backgrounds (Services, Testimonials) |
| `--card` | `#faf9f5` | `#201f1c` | Card fills (How It Works, Services, Testimonials, header dropdowns) |
| `--cardBorder` | `#e6dfd8` | `#2f2c28` | 1px card/hairline-adjacent borders |
| `--ink` | `#141413` | `#faf9f5` | Headlines, primary text |
| `--accent` | `#df2700` | `#ff5c39` | Eyebrow labels, "See all →" links, active states |
| `--accentBtn` | `#df2700` | `#df2700` | Primary CTA button fill (constant across themes) |
| `--body` | `#3d3d3a` | `#cfccc4` | Running text |
| `--muted` | `#6c6a64` | `#a09d96` | Secondary text, captions |
| `--hairline` | `#ebe6df` | `#2a2824` | Section dividers |
| `--navBg` | `rgba(250,249,245,.85)` | `rgba(24,23,21,.85)` | Sticky header (blurred) |
| `--pillBg` | `#f5f0e8` | `#252320` | Language pill, mobile menu pill background |
| `--footerBg` | `#181715` | `#0f0e0d` | Footer — stays dark in both themes |
| `--footerText` | `#a09d96` | `#8e8b82` | Footer body |
| `--footerHead` | `#faf9f5` | `#faf9f5` | Footer headings — constant |
| `--gridline` | `rgba(20,20,19,.06)` | `rgba(250,249,245,.06)` | Hero background grid overlay |

Hardcoded (not theme-dependent): CTA band fill `#ff5c39` with **ink** (`#141413`) text, not white — white on neon is 3.07:1; auth-modal background `#181715` (always dark regardless of page theme). The coral pricing card keeps white body text, so it takes `#df2700`, not the neon.

**Strategy:** Committed. The neon accent is reserved for CTAs, eyebrow labels, the logo, the hero beams and the one full-bleed CTA band — scarce on small elements, generous on the band. Don't introduce a third hue; teal/amber accents exist only as terminology in the legacy DESIGN-claude.md and are **not** present in the shipped export.

**The palette is owned by `brand/apply_brand.py`**, which rewrites the export's hard-coded Anthropic coral on every deploy. Change the shade there (`ACCENT_NEON` / `ACCENT_TEXT`), never in `site/`.

## Typography

| Token | Family | Size | Weight | Line-height | Letter-spacing | Use |
|---|---|---|---|---|---|---|
| Hero title | Newsreader (Amiri if `dir=rtl`) | 64px desktop / 50px mobile / 38px narrow | 400 | 1.04 | -1.5px | H1, homepage hero |
| Section H2 | Newsreader | 38px desktop / 30px mobile | 400 | 1.1–1.15 | -0.6px | Section headings |
| Card H3 | Newsreader | 23–26px | 400 | 1.15–1.2 | -0.3 to -0.4px | Card/work-item titles |
| Body | Inter (default, unstyled inherit) | 15–18px | 400 | 1.55–1.65 | 0 | Paragraphs, descriptions |
| Nav / label | Inter | 14–16px | 500 | 1.3–1.4 | 0 | Nav links, CTA button labels |
| Eyebrow / metadata | JetBrains Mono (Noto Sans Arabic if RTL) | 11–13px | 400–500 | 1.4 | 1.5–2px, uppercase | Eyebrow pills, category tags, work item metadata |

**Principles:** Display type is always weight 400 — never bold — with negative tracking; this is the single most load-bearing rule carried over from the Claude.com reference. Body copy is plain Inter at 400 with no tracking. JetBrains Mono is reserved for short uppercase labels, not body text.

## Layout

- **Base spacing:** `padX` (page gutter) 56px desktop / 28px mobile / 20px narrow. `sectionPadY` (vertical rhythm between bands) 88px desktop / 56px mobile.
- **Grids:** How It Works & Selected Work: `1fr 1fr` desktop → `1fr` mobile. Services: `repeat(2,1fr)` desktop → `1fr` mobile. FAQ: `.42fr .58fr` desktop → `1fr` mobile. Footer: `1.3fr 1fr` desktop → `1fr` mobile.
- **Radii:** buttons/inputs 8px, cards 12–20px (How It Works cards 18px, Services cards 14px, Testimonial card 20px), pills/badges 9999px.
- No max-content-width container is declared in the export (full-bleed sections with `padX` gutters, not a centered `max-width` wrapper) — don't introduce one without checking it doesn't fight the existing full-bleed hero background effects.

## Components (as shipped)

Sections present on the homepage (`isHome`), top to bottom — see the earlier link-audit table for which have real navigation:

1. **Header** — sticky, blurred `--navBg`, language switcher pill, theme toggle, auth pill, hamburger menu (mobile), "Configurator" CTA (`--accentBtn`) + secondary "Contact" button.
2. **Hero — Showcase** — full-bleed animated grid/beam background (beams neon), interactive service-flag panels; the active panel carries a real "Read the case study" link to `/work/<slug>/`. Eyebrow + H1 + sub + two CTAs.
3. **Logo Carousel** — passive marquee, no interactive elements by design.
4. **How It Works** — numbered ruled strip (no cards), no CTA (informational only).
5. **Selected Work** — "View all →" links to `/work/`, each project card to its own `/work/<slug>/` page. Both were dead in the export (styled clickable, no handler); `seo/apply_content.py:wire_work_links()` wires them on every deploy.
6. **Services** — 2-up category cards, "See all services" (`onClick`) + per-item `onOpen` handlers.
7. **Testimonials** — carousel with dot + prev/next controls (`onClick`, UI-only, not navigational).
8. **FAQ** — accordion (`onClick` toggle, UI-only).
9. **CTA Band** — full-bleed coral (`#cc785c`) card, single `onClick` CTA.
10. **Footer** — 3-column (Services / Work-Nav / Elsewhere), tagline + newsletter input, social row with **real `<a href>`** links (GitHub, LinkedIn, WhatsApp, email) — the only real external links on the page besides header tel/email.
11. **Auth modal** — always-dark overlay regardless of page theme, login/signup tabs, real `<input>` fields.

**Pattern to follow when fixing links:** the footer's "Elsewhere" column (`<a href="https://github.com/...">`) is the existing correct pattern for a real link with `text-decoration:none;color:inherit`. Reuse that shape — not a new `onClick` span — for any CTA being converted to a real link.

## Do's and Don'ts

### Do
- Keep both themes in sync — any new component needs a light and a dark value for every color it touches, following the `themes.light` / `themes.dark` token pairs above.
- Use `<a href="...">` for anything that is genuinely a link to another page/section/URL, styled to match the existing footer social-link pattern (`text-decoration:none;color:inherit`).
- Keep Newsreader/Inter/JetBrains Mono self-hosted via `site/assets/fonts.css` — do not add a Google Fonts `<link>`.
- Preserve the RTL font swap (Newsreader→Amiri, JetBrains Mono→Noto Sans Arabic) for any new text-bearing element.

### Don't
- Don't introduce Copernicus/StyreneB/Tiempos Headline — those are DESIGN-claude.md's Anthropic-licensed references, not what's actually shipped. Use Newsreader/Inter.
- Don't add a third accent hue (teal/amber) — not present in the live export regardless of what the legacy reference doc lists.
- Don't ship a clickable-looking element (`cursor:pointer`, an arrow glyph, "View all") without a working `onClick` or `href` — that's the exact defect this file exists to prevent recurring.
- Don't hand-edit the accent, the logo or the portfolio links in `site/`: they are owned by `brand/apply_brand.py` and `seo/apply_content.py`, and `site/index.html` is a copy that only regenerates on a full export unpack, so hand edits there silently fail to reach the served homepage.
- Don't hand-edit `site/GeorgeAI.dc.html` / `frontend/template/` as a permanent fix — see PRODUCT.md's design principle on this; those directories are regenerated from `exports/*.zip` on every deploy.

## Responsive Behavior

| Breakpoint | Width | Key changes |
|---|---|---|
| Narrow | < 560px | Hero title drops to 38px |
| Mobile | < 860px | `padX` 28px, `sectionPadY` 56px, all grids collapse to `1fr`, hamburger menu replaces horizontal nav, CTA band stacks column/flex-start |
| Desktop | ≥ 860px | `padX` 56px, `sectionPadY` 88px, 2-up grids, horizontal nav, CTA band row/center |

There is no distinct tablet tier — layout is binary (mobile/desktop) driven by `isMobile`, with `isNarrow` only affecting hero title size within mobile.
