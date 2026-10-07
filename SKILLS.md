# Skill-uri necesare — proiectul `georgeai_dev` (georgeai.dev)

**Audiență:** project manager (planificare resurse), team leads (asignare task-uri), stakeholder/clienți (vedere de ansamblu), HR/recruiting (recrutare și identificare de gap-uri).

**Data analizei:** 30 august 2026 · **Sursa:** analiza directă a codului din repository.

---

## Rezumat pentru stakeholderi (o pagină)

`georgeai_dev` nu este „un site". Este un **pipeline de publicare** plus un **backend** plus un **lanț de plăți monitorizat**. Site-ul public (georgeai.dev) este proiectat într-un tool de design extern care exportă un `.zip`; repository-ul despachetează acel export și **re-aplică peste el, la fiecare deploy, 13 straturi proprii** (SEO, conținut, brand, imagini, legal, hero cinematic, widget de lead-uri etc.), apoi îl trimite pe un VPS.

Consecința pentru planificare: proiectul cere un profil **full-stack cu accent pe automatizare**, nu un frontend developer clasic. Munca reală nu este „scrie HTML", ci „scrie cod Python care rescrie HTML generat de altcineva, în mod idempotent, fără să strice producția".

**Dimensiune actuală:** ~4.300 linii Python (pipeline + backend), ~2.600 linii JavaScript propriu (fără export), 2 workflow-uri CI, 5 limbi de conținut.

---

## Pasul 1: Sursa listei de skill-uri

Nu există în acest mediu o bază de date de skill-uri la nivel de organizație (tip HR skills matrix sau catalog de competențe). Ce există și a fost folosit ca sursă:

- **Registrul de agent-skills al proiectului**: `skills-lock.json` și `.claude/skills/` (playbook-uri interne: `georgeai-deploy`, `georgeai-backend`, `georgeai-seo`, `georgeai-vps`, `georgeai-n8n`). Acestea confirmă ce zone au fost considerate destul de complexe încât să merite documentație dedicată, deci sunt un indicator direct de competențe critice.
- **Documentația de arhitectură a proiectului**: `CLAUDE.md`, `DESIGN-claude.md`, `docs/`.
- **Codul propriu-zis**: dependențe, scripturi, configurații de infrastructură, workflow-uri CI.

Lista de mai jos este derivată din aceste trei surse, nu dintr-un catalog extern.

---

## Pasul 2 și 3: Skill-urile necesare, pe categorii

Legendă nivel: **Esențial** = fără el proiectul nu poate fi menținut · **Important** = necesar pentru dezvoltare curentă · **Util** = necesar ocazional sau pentru extindere.

### 1. Backend

| Skill | Nivel | De ce este necesar aici |
|---|---|---|
| **Python 3.12** | Esențial | Limbajul întregului pipeline de deploy și al backend-ului. Toate cele 13 straturi de post-procesare sunt scripturi Python (`seo/`, `brand/`, `images/`, `idn/`). |
| **Django 5.2** | Esențial | `backend/` servește exportul static plus un API de autentificare. Include un `User` custom bazat pe email (fără username), ceea ce cere înțelegerea `AUTH_USER_MODEL` și a migrărilor aferente. |
| **Django REST Framework** | Important | API-ul `/api/auth/{signup,login,logout,me}`, configurat deliberat **doar** cu SessionAuthentication și renderer JSON. |
| **PostgreSQL 16** | Important | Baza de date rulează într-un container partajat pe VPS (`gethub-postgres`). Nu există bază locală: dezvoltarea cere tunel SSH pe portul 5434. |
| **Securitate web aplicată (CSRF, sesiuni, CSP)** | Important | Proiectul are decizii de securitate deliberate și contra-intuitive care trebuie înțelese, nu „corectate": `CSRF_COOKIE_HTTPONLY = False` este intenționat, iar `nginx.conf` livrează un `Content-Security-Policy-Report-Only` care încă nu este impus. |

### 2. Frontend

