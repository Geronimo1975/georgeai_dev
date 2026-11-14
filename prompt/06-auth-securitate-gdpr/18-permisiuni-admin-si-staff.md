# 06.18 — Permisiuni admin și staff

**Secțiune:** Autentificare, securitate & GDPR  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Roluri interne: superadmin, support (poate vedea metadate, nu conținut, fără consimțământ), billing. Accesul la conținutul unei conversații de către support se loghează și cere motiv.

**Acceptare:** teste de permisiuni; audit log.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
