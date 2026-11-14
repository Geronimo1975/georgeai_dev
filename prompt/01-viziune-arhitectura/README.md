# Viziune & arhitectură

Prompturi care fixează direcția: ce înseamnă „ca claude.ai”, cum se leagă consola de site-ul static existent și ce decizii tehnice se iau o singură dată.

> **Context comun (lipește-l înaintea promptului dacă agentul nu are CLAUDE.md):**
> Repo `georgeai_dev` — Django 5.2 + DRF (SessionAuthentication, user custom pe email în `backend/accounts`), PostgreSQL în containerul `gethub-postgres`, deploy pe VPS `85.215.69.83` în spatele Traefik. Ținta: **GeorgeAI Console**, o consolă de chat AI cu paritate funcțională și de UX față de **claude.ai** (sidebar cu conversații, proiecte cu knowledge, artifacts în panou lateral, streaming token-cu-token, model picker, upload fișiere, căutare, share, setări, limite de utilizare). Paleta live: `brand/palette.json` (canvas `#02060a`, accent `#fb5e31`/`#b23c0a`, Plus Jakarta Sans). Nu edita niciodată `site/` sau `frontend/template/` — sunt build output.

| # | Prompt | Fișier |
|---|---|---|
| 01 | Audit de paritate claude.ai | [01-audit-de-paritate-claude-ai.md](01-audit-de-paritate-claude-ai.md) |
| 02 | Document de arhitectură | [02-document-de-arhitectura.md](02-document-de-arhitectura.md) |
| 03 | ADR: alegerea stack-ului frontend | [03-adr-alegerea-stack-ului-frontend.md](03-adr-alegerea-stack-ului-frontend.md) |
| 04 | ADR: transport pentru streaming | [04-adr-transport-pentru-streaming.md](04-adr-transport-pentru-streaming.md) |
| 05 | Modelul de date complet | [05-modelul-de-date-complet.md](05-modelul-de-date-complet.md) |
| 06 | Structura de aplicații Django | [06-structura-de-aplicatii-django.md](06-structura-de-aplicatii-django.md) |
| 07 | Rutare consolă vs site static | [07-rutare-consola-vs-site-static.md](07-rutare-consola-vs-site-static.md) |
| 08 | Abstracție multi-model | [08-abstractie-multi-model.md](08-abstractie-multi-model.md) |
| 09 | Bugetul de performanță | [09-bugetul-de-performanta.md](09-bugetul-de-performanta.md) |
| 10 | Hartă de feature flags | [10-harta-de-feature-flags.md](10-harta-de-feature-flags.md) |
| 11 | Endpoint de bootstrap | [11-endpoint-de-bootstrap.md](11-endpoint-de-bootstrap.md) |
| 12 | Convenții API | [12-conventii-api.md](12-conventii-api.md) |
| 13 | Strategia de cache | [13-strategia-de-cache.md](13-strategia-de-cache.md) |
| 14 | Background jobs | [14-background-jobs.md](14-background-jobs.md) |
| 15 | Plan de lansare în faze | [15-plan-de-lansare-in-faze.md](15-plan-de-lansare-in-faze.md) |
| 16 | Glosar de produs | [16-glosar-de-produs.md](16-glosar-de-produs.md) |
| 17 | Inventar de risc | [17-inventar-de-risc.md](17-inventar-de-risc.md) |
| 18 | Diferențiatori față de claude.ai | [18-diferentiatori-fata-de-claude-ai.md](18-diferentiatori-fata-de-claude-ai.md) |
| 19 | Checklist Definition of Done | [19-checklist-definition-of-done.md](19-checklist-definition-of-done.md) |
| 20 | Revizuire de arhitectură adversarială | [20-revizuire-de-arhitectura-adversariala.md](20-revizuire-de-arhitectura-adversariala.md) |
