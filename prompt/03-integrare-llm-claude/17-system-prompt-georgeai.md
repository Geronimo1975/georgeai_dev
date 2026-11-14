# 03.17 — System prompt GeorgeAI

**Secțiune:** Integrare LLM (Claude API)  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Scrie system prompt-ul de bază al consolei: identitate, ton, formatare Markdown, când să creeze artifacts, limbi suportate, ce nu face. Versionat în repo (`backend/llm/prompts/base.md`).

**Acceptare:** test că promptul se încarcă; changelog pentru fiecare versiune.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
