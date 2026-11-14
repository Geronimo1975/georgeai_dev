# 03.07 — Files API

**Secțiune:** Integrare LLM (Claude API)  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Folosește Anthropic Files API pentru fișierele refolosite (knowledge de proiect, atașamente mari) ca să nu retrimiți base64 la fiecare tură; păstrează maparea `Attachment.provider_file_id`.

**Acceptare:** fallback la base64 dacă Files API nu e disponibil; curățare la ștergerea fișierului.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
