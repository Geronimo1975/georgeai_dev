# DevOps, deploy & observabilitate

Cum ajunge consola în producție pe VPS-ul existent, fără să afecteze site-ul static și restul serviciilor `gethub-*`.

> **Context comun (lipește-l înaintea promptului dacă agentul nu are CLAUDE.md):**
> Repo `georgeai_dev` — Django 5.2 + DRF (SessionAuthentication, user custom pe email în `backend/accounts`), PostgreSQL în containerul `gethub-postgres`, deploy pe VPS `85.215.69.83` în spatele Traefik. Ținta: **GeorgeAI Console**, o consolă de chat AI cu paritate funcțională și de UX față de **claude.ai** (sidebar cu conversații, proiecte cu knowledge, artifacts în panou lateral, streaming token-cu-token, model picker, upload fișiere, căutare, share, setări, limite de utilizare). Paleta live: `brand/palette.json` (canvas `#02060a`, accent `#fb5e31`/`#b23c0a`, Plus Jakarta Sans). Nu edita niciodată `site/` sau `frontend/template/` — sunt build output.

| # | Prompt | Fișier |
|---|---|---|
| 01 | Dockerfile de producție | [01-dockerfile-de-productie.md](01-dockerfile-de-productie.md) |
| 02 | Serviciul georgeai-app în compose | [02-serviciul-georgeai-app-in-compose.md](02-serviciul-georgeai-app-in-compose.md) |
| 03 | Traefik pentru streaming | [03-traefik-pentru-streaming.md](03-traefik-pentru-streaming.md) |
| 04 | Mediu de staging | [04-mediu-de-staging.md](04-mediu-de-staging.md) |
| 05 | Script de deploy pentru aplicație | [05-script-de-deploy-pentru-aplicatie.md](05-script-de-deploy-pentru-aplicatie.md) |
| 06 | CI pentru consolă | [06-ci-pentru-consola.md](06-ci-pentru-consola.md) |
| 07 | Deploy continuu | [07-deploy-continuu.md](07-deploy-continuu.md) |
| 08 | Migrații fără downtime | [08-migratii-fara-downtime.md](08-migratii-fara-downtime.md) |
| 09 | Backup și restore | [09-backup-si-restore.md](09-backup-si-restore.md) |
| 10 | Logare structurată | [10-logare-structurata.md](10-logare-structurata.md) |
| 11 | Error tracking | [11-error-tracking.md](11-error-tracking.md) |
| 12 | Metrici și dashboard-uri | [12-metrici-si-dashboard-uri.md](12-metrici-si-dashboard-uri.md) |
| 13 | Uptime și alerte | [13-uptime-si-alerte.md](13-uptime-si-alerte.md) |
| 14 | Pagină de status | [14-pagina-de-status.md](14-pagina-de-status.md) |
| 15 | Resurse VPS | [15-resurse-vps.md](15-resurse-vps.md) |
| 16 | Test de încărcare | [16-test-de-incarcare.md](16-test-de-incarcare.md) |
| 17 | Connection pooling | [17-connection-pooling.md](17-connection-pooling.md) |
| 18 | Maintenance mode | [18-maintenance-mode.md](18-maintenance-mode.md) |
| 19 | Runbook operațional | [19-runbook-operational.md](19-runbook-operational.md) |
| 20 | Actualizarea skill-urilor de proiect | [20-actualizarea-skill-urilor-de-proiect.md](20-actualizarea-skill-urilor-de-proiect.md) |
