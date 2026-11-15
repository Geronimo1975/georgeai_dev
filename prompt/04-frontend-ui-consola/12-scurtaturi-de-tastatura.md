# 04.12 — Scurtături de tastatură

**Secțiune:** Frontend — UI-ul consolei  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Implementează scurtăturile claude.ai-like: Cmd+K căutare, Cmd+Shift+O new chat, Cmd+/ ajutor scurtături, Esc stop/închide, Shift+Cmd+; copy ultimul răspuns. Modal de ajutor.

**Acceptare:** nu interferează cu tastarea în composer; documentate.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
