# Frontend — UI-ul consolei

Interfața care trebuie să se simtă ca claude.ai: layout, composer, randarea mesajelor, tranziții. Pentru fiecare prompt invocă skill-ul `ui-ux-pro-max` și respectă `brand/palette.json`.

> **Context comun (lipește-l înaintea promptului dacă agentul nu are CLAUDE.md):**
> Repo `georgeai_dev` — Django 5.2 + DRF (SessionAuthentication, user custom pe email în `backend/accounts`), PostgreSQL în containerul `gethub-postgres`, deploy pe VPS `85.215.69.83` în spatele Traefik. Ținta: **GeorgeAI Console**, o consolă de chat AI cu paritate funcțională și de UX față de **claude.ai** (sidebar cu conversații, proiecte cu knowledge, artifacts în panou lateral, streaming token-cu-token, model picker, upload fișiere, căutare, share, setări, limite de utilizare). Paleta live: `brand/palette.json` (canvas `#02060a`, accent `#fb5e31`/`#b23c0a`, Plus Jakarta Sans). Nu edita niciodată `site/` sau `frontend/template/` — sunt build output.

| # | Prompt | Fișier |
|---|---|---|
| 01 | Scaffold SPA | [01-scaffold-spa.md](01-scaffold-spa.md) |
| 02 | Design tokens | [02-design-tokens.md](02-design-tokens.md) |
| 03 | Layout cu sidebar | [03-layout-cu-sidebar.md](03-layout-cu-sidebar.md) |
| 04 | Ecranul New chat | [04-ecranul-new-chat.md](04-ecranul-new-chat.md) |
| 05 | Composer-ul | [05-composer-ul.md](05-composer-ul.md) |
| 06 | Randarea streamului | [06-randarea-streamului.md](06-randarea-streamului.md) |
| 07 | Randare Markdown | [07-randare-markdown.md](07-randare-markdown.md) |
| 08 | Acțiuni pe mesaj | [08-actiuni-pe-mesaj.md](08-actiuni-pe-mesaj.md) |
| 09 | Panou Thinking și tools | [09-panou-thinking-si-tools.md](09-panou-thinking-si-tools.md) |
| 10 | Lista de conversații | [10-lista-de-conversatii.md](10-lista-de-conversatii.md) |
| 11 | Paleta de comenzi și căutarea | [11-paleta-de-comenzi-si-cautarea.md](11-paleta-de-comenzi-si-cautarea.md) |
| 12 | Scurtături de tastatură | [12-scurtaturi-de-tastatura.md](12-scurtaturi-de-tastatura.md) |
| 13 | Pagina de setări | [13-pagina-de-setari.md](13-pagina-de-setari.md) |
| 14 | Indicatorul de utilizare | [14-indicatorul-de-utilizare.md](14-indicatorul-de-utilizare.md) |
| 15 | Stări goale, încărcare, erori | [15-stari-goale-incarcare-erori.md](15-stari-goale-incarcare-erori.md) |
| 16 | Experiența mobilă | [16-experienta-mobila.md](16-experienta-mobila.md) |
| 17 | Animații și micro-interacțiuni | [17-animatii-si-micro-interactiuni.md](17-animatii-si-micro-interactiuni.md) |
| 18 | Accesibilitate | [18-accesibilitate.md](18-accesibilitate.md) |
| 19 | Internaționalizare | [19-internationalizare.md](19-internationalizare.md) |
| 20 | Paritate vizuală — review | [20-paritate-vizuala-review.md](20-paritate-vizuala-review.md) |
