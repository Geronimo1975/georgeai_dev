# Free Visibility Audit widget — design

**Date:** 2026-07-02
**Status:** approved by George (conversation, 2026-07-02)

## Goal

Lead-generation widget on georgeai.dev: a floating "Free Visibility Audit" button
opens a modal form (First name, Surname, Email, Contact number, Website URL).
Submission triggers an automated SEO / AEO / AIO / GEO audit of the prospect's
site, delivered by email. Test case: macrocosm.co.za.

## Architecture

```
georgeai.dev (static, nginx)                n8n (app.n8n-studio.com)
┌──────────────────────────┐   POST JSON   ┌─────────────────────────────────┐
│ audit.js                 │ ────────────▶ │ Webhook georgeai-free-audit     │
│  floating button + modal │  (CORS)       │  → validate + sanitize          │
│  5 fields + honeypot     │ ◀──────────── │  → respond immediately          │
└──────────────────────────┘   200 JSON    │  → save lead (Data Table)       │
                                           │  → notify George (Gmail)        │
                                           │  → parallel site checks         │
                                           │  → Claude synthesizes report    │
                                           │  → Gmail report to prospect     │
                                           └─────────────────────────────────┘
```

## Frontend (this repo)

- **`backend/assets/audit.js`** — self-contained IIFE, CSS injected from JS,
  no dependencies. Kept out of the design export (same rationale as `auth.js`)
  so it survives re-exports.
- **Floating button** bottom-right, coral `#cc785c`, per `DESIGN-claude.md`
  (serif modal title, cream surfaces, 8/12px radii, coral CTA).
- **Modal fields:** First name, Surname, Email, Contact number, Website URL.
  Client-side validation; URL auto-normalized to `https://`. Hidden honeypot
  field for spam; submissions with it filled are dropped server-side.
- **Submit:** `POST` JSON to the n8n production webhook. Success → inline
  confirmation ("Your audit is on its way — check your inbox"). Failure →
  error message with `mailto:` fallback.
- **`deploy.sh`** gains an idempotent step (runs also with `--no-content`):
  copy `backend/assets/auth.js` and `backend/assets/audit.js` into `site/`
  (fixes the current `/auth.js` 404 in nginx-only prod) and inject
  `<script src="/audit.js" defer>` into `index.html`.

## n8n workflow `georgeai-free-audit`

1. **Webhook** (POST, path `georgeai-free-audit`, CORS restricted to
   georgeai.dev origins, respond immediately with `{ok: true}`).
2. **Validate**: required fields, email/URL shape, honeypot empty — else stop.
3. **Save lead** to n8n Data Table `audit_leads`; **notify George** via Gmail.
4. **Checks** against the submitted URL (tolerant of failures — a missing
   robots.txt is itself a finding):
   - homepage HTML: title, meta description, headings, OG tags, JSON-LD schema
   - `robots.txt`: rules for GPTBot, ClaudeBot, PerplexityBot, Google-Extended, CCBot
   - `llms.txt` present/absent
   - `sitemap.xml`, HTTPS/redirect behavior, canonical
   - Google PageSpeed Insights API (mobile; Core Web Vitals)
5. **Claude API node** (claude-sonnet-5): synthesizes an HTML report with a
   score per section (SEO / AEO / AIO / GEO), concrete findings, 3–5 priority
   recommendations, georgeai.dev branding and CTA to services.
6. **Gmail**: report to prospect (from George's Gmail), copy/notification to
   George.

## Out of scope (YAGNI)

Django backend changes, double opt-in, PDF generation, server-side rate
limiting beyond honeypot + n8n validation.

## Testing

- Local: open `site/index.html` after a dry-run injection; verify modal UX and
  a mocked webhook call.
- E2E: submit the live form with macrocosm.co.za as the audit URL; verify lead
  row, notification email, and report email.
