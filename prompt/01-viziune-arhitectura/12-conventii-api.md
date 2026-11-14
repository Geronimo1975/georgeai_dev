# 01.12 — Convenții API

**Secțiune:** Viziune & arhitectură  
**Țintă:** GeorgeAI Console — paritate cu claude.ai

## Prompt

Scrie `docs/console/API-CONVENTIONS.md`: prefix `/api/console/v1/`, ID-uri UUIDv7 sau ULID, paginare cursor, format de erori unitar (`{error: {type, message, retry_after}}`), idempotency-key pentru POST-uri de mesaje, versiune de schemă.

**Acceptare:** aplică convențiile într-un `exception_handler` DRF și o clasă de paginare comună.

## Reguli generale

- Citește `CLAUDE.md` și skill-urile din `.claude/skills/` relevante înainte de a începe.
- Pentru orice lucru de UI invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.
- Inspiră-te din UX-ul claude.ai, dar nu copia logo-ul, numele sau asset-urile Anthropic.
- Nu edita `site/` sau `frontend/template/`; nu comite secrete; nu deploya în producție fără confirmare.
- La final: rulează testele, actualizează `docs/console/PARITY.md` dacă ai schimbat o funcție și rezumă ce rămâne de făcut.
