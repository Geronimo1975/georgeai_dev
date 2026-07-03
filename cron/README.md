# cron/ — scheduled site & payments verification

Professional monitoring layer for georgeai.dev. Each runner wraps a test
suite from `tests/`, logs to `cron/logs/` (gitignored, last 30 days kept),
and exits non-zero on failure so cron's `MAILTO` sends an alert.

| Runner | Suite | What it guards |
|---|---|---|
| `check_payments.sh` | `tests/test_payments_pipeline.py` | The money path: /pricing/ page (7 buy buttons, copy rules, sitemap), Stripe payment links + prices + page↔Stripe consistency, n8n stripe-orders workflow active + webhook up + `orders` table schema + no failed order executions |

## Install (crontab)

```cron
MAILTO=contact@georgeai.dev
# payments pipeline — every 6 hours
0 */6 * * * /Users/Geronimo/Projects/georgeai_dev/cron/check_payments.sh
```

The tests read `STRIPE_TOKEN` and `N8N_API_KEY` from the repo-root `.env`
(never committed, never printed). All checks are **read-only / side-effect
free** — no orders are created, no emails sent, no money moved.

## Go-live switch

The suite asserts the Stripe mode it expects (default: `test`). After
switching the site to live payment links, run with:

```cron
0 */6 * * * GEORGEAI_STRIPE_MODE=live /Users/Geronimo/Projects/georgeai_dev/cron/check_payments.sh
```

## Running manually

```bash
python3 tests/test_payments_pipeline.py   # standalone, no dependencies
pytest tests/ -v                          # same checks via pytest
./cron/check_payments.sh                  # exactly what cron runs (logs + exit code)
```

## Adding a new suite

1. Add `tests/test_<area>.py` — plain `test_*` functions with asserts,
   stdlib-only HTTP, plus the same `main()` runner pattern.
2. Add `cron/check_<area>.sh` copied from `check_payments.sh`.
3. Register it in the crontab and in the table above.
