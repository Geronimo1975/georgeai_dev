# 08.15 — Resurse VPS

**Secțiune:** DevOps, deploy & observabilitate  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Evaluează dacă VPS-ul `85.215.69.83` duce consola alături de n8n, Postgres și celelalte containere: CPU/RAM/disk, limite de resurse în compose, swap.

**Acceptare:** raport cu măsurători + limite `deploy.resources` setate.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
