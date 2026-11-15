# 05.04 — Sandbox pentru HTML/React

**Secțiune:** Artifacts, proiecte & fișiere  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Randează artifactele HTML/React într-un iframe izolat pe un subdomeniu separat (ex. `sandbox.georgeai.dev`) cu `sandbox="allow-scripts"`, CSP strict și listă albă de CDN-uri.

**Acceptare:** artifactul nu poate citi cookie-urile consolei; test de escape documentat.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
