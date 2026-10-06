/* n8n page: live HUD + animated workflow canvas. The HUD reads real aggregates from the
   `georgeai-stats` workflow on app.n8n-studio.com (docs/n8n-georgeai-stats.json); the canvas is a
   browser-only simulation of four real workflow shapes, so it never needs a key. Sibling of
   jarvis.js: same page skeleton, same reduced-motion and visibility rules. */
(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const root = $('#lab'); if (!root) return;
  const rmq = matchMedia('(prefers-reduced-motion: reduce)');
  const L = (() => { const l = (document.documentElement.lang || 'en').slice(0, 2); return ['en', 'de', 'fr', 'ro', 'ar'].includes(l) ? l : 'en'; })();
  const T = (k) => (STR[L] && STR[L][k]) || STR.en[k];
  const STR = {
    en: { start: 'Trigger received', done: 'Done in', retry: 'Retry succeeded', err: 'Error caught, retrying', live: 'Live', offline: 'Stats offline', updated: 'updated', s: 's', ms: 'ms', run: 'Running', ok: 'Success', queued: 'Queued', now: 'just now' },
    de: { start: 'Trigger empfangen', done: 'Fertig in', retry: 'Wiederholung erfolgreich', err: 'Fehler abgefangen, Wiederholung', live: 'Live', offline: 'Statistik offline', updated: 'aktualisiert', s: 's', ms: 'ms', run: 'Läuft', ok: 'Erfolg', queued: 'Wartet', now: 'gerade eben' },
    fr: { start: 'Déclencheur reçu', done: 'Terminé en', retry: 'Nouvelle tentative réussie', err: 'Erreur interceptée, nouvelle tentative', live: 'En direct', offline: 'Stats hors ligne', updated: 'mis à jour', s: 's', ms: 'ms', run: 'En cours', ok: 'Succès', queued: 'En attente', now: 'à l’instant' },
    ro: { start: 'Trigger primit', done: 'Gata în', retry: 'Reîncercare reușită', err: 'Eroare prinsă, reîncerc', live: 'Live', offline: 'Statistici offline', updated: 'actualizat', s: 's', ms: 'ms', run: 'Rulează', ok: 'Succes', queued: 'În așteptare', now: 'chiar acum' },
    ar: { start: 'تم استلام المشغّل', done: 'اكتمل خلال', retry: 'نجحت إعادة المحاولة', err: 'تم التقاط خطأ، إعادة المحاولة', live: 'مباشر', offline: 'الإحصاءات غير متاحة', updated: 'حُدّث', s: 'ث', ms: 'مللي ث', run: 'قيد التشغيل', ok: 'نجاح', queued: 'في الانتظار', now: 'الآن' }
  };

  /* ---------- live HUD (real numbers) ---------- */
  const STATS = 'https://app.n8n-studio.com/webhook/georgeai-stats';
  const badge = $('#live'), tiles = { active: $('#st-active'), runs7: $('#st-runs7'), runs24: $('#st-runs24'), rate: $('#st-rate'), dur: $('#st-dur') };
  const spark = $('#spark');
  function count(el, to, fmt) {
    if (!el) return; const from = 0, t0 = performance.now(), d = rmq.matches ? 0 : 1100;
    const step = now => { const p = d ? Math.min(1, (now - t0) / d) : 1, e = 1 - Math.pow(1 - p, 3); el.textContent = fmt(from + (to - from) * e); if (p < 1) requestAnimationFrame(step); };
    requestAnimationFrame(step);
  }
  function paintHud(s) {
    count(tiles.active, s.workflows_active, v => Math.round(v) + ' / ' + s.workflows_total);
    count(tiles.runs7, s.runs_7d, v => Math.round(v).toLocaleString());
    count(tiles.runs24, s.runs_24h, v => Math.round(v).toLocaleString());
    if (s.success_rate != null) count(tiles.rate, s.success_rate, v => v.toFixed(1) + ' %');
    if (s.avg_duration_ms != null) count(tiles.dur, s.avg_duration_ms, v => v >= 1000 ? (v / 1000).toFixed(1) + ' ' + T('s') : Math.round(v) + ' ' + T('ms'));
    if (spark && s.per_day) {
      const max = Math.max(1, ...s.per_day.map(d => d.runs)), w = 100, h = 40, n = s.per_day.length;
      const dx = n > 1 ? w / (n - 1) : 0;  // single-day payload -> one point at x=0, no Infinity/NaN
      const pts = s.per_day.map((d, i) => [i * dx, h - 4 - (d.runs / max) * (h - 8)]);
      spark.innerHTML = `<path class="area" d="M0 ${h} ${pts.map(p => 'L' + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ')} L${w} ${h} Z"/><path class="line" d="${pts.map((p, i) => (i ? 'L' : 'M') + p[0].toFixed(1) + ' ' + p[1].toFixed(1)).join(' ')}"/>` +
        pts.map(p => `<circle cx="${p[0].toFixed(1)}" cy="${p[1].toFixed(1)}" r="1.6"/>`).join('');
    }
    const at = new Date(s.generated_at || Date.now());
    badge.innerHTML = `<span class="dot"></span>${T('live')} · ${T('updated')} ${at.toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' })}`;
    badge.classList.add('on');
  }
  function loadStats() {
    let cached = null; try { cached = JSON.parse(sessionStorage.getItem('n8n-stats') || 'null'); } catch (_) {}
    if (cached && Date.now() - Date.parse(cached.generated_at) < 3e5) { paintHud(cached); return; }
    fetch(STATS, { mode: 'cors' }).then(r => { if (!r.ok) throw 0; return r.json(); }).then(s => { paintHud(s); try { sessionStorage.setItem('n8n-stats', JSON.stringify(s)); } catch (_) {} })
      .catch(() => { badge.innerHTML = `<span class="dot"></span>${T('offline')}`; badge.classList.add('off'); });
  }
  loadStats();

  /* ---------- workflow scenarios (shapes of real georgeai workflows) ---------- */
  // node kinds: trigger | ai | app | logic | out. Durations are per-node run times (ms) in the simulation.
  const SC = {
    lead: { name: 'Lead intake', nodes: [
      ['t', 40, 180, 'Webhook', 'trigger', 250, 'georgeai.dev form'], ['v', 190, 180, 'Validate', 'logic', 180, 'e-mail · URL'], ['ai', 340, 180, 'Claude', 'ai', 1400, 'audit the site'],
      ['db', 500, 90, 'Data table', 'app', 220, 'audit_leads'], ['m', 500, 180, 'Gmail', 'app', 480, 'report to lead'], ['sl', 500, 270, 'Slack', 'app', 200, 'notify George'], ['e', 660, 180, 'Done', 'out', 120, 'lead scored']],
      edges: [['t', 'v'], ['v', 'ai'], ['ai', 'db'], ['ai', 'm'], ['ai', 'sl'], ['db', 'e'], ['m', 'e'], ['sl', 'e']] },
    stripe: { name: 'Stripe → order', nodes: [
      ['t', 40, 180, 'Stripe', 'trigger', 200, 'checkout.session'], ['f', 190, 180, 'Map product', 'logic', 150, 'metadata.slug'], ['db', 340, 110, 'Data table', 'app', 240, 'orders'],
      ['inv', 340, 250, 'Invoice', 'logic', 380, 'PDF · §14 UStG'], ['m', 500, 180, 'Gmail', 'app', 520, 'confirmation'], ['e', 660, 180, 'Done', 'out', 120, 'order booked']],
      edges: [['t', 'f'], ['f', 'db'], ['f', 'inv'], ['db', 'm'], ['inv', 'm'], ['m', 'e']] },
    phone: { name: 'Missed call → booking', nodes: [
      ['t', 40, 180, 'VAPI', 'trigger', 300, 'voice agent'], ['stt', 190, 180, 'Transcript', 'logic', 200, 'DE · EN · RO'], ['ai', 340, 180, 'Claude', 'ai', 1200, 'intent + slot'],
      ['cal', 500, 110, 'Calendar', 'app', 460, 'find free slot'], ['crm', 500, 250, 'CRM', 'app', 300, 'upsert contact'], ['sms', 660, 180, 'WhatsApp', 'app', 350, 'confirm'], ['e', 780, 180, 'Done', 'out', 100, 'booked']],
      edges: [['t', 'stt'], ['stt', 'ai'], ['ai', 'cal'], ['ai', 'crm'], ['cal', 'sms'], ['crm', 'sms'], ['sms', 'e']] },
    inbox: { name: 'Inbox triage', nodes: [
      ['t', 40, 180, 'IMAP', 'trigger', 220, 'new e-mail'], ['ai', 190, 180, 'Claude', 'ai', 900, 'classify'], ['sw', 340, 180, 'Switch', 'logic', 90, 'route'],
      ['a', 500, 90, 'Reply draft', 'app', 700, 'support'], ['b', 500, 180, 'CRM', 'app', 260, 'sales'], ['c', 500, 270, 'Archive', 'app', 120, 'newsletter'], ['e', 660, 180, 'Done', 'out', 100, 'sorted']],
      edges: [['t', 'ai'], ['ai', 'sw'], ['sw', 'a'], ['sw', 'b'], ['sw', 'c'], ['a', 'e'], ['b', 'e'], ['c', 'e']], flaky: 'a' }
  };
  const NS = 'http://www.w3.org/2000/svg', svg = $('#wf'), log = $('#runlog'), chips = $$('.chip[data-sc]');
  const ses = { runs: 0, ok: 0, ms: 0 }, sesEl = { runs: $('#s-runs'), ok: $('#s-ok'), avg: $('#s-avg') };
  let cur = null, running = false, timer = null, pulses = [];
  const el = (n, a = {}) => { const e = document.createElementNS(NS, n); for (const k in a) e.setAttribute(k, a[k]); return e; };

  function build(key) {
    cur = SC[key]; svg.innerHTML = ''; pulses = [];
    const W = 120, H = 56, pos = {}; cur.nodes.forEach(n => pos[n[0]] = { x: n[1], y: n[2] });
    const gE = el('g', { class: 'edges' }), gN = el('g', { class: 'nodes' }); svg.append(gE, gN);
    cur.edges.forEach(([a, b]) => { const A = pos[a], B = pos[b]; const d = `M${A.x + W} ${A.y + H / 2} C ${A.x + W + 40} ${A.y + H / 2}, ${B.x - 40} ${B.y + H / 2}, ${B.x} ${B.y + H / 2}`; gE.appendChild(el('path', { d, 'data-e': a + '-' + b })); });
    cur.nodes.forEach(n => {
      const g = el('g', { class: 'node ' + n[4], 'data-n': n[0], transform: `translate(${n[1]} ${n[2]})` });
      g.appendChild(el('rect', { width: W, height: H, rx: 12 }));
      const t1 = el('text', { x: 14, y: 24, class: 'nm' }); t1.textContent = n[3];
      const t2 = el('text', { x: 14, y: 42, class: 'sub' }); t2.textContent = n[6];
      const st = el('circle', { cx: W - 14, cy: 16, r: 4, class: 'st' });
      g.append(t1, t2, st); gN.appendChild(g);
    });
    svg.setAttribute('viewBox', `0 0 ${Math.max(...cur.nodes.map(n => n[1])) + W + 40} 360`);
    chips.forEach(c => c.setAttribute('aria-pressed', String(c.dataset.sc === key)));
  }
  const node = id => $(`.node[data-n="${id}"]`, svg), edge = (a, b) => $(`path[data-e="${a}-${b}"]`, svg);
  const wait = ms => new Promise(r => setTimeout(r, rmq.matches ? Math.min(ms, 120) : ms));
  function line(text, cls) {
    const m = document.createElement('div'); m.className = 'rl ' + (cls || '');
    const t = document.createElement('span'); t.className = 'mono'; t.textContent = new Date().toLocaleTimeString('de-DE', { hour12: false });
    const b = document.createElement('span'); b.textContent = text; m.append(t, b); log.appendChild(m);
    while (log.children.length > 14) log.firstChild.remove(); log.scrollTop = log.scrollHeight;
  }
  function pulse(a, b, ms) {
    const p = edge(a, b); if (!p) return wait(ms);
    p.classList.add('hot'); if (rmq.matches) return wait(60);
    const c = el('circle', { r: 5, class: 'pulse' }); svg.appendChild(c);
    const len = p.getTotalLength(), t0 = performance.now();
    return new Promise(res => { const f = now => { const k = Math.min(1, (now - t0) / ms), pt = p.getPointAtLength(len * k); c.setAttribute('cx', pt.x); c.setAttribute('cy', pt.y); if (k < 1) requestAnimationFrame(f); else { c.remove(); res(); } }; requestAnimationFrame(f); });
  }
  async function runNode(id, seen) {
    if (seen.has(id)) return; seen.add(id);
    const n = cur.nodes.find(x => x[0] === id), g = node(id); g.classList.add('run'); g.classList.remove('ok', 'err');
    let ms = n[5];
    if (cur.flaky === id && ses.runs % 3 === 1) { await wait(ms * .6); g.classList.replace('run', 'err'); line(n[3] + ' · ' + T('err'), 'err'); await wait(500); g.classList.replace('err', 'run'); await wait(ms * .6); line(n[3] + ' · ' + T('retry'), 'ok'); ms *= 1.7; }
    else await wait(ms);
    g.classList.replace('run', 'ok'); line(n[3] + ' · ' + n[6] + ' · ' + Math.round(ms) + ' ' + T('ms'));
    const outs = cur.edges.filter(e => e[0] === id).map(e => e[1]);
    await Promise.all(outs.map(async b => { await pulse(id, b, 420); await runNode(b, seen); }));
  }
  async function run(key) {
    if (running) return; running = true; clearTimeout(timer);
    if (!cur || SC[key] !== cur) build(key);
    $$('.node', svg).forEach(g => g.classList.remove('ok', 'err', 'run')); $$('path.hot', svg).forEach(p => p.classList.remove('hot'));
    root.classList.add('busy'); line(cur.name + ' · ' + T('start'), 'you');
    const t0 = performance.now(); await runNode(cur.nodes[0][0], new Set());
    const ms = performance.now() - t0; ses.runs++; ses.ok++; ses.ms += ms;
    line(T('done') + ' ' + (ms / 1000).toFixed(1) + ' ' + T('s'), 'ok'); root.classList.remove('busy');
    sesEl.runs.textContent = ses.runs; sesEl.ok.textContent = Math.round(ses.ok / ses.runs * 100) + ' %'; sesEl.avg.textContent = (ses.ms / ses.runs / 1000).toFixed(1) + ' ' + T('s');
    running = false; schedule();
  }
  const KEYS = Object.keys(SC); let auto = 0;
  function schedule() { clearTimeout(timer); if (document.hidden || rmq.matches) return; timer = setTimeout(() => run(KEYS[++auto % KEYS.length]), 6500); }
  chips.forEach(c => c.addEventListener('click', () => { auto = KEYS.indexOf(c.dataset.sc); clearTimeout(timer); if (running) return; run(c.dataset.sc); }));
  document.addEventListener('visibilitychange', () => document.hidden ? clearTimeout(timer) : schedule());
  build('lead');
  // start once the canvas is on screen, so the first run is seen and not wasted
  const io = new IntersectionObserver(es => { if (es.some(e => e.isIntersecting)) { io.disconnect(); setTimeout(() => run('lead'), 500); } }, { threshold: .3 });
  io.observe(root);
})();
