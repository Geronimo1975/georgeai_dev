# `improve-animations` — cum îl folosești pe georgeai.dev

## Ce face
Skill **advisor, read-only**: face recon pe codul de motion, auditează pe 8 categorii
(scop/frecvență, easing/durată, fizicalitate/origine, întreruptibilitate, performanță,
accesibilitate, coeziune/tokens, oportunități ratate) și scrie **planuri
self-contained** în `plans/` (sau `animation-plans/`). **Nu modifică sursa.**

## Cum îl invoci
Scrii pur și simplu în prompt ce vrei — skill-ul se declanșează pe formulări de tip
"audit the motion", "improve the animations", "roadmap of animation fixes".
Sau explicit: `Skill: improve-animations` / `/improve-animations`.

Efort: `quick` | `standard` (default) | `deep`.

## Unde trăiește motion-ul în acest repo
- `hero/hero-motion.css` + `hero-motion.js` — entrance choreography, pointer parallax
- `hero/hero-cinema.css` + `hero-cinema.js` — stage video backdrop
- `seo/responsive.css`, `brand/apply_brand.py` (accent/token-uri)
- `pages/pricing/index.html`, `backend/assets/audit.js` (modal lead widget)
- paginile generate: `seo/generate_service_pages.py`

⚠️ Nu audita `site/` sau `frontend/template/` — sunt build output, se regenerează la fiecare deploy.
Fix-urile se aplică în `hero/`, `seo/`, `brand/`, `pages/`, `backend/assets/`.

---

## 20 de comenzi pentru acest proiect

1. `improve-animations` — audit standard pe tot repo-ul, ignoră `site/` și `frontend/template/`.
2. `improve-animations quick pe hero/` — pass rapid doar pe `hero-motion.css` + `hero-motion.js`.
3. `improve-animations deep pe hero/` — audit complet al entrance choreography din hero.
4. `improve-animations` — auditează doar categoria *Easing & duration* în `hero/hero-motion.css`; caută `ease-in` și `transition: all`.
5. `improve-animations` — verifică *Interruptibility*: ce se întâmplă dacă mut mouse-ul în timpul entrance-ului hero (`hero-motion.js`).
6. `improve-animations` — audit *Accessibility*: unde lipsește `prefers-reduced-motion` în `hero/`, `seo/responsive.css`, `backend/assets/audit.js`.
7. `improve-animations` — audit *Performance*: proprietăți non-compozitate (animăm `top`/`width`/`box-shadow` în loc de `transform`/`opacity`).
8. `improve-animations` — audit *Physicality & origin*: `transform-origin` pe hover-urile cardurilor de servicii și News.
9. `improve-animations` — audit *Cohesion & tokens*: propune un scale `--ease-*` / `--duration-*` unic partajat de hero, pricing și widget.
10. `improve-animations` — frequency map: ce animație e lovită la fiecare load (hero) vs. rar (modal signin), și re-prioritizează severitățile după asta.
11. `improve-animations` — motion pe pointer parallax: e prea agresiv? Propune un plan cu valori exacte de damping.
12. `improve-animations quick pe pages/pricing/index.html` — hover/press pe cele 7 butoane de buy.
13. `improve-animations` — audit pe `backend/assets/audit.js`: enter/exit al modalului de lead capture.
14. `improve-animations` — audit pe modalul de signin/signup injectat de `backend/assets/auth.js`.
15. `improve-animations` — audit pe paginile generate de `seo/generate_service_pages.py` (hub `/services/` + `/blog/`).
16. `improve-animations` — *Missed opportunities*: unde lipsește feedback de motion pe stările de loading/success ale formularelor.
17. `improve-animations` — verifică dacă `hero/hero-cinema.js` mai face treabă după fix-urile de contrast din `f23080c`.
18. `improve-animations` — auditează interacțiunea video-hero ↔ entrance: se bat cap în cap `hero-motion` și `hero-cinema`?
19. `improve-animations` — dă-mi doar top 3 findings cu cel mai mare leverage, cu planuri gata de executat.
20. `improve-animations execute plans/<nume>.md` — rulează un plan deja scris (sau: dă planul unui subagent ieftin).

## Flux tipic
```
improve-animations deep pe hero/          # → plans/*.md
cat plans/*.md                            # citește prioritizarea
improve-animations execute plans/01-*.md  # aplică unul câte unul
./deploy.sh --no-content                  # re-aplică layerele, hero inclus
```
