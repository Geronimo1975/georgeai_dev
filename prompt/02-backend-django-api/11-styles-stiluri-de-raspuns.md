# 02.11 — Styles (stiluri de răspuns)

**Secțiune:** Backend Django & API  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Replică „Styles” din claude.ai: stiluri predefinite (Normal, Concis, Explicativ, Formal) + stiluri custom create de user, fiecare cu un fragment de system prompt.

**Acceptare:** CRUD stiluri, selectare per conversație, aplicat la următorul mesaj.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
