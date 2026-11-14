# 04.04 — Ecranul New chat

**Secțiune:** Frontend — UI-ul consolei  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Ecran gol ca pe claude.ai: salut personalizat cu ora zilei, composer mare centrat, sugestii rapide (chips) adaptate serviciilor georgeai.dev, selectorul de proiect.

**Acceptare:** composer-ul primește focus automat; la primul mesaj, tranziție fluidă spre vizualizarea de conversație.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
