# Domain registry — design

Date: 2026-09-18
Status: approved (brainstorm), awaiting implementation plan

## Why

George's Hostinger account holds 19 domains that together form the portfolio
around georgeai.dev. Today the only record of them is `Domenii/`, a snapshot
generated from the Hostinger API and classified by *observed* state (what curl
returns). That cannot be a source of truth: when a site goes down the "truth"
silently moves from Deployed to Undeployed, and nothing records what each
domain is *for*.

This is sub-project 0 of a five-part programme. Everything else reads from
this registry:

1. Unified VPS routing (registry → Traefik routers/redirects)
2. Periodic checks + alerts (cron/n8n runs the sync)
3. Public portfolio section on georgeai.dev (registry → `georgeai_work.json` → `/work/`)
4. SEO/GEO/SEA/AIO per domain (fields in the registry + `geo` audits)

Each of those gets its own spec. This spec covers only the registry and its sync.

## Scope

In:
- `domains/<domain>.yaml` — one hand-written file per domain holding intent only
- `domains/sync.py` — reads registry + Hostinger API + live DNS/HTTP, writes
  `domains/REPORT.md`, exits non-zero on drift
- Schema validation with hard failures
- Seeding all 19 current domains
- Unit tests for validation and drift detection (no network)
- Removal of `Domenii/` (its information moves into the generated report)

Out (later sub-projects): Traefik generation, alert delivery, public pages,
SEO fields beyond the placeholder, any write to Hostinger.

## Registry format

Path: `domains/<domain>.yaml`, one file per domain, filename equals `domain`.

```yaml
domain: georgeai.de
intent: redirect            # live | redirect | external | hold | sell | drop
category: brand             # brand | product | client | experiment
owner: george
public: false               # true → listed on georgeai.dev (sub-project 3)
routing:
  target: https://georgeai.dev   # redirect: destination URL; live: service name
email: hostinger            # hostinger | none | external
registrar: hostinger        # hostinger | other
dns: hostinger              # hostinger | cloudflare | other
notes: "Free text."
seo:
  primary_keyword: ~        # placeholder, filled in sub-project 4
```

Rules:
- Only intent lives here. No observed data (IP, HTTP status, expiry, MX) —
  that is the sync's job.
- `intent` meanings:
  - `live` — own site served from the VPS; `routing.target` names the service
  - `redirect` — 301 to `routing.target` (absolute URL)
  - `external` — hosted elsewhere; Hostinger holds only registrar/DNS
  - `hold` — kept, no site; will get a "coming soon" page in sub-project 1
  - `sell` — for sale; will get an offer landing in sub-project 1
  - `drop` — let it expire; auto-renew must be off
- Required: `domain`, `intent`, `category`, `owner`, `public`, `email`,
  `registrar`, `dns`. `routing.target` required when `intent` is `live` or
  `redirect`, forbidden otherwise. `public` may only be true when `intent` is
  `live` or `external`.
- Unknown keys, unknown enum values, or a filename that does not match
  `domain` → validation error, sync refuses to run, exit code 2.

## Sync behaviour — `domains/sync.py`

Inputs:
- registry files
- Hostinger API (`developers.hostinger.com`): `/api/domains/v1/portfolio`,
  `/api/domains/v1/portfolio/{domain}`, `/api/dns/v1/zones/{domain}`,
  `/api/billing/v1/subscriptions`. Token from `HOSTINGER_TOKEN` (root `.env`,
  gitignored). Send a non-Python User-Agent — Cloudflare blocks
  `Python-urllib` with error 1010. Retry on 429/5xx.
- live probe per domain: A/AAAA resolution, `https://` then `http://` with
  redirects followed, final URL, status, `<title>`; parked detection by the
  Hostinger parking page title / parking IPs.

Output: `domains/REPORT.md` (gitignored, regenerated every run) with:
1. **Summary** — counts per intent, run timestamp.
2. **Drift** — one row per finding, `domain | intent | finding | evidence`.
   Findings:
   - `live` but final status not 2xx, or parked
   - `redirect` but final URL host ≠ target host, or parked
   - `external` but A record → our VPS (85.215.69.83)
   - `hold`/`sell` but serving a real site (2xx, not parked) — likely stale intent
   - `drop` but subscription `is_auto_renewed: true`
   - any intent except `drop`: expiry < 60 days, or subscription `non_renewing`
   - `email: hostinger` but no `mx*.hostinger.com` MX; `email: none` but MX present
   - `dns: hostinger` but nameservers not `*.dns-parking.com`
3. **Unregistered** — domains in Hostinger with no YAML (forces a decision).
4. **Orphans** — YAML files whose domain is not in Hostinger.
5. **Inventory** — full table (domain, intent, observed status, A, expiry,
   email) so the report also replaces `Domenii/README.md`.

Exit codes: `0` clean, `1` drift/unregistered/orphans present, `2` registry
invalid, `3` API/network failure (report not written).

Run: `set -a; . ./.env; set +a; python3 domains/sync.py` from repo root.
Optional `--offline` reads a cached API dump for tests.

Dependency: `pyyaml`, declared in a new root `requirements.txt`.

## Seeding (initial intents)

| intent | domains |
|---|---|
| live | georgeai.dev, aiopify.com, findajob.pro, n8n-studio.com, profm.app, djaingo.com |
| redirect | georgeai.de → https://georgeai.dev · aeopify.com → https://aiopify.com · doctormag.de → https://doctomag.de · cleosdeco.de → https://cleosdeco.com |
| external | cleosdeco.com (Hostinger shared hosting), get-hub.io (external IP), profm24.de (Cloudflare DNS, pending transfer) |
| hold | gti-europe.de, inteliskool.com, medx.travel, doctomag.de, met-ro.com, prmedex.com |
| drop | — |

`profm24.de` becomes `drop` (or is deleted) once the pending transfer is
cancelled in hPanel. Expected first report: the four `redirect` domains and
the three VPS-404 `hold` domains show drift until sub-project 1 lands — that
is the point.

`email` seeded from current MX: hostinger for cleosdeco.com, cleosdeco.de,
georgeai.de, georgeai.dev, gti-europe.de, n8n-studio.com, prmedex.com;
none elsewhere. `n8n-studio.com` appears twice in the Hostinger portfolio
(two ids); the registry has one file and the sync de-duplicates by name.

## Testing

- Unit tests (`domains/tests/`, Django-free, `python -m unittest`):
  - schema: each rule above has a failing fixture and a passing one
  - drift: fixture registry + fixture API/probe dumps → expected findings,
    including "clean" and "unregistered/orphan"
  - report rendering smoke test
- One real run at the end with the report shown to George.

## Migration

- Delete `Domenii/` after the first successful real run; `.gitignore` gets
  `domains/REPORT.md`.
- `CLAUDE.md` gains a short "Domain registry" section pointing here.
