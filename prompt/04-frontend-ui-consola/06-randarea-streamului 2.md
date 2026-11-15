# 04.06 — Randarea streamului

**Secțiune:** Frontend — UI-ul consolei  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Hook `useMessageStream` care consumă SSE, aplică delta-urile într-un store, gestionează reconectarea cu `Last-Event-ID` și stările (connecting/streaming/done/error/stopped).
**Acceptare:** fără re-render al întregii liste la fiecare token (memoizare pe mesaj); 60 fps la 100 tok/s.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
