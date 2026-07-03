#!/usr/bin/env bash
#
# cron/check_payments.sh — scheduled health check for the georgeai.dev
# payments pipeline. Runs tests/test_payments_pipeline.py, keeps a log,
# and exits non-zero on any failure (so cron's MAILTO fires).
#
# Schedule (crontab -e), e.g. every 6 hours:
#   MAILTO=contact@georgeai.dev
#   0 */6 * * * /Users/Geronimo/Projects/georgeai_dev/cron/check_payments.sh
#
# After go-live, switch the expected Stripe mode:
#   0 */6 * * * GEORGEAI_STRIPE_MODE=live /Users/Geronimo/Projects/georgeai_dev/cron/check_payments.sh
#
set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_DIR="$PROJECT_DIR/cron/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/payments-$(date +%Y%m%d).log"

{
  echo "===== $(date '+%Y-%m-%d %H:%M:%S') ====="
  if python3 "$PROJECT_DIR/tests/test_payments_pipeline.py"; then
    echo "RESULT: OK"
    STATUS=0
  else
    echo "RESULT: FAILURES DETECTED"
    STATUS=1
  fi
} >> "$LOG_FILE" 2>&1

# keep the last 30 daily logs
ls -1t "$LOG_DIR"/payments-*.log 2>/dev/null | tail -n +31 | xargs rm -f 2>/dev/null || true

# on failure, print the day's log to stdout so cron mails it (MAILTO)
if [ "$STATUS" -ne 0 ]; then
  cat "$LOG_FILE"
fi
exit "$STATUS"
