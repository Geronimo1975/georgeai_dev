# Stripe Payment Links

**Account:** get-hub Sandbox (`acct_1TIuuYEffkWmXH1r`) — **TEST MODE**.
Test checkout card: `4242 4242 4242 4242`.

**Production currently sells through `mailto:`, not Stripe.** Commit `39e6f31`
replaced all 7 buy hrefs with prefilled order mails so that no visitor could be
sent into a sandbox checkout. The test links below still exist in Stripe; they
are simply not linked from anywhere. Go-live re-wires the buttons — see the
checklist at the bottom of this file.

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
| lead-pack-100 | https://buy.stripe.com/test_dRm5kD1hP0Hget1cpVdEs00 |
| lead-pack-500 | https://buy.stripe.com/test_00waEX7Gd0Hg70zey3dEs01 |
| visibility-audit | https://buy.stripe.com/test_fZu5kD3pX3Ts84D89FdEs02 |
| phone-24-7 | https://buy.stripe.com/test_00w9ATd0xey6acLcpVdEs03 |
| chatbot | https://buy.stripe.com/test_9B63cv5y5ahQ4Srey3dEs04 |
| autopilot | https://buy.stripe.com/test_14AcN5gcJ0Hg5Wv4XtdEs05 |
| prospects | https://buy.stripe.com/test_9B6fZh9Oley62Kj4XtdEs06 |

All links: currency EUR, tax behavior exclusive, billing address collection **required**,
phone number collection **on**. Each payment link and product carries
`metadata.data_product = <slug>` so the n8n webhook (Task 6) can map a
`checkout.session.completed` event back to the product.

## Catalog (product / price IDs, test mode)

| data-product | Product | Prices |
|---|---|---|
| lead-pack-100 | `prod_UoQn98E9ifNZd9` | `price_1TonwqEffkWmXH1rOvY4zFVJ` — €299 one-time |
| lead-pack-500 | `prod_UoQoh1zTiS3Ghv` | `price_1TonwsEffkWmXH1rS6zkF0xL` — €990 one-time |
| visibility-audit | `prod_UoQoe6TR042jjY` | `price_1TonwuEffkWmXH1rrktBIMbX` — €490 one-time |
| phone-24-7 | `prod_UoQocGs4beo9rQ` | `price_1TonwyEffkWmXH1rYcA3Xv84` — €690/mo · `price_1TonwwEffkWmXH1rsrPYrqDp` — €990 setup |
| chatbot | `prod_UoQoeY3J47m1AI` | `price_1Tonx2EffkWmXH1rtDmLFcWF` — €390/mo · `price_1Tonx0EffkWmXH1rzKmQvutG` — €1,900 setup |
| autopilot | `prod_UoQodzPVUIdu9h` | `price_1Tonx7EffkWmXH1rLT2P9umh` — €750/mo · `price_1Tonx5EffkWmXH1rNxu3gQYp` — €2,500 setup |
| prospects | `prod_UoQo52WQMgCxkk` | `price_1Tonx9EffkWmXH1rPZKfbLmw` — €990/mo |

Setup + subscription products combine both prices in one payment link (the
setup fee lands on the first invoice).

## Order storage: n8n data table `orders`

- data table `orders` (`MGvuy74ouTb6vUpB`) on **app.n8n-studio.com** (George's OWN n8n, his VPS) — columns: status, product, amount, email, client_name, session_id, ordered_at
- REPLACES the earlier monday.com Orders board (`5099628523`), which was **deleted 2026-07-02**: it had been created on the Rotocon company monday account by mistake — order data must never live on the employer's account. If monday tracking is wanted later, use a personal/georgeai monday account + its own n8n credential.

## n8n stripe-orders workflow

- workflow `stripe-orders` (`Nx1WqOlQ1k3IWdgB`) on https://app.n8n-studio.com — ACTIVE, E2E-tested 2026-07-02 (real test purchase → all 4 nodes success); export in `docs/n8n-stripe-orders.json`. Old copy on n8n.rotocon.world (`hGndKGfKRk9tKIoG`) DEACTIVATED — wrong instance, see .claude/skills/georgeai-n8n.
- webhook (production): `https://app.n8n-studio.com/webhook/stripe-orders` (POST) — Stripe endpoint `we_1TopbREffkWmXH1rTlxClClL` (sandbox, name georgeai-stripe-orders)
- flow: checkout.session.completed → **fetch-back session from Stripe API** (anti-forgery: forged webhook posts die on the fetch; all order data incl. the client email comes from Stripe, never from the raw POST) → (Brevo email to George) + (row in `orders` data table, status=New) + (Brevo onboarding email to client; lead packs get the ICP questionnaire)
- credentials on app.n8n-studio.com: `Stripe account` (`OnWk28SXJXBAkCl0`, restricted test key) for the fetch-back; `Brevo SMTP` (`aK6Bete8OTRMNACY`, sender george.cucuiet@gmx.de) for both emails.
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


