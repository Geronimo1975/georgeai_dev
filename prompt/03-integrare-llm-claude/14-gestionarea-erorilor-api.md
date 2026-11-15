# 03.14 — Gestionarea erorilor API

**Secțiune:** Integrare LLM (Claude API)  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Mapează erorile Anthropic (overloaded, rate_limit, invalid_request, context too long, refusal) pe mesaje clare în UI, ca pe claude.ai („Claude is temporarily overloaded — try again”), cu buton Retry.

**Acceptare:** fiecare tip de eroare are test și text tradus RO/DE/EN.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
