#!/usr/bin/env python3
"""Payments-pipeline health checks for georgeai.dev.

Validates the whole order chain end-to-end, read-only / side-effect-free,
so it is safe to run on a cron schedule:

  1. Site      — /pricing/ live, 7 buy buttons, correct slugs, copy rules,
                 sitemap + homepage links.
  2. Stripe    — the 7 Payment Links exist, are active, carry the right
                 metadata.data_product, their prices match the catalog, and
                 the live page's buy hrefs point at exactly those links.
  3. n8n       — the stripe-orders workflow is active on app.n8n-studio.com,
                 the `orders` data table exists with the expected columns,
                 and the production webhook answers (with a filtered ping
                 that the workflow ignores — no orders, no emails).

Run directly (cron-friendly, exit code 0/1):   python3 tests/test_payments_pipeline.py
Or with pytest (developer workflow):           pytest tests/ -v

Secrets come from the repo-root .env (STRIPE_TOKEN, N8N_API_KEY) and are
never printed. Expected Stripe mode is "test" until go-live — then set
GEORGEAI_STRIPE_MODE=live (env) or flip EXPECTED_STRIPE_MODE below.
"""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from functools import lru_cache
from pathlib import Path

# --------------------------------------------------------------------------
# configuration
# --------------------------------------------------------------------------
ROOT = Path(__file__).resolve().parents[1]

SITE = "https://georgeai.dev"
N8N_BASE = "https://app.n8n-studio.com"          # George's OWN instance — see .claude/skills/georgeai-n8n
N8N_WORKFLOW_ID = "Nx1WqOlQ1k3IWdgB"             # stripe-orders
N8N_ORDERS_TABLE_ID = "MGvuy74ouTb6vUpB"         # data table `orders`
ORDERS_COLUMNS = {"status", "product", "amount", "email", "client_name", "session_id", "ordered_at"}

EXPECTED_STRIPE_MODE = os.environ.get("GEORGEAI_STRIPE_MODE", "test")  # "test" | "live"

# slug -> expected price amounts in EUR cents (None = not applicable)
CATALOG = {
    "lead-pack-100":    {"one_time": 29900,  "monthly": None},
    "lead-pack-500":    {"one_time": 99000,  "monthly": None},
    "visibility-audit": {"one_time": 49000,  "monthly": None},
    "phone-24-7":       {"one_time": 99000,  "monthly": 69000},
    "chatbot":          {"one_time": 190000, "monthly": 39000},
    "autopilot":        {"one_time": 250000, "monthly": 75000},
    "prospects":        {"one_time": None,   "monthly": 99000},
}

# outcome-only copy rule: these must never appear on the sales page
FORBIDDEN_WORDS = ("apify", "apollo", "n8n", "make.com", "monday", "django", "dataforseo", "wordpress")
TRUST_COPY = "Engineer, not agency"

TIMEOUT = 30


def _load_env() -> dict:
    env = {}
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                env[k.strip()] = v.strip()
    env.update({k: v for k, v in os.environ.items() if k in ("STRIPE_TOKEN", "N8N_API_KEY")})
    return env


ENV = _load_env()


# --------------------------------------------------------------------------
# http helpers (stdlib only — no pip dependencies for the cron runner)
# --------------------------------------------------------------------------
def _http(url: str, headers: dict | None = None, data: bytes | None = None,
          method: str = "GET") -> tuple[int, str]:
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return resp.status, resp.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")


def _stripe(path: str) -> dict:
    token = ENV.get("STRIPE_TOKEN")
    assert token, "STRIPE_TOKEN missing from .env"
    status, body = _http(f"https://api.stripe.com{path}",
                         headers={"Authorization": f"Bearer {token}"})
    assert status == 200, f"Stripe API {path} -> HTTP {status}: {body[:200]}"
    return json.loads(body)


