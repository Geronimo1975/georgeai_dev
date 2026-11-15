# 02.02 — ContentBlock polimorf

**Secțiune:** Backend Django & API  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Modelează conținutul mesajelor ca listă ordonată de blocuri (`text`, `thinking`, `tool_use`, `tool_result`, `image`, `document`) compatibilă 1:1 cu formatul Messages API Anthropic, ca să putem reconstrui istoricul fără transformări fragile.

**Acceptare:** serializare/deserializare round-trip testată pe toate tipurile de bloc.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
