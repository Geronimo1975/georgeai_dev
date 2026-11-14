# 05.20 — Review de securitate artifacts & fișiere

**Secțiune:** Artifacts, proiecte & fișiere  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Fă un review dedicat al sandbox-ului de artifacts și al uploadului: XSS, escape din iframe, SSRF prin URL-uri, zip bombs, fișiere polyglot, prompt injection în documente.

**Acceptare:** raport cu constatări și remedieri; nu modifica codul fără confirmare.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
