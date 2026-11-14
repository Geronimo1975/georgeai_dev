# 09.07 — Teste frontend unitare

**Secțiune:** Testare & calitate  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Vitest + Testing Library pentru: reducer-ul de stream, randarea Markdown parțial, composer (Enter/Shift+Enter, atașamente), navigarea ramurilor.
**Acceptare:** acoperire ≥ 80% pe logica de stare.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
