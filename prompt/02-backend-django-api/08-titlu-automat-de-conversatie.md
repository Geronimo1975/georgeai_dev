# 02.08 — Titlu automat de conversație

**Secțiune:** Backend Django & API  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

După primul schimb, rulează un job cu `claude-haiku-5-5` care generează un titlu de 3–6 cuvinte în limba conversației și îl trimite UI-ului prin stream (eveniment `conversation_title`).

**Acceptare:** fallback la primele 40 de caractere dacă jobul eșuează; nu blochează răspunsul.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
