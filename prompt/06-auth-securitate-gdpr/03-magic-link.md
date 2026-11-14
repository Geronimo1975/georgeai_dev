# 06.03 — Magic link

**Secțiune:** Autentificare, securitate & GDPR  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Login fără parolă prin link pe email (ca opțiunea „Continue with email” a claude.ai), cu token unic, expirare 15 min și protecție la enumerarea conturilor.

**Acceptare:** rate limit per email și IP; teste.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
