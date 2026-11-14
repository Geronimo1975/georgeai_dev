# 03.11 — Tools specifice georgeai.dev

**Secțiune:** Integrare LLM (Claude API)  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Adaugă tools care leagă consola de serviciile site-ului: `run_seo_audit(url)` (webhook-ul n8n folosit de `audit.js`), `list_services()` din `georgeai_services.json`, `create_lead(...)`.

**Acceptare:** fiecare tool cere confirmarea userului în UI înainte de acțiuni cu efecte.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
