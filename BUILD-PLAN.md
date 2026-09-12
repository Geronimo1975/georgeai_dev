# GeorgeAI — Master Build Plan

Cinematic scroll-storytelling agency site for **GeorgeAI** (georgeai.dev).
Part 1 is the creative brief. Part 2 is the implementation spec for Claude Code.
Status: APPROVED 2026-09-12. Site built at `pages/cinematic/` with the designed still hero (no Higgsfield credits yet). Video chain pending: once credits exist, generate per §5/§6, place `assets/hero-scrub.mp4`, and add `data-src="assets/hero-scrub.mp4"` to `#video` in index.html.

Identity reference for every Higgsfield generation:
`Media/553517285_24478507705111025_4371849374889154092_n.jpg`
(George, black and white portrait: dark curly hair, rectangular black-framed glasses, black shirt, chin on fist, an hourglass in the foreground.)

Money note, checked today: the Higgsfield account is on the free plan with **0 credits**. The video chain below needs roughly 40 to 170 credits depending on model. Credits must be topped up before Phase 6, or the site ships with the designed still hero first and the video lands later (the build supports both).

---

# PART 1 — CREATIVE BRIEF

## 1. Website overview

| | |
|---|---|
| Brand | GeorgeAI |
| Type | Agency (one-person AI automation studio, Hamburg area, Germany) |
| Audience | Owner-run trades, clinics, service firms and Mittelstand companies in Germany and the DACH region that lose hours, and leads, to manual work |
| One-line promise | We automate your business with AI. Practically. Measurably. |
| Primary CTA | Free visibility audit (existing lead widget: `audit.js` → n8n webhook → emailed report) |
| Secondary CTA | Fixed-price packages at `/pricing/` |
| Languages | English first; DE strings prepared for the existing i18n pipeline later |
| Tone | Cinematic, premium, futuristic, and above all trustworthy B2B |

## 2. Core positioning

**The brand premise: time.** George's own portrait holds an hourglass. Every business owner we serve is out of time: the Saturday enquiry nobody answered, the invoice typed twice, the lead that went cold in a spreadsheet. GeorgeAI builds systems that give that time back. The hourglass, the sand, the flow of grains through a narrow neck into a wide calm pool, is the visual and narrative spine of the whole site. Sand becomes data. Data becomes a running machine. The machine gives the owner the evening back.

Headline promise: **Your business, running while you sleep.**

Positioning statement: GeorgeAI is the practical AI partner for small and mid-size German companies. Not a slide deck, not a chatbot demo. Working automations, live in about two weeks, measured in hours saved and enquiries booked.

Why us, in the buyer's words:
- "I do not have time to learn another tool." → We build it, connect it, and hand it over running.
- "AI sounds like hype." → Every project starts with one process and one number to move.
- "Who do I actually talk to?" → One person. 8+ years running infrastructure and building automation. He picks up.
- "Is it compliant?" → Built in Germany, hosted in Germany, GDPR by default.

## 3. Brand personality

- **Calm confidence.** Never shouting. Short sentences. Numbers instead of adjectives.
- **Engineer, not salesman.** The site shows systems running, not people pointing at screens.
- **Practical futurism.** Holograms and light, yes, but every scene ends in something a plumber recognises: a booked calendar, a closed ticket, a paid invoice.
- **Multilingual host.** English, German, French, Romanian. The site says so once; the pipeline already handles it.
- Voice rules: plain words, no corporate filler, no em dashes, one idea per line. Deliberate devices allowed: triplets and staccato punches.

## 4. Visual direction

One committed direction: **Black-void studio, emerald cold light, orange warm signal.**

