# Stripe Payment Links

**Account:** get-hub Sandbox (`acct_1TIuuYEffkWmXH1r`) — **TEST MODE**.
Before real sales: recreate these in live mode (same catalog below), swap the URLs
in `pages/pricing/index.html`, and redeploy. Test checkout card: `4242 4242 4242 4242`.

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

- data table `orders` (`Safgo17NCrOS579A`) on **n8n.rotocon.world** (George's personal n8n project) — columns: status, product, amount, email, client_name, session_id, ordered_at
- REPLACES the earlier monday.com Orders board (`5099628523`), which was **deleted 2026-07-02**: it had been created on the Rotocon company monday account by mistake — order data must never live on the employer's account. If monday tracking is wanted later, use a personal/georgeai monday account + its own n8n credential.

## n8n stripe-orders workflow

- workflow `stripe-orders` (`hGndKGfKRk9tKIoG`) on https://n8n.rotocon.world — ACTIVE; export in `docs/n8n-stripe-orders.json`
- webhook (production): `https://n8n.rotocon.world/webhook/stripe-orders` (POST)
- flow: checkout.session.completed → **fetch-back session from Stripe API** (anti-forgery: forged webhook posts die on the fetch; all order data incl. the client email comes from Stripe, never from the raw POST) → (Gmail notify George) + (monday Orders item, Status=New) + (Gmail onboarding email to client; lead packs get the ICP questionnaire)
- **MANUAL STEP 1 (2 min):** create an n8n credential named **"Stripe API"** (type: Stripe API) with a restricted key (read access to Checkout Sessions is enough) and assign it to the "Fetch Session from Stripe" node.
- **MANUAL STEP 2 (2 min):** the Stripe MCP cannot create webhook endpoints. In the Stripe dashboard (test mode) → Developers → Webhooks → Add endpoint: URL `https://n8n.rotocon.world/webhook/stripe-orders`, event `checkout.session.completed`. Repeat in live mode when switching the links live.
- known limitation (accepted for Phase 1): no dedup on session id — a Stripe webhook retry could create a duplicate monday item/email. Add a lookup-before-create if it ever happens in practice.


