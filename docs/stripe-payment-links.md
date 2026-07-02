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

## monday.com Orders board

- board_id: `5099628523` (private, workspace rotocon-world) — https://rotocon-world.monday.com/boards/5099628523
- columns: status=`color_mm4wwx4p` (New / In progress / Delivered / Canceled), product=`text_mm4w8h7g`, amount=`numeric_mm4w1shj`, email=`email_mm4wv0kj`, stripe_session=`text_mm4wv6td`
- email column payload must be an object: `{"email": "...", "text": "..."}` (plain string is rejected)
- smoke-test item "TEST — delete me" (`3043643341`) left on the board — delete after verifying