| Skill | Nivel | De ce este necesar aici |
|---|---|---|
| **JavaScript vanilla (fără framework)** | Esențial | Tot codul de frontend propriu este JS pur, fără build step: `hero/hero-motion.js` (691 linii), `hero/hero-cinema.js` (1.304 linii), `backend/assets/auth.js`, `backend/assets/audit.js`. Un profil care lucrează doar cu React nu poate întreține acest cod. |
| **CSS avansat (custom properties, scroll-driven, teme)** | Esențial | ~1.000 de linii de CSS propriu cu sistem de tokens, teme light/dark, coregrafie de intrare și legibilitate peste video. |
| **DOM prin structură, nu prin selectori** | Esențial | Exportul din tool-ul de design **nu are clase sau id-uri stabile** și este re-randat client-side la fiecare `setState`. Codul propriu se agață de structură și folosește `MutationObserver`. Este cel mai neobișnuit skill din proiect și cel mai greu de recrutat. |
| **Animație și motion design pe web** | Important | Hero-ul are coregrafie de intrare, parallax de pointer, video de fundal și un strat „cinema" scroll-scrubbed. Există reguli interne stricte: doar `transform` și `opacity`, curbe de easing definite, `prefers-reduced-motion` obligatoriu. |
| **Accesibilitate (WCAG AA)** | Important | Contrastul este testat automat (`tests/test_hero_contrast.py`) și există un strat de brand care rescrie culorile exportului pentru a atinge AA (`brand/apply_brand.py`). |
| **Internaționalizare (5 limbi)** | Util | Conținutul există în EN/DE/FR/RO și încă o limbă, inclusiv textele legale. |

### 3. DevOps și infrastructură

| Skill | Nivel | De ce este necesar aici |
|---|---|---|
| **Bash (scripting de nivel mediu-avansat)** | Esențial | `deploy.sh` este orchestratorul întregului proces: despachetare, 13 straturi, rsync, restart container, health checks. |
| **Docker și Docker Compose** | Esențial | Producția rulează în containere (`deploy/docker-compose.yml`): nginx + aplicația Django, pe o rețea Docker externă partajată. |
| **nginx** | Important | Configurație proprie cu header-e per locație (`deploy/nginx.conf`). |
| **Traefik v2.11 + Let's Encrypt** | Important | Routing-ul și certificatele TLS se fac prin labels Docker, nu prin fișiere de config. |
| **Administrare VPS Linux, SSH, rsync** | Esențial | Deploy-ul înseamnă sincronizare pe un VPS real (85.215.69.83) prin alias SSH. Nu există platformă PaaS care să ascundă asta. |
| **GitHub Actions** | Important | Două pipeline-uri: `backend-ci.yml` (pip-audit + migrate + teste, cu Postgres service container) și `payments-pipeline.yml` (verificare la fiecare 6 ore, direct pe producție). |
| **ffmpeg** | Util | Pipeline-ul re-multiplexează video-urile exportului (`+faststart`) și re-encodează hero-ul. |

### 4. Automatizare, integrări și plăți

| Skill | Nivel | De ce este necesar aici |
|---|---|---|
| **Stripe (Payment Links, metadata, mod test/live)** | Esențial | Întregul flux de bani. Există 7 butoane de plată, fiecare produs poartă `metadata.data_product`, iar trecerea din test în live este o procedură documentată (`docs/stripe-payment-links.md`, `scripts/stripe_golive.py`). |
| **n8n (workflow automation)** | Esențial | Checkout-urile Stripe intră printr-un webhook într-un workflow n8n care scrie în tabelul `orders` și trimite emailul de confirmare. Fără acest skill, comenzile nu pot fi depanate. |
| **Integrare API și webhook-uri** | Important | Widget-ul de audit (`backend/assets/audit.js`) trimite lead-urile către un webhook n8n care generează un raport. |

### 5. SEO, GEO și conținut

