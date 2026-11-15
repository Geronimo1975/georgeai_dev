# 03.04 — Prompt caching

**Secțiune:** Integrare LLM (Claude API)  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Aplică `cache_control` pe system prompt, knowledge-ul de proiect și prefixul stabil al istoricului. Loghează `cache_creation_input_tokens` și `cache_read_input_tokens`.

**Acceptare:** dashboard admin cu rata de cache hit; scădere de cost măsurată pe o conversație de 20 de ture.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
