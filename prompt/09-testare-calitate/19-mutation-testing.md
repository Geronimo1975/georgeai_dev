# 09.19 — Mutation testing

**Secțiune:** Testare & calitate  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Rulează mutation testing (`mutmut`) pe modulele critice (ramuri, entitlements, limite de utilizare) și întărește testele unde mutanții supraviețuiesc.

**Acceptare:** scor de mutație ≥ 80% pe aceste module.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
