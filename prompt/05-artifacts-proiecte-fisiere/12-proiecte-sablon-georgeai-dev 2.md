# 05.12 — Proiecte șablon georgeai.dev

**Secțiune:** Artifacts, proiecte & fișiere  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Creează 5 proiecte șablon aliniate cu serviciile: „Audit SEO/GEO”, „Workflow n8n”, „Aplicație Django”, „CRM/ERP setup”, „Consultanță AI” — fiecare cu instrucțiuni și knowledge inițial.
**Acceptare:** userul poate porni dintr-un șablon din ecranul de proiecte; seed prin management command.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
