# Prompturi — GeorgeAI Console

Bibliotecă de **200 de prompturi** în 10 secțiuni, pentru a transforma georgeai.dev într-o
**consolă de chat AI la paritate cu claude.ai** — construită pe backend-ul Django existent.

## Steaua polară: „să se simtă ca claude.ai”

Fiecare prompt trebuie să împingă proiectul spre aceeași experiență ca claude.ai:

1. **Sidebar** cu New chat, căutare, Projects, Starred și Recents grupate pe dată.
2. **Streaming token-cu-token** cu Stop, Retry, Edit și ramuri „< 2/3 >”.
3. **Composer** cu atașamente, model picker, extended thinking și stiluri.
4. **Artifacts** randate într-un panou lateral, cu versiuni și publicare.
5. **Projects** cu knowledge și instrucțiuni proprii.
6. **Setări, utilizare și planuri** (Free/Pro/Team) cu limite clare.
7. **Calitate de produs**: rapid, accesibil, dark/light, mobil, EN/DE/RO.

Paritatea e funcțională și de UX — **nu** copiem numele, logo-ul sau asset-urile Anthropic; brandul rămâne GeorgeAI (`brand/palette.json`).

## Plan și status

**[PLAN.md](PLAN.md)** pune cele 200 de prompturi în faze (0–6) și marchează ce e deja aplicat. MVP-ul Fazei 1 rulează local: consola la `/console/`, dashboard-ul Django la `/admin/`.

## Secțiuni

| Folder | Temă | Prompturi |
|---|---|---|
| [01-viziune-arhitectura](01-viziune-arhitectura/README.md) | Viziune & arhitectură | 20 |
| [02-backend-django-api](02-backend-django-api/README.md) | Backend Django & API | 20 |
| [03-integrare-llm-claude](03-integrare-llm-claude/README.md) | Integrare LLM (Claude API) | 20 |
| [04-frontend-ui-consola](04-frontend-ui-consola/README.md) | Frontend — UI-ul consolei | 20 |
| [05-artifacts-proiecte-fisiere](05-artifacts-proiecte-fisiere/README.md) | Artifacts, proiecte & fișiere | 20 |
| [06-auth-securitate-gdpr](06-auth-securitate-gdpr/README.md) | Autentificare, securitate & GDPR | 20 |
| [07-planuri-plati-utilizare](07-planuri-plati-utilizare/README.md) | Planuri, plăți & limite de utilizare | 20 |
| [08-devops-deploy-observabilitate](08-devops-deploy-observabilitate/README.md) | DevOps, deploy & observabilitate | 20 |
| [09-testare-calitate](09-testare-calitate/README.md) | Testare & calitate | 20 |
| [10-produs-ux-crestere](10-produs-ux-crestere/README.md) | Produs, UX & creștere | 20 |

## Cum folosești prompturile

- Ordinea recomandată: **01 → 02 → 03 → 04**, apoi 05–07 în paralel, iar 08–10 pe tot parcursul.
- Un prompt = o sesiune / un PR. Copiază conținutul secțiunii „Prompt” din fișier într-o sesiune Claude Code.
- Fiecare README de secțiune conține un **bloc de context comun** de lipit dacă agentul nu citește `CLAUDE.md`.
- Prompturile din 01 produc documentele (`docs/console/*`) la care fac referire celelalte — rulează-le primele.
