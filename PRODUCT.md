# Product

## Register

brand

## Users

Owner-operators of small German trades, clinics, and service firms (Handwerk, Praxen, Dienstleister) — people who run the business AND answer the phone, so enquiries that come in outside working hours (evenings, Saturdays) get missed and lost. They land on georgeai.dev evaluating whether to hire George for a pilot: skimming for credibility (years, project count, language coverage), scanning the services on offer, and looking for a low-commitment next step (book a pilot call) rather than a hard sale.

## Product Purpose

georgeai.dev is George's solo-consultant portfolio and sales site for AI voice agent + AI website assistant services aimed at German SMBs. The AI agent answers the phone and the site, qualifies the enquiry, and books it into the owner's calendar — day or night, in the caller's language. The site's job is to convert a skimming visitor into a booked pilot conversation. Success = enquiries reaching "See the services" / "Ask about a pilot" / "Book a pilot call" and actually completing that action — which requires those CTAs to be real, working, accessible links, not decorative dead ends.

## Brand Personality

Credible, direct, warm-professional. A solo consultant who has done this 40+ times over 8+ years in five languages, speaking plainly to a busy owner-operator — not a startup selling hype, not a faceless agency. Confidence comes from specifics (years, project count, ~2-week pilot timeline, real Impressum/legal presence), not from marketing adjectives.

## Anti-references

- Generic SaaS template clichés: gradient hero-metric blocks, identical icon+heading card grids, glassmorphism-as-decoration.
- "AI slop" patterns already found on this homepage: pseudo-links (`onClick` with no `href`), a "View all →" and project cards that look clickable but have no handler at all (Selected Work section) — anything that *looks* interactive but doesn't work erodes exactly the trust this site is trying to build.
- Cold corporate-agency impersonality — the site should read as one credible person, not an anonymous enterprise vendor.
- Drifting off the established cream/coral/serif editorial identity (see DESIGN-claude.md) toward generic cool-blue/slate "AI tool" visual defaults.

## Design Principles

1. **No dead or pseudo-links.** Every element that visually reads as a link or CTA (cursor:pointer, an arrow, "View all") must actually navigate — and where it points to another page/section, it should be a real semantic `<a href>`, not an `onClick`-only span, so it's crawlable and keyboard-operable.
2. **Trust is the conversion lever.** Prioritize concrete credibility signals (years, project count, languages, legal/Impressum completeness) over generic marketing claims — this is a direct carryover from the `trust-and-positioning-remediation` branch this repo is currently on.
3. **Protect the cream/coral/serif editorial identity.** It's a deliberate counter-positioning against cold-blue "AI tool" competitors (per DESIGN-claude.md) — don't reach for generic SaaS defaults when fixing or extending sections.
4. **Speak to the missed-call pain, not abstract AI capability.** Copy and CTAs should stay anchored to "the enquiry you miss on a Saturday," not feature lists.
5. **Repo-side HTML fixes are provisional.** `site/GeorgeAI.dc.html` and `frontend/template/` are wiped and regenerated from `exports/*.zip` on every `./deploy.sh` run. A fix applied directly there is a stopgap until the same change is made in the source design-tool export — flag this every time such a file is edited.

## Accessibility & Inclusion

Target WCAG AA. Every navigational CTA and card must be a real `<a href>` (or correct interactive semantics) with a visible focus state and full keyboard operability — no `onClick`-only spans/divs standing in for links, no interactive element missing `role`/`tabindex` where a native element isn't used.