def _n8n(path: str) -> dict:
    key = ENV.get("N8N_API_KEY")
    assert key, "N8N_API_KEY missing from .env"
    status, body = _http(f"{N8N_BASE}/api/v1{path}", headers={"X-N8N-API-KEY": key})
    assert status == 200, f"n8n API {path} -> HTTP {status}: {body[:200]}"
    return json.loads(body, strict=False)


@lru_cache(maxsize=None)
def _pricing_html() -> str:
    status, body = _http(f"{SITE}/pricing/")
    assert status == 200, f"/pricing/ -> HTTP {status}"
    return body


@lru_cache(maxsize=None)
def _buy_buttons() -> dict[str, str]:
    """slug -> href from the LIVE pricing page."""
    buys = re.findall(r'class="buy"[^>]*data-product="([^"]+)"[^>]*href="([^"]+)"', _pricing_html())
    return dict(buys)


@lru_cache(maxsize=None)
def _stripe_links_by_slug() -> dict[str, dict]:
    links = _stripe("/v1/payment_links?limit=100")["data"]
    return {l.get("metadata", {}).get("data_product"): l
            for l in links if l.get("metadata", {}).get("data_product")}


# --------------------------------------------------------------------------
# 1. site checks
# --------------------------------------------------------------------------
def test_pricing_page_is_live():
    assert len(_pricing_html()) > 5000, "/pricing/ answered but body is suspiciously small"


def test_pricing_has_all_seven_buy_buttons():
    buttons = _buy_buttons()
    missing = set(CATALOG) - set(buttons)
    extra = set(buttons) - set(CATALOG)
    assert not missing, f"buy buttons missing for: {sorted(missing)}"
    assert not extra, f"unexpected buy buttons: {sorted(extra)}"


def test_buy_buttons_point_to_stripe():
    bad = {s: h for s, h in _buy_buttons().items() if "buy.stripe.com" not in h}
    assert not bad, f"buy hrefs not pointing at Stripe: {bad}"


def test_no_tool_names_on_page():
    html = _pricing_html().lower()
    leaked = [w for w in FORBIDDEN_WORDS if w in html]
    assert not leaked, f"forbidden tool names on the sales page: {leaked}"


def test_trust_copy_present():
    assert TRUST_COPY in _pricing_html(), f'missing trust copy: "{TRUST_COPY}"'


def test_pricing_in_sitemap():
    status, body = _http(f"{SITE}/sitemap.xml")
    assert status == 200, f"sitemap.xml -> HTTP {status}"
    assert f"{SITE}/pricing/" in body, "/pricing/ missing from sitemap.xml"


def test_homepage_links_to_pricing():
    status, body = _http(f"{SITE}/")
    assert status == 200, f"homepage -> HTTP {status}"
    assert 'href="/pricing/"' in body, "homepage has no crawlable link to /pricing/"


# --------------------------------------------------------------------------
# 2. Stripe checks
# --------------------------------------------------------------------------
def test_stripe_payment_links_exist_and_active():
    links = _stripe_links_by_slug()
    missing = set(CATALOG) - set(links)
    assert not missing, f"Stripe payment links missing for: {sorted(missing)}"
    inactive = [s for s in CATALOG if not links[s]["active"]]
    assert not inactive, f"payment links inactive: {inactive}"


def test_stripe_mode_matches_expectation():
    links = _stripe_links_by_slug()
    for slug in CATALOG:
        livemode = links[slug]["livemode"]
        expected_live = EXPECTED_STRIPE_MODE == "live"
        assert livemode == expected_live, (
            f"{slug}: livemode={livemode} but expected mode is {EXPECTED_STRIPE_MODE!r} "
            "(set GEORGEAI_STRIPE_MODE=live after go-live)")


def test_page_hrefs_match_stripe_links():
    """Each buy button must point at THE payment link carrying its own slug."""
    links = _stripe_links_by_slug()
    for slug, href in _buy_buttons().items():
        expected = links[slug]["url"]
        assert href == expected, f"{slug}: page href {href} != Stripe link {expected}"


