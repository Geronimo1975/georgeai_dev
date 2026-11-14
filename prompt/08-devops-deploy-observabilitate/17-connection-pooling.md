# 08.17 — Connection pooling

**Secțiune:** DevOps, deploy & observabilitate  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Configurează pooling de conexiuni Postgres (pgbouncer sau `CONN_MAX_AGE` + pool psycopg) compatibil cu ASGI și streamuri lungi.

**Acceptare:** nicio scurgere de conexiuni după testul de încărcare.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
