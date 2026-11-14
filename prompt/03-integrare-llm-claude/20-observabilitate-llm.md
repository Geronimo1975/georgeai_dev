# 03.20 — Observabilitate LLM

**Secțiune:** Integrare LLM (Claude API)  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Logare structurată per apel: request id Anthropic, model, latențe (TTFT, total), tokeni, eroare — fără conținut. Panou admin cu p50/p95 și erori pe ultimele 24h.

**Acceptare:** corelare request id ↔ mesaj din DB pentru debugging.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
