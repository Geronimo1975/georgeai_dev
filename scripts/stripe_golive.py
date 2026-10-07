#!/usr/bin/env python3
"""Mirror the georgeai.dev product catalog into Stripe LIVE mode.

Creates, idempotently, the 7 products / 10 prices / 7 payment links that
pages/pricing/index.html sells, each carrying metadata.data_product = <slug>
so the n8n `stripe-orders` workflow can map checkout.session.completed back
to a product.

Stdlib only, same as tests/test_payments_pipeline.py (the cron runner has no
pip deps). Read-only by default: pass --apply to actually write to Stripe.

    python3 scripts/stripe_golive.py                 # dry run, shows the plan
    python3 scripts/stripe_golive.py --apply         # create in live mode
    python3 scripts/stripe_golive.py --apply --write-html   # + swap the 7 hrefs

The live key is read from the repo-root .env as STRIPE_LIVE_TOKEN (or the env
var of the same name) and is never printed. A key starting sk_test_/rk_test_
is refused: this script exists to build the LIVE catalog.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PRICING_HTML = ROOT / "pages" / "pricing" / "index.html"
API = "https://api.stripe.com/v1"
TIMEOUT = 30

# The single source of truth for what we sell. Amounts are EUR cents and MUST
# stay in sync with CATALOG in tests/test_payments_pipeline.py and with the
# copy in pages/pricing/index.html — the test suite exists to catch that drift.
CATALOG = [
    {"slug": "lead-pack-100",    "name": "New Customers, Delivered — 100 verified contacts",
     "one_time": 29900,  "monthly": None},
    {"slug": "lead-pack-500",    "name": "New Customers, Delivered — 500 verified contacts",
     "one_time": 99000,  "monthly": None},
    {"slug": "visibility-audit", "name": "Get Found — by Google and by AI",
     "one_time": 49000,  "monthly": None},
    {"slug": "phone-24-7",       "name": "Your Phone, Answered 24/7",
     "one_time": 99000,  "monthly": 69000},
    {"slug": "chatbot",          "name": "A Website That Sells While You Sleep",
     "one_time": 190000, "monthly": 39000},
    {"slug": "autopilot",        "name": "Your Business on Autopilot",
     "one_time": 250000, "monthly": 75000},
    {"slug": "prospects",        "name": "A Steady Stream of Interested Prospects",
     "one_time": None,   "monthly": 99000},
]


# --------------------------------------------------------------------------
# env + http
# --------------------------------------------------------------------------
# STRIPE_LIVE_TOKEN (a restricted live key, preferred) wins; STRIPE_SECRET is
# the unrestricted sk_live_ key already in .env and is accepted with a warning.
KEY_VARS = ("STRIPE_LIVE_TOKEN", "STRIPE_SECRET")


def load_key() -> str:
    import os
    values = {}
    env_file = ROOT / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            name, _, value = line.strip().partition("=")
            if name in KEY_VARS and value.strip():
                values[name] = value.strip()
    values.update({k: v for k in KEY_VARS if (v := os.environ.get(k, "").strip())})

    for name in KEY_VARS:
        key = values.get(name)
        if not key:
            continue
        if "_test_" in key:
            print(f"note: {name} is a TEST-mode key — skipping it", file=sys.stderr)
            continue
        if key.startswith("sk_"):
            print(f"warning: {name} is an UNRESTRICTED live secret key. It works, but a\n"
                  "         restricted key limited to Products / Prices / Payment Links\n"
                  "         would be the safer thing to keep sitting in .env.\n",
                  file=sys.stderr)
        return key

    sys.exit("No live Stripe key found. Set STRIPE_LIVE_TOKEN (restricted live key with\n"
             "write access to Products, Prices and Payment Links) in the repo-root .env.")


def api(key: str, path: str, params: dict | None = None, method: str = "GET") -> dict:
    """One Stripe API call. Nested dicts are flattened Stripe-style (a[b]=c)."""
    flat: list[tuple[str, str]] = []

    def walk(prefix: str, value) -> None:
        if isinstance(value, dict):
            for k, v in value.items():
                walk(f"{prefix}[{k}]" if prefix else k, v)
        elif isinstance(value, list):
            for i, v in enumerate(value):
                walk(f"{prefix}[{i}]", v)
        elif value is not None:
            flat.append((prefix, str(value).lower() if isinstance(value, bool) else str(value)))

    walk("", params or {})
    body = urllib.parse.urlencode(flat).encode() if method == "POST" else None
    url = f"{API}{path}"
    if method == "GET" and flat:
        url += "?" + urllib.parse.urlencode(flat)
    req = urllib.request.Request(url, data=body, method=method, headers={
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/x-www-form-urlencoded",
        "Stripe-Version": "2024-06-20",
    })
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as e:
        detail = json.loads(e.read() or b"{}").get("error", {}).get("message", "")
        sys.exit(f"Stripe API {method} {path} failed ({e.code}): {detail}")


# --------------------------------------------------------------------------
# idempotent upserts — everything is looked up by metadata.data_product first
# --------------------------------------------------------------------------
def find_product(key: str, slug: str) -> dict | None:
    q = f"active:'true' AND metadata['data_product']:'{slug}'"
    hits = api(key, "/products/search", {"query": q, "limit": 1}).get("data", [])
    return hits[0] if hits else None


def upsert_product(key: str, item: dict, apply: bool) -> dict:
    found = find_product(key, item["slug"])
    if found:
        print(f"  product   exists  {item['slug']:<17} {found['id']}")
        return found
    if not apply:
        print(f"  product   CREATE  {item['slug']:<17} \"{item['name']}\"")
        return {"id": f"<prod:{item['slug']}>"}
    made = api(key, "/products", {
        "name": item["name"],
        "metadata": {"data_product": item["slug"]},
    }, method="POST")
    print(f"  product   created {item['slug']:<17} {made['id']}")
    return made


def upsert_price(key: str, product_id: str, slug: str, amount: int,
                 recurring: bool, apply: bool) -> dict:
    kind = "monthly" if recurring else "one-time"
    if not product_id.startswith("<"):
        for p in api(key, "/prices", {"product": product_id, "active": True, "limit": 100}).get("data", []):
            same_kind = bool(p.get("recurring")) == recurring
            if same_kind and p["unit_amount"] == amount and p["currency"] == "eur":
                print(f"  price     exists  {slug:<17} {p['id']}  {amount/100:>8.2f} EUR {kind}")
                return p
    if not apply:
        print(f"  price     CREATE  {slug:<17} {'':<28}{amount/100:>8.2f} EUR {kind}")
        return {"id": f"<price:{slug}:{kind}>"}
    params = {
        "product": product_id,
        "currency": "eur",
        "unit_amount": amount,
        # § 19 UStG (Kleinunternehmer): no VAT is ever added, so the amount shown
        # IS the amount charged. "inclusive" keeps that true even if Stripe Tax is
        # switched on later; "exclusive" would start adding 19% on top.
        "tax_behavior": "inclusive",
        "metadata": {"data_product": slug},
    }
    if recurring:
        params["recurring"] = {"interval": "month"}
    made = api(key, "/prices", params, method="POST")
    print(f"  price     created {slug:<17} {made['id']}  {amount/100:>8.2f} EUR {kind}")
    return made


def upsert_link(key: str, slug: str, line_items: list[dict], apply: bool) -> str:
    for link in api(key, "/payment_links", {"active": True, "limit": 100}).get("data", []):
        if link.get("metadata", {}).get("data_product") == slug:
            print(f"  link      exists  {slug:<17} {link['url']}")
            return link["url"]
    if not apply:
        print(f"  link      CREATE  {slug:<17} ({len(line_items)} line item(s))")
        return f"<link:{slug}>"
    made = api(key, "/payment_links", {
        "line_items": line_items,
        "metadata": {"data_product": slug},
        "billing_address_collection": "required",
        "phone_number_collection": {"enabled": True},
    }, method="POST")
    print(f"  link      created {slug:<17} {made['url']}")
    return made["url"]


# --------------------------------------------------------------------------
# pricing page rewrite
# --------------------------------------------------------------------------
def write_hrefs(urls: dict[str, str]) -> None:
    """Point the 7 buy buttons at their live Payment Link.

    All-or-nothing: the whole file is rewritten once, after every slug has
    matched, so a partial patch can never ship a half-wired sales page.
    """
    html = PRICING_HTML.read_text()
    out = html
    for slug, url in urls.items():
        pattern = re.compile(r'(<a class="buy" data-product="%s" href=")[^"]*(")' % re.escape(slug))
        out, n = pattern.subn(lambda m: m.group(1) + url + m.group(2), out, count=1)
        if n != 1:
            sys.exit(f"buy button for {slug!r} not found in {PRICING_HTML} — aborting, file untouched")
    PRICING_HTML.write_text(out)
    print(f"\nrewrote {len(urls)} hrefs in {PRICING_HTML.relative_to(ROOT)}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--apply", action="store_true", help="actually write to Stripe (default: dry run)")
    ap.add_argument("--write-html", action="store_true",
                    help="also swap the 7 buy-button hrefs in pages/pricing/index.html")
    args = ap.parse_args()

    key = load_key()
    acct = api(key, "/account")
    mode = "LIVE" if acct.get("charges_enabled") else "restricted/unknown"
    print(f"account {acct.get('id')} ({acct.get('business_profile', {}).get('name') or '—'}) — {mode}")
    print(f"mode: {'APPLY — writing to Stripe' if args.apply else 'DRY RUN — nothing is written'}\n")

    urls: dict[str, str] = {}
    for item in CATALOG:
        print(item["slug"])
        product = upsert_product(key, item, args.apply)
        line_items = []
        if item["monthly"]:
            price = upsert_price(key, product["id"], item["slug"], item["monthly"], True, args.apply)
            line_items.append({"price": price["id"], "quantity": 1})
        if item["one_time"]:
            price = upsert_price(key, product["id"], item["slug"], item["one_time"], False, args.apply)
            line_items.append({"price": price["id"], "quantity": 1})
        urls[item["slug"]] = upsert_link(key, item["slug"], line_items, args.apply)
        print()

    print("| data-product | Payment Link |\n|---|---|")
    for slug, url in urls.items():
        print(f"| {slug} | {url} |")

    if args.write_html:
        if not args.apply:
            sys.exit("\n--write-html needs --apply (a dry run has no real URLs to write)")
        write_hrefs(urls)
        print("Next: ./deploy.sh --no-content, then "
              "GEORGEAI_STRIPE_MODE=live python3 tests/test_payments_pipeline.py")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
