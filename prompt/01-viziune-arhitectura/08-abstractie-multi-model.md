# 01.08 — Abstracție multi-model

**Secțiune:** Viziune & arhitectură  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Proiectează interfața `llm.providers.base.ChatProvider` (stream, count_tokens, list_models, supports_tools, supports_thinking, supports_vision) ca să putem adăuga alți furnizori fără să atingem view-urile. Implementarea implicită: Anthropic cu `claude-opus-5-5`, `claude-sonnet-5-5`, `claude-haiku-5-5`.

**Acceptare:** tipuri clare (dataclasses/TypedDict), evenimente de stream normalizate, test unitar cu un provider fake.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
