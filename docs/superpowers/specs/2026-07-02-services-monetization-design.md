# georgeai.dev — Productized Services & Monetization (Phase 1)

**Date:** 2026-07-02
**Status:** Approved by George (copy, prices, and two-phase approach confirmed)
**Goal:** The site must generate revenue directly: visitors can buy productized
automation services on the page, without a sales call for the entry products.

## Positioning rule (governs all copy)

**Sell outcomes, never tools.** Client-facing copy names the result ("we find
you customers", "your inbox sorts itself", "instant answers about your
business"). The delivery stack — Apify, Apollo.io, n8n, Make.com, monday.com,
Python/Django, DataForSEO, Ahrefs, WordPress — is internal and never appears on
the page. The only implicit technology signal is credibility copy:
*"Engineer, not agency."*

## Hero (announcement)

> **"AI automations that pay for themselves."**
> AI systems delivered by a Python engineer with 4 years in AI &
> digitalization — not an agency reselling tools. 100% GDPR-compliant, built
> for the German market.

- Primary CTA: **"Order a Lead Pack — 100 verified contacts, €299"** (direct Stripe checkout)
- Secondary CTA: **"Free automation audit"** (booking / contact)

## Product catalog (final copy + prices)

Page order is deliberate: two low-ticket direct-purchase products first, then
high-ticket recurring services that route through the free audit call.

| # | Client-facing name | Price | Promise (site copy) | Internal fulfillment (never on page) |
|---|---|---|---|---|
| 1 | **New Customers, Delivered** | €299 one-time (100 contacts); €990 (500) | "100 verified decision-makers from your exact target market — name, role, email, phone — ready to contact. Delivered in 5 days." | Apify scraping → Apollo.io enrichment/verification → n8n dedupe/validation → CSV/Sheet delivery; order tracked on monday.com |
| 2 | **Get Found — by Google and by AI** | €490 one-time | "A complete report showing where your business is invisible — in Google and in ChatGPT/AI search — and exactly what to fix. In 48 hours." | DataForSEO + Ahrefs MCP + seo-*/geo-* agents → PDF report |
| 3 | **Your Phone, Answered 24/7** | €990 setup + from €690/mo | "Every call answered. Every appointment booked. Every lead qualified — even at 2 AM. Fully GDPR-compliant." | Vapi/Retell voice platform + n8n booking & CRM sync; AI disclosure per EU AI Act Art. 50 |
| 4 | **A Website That Sells While You Sleep** | €1,900 setup + from €390/mo | "Your website answers customer questions instantly, in their language, and captures every lead." | Custom chatbot, Python/Django + RAG on client data |
| 5 | **Your Business on Autopilot** | from €2,500 project + from €750/mo | "Your inbox sorts itself. Double work disappears. You see everything that matters about your business — instantly, in one place." | n8n/Make workflows, monday.com, ERP integrations, automated DB analyses + crons + periodic tests ("Managed Monitoring") |
| 6 | **A Steady Stream of Interested Prospects** | €990/mo | "Qualified prospects replying in your inbox every week. Native-German outreach, fully compliant, done for you." | Apollo lists + n8n sequences + WordPress landing pages |

**Trust band (no tool names):**
*"4 years building AI systems for real businesses · Engineer, not agency ·
GDPR-first · Made for the German market"*

## Compliance constraints (DACH)

- Never advertise "AI cold calls". Voice product is positioned as inbound
  receptionist, lead qualification, follow-up, customer reactivation.
- B2B outbound calls require documented presumed consent (UWG §7).
- From 2026-08-02, EU AI Act Art. 50 requires disclosing that a caller/chat
  agent is an AI. Compliance is a *selling point* in copy ("fully
  GDPR-compliant"), and a delivery requirement.

## Architecture — Phase 1 (no new backend)

1. **`/services` page, repo-owned.** Static HTML written by hand in this repo
   (NOT in the design tool export), styled per `DESIGN-claude.md`
   (cream/coral/dark, #cc785c primary). Deployed by `deploy.sh` the same way
   as the `seo/` layer (copied into `site/` on every deploy, idempotent,
   survives re-exports). nginx serves it; add a location/rewrite so
   `/services` resolves to the file.
2. **Stripe Payment Links** on every product card: one-time payments for Lead
   Packs, audit, and setup fees; subscriptions for monthly retainers. No
   server code. George creates the links in the Stripe dashboard; the page
   references them as plain URLs.
3. **Order pipeline (n8n, account: app.n8n-studio.com):**
   Stripe webhook → n8n workflow →
   (a) notify George (Telegram/email),
   (b) create an item on a monday.com "Orders" board with a status pipeline,
   (c) send the client an onboarding email (for Lead Packs: an ICP/niche
   specification form).
4. **Fulfillment: semi-automatic at launch.** Orders land on the monday.com
   board; George runs the Lead Pack pipeline from Claude Code using installed
   MCPs (Apollo, Apify-style scraping, DataForSEO) — ~30 min/order. Full n8n
   automation only after demand is validated.
5. **Homepage links:** the existing export's nav gains a link to `/services`
   (injected by `deploy.sh`, idempotent, same pattern as `auth.js`).

## Phase 2 (explicitly out of scope now)

Django client portal (auth already exists in `backend/`): order history,
downloadable deliverables (lead packs, reports), integrated Stripe Checkout,
invoicing. Build only after 5–10 Phase-1 sales.

## Error handling / edge cases

- Stripe webhook loss: n8n workflow failures alert George; monday.com board is
  the source of truth for open orders, reconciled against the Stripe dashboard.
- Payment Link opened but not paid: no action (Stripe handles cart recovery
  emails if enabled).
- The `/services` page must not depend on `support.js` or the export's client-
  side rendering — it is self-contained HTML/CSS (inline or repo-owned assets).

## Testing / acceptance

- `./deploy.sh --no-content` publishes the page; `https://georgeai.dev/services`
  returns 200 with correct styling on mobile + desktop.
- Every Buy button opens the correct Stripe checkout with the correct price.
- A Stripe test-mode payment produces: Telegram/email notification + monday.com
  order item + client onboarding email.
- Homepage nav shows the Services link after a full re-export deploy.

## Open items (need George / external dashboards)

- Stripe account payment links (7 links: 299, 990, 490, 990+690/mo, 1900+390/mo,
  2500+750/mo, 990/mo) — created in Stripe dashboard, test mode first.
- monday.com "Orders" board (can be created via MCP).
- Booking mechanism for the free audit (mailto at launch; Cal.com later).
