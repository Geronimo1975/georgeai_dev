# 04.05 — Composer-ul

**Secțiune:** Frontend — UI-ul consolei  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Composer cu textarea autoextensibilă, atașare fișiere (buton + drag & drop + paste imagini), model picker, toggle extended thinking, meniu stil, buton Send care devine Stop în timpul generării.
**Acceptare:** Enter trimite, Shift+Enter linie nouă (configurabil); draft-ul se păstrează per conversație.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
