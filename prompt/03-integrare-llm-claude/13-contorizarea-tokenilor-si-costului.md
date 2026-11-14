# 03.13 — Contorizarea tokenilor și costului

**Secțiune:** Integrare LLM (Claude API)  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Salvează pentru fiecare mesaj asistent: input/output/cache tokens, model, cost calculat din catalog, durata, TTFT. Agregate zilnice per user.

**Acceptare:** `UsageEvent` populat din evenimentul final al streamului; test cu valori cunoscute.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
