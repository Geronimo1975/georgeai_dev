---
name: georgeai-n8n
description: Work with the project's n8n instance (app.n8n-studio.com — George's OWN VPS) — building, editing, or debugging workflows for georgeai.dev.
---

# n8n for georgeai.dev

**Instance: `https://app.n8n-studio.com`** — George's OWN n8n, running on HIS
VPS 85.215.69.83 (containers `n8n-main`, `n8n-worker-1/2` behind Traefik).
**ALL georgeai.dev workflow work targets THIS instance. This is George's
explicit instruction — do not "correct" it.**

## ⚠️ The wrong instance (do not build here)

`https://n8n.rotocon.world` (31.70.79.209) is a **different instance** on a
different server. **The Codex.ai n8n connector (`mcp__claude_ai_n8n__*`)
authenticates THERE, not to app.n8n-studio.com** — so building through that
connector silently lands work on the wrong instance. This happened on
2026-07-02 (stripe-orders + data tables were built on rotocon.world and had to
be migrated). If a tool's account/instance can't be confirmed as
app.n8n-studio.com, STOP and confirm with George first.

## Tooling (in preference order)

1. **n8n REST API on app.n8n-studio.com** — API key in the project `.env` as
   `N8N_STUDIO_API_KEY` (ask George to generate one under Settings → n8n API if
   missing). Base: `https://app.n8n-studio.com/api/v1/`. Never print the key.
2. **`mcp__n8n-mcp__*`** — check which base URL it is configured for before
   trusting it; its API key failed auth as of 2026-07-02.
3. **SSH to the VPS** (`macbook-air` alias) — the n8n containers run there;
   `docker exec n8n-main n8n ...` CLI as a last resort.
4. **`mcp__claude_ai_n8n__*`** (Codex.ai connector) — ONLY for the legacy
   assets still on n8n.rotocon.world; never for new georgeai work.

## Known assets

- **app.n8n-studio.com** (authoritative): stripe-orders order pipeline (being
  migrated here 2026-07-02 — see repo `docs/n8n-stripe-orders.json`).
- **n8n.rotocon.world** (legacy, to migrate/retire): workflow
  `georgeai-free-audit` (`RpKfWXjt7WuizKMl`) + data table `audit_leads`
  (`SkhPhTtX5xKxw8aa`); old copy of stripe-orders (`hGndKGfKRk9tKIoG`,
  deactivate after migration) + data table `orders` (`Safgo17NCrOS579A`).

## Conventions

- Local port **5433** is the (rotocon) n8n postgres tunnel — reserved.
  georgeai's own DB tunnel uses 5434; never swap them.
- Validate workflows before publishing; test with pinned data rather than
  toggling live workflows.
- Workflows touching georgeai.dev content should call the site or its API, not
  poke files on the VPS directly.
