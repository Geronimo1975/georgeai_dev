# 02.01 — Modelele Conversation și Message

**Secțiune:** Backend Django & API  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Implementează în `backend/console/models.py` modelele `Conversation` (owner, project nullable, title, model, style, is_starred, archived_at, updated_at) și `Message` (conversation, parent nullable pentru ramuri, role, model, stop_reason, token_in/out, created_at).

**Acceptare:** migrații, admin Jazzmin, teste pentru crearea unui arbore cu 2 ramuri.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
