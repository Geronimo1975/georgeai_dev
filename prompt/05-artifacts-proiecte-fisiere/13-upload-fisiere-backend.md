# 05.13 — Upload fișiere — backend

**Secțiune:** Artifacts, proiecte & fișiere  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Endpoint de upload cu limită de mărime per plan, validare MIME reală (nu doar extensie), scanare antivirus opțională (ClamAV), stocare pe disc/volum Docker sau S3-compatibil.

**Acceptare:** URL-uri semnate cu expirare pentru descărcare; teste pentru fișiere malițioase.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
