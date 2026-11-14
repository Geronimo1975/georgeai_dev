# 04.02 — Design tokens

**Secțiune:** Frontend — UI-ul consolei  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Transformă `brand/palette.json` în CSS custom properties (light/dark, `prefers-color-scheme` + override manual), scală tipografică Plus Jakarta Sans, spațieri, raze, umbre — echivalentul sistemului vizual calm al claude.ai, dar cu brandul GeorgeAI.

**Acceptare:** `tokens.css` generat dintr-un script; contrast WCAG AA verificat automat.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
