# 03.02 — Catalog de modele

**Secțiune:** Integrare LLM (Claude API)  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Model picker ca pe claude.ai: catalog `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-haiku-5-5` cu nume afișat, descriere scurtă, fereastră de context, capabilități, cost per MTok și planurile care au acces.

**Acceptare:** catalog într-un singur fișier de config; endpoint `GET /models`; modelele indisponibile apar dezactivate cu tooltip „Upgrade”.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
