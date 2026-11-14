# Plan de execuție — GeorgeAI Console

Ordinea optimă în care se aplică cele 200 de prompturi. Fiecare fază e demonstrabilă singură,
iar o fază începe abia după ce criteriile de ieșire ale celei anterioare sunt îndeplinite.

Legendă: ✅ aplicat · 🟡 parțial (MVP) · ⬜ de făcut

## Ce rulează acum (local)

```bash
cd backend && ./dev.sh                     # SQLite local, nu atinge Postgres-ul din producție
cd backend && LLM_PROVIDER=fake ./dev.sh   # fără costuri API (provider offline)
```

| Ce | URL |
|---|---|
| Consola (frontend) | http://127.0.0.1:8000/console/ |
| Dashboard Django (control) | http://127.0.0.1:8000/admin/ |
| Login local | `backend/.dev-credentials` (gitignored) |

Mediul virtual stă în `~/.venvs/georgeai_dev`, **în afara iCloud** (un `.venv` din iCloud
blochează importurile minute întregi, pentru că fișierele sunt descărcate la cerere).

---

## Faza 0 — Fundație (decizii + schelet)

| Prompt | Status | Notă |
|---|---|---|
| 01.03 ADR stack frontend | ✅ | Decis: SPA **fără build** (vanilla JS + Django). Motiv: repo-ul e în iCloud (`node_modules` aici e inutilizabil), un singur dezvoltator, zero toolchain. Se poate trece la Vite mai târziu fără să schimbăm API-ul. |
| 01.04 ADR streaming | ✅ | SSE peste `fetch` POST + `ReadableStream`; Stop = abort la client, serverul salvează textul parțial. |
| 01.06 Aplicații Django | 🟡 | O singură aplicație `console` pentru MVP; se sparge în `llm/projects/artifacts/billing` când apar acele faze. |
| 01.08 Abstracție multi-model | 🟡 | `console/llm.py`: `AnthropicProvider` + `FakeProvider`, `LLM_PROVIDER=auto/fake/anthropic`. |
| 01.11 Bootstrap | ✅ | `GET /api/console/v1/bootstrap` |
| 01.01, 01.02, 01.05, 01.07, 01.09, 01.10, 01.12–01.20 | ⬜ | Documentele din `docs/console/` urmează. |

## Faza 1 — Chat ca pe claude.ai ← **suntem aici**

| Prompt | Status | Notă |
|---|---|---|
| 02.01 Conversation / Message | ✅ | Arborele prin `Message.parent` e pregătit pentru ramuri. |
| 02.03 CRUD conversații | ✅ | Listare, creare, redenumire, stea, ștergere; altui user i se răspunde cu 404. |
| 02.04 Trimiterea mesajelor | 🟡 | Fără Idempotency-Key deocamdată. |
| 02.05 Streaming SSE | 🟡 | Evenimente normalizate; reluarea cu `Last-Event-ID` nu e făcută încă. |
| 02.06 Stop | ✅ | Răspunsul parțial e salvat cu `user_cancelled`. |
| 02.07 Regenerare / ramuri | 🟡 | Retry înlocuiește ultimul răspuns; edit și navigarea „< 2/3 >” sunt ⬜. |
| 02.08 Titlu automat | ✅ | Haiku 5.5 (fake: primele 48 de caractere), apare animat în sidebar. |
| 03.01 Client Anthropic | ✅ | Streaming, retry-uri, `cache_control` pe system prompt. |
| 03.02 Catalog modele | ✅ | Opus / Sonnet / Haiku 5.5 în model picker. |
| 03.14 Erori API | 🟡 | Mesaje clare: overloaded, rate limit, cheie invalidă, **credit epuizat**. |
| 03.17 System prompt | ✅ | `backend/console/prompts/base.md` |
| 04.01 Scaffold SPA | ✅ | `/console/*` → `console/templates/console/index.html` + `static/console/`. |
| 04.02 Design tokens | ✅ | Din `brand/palette.json`, dark/light, Plus Jakarta Sans servit local. |
| 04.03 Layout cu sidebar | ✅ | Grupare Starred / Today / Yesterday / 7 / 30 zile, sidebar pliabil, drawer pe mobil. |
| 04.04 Ecranul New chat | ✅ | Salut în funcție de oră, composer centrat, sugestii georgeai.dev. |
| 04.05 Composer | 🟡 | Model picker, Send↔Stop, Enter/Shift+Enter, ciornă per chat; atașamentele sunt ⬜. |
| 04.06 Randarea streamului | ✅ | Paint pe `requestAnimationFrame`, auto-scroll lipit de final. |
| 04.07 Markdown | 🟡 | marked + DOMPurify (vendored), blocuri de cod cu Copy; Shiki și KaTeX sunt ⬜. |
| 04.08 Acțiuni pe mesaj | 🟡 | Copy, Retry; 👍/👎 și Edit sunt ⬜. |
| 04.10 Lista de conversații | 🟡 | Meniu cu Star / Rename / Delete; virtualizarea e ⬜. |
| 04.12 Scurtături | 🟡 | ⌘K, ⌘⇧O, Esc. |
| 04.16 Mobil | 🟡 | Verificat la 375px, fără scroll orizontal. |
| 06.01 Login consolă | 🟡 | `/console/login/` cu sesiunea Django; signup, verificarea emailului și resetarea parolei sunt ⬜. |
| 09.02 Provider fake | ✅ | Folosit de toate testele. |
| 09.04 / 09.06 Teste | 🟡 | `console/tests.py`: 8 teste (stream, regenerare, 404 anti-IDOR, PATCH/DELETE, login). |

**Ieșire din Faza 1:** ramuri cu edit, căutare full-text (02.09), preferințe și styles (02.10–02.11),
setări (04.13), i18n (04.19), accesibilitate (04.18).

## Faza 2 — Proiecte & fișiere
02.12–02.13 · 03.05–03.07 · 05.08–05.16 · 09.03

## Faza 3 — Artifacts
05.01–05.07 · 05.18 · 05.20 · 09.09

## Faza 4 — Monetizare & limite
07.01–07.20 · 02.16 · 03.13 · 04.14 · 09.13

## Faza 5 — Producție & conformitate
06.02–06.20 · 08.01–08.20 · 09.14–09.16 — **blocant pentru publicare:** 06.11–06.13 (Datenschutz, AGB, AVV), 08.03 (Traefik pentru SSE), `seo/legal.json` completat.

## Faza 6 — Produs & creștere
10.01–10.20 · 01.18 · 05.17 · 05.19

---

## Rețeta pentru fiecare prompt

1. Deschide fișierul promptului și lipește secțiunea „Prompt” într-o sesiune nouă (un prompt = un PR).
2. Rulează `cd backend && ./dev.sh` și verifică în `/console/` și în `/admin/`.
3. Rulează testele (`python manage.py test console accounts`, cu `DATABASE_URL=sqlite:///db.sqlite3`).
4. Actualizează statusul în acest fișier.
