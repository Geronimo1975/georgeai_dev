# 03.01 — Client Anthropic de bază

**Secțiune:** Integrare LLM (Claude API)  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Implementează `llm/providers/anthropic.py` cu SDK-ul oficial `anthropic` (Python): stream de mesaje, mapare pe evenimentele normalizate ale consolei, cheie din `.env` (`ANTHROPIC_API_KEY`), timeout-uri și retry cu backoff pentru 429/529.

**Acceptare:** consultă documentația curentă (Context7 / skill `claude-api`), test cu răspunsuri înregistrate.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