def test_stripe_prices_match_catalog():
    links = _stripe_links_by_slug()
    for slug, expected in CATALOG.items():
        items = _stripe(f"/v1/payment_links/{links[slug]['id']}/line_items")["data"]
        one_time = sorted(i["price"]["unit_amount"] for i in items if not i["price"].get("recurring"))
        monthly = sorted(i["price"]["unit_amount"] for i in items if i["price"].get("recurring"))
        exp_ot = [expected["one_time"]] if expected["one_time"] else []
        exp_mo = [expected["monthly"]] if expected["monthly"] else []
        assert one_time == exp_ot, f"{slug}: one-time prices {one_time} != {exp_ot}"
        assert monthly == exp_mo, f"{slug}: monthly prices {monthly} != {exp_mo}"
        for i in items:
            assert i["price"]["currency"] == "eur", f"{slug}: currency {i['price']['currency']} != eur"


# --------------------------------------------------------------------------
# 3. n8n checks
# --------------------------------------------------------------------------
def test_n8n_workflow_active():
    wf = _n8n(f"/workflows/{N8N_WORKFLOW_ID}")
    assert wf.get("active") is True, "stripe-orders workflow is NOT active"
    node_names = {n["name"] for n in wf.get("nodes", [])}
    for required in ("Stripe Webhook", "Fetch Session from Stripe", "Extract Order",
                     "Notify George", "Onboard Client", "Store Order"):
        assert required in node_names, f"workflow node missing: {required}"


def test_n8n_orders_table_schema():
    tables = _n8n("/data-tables").get("data", [])
    table = next((t for t in tables if t["id"] == N8N_ORDERS_TABLE_ID), None)
    assert table, f"data table {N8N_ORDERS_TABLE_ID} (orders) not found"
    cols = {c["name"] for c in table.get("columns", [])}
    missing = ORDERS_COLUMNS - cols
    assert not missing, f"orders table missing columns: {sorted(missing)}"


def test_n8n_webhook_answers():
    """POST a non-order event type; the workflow's IF filter drops it, so this
    is side-effect-free (no order row, no emails) but proves the endpoint is up."""
    status, _ = _http(f"{N8N_BASE}/webhook/stripe-orders",
                      headers={"Content-Type": "application/json"},
                      data=json.dumps({"type": "healthcheck.ping"}).encode(),
                      method="POST")
    assert status == 200, f"production webhook -> HTTP {status}"


def test_n8n_no_recent_order_failures():
    """Recent webhook executions must not be errors (transient issues would
    mean lost orders — surface them here)."""
    execs = _n8n(f"/executions?workflowId={N8N_WORKFLOW_ID}&limit=10").get("data", [])
    errors = [e["id"] for e in execs if e.get("status") == "error"]
    assert not errors, f"recent stripe-orders executions failed: {errors} — check {N8N_BASE}"


# --------------------------------------------------------------------------
# standalone runner (cron entrypoint) — pytest not required
# --------------------------------------------------------------------------
def main() -> int:
    checks = [(name, fn) for name, fn in sorted(globals().items())
              if name.startswith("test_") and callable(fn)]
    failures = []
    print(f"georgeai.dev payments pipeline — {len(checks)} checks "
          f"(stripe mode: {EXPECTED_STRIPE_MODE})\n")
    for name, fn in checks:
        try:
            fn()
            print(f"  ✓ {name}")
        except AssertionError as e:
            failures.append((name, str(e)))
            print(f"  ✗ {name}: {e}")
        except Exception as e:  # network/API breakage is a failure too
            failures.append((name, f"{type(e).__name__}: {e}"))
            print(f"  ✗ {name}: {type(e).__name__}: {e}")
    print(f"\n{len(checks) - len(failures)}/{len(checks)} passed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
