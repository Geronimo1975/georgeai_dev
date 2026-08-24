# Stripe go-live runbook

**Status as of 2026-08-19: still TEST mode.** `tests/test_payments_pipeline.py`
passes 15/15, but it passes *because* `EXPECTED_STRIPE_MODE` defaults to `test`.
Every buy button on `/pricing/` points at a sandbox Payment Link
(`acct_1TIuuYEffkWmXH1r`, get-hub Sandbox). **Nobody can pay you right now.**

This cannot be automated end to end from this repo: the `STRIPE_TOKEN` in the
root `.env` is an `rk_test_` restricted **test** key. Creating live Payment
Links needs a live-mode key, and switching a business to taking real money is a
decision, not a deploy step.

## Before you start

- [ ] Stripe account is out of sandbox: business details, bank account, and tax
      settings completed and verified.
- [ ] You have decided the seven prices are final. They live in **three** places
      that must agree — `pages/pricing/index.html`, Stripe, and the `CATALOG`
      dict in `tests/test_payments_pipeline.py`. The suite exists to catch
      exactly that drift.
- [ ] A live-mode restricted key with write access to Payment Links and Prices.
      Give it the narrowest scopes that work: `Products: write`,
      `Prices: write`, `Payment Links: write`, `Checkout Sessions: read`.

## Steps

1. **Put the live key in the root `.env`** as `STRIPE_TOKEN_LIVE` (keep the test
   key in place — the suite still needs it to check the test pipeline).

2. **Recreate the seven products, prices and links in live mode.** Each Payment
   Link and product must carry `metadata.data_product = <slug>`; that metadata
   is the only thing tying a `checkout.session.completed` event back to a
   product in the n8n `stripe-orders` workflow. Get the slugs from
   `docs/stripe-payment-links.md`. Miss the metadata and orders land in the
   table with a null product.

3. **Swap the URLs** in `pages/pricing/index.html` (7 `data-product` buttons)
   and update `docs/stripe-payment-links.md` with the new IDs.

4. **Point n8n at live.** The `stripe-orders` workflow on
   **app.n8n-studio.com** (George's own VPS — not `n8n.rotocon.world`) needs a
   live-mode webhook endpoint and signing secret registered in Stripe for
   `checkout.session.completed`.

5. **Flip the expectation and redeploy:**
   ```bash
   ./deploy.sh
   GEORGEAI_STRIPE_MODE=live python3 tests/test_payments_pipeline.py
   ```
   Then set `GEORGEAI_STRIPE_MODE=live` in the crontab (`cron/README.md`) and in
   the `payments-pipeline.yml` GitHub Actions workflow, so the 6-hourly check
   guards the live chain instead of the dead test one.

6. **Buy something.** One real purchase of the cheapest product, with a real
   card. Confirm: the Stripe payment succeeds, the n8n `orders` table gets a row
   with the right `data_product`, and the confirmation email arrives. Then
   refund it.

## Rollback

Swap the URLs in `pages/pricing/index.html` back to the test links, redeploy,
and unset `GEORGEAI_STRIPE_MODE`. The live links can stay — deactivating them
in Stripe is enough. Nothing else in the repo is mode-aware.