- Canvas is the brand's near-black with a blue cast (`#02060a`), never pure black.
- Two light sources in every frame and on every page: a cool **emerald/teal rim light** (new, secondary) and the brand's **hot orange accent** (`#fb5e31`) used as the single "signal" colour, in rare doses: the CTA, the hourglass sand, one glowing node in each scene.
- Materials: matte black, brushed dark steel, glass, volumetric haze, floating light particles. No chrome, no neon grids, no acid green.
- Signature element: **the sand line.** A thin orange SVG path, drawn by hand, that runs down the whole page like sand falling through an hourglass neck, drawing itself on scroll, splitting into three streams at the pillars, and pooling into the CTA. Remove it and the page is a different page. That is the test it passes.
- Subtle film grain over everything, fixed layer, 4% opacity, animated at 12fps via `steps()`.
- Banned looks (per the skill's design bar): cream + serif + terracotta, near-black + acid-green, near-black + amber + high-contrast serif. Our cold emerald against warm orange is deliberately neither.

## 5. Higgsfield Seedance 2.0 asset generation

Settings for every clip: image-to-video, **1080p, 16:9, 8 to 12 seconds**, standard mode, no audio. Model: Seedance 2.0 (fall back to the mid-priced model if credits demand; preflight both with `get_cost: true` and present the numbers before spending).

Identity: the reference portrait is passed as the character reference on every start frame and, where the model supports it, on every video call. Restate in every prompt: *"a man in his late forties, short dark curly hair with grey at the temples, rectangular black-framed glasses, clean shaven, fitted black shirt, calm half smile."*

Workflow (Tier 2, chained, three segments joined as one shot):
1. Preflight the start frame (about 2 credits). Generate. Inspect for likeness, trademarks, anatomy, and the two-sided negative space. Show George. Gate.
2. Preflight segment 1 across models. George picks the model. Generate segment 1. Extract start/mid/end frames. ⛔ Video gate: George watches it from `review/`.
3. Extract the final frame as full-quality PNG, upload (`media_upload` → PUT → `media_confirm`), use as `start_image` for segment 2. Repeat for segment 3.
4. Every seam lands inside motion or a light sweep, never rest-to-rest (the seam law).
5. Join with a single-encode `concat`; if a seam shows, `xfade` 0.25s.
6. Supporting stills (about 2 credits each, same world, same grade): pillar 1, pillar 2, pillar 3, the About portrait scene, one factory ending frame is free from the video.

Standing guards in every prompt: *"No text, no logos, no lettering anywhere."* Decline presets.

## 6. Three cinematic scenes (one continuous shot, 24 to 30 s total)

Camera language: one unbroken camera. Orbit → push-in → pull-back-and-rise. Scrolling down reads as arriving, entering, and finally overseeing. The subject (George) stays in the left third for scenes 1 and 2 so captions live on the right; scene 3 clears the centre for the settle.

**Scene 1 — HERO ORBIT (0 to 10 s)**
George stands in a black-void studio, weight on one leg, hands relaxed, calm half smile, looking just past the lens. Emerald rim light from behind-left carves his silhouette; a warm orange key from low-right touches the glasses and jaw. Fine dust drifts in the beams. On a low plinth beside him an hourglass glows faintly, sand trickling orange. Camera performs one slow 180° orbit from his left profile to a three-quarter front, ending as the orbit continues past his shoulder toward a dark desk emerging in the haze behind him. **Ends mid-motion** (seam inside the camera move).

*Video prompt:* "One continuous shot, no cuts. A man in his late forties, short dark curly hair with grey at the temples, rectangular black-framed glasses, fitted black shirt, stands calm in a black-void studio filled with faint volumetric haze. Emerald-teal rim light from behind his left shoulder outlines his silhouette; a warm orange key light from low front-right catches his glasses and jaw. Fine dust drifts through the light beams. A glass hourglass on a low black plinth beside him glows softly, orange sand trickling. The camera orbits slowly and smoothly around him, from his left profile toward a three-quarter front view, at constant height and speed. He stays alive: a slow breath, a slight turn of the head to follow the camera, a subtle shift of weight. The orbit keeps moving as the shot ends, the camera now passing his right shoulder, revealing a dark desk with faint floating lights in the haze behind him. The scene fills the frame edge to edge, the right half a receding soft dark studio depth. Cinematic, photorealistic, 1080p, 16:9. No text, no logos, no lettering anywhere."

**Scene 2 — THE BUILDER (10 to 20 s)**
The camera continues its curve and pushes in past George's shoulder to the desk. He is now seated, sleeves pushed up, one hand resting on the matte desk. Above the desk, translucent holographic panes float: node-and-wire workflow graphs (n8n style, abstract, no legible text), pulsing connection lines, a calendar grid filling itself, a phone waveform answering. Emerald light from the panes, one orange node pulsing at the centre of the graph. Slow cinematic push-in toward that orange node until it fills a third of the frame and its light blooms. **Ends inside the bloom** (light sweep motivates the texture refresh for the seam).

*Video prompt:* "One continuous shot, no cuts, continuing a smooth camera move. The camera glides forward past the right shoulder of the same man (late forties, dark curly hair, black-framed glasses, black shirt), who is now seated at a long matte black desk in a dark studio, sleeves pushed up, one hand resting on the desk, focused and calm. Above the desk float translucent holographic panes in emerald-teal light: abstract node-and-wire workflow diagrams, pulsing connection lines, a calendar grid filling itself square by square, a soft audio waveform. No readable text on any pane, only shapes and light. One node at the centre of the main diagram pulses warm orange. The camera pushes in slowly and steadily toward that orange node. The man stays alive: he taps once on the desk, glances up at the panes, breathes. Panes drift gently, particles float. As the shot ends the orange node fills a third of the frame and its glow blooms softly across the lens with a beat of soft blur. Cinematic, photorealistic, 1080p, 16:9. No text, no logos, no lettering anywhere."

**Scene 3 — THE AUTOMATED FACTORY (20 to 30 s)**
Out of the orange bloom the camera pulls back and rises. The single node becomes one light in a vast dark hall: a network of quiet machines, conveyors, robotic arms, and server racks connected by emerald light-lines, everything running in rhythm with no humans on the floor. Orange lights mark each completed cycle, blinking in sequence like sand grains landing. George stands on a mezzanine walkway at the lower-left, small, hands in pockets, watching. Camera continues rising and slowing to a **composed rest**: a wide symmetrical overview, the hall bisecting the frame, George a small silhouette lower-left, generous dark ceiling space above for the settle headline and CTA.

*Video prompt:* "One continuous shot, no cuts, continuing from a soft orange light bloom that clears. The camera pulls back and rises slowly out of a single orange point of light, revealing it as one indicator among many in a vast dark industrial hall: quiet robotic arms, conveyors, and dark server racks connected by thin lines of emerald-teal light, all moving in calm rhythm with no people on the floor. Small orange lights blink in sequence as each cycle completes. Faint haze, dust in the light. On a steel mezzanine walkway at the lower left stands the same man (dark curly hair, black-framed glasses, black shirt), small in frame, hands in pockets, watching calmly. The camera keeps rising and decelerates to a full stop on a wide symmetrical overview: the hall dead centre, same distance from left and right edges, its receding depth filling the frame edge to edge, the upper third a calm dark ceiling of soft haze. The machines keep working quietly in the final frame. Cinematic, photorealistic, 1080p, 16:9. No text, no logos, no lettering anywhere."

Start-frame prompt (Scene 1, frame one, 2k, 16:9, character reference attached): "A man in his late forties, short dark curly hair with grey at the temples, rectangular black-framed glasses, clean shaven, fitted black shirt, standing calm in left profile in a black-void photo studio filled with faint volumetric haze, composed as the first moment of a slow camera orbit around him. Emerald-teal rim light from behind his left shoulder outlines his silhouette; a warm orange key light from low front-right touches his glasses and jaw. A glass hourglass on a low black plinth beside him glows softly with orange sand. Fine dust in the beams. He occupies the left third of the frame; the right two thirds are one continuous receding soft dark studio depth in the same haze. Cinematic, photorealistic, 16:9. No text, no logos, no lettering anywhere."

## 7. Website structure

**Revised 2026-09-12 (George): multi-page, not one-page.** Seven pages under `/cinematic/`, shared nav, footer, `style.css`, `script.js`. Generated from fragments by a scratchpad script; the pricing page is parsed from `pages/pricing/index.html` so prices and Stripe links keep one source of truth.

| Page | Content |
|---|---|
| `/cinematic/` | Boot line → portrait behind floating holographic HUD panels (pointer parallax) → 1200vh scrubbed hero (6 bands) → stats → teaser of the three pillars → CTA |
| `/cinematic/services/` | Three pillars + three highlighted packages |
| `/cinematic/assistant/` | **Jarvis**: command-room hero (canvas wireframe globe, live tiles, radar) + in-browser assistant demo (`jarvis.js`: text and voice in, speech out, rule-based intents, live device panel) + how it works |
| `/cinematic/about/` | Mission (hourglass) + story + CV timeline |
| `/cinematic/work/` | Three case tiles |
| `/cinematic/contact/` | Turn-the-hourglass moment + free audit CTA + direct contact cards |
| `/cinematic/pricing/` | All 7 packages, one-time and monthly, buy buttons with `data-product` slugs |

Hero portrait, AI version (when Higgsfield credits exist): regenerate the home hero still with the identity reference: George behind translucent holographic panels, emerald light, black shirt, like the Pinterest reference he sent, then swap `assets/george.jpg` for it. The HTML/CSS panels stay on top.

Original one-page outline, kept for reference:

```
[Nav]  fixed, glass, wordmark left, 4 links, CTA pill right
[Hero] 1200vh pinned scrub, 3 chapters × 2 bands + settle band
[Stats strip]  animated counters on a marquee track
[Mission]  the hourglass idea, 2-column, self-drawing sand line
[Three pillars]  Automation · AI Visibility · Web Systems
[Story]  George's path, horizontal timeline, CV facts
[Services / Packages]  fixed-price cards → /pricing/, plus "not sure? audit"
[Featured work]  3 anonymised case tiles + Media/ mock images
[Interactive moment]  "Turn the hourglass" press-and-hold
[Final CTA]  free visibility audit widget trigger
[Footer]
```

## 8. Hero section (band map, 1200vh, starting points)

| Band | Range | Footage | Copy (verbatim) | Entrance |
|---|---|---|---|---|
| 1 | 0.00–0.12 | Orbit begins, profile | **GeorgeAI** / "Your business, running while you sleep." | Blur-to-sharp (haze clears) |
| 2 | 0.14–0.30 | Orbit, hourglass visible | "Every owner we meet is out of time." / "Saturday enquiries. Twice-typed invoices. Leads that go cold." | Drift-down (sand falls) |
| 3 | 0.34–0.48 | Push past shoulder to desk | "So we build the machine." | Approach-from-depth |
| 4 | 0.50–0.64 | Holograms, orange node | "n8n workflows. AI agents. Your tools, finally talking." / "Live in about two weeks." | Grid snap-align (nodes connect) |
| 5 | 0.68–0.82 | Pull back, factory reveals | "Then it runs." / "Night shift included." | Word-punch with overshoot |
| 6 (settle) | 0.86–1.00 | Composed overview | **"Practical AI for the German Mittelstand."** / "8+ years. 40+ projects. One person who picks up the phone." / [Get your free visibility audit] [See packages] | Word-by-word rise, staged settle |

Bands 1 to 4 sit right of centre (George is left). Band 5 uses the two-sided scrim variant. Band 6 uses the upper-centred ellipse over the dark ceiling.

Static-hero copy (phones, reduced motion, video failed): headline "Your business, running while you sleep.", sub "Practical AI automation for German trades, clinics and service firms. Live in about two weeks.", CTA "Get your free visibility audit", over `hero-ending.jpg` (or the poster until the video exists).

## 9. Animated stats strip

Counters ease up on entry (600 ms, expo-out, tabular numerals), one glow pulse when done, then rest. Ordered as the eye reads:

- **8+** years in infrastructure and automation
- **40+** projects delivered
- **15+** technologies in production
- **4** languages spoken (EN · DE · FR · RO)
- **~2 weeks** to a live pilot
- **4,600 m²** smart building run end to end

Source: CV and `seo/hero.json` proof floor. No invented numbers.

## 10. Mission section

Kicker: "Why GeorgeAI exists"
Headline: **"AI should give you your evening back. Not another dashboard."**
Body: "Most AI talk is slides. We start with one process that eats your week, one number that should move, and we ship the automation that moves it. If it does not save hours or book enquiries, we do not build it."
Living element: the sand line splits here into three streams, drawn on scroll.
Image: `hero-ending.jpg` reused, cropped to the hourglass plinth, with a slow emerald light drift.

## 11. Three pillars section

Three cards, equal weight, each with a generated still in the hero's world.

1. **AI Automation** — "Connect every tool. Kill the busywork." n8n and Make workflows, AI agents that read, sort, answer and book. Phone and web enquiries handled 24/7 in the caller's language.
2. **AI Visibility (SEO · AIO · GEO)** — "Be found by people and by AI." Technical SEO, AI Overviews, ChatGPT and Perplexity citations, structured data, content that ranks and gets quoted.
3. **Web Systems** — "The site and the backend behind it." Django, Python, PostgreSQL, APIs, micro-ERP and CRM. Sites that look sharp and convert, plumbed into the automation.

Layout differs from Mission: horizontal scroll-snap row on desktop, stacked on mobile. Card hover lifts 6px, emerald border glow, orange dot pulses once.

## 12. Story section

Kicker: "The person behind the machine"
Headline: **"Twenty years of making systems work. Now they run on AI."**
Timeline (horizontal, draw-on-scroll):
- 2007–2014 · Division Manager, finance and reporting. Built controlling systems that made decisions 30% faster.
- 2011–2018 · Founded and scaled a web and SEO agency. WordPress, Joomla, technical SEO, ERP integrations.
- 2013–2014 · Plant Manager. Cut production costs 15%, incidents 20%, by automating the workflow.
- 2018–2024 · Head of Infrastructure, UMCH Medical University Hamburg. Ran a 4,600 m² smart building: Meraki networks, KNX and DALI automation, access control, LMS.
- 2023–2025 · Certified AI Engineer (EITC) and Python full-stack developer (DCI Berlin).
- 2025 → · GeorgeAI. Claude Code, n8n, RAG and Django for companies that want AI that works.
Portrait: generated still of George in the studio world (same identity reference), or the real portrait treated with the emerald/orange duotone. Two Masters (Healthcare Administration, European Law) mentioned in one quiet line. Languages line.

## 13. Product / Service / Community section

Headline: **"Fixed prices. No surprises."**
Pulls the seven packages from `pages/pricing/index.html` (names and prices must stay in sync with `tests/test_payments_pipeline.py` CATALOG). Three highlighted cards plus a "See all packages" link to `/pricing/`. Under them: "Not sure where to start? The free audit tells you." → CTA.

## 14. Featured work / content section

Headline: **"Systems we have shipped."**
Three tiles, anonymised by sector (client names only with written permission; `seo/testimonials.json` rule applies):
- Medical university, Hamburg — smart-building infrastructure and LMS for 4,600 m².
- Trades and clinics — AI voice agent and web assistant, enquiries booked in the caller's language.
- SEO agency era — organic traffic and lead generation for SMBs across DE and RO.
Imagery: `Media/medical_ai.png`, `Media/concept_smart_home.png`, `Media/SEO_AI.png` re-graded to the palette. Link to `/blog/` for articles.

## 15. Interactive moment

**"Turn the hourglass."** Press and hold the glowing hourglass SVG. The sand line above flows faster while held, progress ring fills; release early and it eases back. Completing it flips the hourglass and lights up three lines in sequence: "Enquiries answered." "Invoices sent." "Evening free." Reduced motion: final state shown, no hold needed. Lives between Featured work and Final CTA.

## 16. Final CTA section

Headline: **"Find out what AI can automate in your business. Free."**
Body: "Enter your website. In a few minutes you get a report: where you lose enquiries, what AI could handle, and what it would cost. No call required."
Button: "Get my free visibility audit" → opens the existing `audit.js` modal (`window.GeorgeAudit.open()` or the widget's trigger). Secondary link: "Or see fixed packages →" `/pricing/`.
Trust line: "Built and hosted in Germany · GDPR by default · Replies in EN, DE, FR, RO."
Form handling: the widget posts to the existing n8n webhook that emails the report. Success state matches the truth: "Report on its way to your inbox."

## 17. Footer

Wordmark, one-line description, columns: Services (Automation, AI Visibility, Web Systems, Pricing), Company (About, Blog, Contact), Legal (Impressum, Datenschutz from `legal-data.js` identity). Social: LinkedIn, GitHub (muted grey). Line: "© 2026 GeorgeAI · Hanstedt, Germany". Note: "Cinematic imagery generated with AI; the person shown is George." Dark footer `#000305`.

## 18. Complete visual style guide

```css
:root{
  --canvas:#02060a;  --surface:#0f1317;  --card:#0d1116;  --card-border:#35383b;
  --ink:#ffffff;     --body:#c7ccd1;     --muted:#8b9199;  --hairline:#23272b;
  --accent:#fb5e31;  --accent-hover:#ff7a55;  --accent-muted:rgba(251,94,49,.18);
  --btn-label:#02060a;
  --emerald:#19c39a; --emerald-deep:#0b6b58; --emerald-muted:rgba(25,195,154,.14);
  --footer:#000305;
  --tshadow:0 1px 2px rgba(2,6,10,.95),0 3px 12px rgba(2,6,10,.78),0 10px 44px rgba(2,6,10,.8);
  --ease-out:cubic-bezier(.16,1,.3,1); --ease-inout:cubic-bezier(.65,0,.35,1);
}
```
Contrast (computed): ink/canvas 20.3:1, body/canvas 12.6:1, muted/canvas 6.4:1, accent/canvas 6.5:1, emerald `#19c39a` on canvas 9.1:1, btn-label on accent 6.5:1. White on orange is banned (3.1:1). Emerald is for light, borders and glows only, never for body text under 18px.

Spacing scale 4/8/12/16/24/32/48/64/96/144. Radius 12px cards, 999px pills. Grain overlay 4%. Section padding `clamp(96px,12vw,160px)`.

## 19. Typography

- Display: **Plus Jakarta Sans** 700/800 (brand source of truth, vendored woff2 in `seo/vendor/fonts/`). Hero H1 `clamp(2.8rem,7.5vw,7.5rem)`, line-height .95, letter-spacing -.03em. Huge, kinetic.
- Body: **Plus Jakarta Sans** 400/500, 18px/1.6, max `62ch` on the paragraph element.
- Mono labels: **JetBrains Mono** 500, 12–13px, uppercase, tracking .12em, for kickers, counters, HUD chips. (The deviation from the site's single-family rule is deliberate and confined to labels; the brand palette file flags mono headings, not mono labels.)
- Section H2 `clamp(2rem,4.5vw,4.5rem)`. Tabular numerals on all stats.

## 20. Animation direction

- Hero: scrubbed video, `--k` driven entrances per band (see band map), fully reversible.
- Kinetic type: split into `.w`/`.c` spans once at load with seeded RNG; transform and opacity only.
- Sand line: `stroke-dashoffset` driven by ScrollTrigger scrub 1.2 across the page.
- Section entrances: IntersectionObserver `.in`, 80–120 ms stagger, delays retired after entrance.
- One living element per section at whisper level, ≥4 s cycles, negative delays, paused off-screen and on hidden tab.
- Grain: fixed pseudo-element, `steps(8)` background-position loop.
- Nothing snaps. Two easing tokens everywhere.

## 21. Interaction design

- Nav turns glass after 80px scroll; active link underline slides.
- Buttons: 150 ms lift, accent glow on pseudo-element opacity; `:focus-visible` orange ring.
- Cards: hover lift + emerald border; pointer parallax 4px on pillar stills (desktop only).
- Magnetic CTA within 60px radius (desktop, fine pointer).
- Custom cursor: none (keep it honest and fast).
- Press-and-hold hourglass (section 15).

## 22. Scroll behavior

- **Lenis** smooth scroll (lerp .09) synced to GSAP ticker; disabled under reduced motion and on coarse pointers.
- GSAP ScrollTrigger pins the hero stage for 1200vh; progress drives video time through the gated lerp loop.
- Flick test validates every band (120/240/360 px steps; every beat readable 5–6 flicks; none skippable at 360).
- Anchor links scroll via Lenis with offset for the nav.
- `overflow-x: clip` on html and body.

## 23. Mobile behavior

- Five static-hero gates (identical in CSS and JS): ≤720px, portrait ≤1024px, portrait coarse, landscape coarse ≤560px tall, reduced motion. These get the designed still hero with the static copy block; no video or poster download.
- Pillars stack; timeline becomes vertical; stats strip becomes a 2×3 grid.
- Touch targets ≥44px; nav collapses to a sheet.
- Interactive moment works with touch (pointer events).
- Tested at 375×812, 375×667, 768 portrait.

## 24. Technical implementation

Deliverables (static, in `pages/cinematic/` during build, promotable to the site root via `apply_pages`):
```
index.html
style.css
script.js
assets/
  hero-scrub.mp4      (chained 3-segment, -g 8, crf 18–22, faststart, no audio)
  hero-poster.jpg  hero-ending.jpg
  pillar-automation.jpg  pillar-visibility.jpg  pillar-web.jpg  story-portrait.jpg
  work-*.jpg  favicon.svg  grain.png
```
CDN (pinned): GSAP 3.12.x core + ScrollTrigger, Lenis 1.1.x. Fonts: vendored Plus Jakarta Sans + Google JetBrains Mono with preconnect. No React, no build step.

Engineering standard (all mandatory, from `.claude/skills/10k-websites/references/scrub-pipeline.md`):
Blob fetch with streamed loading ring and 20 s watchdog · poster first, video second · dt-normalised lerp loop that rests · gated seeks with error escape · delta-gated DOM writes · band pacing in vh with the flick test · four-layer legibility (base scrim, per-band scrim, text-shadow token, chips) and the worst-frame audit ≥3.5:1 · five live static-hero gates · complete-without-video · reduced motion honoured live in both directions · semantic landmarks, skip link, `aria-hidden` on decoration · `og:` tags with a `<!-- DEPLOY STEP -->` marker.

Copy gate before anyone sees it: grep for em dashes and for leverage, seamless, empower, unlock, robust, actionable, data-driven, solutions, testament, landscape, delve, elevate. Zero hits.

Deploy: the page is a repo-owned static page, so it ships through the existing pipeline (`pages/` → `apply_pages` → `./deploy.sh --no-content` → rsync → nginx on the VPS). The `apply_widget` layer injects the audit widget automatically. Hostinger is connected but this site lives on the existing VPS; Hostinger stays as an option for a temporary preview subdomain.

Every viewer-facing line in this plan ships verbatim.
