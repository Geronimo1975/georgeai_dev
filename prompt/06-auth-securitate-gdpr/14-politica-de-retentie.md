# 06.14 — Politica de retenție

**Secțiune:** Autentificare, securitate & GDPR  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Implementează retenție configurabilă: conversațiile șterse se purjează definitiv după 30 de zile, fișierele orfane după 7, log-urile după 90; job zilnic.

**Acceptare:** job testat; politica afișată în setări și în Datenschutz.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