| Skill | Nivel | De ce este necesar aici |
|---|---|---|
| **SEO tehnic** | Esențial | Un strat întreg din pipeline: `seo/head.html` (title, meta, OG, JSON-LD), `robots.txt`, `sitemap.xml` regenerat automat, pagini statice crawlabile generate din `georgeai_services.json`. |
| **GEO / optimizare pentru AI search** | Important | Proiectul livrează `llms.txt` și are un document de analiză dedicat (`GEO-ANALYSIS.md`). Este o competență nouă pe piață și rar întâlnită. |
| **Generare de pagini din date** | Important | `seo/generate_service_pages.py` produce hub-ul `/services/`, o pagină per serviciu și `/blog/` din fragmente HTML cu metadate. |
| **Copywriting de conversie** | Util | Textele de marketing sunt versionate ca sursă de adevăr în `seo/hero.json` și `seo/testimonials.json`, tocmai pentru că exportul le suprascrie. |

### 6. Calitate, testare și monitorizare

| Skill | Nivel | De ce este necesar aici |
|---|---|---|
| **Testare Python (stdlib + Django test runner)** | Important | Suita de plăți este scrisă intenționat **doar cu biblioteca standard**, ca să ruleze oriunde fără dependențe (`tests/test_payments_pipeline.py`). |
| **Monitorizare și cron** | Important | `cron/check_payments.sh` plus workflow-ul la 6 ore verifică lanțul complet de comenzi pe producție. |
| **Gândire de tip „regression guard"** | Esențial | Testele există ca să prindă *drift*: prețurile trăiesc în trei locuri (pagina de pricing, Stripe, dicționarul `CATALOG` din teste) și suita cade intenționat dacă se desincronizează. |

### 7. Legal și conformitate (piața germană)

| Skill | Nivel | De ce este necesar aici |
|---|---|---|
| **Conformitate DDG / Impressum / TVA (DE)** | Important | `seo/apply_legal.py` reconstruiește identitatea legală în 5 limbi și **blochează deploy-ul** (exit 2) cât timp datele nu sunt completate. Un Impressum cu placeholder este un defect legal și blochează lansarea Stripe. |
| **GDPR / consimțământ cookie** | Util | Există un banner de consimțământ care interacționează cu restul UI-ului. |

---

## Tabel de sinteză pentru PM și HR

| Categorie | Skill-uri esențiale | Efort de recrutare |
|---|---|---|
| Backend | Python, Django, DRF, PostgreSQL | Mediu — profil comun pe piață |
| Frontend | JS vanilla, CSS avansat, manipulare DOM prin structură | **Ridicat** — piața formează oameni pe framework-uri, nu pe JS pur |
| DevOps | Bash, Docker, VPS/SSH, Traefik, GitHub Actions | Mediu |
| Automatizare | Stripe, n8n | **Ridicat** — n8n este o nișă |
| SEO/GEO | SEO tehnic, GEO/llms.txt | Ridicat pentru GEO, mediu pentru SEO clasic |
| Calitate | Testare Python, monitorizare | Scăzut |
| Legal DE | DDG, Impressum, TVA | Se poate acoperi cu consultanță externă |

---

## Observații pentru planificare (PM și team leads)

1. **Proiectul este în prezent acoperit de o singură persoană.** Toate cele șapte categorii de mai sus sunt concentrate într-un singur profil full-stack. Riscul de *bus factor* este real și este cel mai important punct de discutat la planificarea resurselor.

2. **Cea mai rară combinație este frontend + pipeline.** Straturile care rescriu exportul (`seo/`, `brand/`, `images/`, `idn/`) cer simultan Python bun și înțelegere fină de DOM și CSS. Sunt două competențe pe care piața le separă de obicei în două roluri.

3. **Zone care se pot externaliza sau delega ușor:** conformitatea legală germană (consultanță), copywriting-ul, generarea de conținut pentru blog.

4. **Zone care nu se pot delega fără transfer de cunoștințe:** deploy-ul și straturile lui. Sunt idempotente și au capcane documentate (de exemplu: un export vechi din `~/Downloads` ar da producția înapoi cu două luni). Playbook-urile din `.claude/skills/` sunt punctul de plecare pentru orice onboarding.

5. **Gap-uri vizibile în acest moment:** nu există teste automate pentru frontend-ul propriu (JS-ul de hero, ~2.600 linii, este verificat doar manual și printr-un test de contrast), iar `Content-Security-Policy` este încă în mod „report-only". Ambele sunt candidate naturale pentru primul task al unei persoane noi în echipă.
