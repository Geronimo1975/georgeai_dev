# 01.03 — ADR: alegerea stack-ului frontend

**Secțiune:** Viziune & arhitectură  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Compară 3 opțiuni pentru frontend-ul consolei: (a) React + Vite SPA servit din Django, (b) Django templates + HTMX + streaming SSE, (c) Next.js separat. Criterii: fidelitate față de UX-ul claude.ai (tranziții, panou artifacts, editare inline), cost de mentenanță pentru un singur dezvoltator, SEO irelevant (zonă autentificată), integrarea cu sesiunea Django existentă.

**Acceptare:** `docs/console/adr/0001-frontend-stack.md` în format ADR, cu o recomandare fermă.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
