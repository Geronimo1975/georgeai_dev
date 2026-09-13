/* GeorgeAI cinematic page. Vanilla JS. GSAP + ScrollTrigger + Lenis from CDN (defer, same order).
   Engineering standard: BUILD-PLAN.md §24 and .claude/skills/10k-websites/references/scrub-pipeline.md */
(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const clamp = (v, lo, hi) => Math.min(hi, Math.max(lo, v));
  const smoothstep = (p, e0, e1) => { const t = clamp((p - e0) / (e1 - e0), 0, 1); return t * t * (3 - 2 * t); };
  const rmq = matchMedia('(prefers-reduced-motion: reduce)');
  const coarse = matchMedia('(pointer: coarse)');

  /* ---------- Lenis + GSAP ---------- */
  let lenis = null, lenisTick = null;
  const hasGsap = typeof gsap !== 'undefined' && typeof ScrollTrigger !== 'undefined';
  if (hasGsap) gsap.registerPlugin(ScrollTrigger);
  function startLenis() {
    if (lenis || typeof Lenis === 'undefined' || rmq.matches || coarse.matches) return;
    lenis = new Lenis({ lerp: 0.09, smoothWheel: true });
    if (hasGsap) {
      lenis.on('scroll', ScrollTrigger.update);
      lenisTick = t => { if (lenis) lenis.raf(t * 1000); };
      gsap.ticker.add(lenisTick);
      gsap.ticker.lagSmoothing(0);
    } else {
      const raf = t => { if (!lenis) return; lenis.raf(t); requestAnimationFrame(raf); };
      requestAnimationFrame(raf);
    }
  }
  function stopLenis() {
    if (!lenis) return;
    if (hasGsap && lenisTick) { gsap.ticker.remove(lenisTick); lenisTick = null; }
    lenis.destroy(); lenis = null;
  }
  startLenis();

  // anchor links scroll through Lenis with an offset for the fixed nav
  document.addEventListener('click', e => {
    const a = e.target.closest('a[href^="#"]');
    if (!a || a.hasAttribute('data-audit')) return;
    const el = $(a.getAttribute('href'));
    if (!el) return;
    e.preventDefault();
    closeSheet();
    if (lenis) lenis.scrollTo(el, { offset: -72 }); else el.scrollIntoView({ behavior: rmq.matches ? 'auto' : 'smooth' });
  });

  /* ---------- nav ---------- */
  const nav = $('#nav');
  let navSolid = false;
  function navState() {
    const s = scrollY > 80;
    if (s !== navSolid) { navSolid = s; nav.classList.toggle('solid', s); }
  }
  addEventListener('scroll', navState, { passive: true }); navState();
  const burger = $('.burger'), sheet = $('#sheet');
  function closeSheet() { sheet.hidden = true; burger.setAttribute('aria-expanded', 'false'); document.body.style.overflow = ''; }
  burger.addEventListener('click', () => {
    const open = sheet.hidden;
    sheet.hidden = !open; burger.setAttribute('aria-expanded', String(open));
    document.body.style.overflow = open ? 'hidden' : '';
  });

  /* ---------- the one CTA: the free visibility audit widget (audit.js, injected at deploy) ---------- */
  document.addEventListener('click', e => {
    const a = e.target.closest('[data-audit]');
    if (!a) return;
    e.preventDefault(); closeSheet();
    if (window.gaAudit && typeof window.gaAudit.open === 'function') { window.gaAudit.open(); return; }
    // widget not present (local preview): fall back to the paid audit package
    location.href = '/pricing/#visibility-audit';
  });

  /* ---------- split text (once, seeded) ---------- */
  function rng(seed) { let s = seed >>> 0; return () => (s = (s * 1664525 + 1013904223) >>> 0) / 4294967296; }
  function split(el, fx, seed) {
    const text = el.textContent.trim();
    const r = rng(seed);
    const sr = document.createElement('span'); sr.className = 'sr'; sr.textContent = text;
    const vis = document.createElement('span'); vis.setAttribute('aria-hidden', 'true'); vis.className = 'sharp';
    const words = text.split(' ');
    let ci = 0, total = text.replace(/ /g, '').length;
    words.forEach((w, wi) => {
      const ws = document.createElement('span'); ws.className = 'w';
      ws.style.setProperty('--th', (wi / words.length * 0.55).toFixed(3));
      [...w].forEach(ch => {
        const cs = document.createElement('span'); cs.className = 'c'; cs.textContent = ch;
        cs.style.setProperty('--th', fx === 'grid' ? (ci / total * 0.5 + r() * 0.06).toFixed(3) : (r() * 0.55).toFixed(3));
        cs.style.setProperty('--jx', ((r() - 0.5) * (fx === 'scatter' ? 160 : 60)).toFixed(1) + 'px');
        cs.style.setProperty('--jy', ((r() - 0.5) * 120).toFixed(1) + 'px');
        cs.style.setProperty('--jr', ((r() - 0.5) * 40).toFixed(1) + 'deg');
        ci++; ws.appendChild(cs);
      });
      vis.appendChild(ws);
      if (wi < words.length - 1) vis.appendChild(document.createTextNode(' '));
    });
    el.textContent = ''; el.appendChild(sr); el.appendChild(vis);
    if (fx === 'blur') { const soft = vis.cloneNode(true); soft.className = 'soft'; el.appendChild(soft); }
  }

  /* ---------- hero ---------- */
  const hero = $('#hero'), stage = $('#stage'), video = $('#video'), ring = $('.ring'), poster = $('.poster');
  const portrait = $('.portrait') || $('.still'), beamA = $('.beam-a'), beamB = $('.beam-b'), glowEl = $('.hourglass-glow'), holos = $('.holos');
  if (window.mountGlobe) mountGlobe($('#hero-globe'), { speed: .00008 });
  // holo panels follow the pointer by depth (fine pointers only)
  if (holos && !coarse.matches && !rmq.matches) {
    const panels = $$('.holo', holos); let px = 0, py = 0, hRafP = null;
    const apply = () => { hRafP = null; panels.forEach(h => { const d = +h.dataset.depth || 1; h.style.setProperty('--px', (px * 18 * d).toFixed(1) + 'px'); h.style.setProperty('--py', (py * 12 * d).toFixed(1) + 'px'); }); };
    stage.addEventListener('pointermove', e => { px = e.clientX / innerWidth - .5; py = e.clientY / innerHeight - .5; if (hRafP === null) hRafP = requestAnimationFrame(apply); });
  }
  const bands = $$('.band').map((el, i) => {
    const [a, b] = el.dataset.range.split(',').map(Number);
    const fx = el.dataset.fx;
    $$('.split', el).forEach(h => split(h, fx, 1000 + i * 7));
    return { el, a, b, fx, op: -1, k: -1, first: i === 0, last: i === $$('.band').length - 1 };
  });

  // The video is opt-in: set data-src on #video once assets/hero-scrub.mp4 exists (Higgsfield chain).
  // Without it the still journey carries the hero and no request is made.
  const VIDEO_URL = (video && video.dataset.src) || '';
  const VIDEO_BYTES = 16694491;
  let videoOK = false;

  function heroProgress() {
    if (!hero) return 0;
    const rect = hero.getBoundingClientRect();
    const range = hero.offsetHeight - innerHeight;
    return range > 0 ? clamp(-rect.top / range, 0, 1) : 0;
  }

  // caption bands + still-journey parallax, delta-gated
  let loadK = 0, loadStart = 0;
  function updateCaptions(p, now) {
    if (loadStart && loadK < 1) loadK = clamp((now - loadStart) / 1400, 0, 1);
    for (const bd of bands) {
      const f = Math.min(0.02, (bd.b - bd.a) / 3);
      let op = (bd.first ? 1 : smoothstep(p, bd.a, bd.a + f)) * (bd.last ? 1 : 1 - smoothstep(p, bd.b - f, bd.b));
      let k = clamp((p - bd.a) / Math.min(0.025, (bd.b - bd.a) * 0.35), 0, 1);
      if (bd.first) k = Math.max(k, loadK);
      op = Math.round(op * 200) / 200; k = Math.round(k * 125) / 125;
      if (op !== bd.op) { bd.op = op; bd.el.style.opacity = op; bd.el.classList.toggle('on', op > 0.5); }
      if (k !== bd.k) { bd.k = k; bd.el.style.setProperty('--k', k); }
    }
    if (!videoOK) stillJourney(p);
    const moved = p > 0.03; if (moved !== stage.classList.contains('moved')) stage.classList.toggle('moved', moved);
  }
  // the still journey: while the video does not exist, the poster layers travel with the scroll
  let lastSJ = -1;
  function stillJourney(p) {
    if (!portrait) return;
    const q = Math.round(p * 400) / 400;
    if (q === lastSJ) return; lastSJ = q;
    const s = 1 + q * 0.22, tx = -q * 6, ty = q * 2;
    portrait.style.transform = `translate3d(${tx}vw,${ty}vh,0) scale(${s})`;
    portrait.style.opacity = q < 0.72 ? 1 : 1 - (q - 0.72) / 0.28;
    if (beamA) beamA.style.transform = `rotate(${-14 + q * 30}deg) translate3d(${q * 20}%,0,0)`;
    if (beamB) beamB.style.transform = `translate3d(${-q * 25}%,${-q * 30}%,0) scale(${1 + q * 1.2})`;
    if (beamB) beamB.style.opacity = 0.55 + q * 0.45;
    if (glowEl) glowEl.style.transform = `translate3d(${q * 40}vw,${-q * 30}vh,0) scale(${1 + q * 3})`;
    if (holos) { const f = clamp(1 - q / 0.22, 0, 1); holos.style.opacity = f; holos.style.transform = `translate3d(0,${-(1 - f) * 12}vh,0) scale(${1 + (1 - f) * .15})`; }
  }

  // lerp loop that rests
  let target = 0, shown = 0, rafId = null, lastTick = 0, heroOnScreen = true;
  function tick(now) {
    const dt = Math.min(100, now - (lastTick || now)); lastTick = now;
    shown += (target - shown) * (1 - Math.pow(1 - 0.16, dt / 16.667));
    if (Math.abs(target - shown) < 0.0005 && loadK >= 1) { shown = target; rafId = null; lastTick = 0; }
    else rafId = requestAnimationFrame(tick);
    if (videoOK) requestSeek(shown * video.duration);
    updateCaptions(shown, now);
  }
  function onScroll() { target = heroProgress(); if (rafId === null && heroOnScreen) rafId = requestAnimationFrame(tick); }
  if (hero) new IntersectionObserver(([e]) => { heroOnScreen = e.isIntersecting; if (heroOnScreen) onScroll(); }, { threshold: 0 }).observe(hero);

  // gated seeks
  let seekBusy = false, pendingTime = null;
  function requestSeek(t) {
    if (!video.duration) return;
    if (seekBusy) { pendingTime = t; return; }
    seekBusy = true; video.currentTime = t;
  }
  if (video) video.addEventListener('seeked', () => { seekBusy = false; if (pendingTime !== null) { const t = pendingTime; pendingTime = null; requestSeek(t); } });
  if (video) video.addEventListener('error', () => { seekBusy = false; pendingTime = null; failVideo(); });

  // blob loader with ring + watchdog; a 404 lands in failVideo and the still journey stays
  let inited = false;
  function initHeroOnce() {
    if (inited) return; inited = true;
    loadStart = performance.now() + (rmq.matches ? 0 : 1500);   // the headline assembles as the boot line clears
    loadHeroBlob().catch(failVideo);
  }
  async function loadHeroBlob() {
    if (!VIDEO_URL || location.protocol === 'file:') throw new Error('no video');
    const ctrl = new AbortController();
    let watchdog = setTimeout(() => ctrl.abort(), 20000);
    const res = await fetch(VIDEO_URL, { priority: 'low', signal: ctrl.signal });
    if (!res.ok) throw new Error(res.status);
    const total = Number(res.headers.get('Content-Length')) || VIDEO_BYTES;
    const reader = res.body.getReader(); const chunks = []; let got = 0, lastRing = 0;
    for (;;) {
      const { done, value } = await reader.read(); if (done) break;
      clearTimeout(watchdog); watchdog = setTimeout(() => ctrl.abort(), 20000);
      chunks.push(value); got += value.length;
      const frac = Math.min(1, got / total), now = performance.now();
      if (now - lastRing > 100 || frac === 1) { lastRing = now; ring.style.setProperty('--ld', Math.round(126 * (1 - frac))); }
    }
    clearTimeout(watchdog);
    video.src = URL.createObjectURL(new Blob(chunks, { type: 'video/mp4' })); video.load();
    video.addEventListener('canplay', () => { videoOK = true; requestSeek(heroProgress() * video.duration); stage.classList.add('video-ready'); }, { once: true });
  }
  function failVideo() { videoOK = false; stage.classList.add('video-failed'); }

  // the five static-hero gates, identical to style.css, decided live
  const GATES = ['(max-width: 720px)', '(orientation: portrait) and (max-width: 1024px)', '(orientation: portrait) and (pointer: coarse)', '(orientation: landscape) and (pointer: coarse) and (max-height: 560px)', '(prefers-reduced-motion: reduce)'];
  let scrubOn = false;
  function enableScrub() {
    if (scrubOn) return; scrubOn = true;
    if (!hero) { unpinFinalStates(); return; }
    initHeroOnce();
    addEventListener('scroll', onScroll, { passive: true });
    bands.forEach(b => { b.op = -1; b.k = -1; }); lastSJ = -1;
    unpinFinalStates();
    onScroll();
  }
  function disableScrub() {
    if (!scrubOn) return; scrubOn = false;
    removeEventListener('scroll', onScroll);
    if (rafId !== null) { cancelAnimationFrame(rafId); rafId = null; }
  }
  const MQLS = GATES.map(q => matchMedia(q));
  function applyHeroMode() { if (MQLS.some(m => m.matches)) disableScrub(); else enableScrub(); }
  MQLS.forEach(m => m.addEventListener('change', applyHeroMode));

  /* ---------- the sand line ---------- */
  const sand = $('#sandpath');
  let sandLen = 0, sandST = null;
  function sizeSand() {   // the line ends where it pools: the hourglass in the hold section
    const svg = $('.sand'), sec = $('#hold') || $('#cta') || $('#audit'), main = $('#main');
    if (!svg || !sec) return;
    const heroH = hero ? hero.offsetHeight : ($('.ops') ? $('.ops').offsetHeight : 0), end = sec.getBoundingClientRect().top - main.getBoundingClientRect().top + 90;
    svg.style.top = heroH + 'px';
    svg.style.height = Math.max(0, end - heroH) + 'px';
  }
  function armSand() {
    if (!sand || !hasGsap || rmq.matches) return;
    sizeSand();
    sandLen = sand.getTotalLength();
    sand.style.strokeDasharray = sandLen; sand.style.strokeDashoffset = sandLen;
    sandST = gsap.to(sand, { strokeDashoffset: 0, ease: 'none', scrollTrigger: { trigger: '.sand', start: 'top 80%', end: 'bottom 90%', scrub: 1.2 } });
  }
  armSand();
  addEventListener('resize', () => { sizeSand(); if (hasGsap) ScrollTrigger.refresh(); }, { passive: true });

  /* ---------- reveals + stagger retirement ---------- */
  const io = new IntersectionObserver(es => es.forEach(e => {
    if (!e.isIntersecting) return;
    e.target.classList.add('in'); io.unobserve(e.target);
    setTimeout(() => e.target.classList.add('settled'), 1400);
  }), { rootMargin: '0px 0px -12% 0px' });
  $$('.reveal').forEach(el => io.observe(el));

  /* ---------- counters ---------- */
  const nums = $$('.num');
  function runCounter(el) {
    const to = Number(el.dataset.to), pre = el.dataset.prefix || '', suf = el.dataset.suffix || '';
    const fmt = v => pre + (to >= 1000 ? Math.round(v).toLocaleString('en-US') : Math.round(v)) + suf;
    if (rmq.matches) { el.textContent = fmt(to); el.classList.add('done'); return; }
    const t0 = performance.now(), dur = 900; let last = '';
    const step = now => {
      const t = clamp((now - t0) / dur, 0, 1), e = 1 - Math.pow(2, -10 * t);
      const s = fmt(to * e); if (s !== last) { last = s; el.textContent = s; }
      if (t < 1) requestAnimationFrame(step); else { el.textContent = fmt(to); el.classList.add('done'); }
    };
    requestAnimationFrame(step);
  }
  const cio = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { runCounter(e.target); cio.unobserve(e.target); } }), { threshold: 0.6 });
  nums.forEach(n => cio.observe(n));

  /* ---------- pointer tilt on pillars (fine pointer only) ---------- */
  if (!coarse.matches && !rmq.matches) $$('[data-tilt]').forEach(card => {
    const img = $('img', card);
    card.addEventListener('pointermove', e => {
      const r = card.getBoundingClientRect(); const x = (e.clientX - r.left) / r.width - 0.5, y = (e.clientY - r.top) / r.height - 0.5;
      img.style.transform = `scale(1.06) translate3d(${x * -8}px,${y * -8}px,0)`;
    });
    card.addEventListener('pointerleave', () => { img.style.transform = ''; });
  });

  /* ---------- the interactive moment: turn the hourglass ---------- */
  const hold = $('#hold'), hgbtn = $('#hgbtn'), hglabel = $('.hg-label');
  if (hgbtn) {
  let hp = 0, holding = false, hRaf = null, hLast = 0, holdDone = false;
  function setP(v) { hp = clamp(v, 0, 1); hgbtn.style.setProperty('--p', hp.toFixed(3)); }
  function holdTick(now) {
    const dt = Math.min(60, now - (hLast || now)); hLast = now;
    if (holding) setP(hp + dt / 1600); else setP(hp - dt / 900);
    if (hp >= 1 && !holdDone) { holdDone = true; hold.classList.add('done'); hgbtn.classList.add('done'); hglabel.textContent = 'Done'; hgbtn.setAttribute('aria-pressed', 'true'); }
    if ((holding && hp < 1) || (!holding && hp > 0 && !holdDone)) hRaf = requestAnimationFrame(holdTick); else { hRaf = null; hLast = 0; }
  }
  function startHold(e) { if (holdDone) return; e.preventDefault(); holding = true; hglabel.textContent = 'Keep holding'; if (hRaf === null) hRaf = requestAnimationFrame(holdTick); }
  function endHold() { if (!holding) return; holding = false; if (!holdDone) hglabel.textContent = 'Hold'; if (hRaf === null) hRaf = requestAnimationFrame(holdTick); }
  hgbtn.addEventListener('pointerdown', startHold);
  ['pointerup', 'pointercancel', 'pointerleave'].forEach(ev => hgbtn.addEventListener(ev, endHold));
  hgbtn.addEventListener('keydown', e => { if (e.key === ' ' || e.key === 'Enter') startHold(e); });
  hgbtn.addEventListener('keyup', e => { if (e.key === ' ' || e.key === 'Enter') endHold(); });
  if (rmq.matches) { holdDone = true; hold.classList.add('done'); setP(1); }
  }

  /* ---------- reduced motion, both directions ---------- */
  function pinToFinalStates() {
    stopLenis();
    if (sandST) { sandST.scrollTrigger.kill(); sandST.kill(); sandST = null; sand.style.strokeDashoffset = 0; }
    $$('.reveal').forEach(el => el.classList.add('in', 'settled'));
    nums.forEach(n => { if (!n.classList.contains('done')) runCounter(n); });
    if (hgbtn) { hold.classList.add('done'); hgbtn.classList.add('done'); hgbtn.style.setProperty('--p', '1'); }
  }
  function unpinFinalStates() {
    if (rmq.matches) return;
    startLenis();
    if (!sandST) armSand();
  }
  rmq.addEventListener('change', e => { if (e.matches) pinToFinalStates(); else applyHeroMode(); });
  if (rmq.matches) pinToFinalStates();

  applyHeroMode();   // last: every drive above is declared by now

  /* ---------- pause everything on hidden tabs ---------- */
  document.addEventListener('visibilitychange', () => document.body.classList.toggle('paused', document.hidden));
})();
