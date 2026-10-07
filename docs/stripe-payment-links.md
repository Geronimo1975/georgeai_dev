# Stripe Payment Links

**Account:** get-hub (`acct_1TIuuPRAac2j9d6w`) — **LIVE MODE** since 2026-08-30.
Sandbox was `acct_1TIuuYEffkWmXH1r`; test card `4242 4242 4242 4242`.

**The seven buy buttons now point at live Payment Links.** `scripts/stripe_golive.py
--apply --write-html` created the live catalogue and rewrote the hrefs, replacing the
`mailto:` order mails from `39e6f31`. The test links below still exist in the sandbox
and are no longer linked from anywhere.

## Go-live: `scripts/stripe_golive.py`

Do not rebuild the catalog by hand in the dashboard — a mistyped `690` for a
`69000` is a real invoice. The script mirrors the catalog below into live mode
(7 products, 10 prices, 7 payment links, each carrying
`metadata.data_product`), idempotently, and can swap the hrefs in one pass:

```bash
python3 scripts/stripe_golive.py                        # dry run — prints the plan, writes nothing
python3 scripts/stripe_golive.py --apply                # create in live mode
python3 scripts/stripe_golive.py --apply --write-html   # + rewrite the 7 buy hrefs
```

It reads `STRIPE_LIVE_TOKEN` from the repo-root `.env` (a **restricted live**
key with write access to Products, Prices, Payment Links), never prints it, and
refuses to run against a `_test_` key. Re-running is safe: anything already
carrying the slug in `metadata.data_product` is reused, not duplicated.

| data-product | Payment Link |
|---|---|
| lead-pack-100 | https://buy.stripe.com/14AbJ365u63EcZE0fa7ss00 |
| lead-pack-500 | https://buy.stripe.com/7sYfZj9hG8bM7Fke607ss01 |
| visibility-audit | https://buy.stripe.com/eVqdRbbpO9fQgbQaTO7ss02 |
| phone-24-7 | https://buy.stripe.com/5kQ00l8dC3Vw1gWaTO7ss03 |
| chatbot | https://buy.stripe.com/cNi6oJeC02Rs6Bg1je7ss04 |
| autopilot | https://buy.stripe.com/aFa8wRfG463Ef7M2ni7ss05 |
| prospects | https://buy.stripe.com/3cI14p2Ti3Vw8Jo0fa7ss06 |

All links: currency EUR, tax behavior exclusive, billing address collection **required**,
phone number collection **on**. Each payment link and product carries
`metadata.data_product = <slug>` so the n8n webhook (Task 6) can map a
`checkout.session.completed` event back to the product.

## Catalog (product / price IDs, LIVE mode)

| data-product | Product | Prices |
|---|---|---|
| lead-pack-100 | `prod_VAXOGf6KWivGJ7` | `price_1UACJGRAac2j9d6wzdiV3UEA` — €299 one-time |
| lead-pack-500 | `prod_VAXOYoqD9roS6f` | `price_1UACJIRAac2j9d6wpFkHb4Xp` — €990 one-time |
| visibility-audit | `prod_VAXOjCkUaVhkKh` | `price_1UACJKRAac2j9d6wJEBYVP9h` — €490 one-time |
| phone-24-7 | `prod_VAXOpgaGBt2d0u` | `price_1UACJNRAac2j9d6wrB9vbeT2` — €690/mo · `price_1UACJNRAac2j9d6wOnYwxnAF` — €990 setup |
| chatbot | `prod_VAXOokC1pT5VBQ` | `price_1UACJQRAac2j9d6wxD1VUFbI` — €390/mo · `price_1UACJQRAac2j9d6wephrtn6M` — €1,900 setup |
| autopilot | `prod_VAXOCQ7KY1A4Dp` | `price_1UACJTRAac2j9d6wKgEGuZPq` — €750/mo · `price_1UACJURAac2j9d6w9dUDWRcs` — €2,500 setup |
| prospects | `prod_VAXObI4hhmQtRG` | `price_1UACJWRAac2j9d6w4uwHZShD` — €990/mo |

