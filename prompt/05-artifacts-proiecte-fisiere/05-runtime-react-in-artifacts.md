# 05.05 — Runtime React în artifacts

**Secțiune:** Artifacts, proiecte & fișiere  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Suport pentru componente React cu import-uri dintr-o listă permisă (react, recharts, lucide-react, tailwind), compilate în browser (esbuild-wasm sau Babel standalone) în iframe.

**Acceptare:** erorile de compilare se afișează în panou cu buton „Fix with GeorgeAI” care trimite eroarea în chat.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
