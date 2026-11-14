# 02.10 — Preferințe utilizator

**Secțiune:** Backend Django & API  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Model `UserPreference`: model implicit, stil implicit, temă (system/light/dark), limbă, „ce ar trebui să știe Claude despre tine” (instrucțiuni personale), trimitere cu Enter vs Ctrl+Enter.

**Acceptare:** `GET/PATCH /me/preferences`; instrucțiunile personale ajung în system prompt.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