Setup + subscription products combine both prices in one payment link (the
setup fee lands on the first invoice).

## Order storage: n8n data table `orders`

- data table `orders` (`MGvuy74ouTb6vUpB`) on **app.n8n-studio.com** (George's OWN n8n, his VPS) — columns: status, product, amount, email, client_name, session_id, ordered_at
- REPLACES the earlier monday.com Orders board (`5099628523`), which was **deleted 2026-07-02**: it had been created on the Rotocon company monday account by mistake — order data must never live on the employer's account. If monday tracking is wanted later, use a personal/georgeai monday account + its own n8n credential.

## n8n stripe-orders workflow

- workflow `stripe-orders` (`Nx1WqOlQ1k3IWdgB`) on https://app.n8n-studio.com — ACTIVE, E2E-tested 2026-07-02 (real test purchase → all 4 nodes success); export in `docs/n8n-stripe-orders.json`. Old copy on n8n.rotocon.world (`hGndKGfKRk9tKIoG`) DEACTIVATED — wrong instance, see .claude/skills/georgeai-n8n.
- webhook (production): `https://app.n8n-studio.com/webhook/stripe-orders` (POST) — Stripe endpoint `we_1UACLTRAac2j9d6whC5N047r` (LIVE, checkout.session.completed); sandbox endpoint was `we_1TopbREffkWmXH1rTlxClClL`
- flow: checkout.session.completed → **fetch-back session from Stripe API** (anti-forgery: forged webhook posts die on the fetch; all order data incl. the client email comes from Stripe, never from the raw POST) → (Brevo email to George) + (row in `orders` data table, status=New) + (Brevo onboarding email to client; lead packs get the ICP questionnaire)
- credentials on app.n8n-studio.com: `Stripe account` (`OnWk28SXJXBAkCl0`) for the fetch-back — **must hold a LIVE key now that the buttons are live; a test key makes every real checkout fail at the fetch-back**; `Brevo SMTP` (`aK6Bete8OTRMNACY`, sender george.cucuiet@gmx.de) for both emails.
- go-live checklist, in order:
  1. ~~Impressum~~ **done** (2026-08-26) — `seo/legal.json` carries Greuner Brook 1,
     21271 Hanstedt and the § 19 UStG Kleinunternehmer note; `apply_legal` re-applies
     it in all 5 languages on every deploy. Not yet deployed.
     Because of § 19 the live prices are created with `tax_behavior: "inclusive"`:
     no VAT is added, so €299 is charged as €299. The `/pricing/` page carries no
     VAT qualifier next to the prices — worth adding a "§ 19 UStG — no VAT charged"
     line for German buyers, but that is sales copy, not a blocker.
  2. `python3 scripts/stripe_golive.py --apply --write-html` (needs `STRIPE_LIVE_TOKEN`).
  3. Add a **LIVE-mode** webhook endpoint in Stripe with the same URL,
     `https://app.n8n-studio.com/webhook/stripe-orders`, event `checkout.session.completed`.
  4. Swap the n8n `Stripe account` credential (`OnWk28SXJXBAkCl0`) to a live restricted
     key — the workflow's anti-forgery fetch-back cannot read a live session with a test key.
  5. `./deploy.sh --no-content`, then
     `GEORGEAI_STRIPE_MODE=live python3 tests/test_payments_pipeline.py`.
  6. Set `GEORGEAI_STRIPE_MODE=live` in the crontab (`cron/README.md`).
  7. One real low-value purchase end-to-end, then refund it.
  - Optional: verify contact@georgeai.dev as Brevo sender for nicer branding.
- known limitation (accepted for Phase 1): no dedup on session id — a Stripe webhook retry could create a duplicate order row/email. Add a rowNotExists check before insert if it ever happens in practice.


