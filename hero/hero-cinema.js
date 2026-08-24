/* ---------------------------------------------------------------------------
 * hero-cinema.js — the scroll-driven cinematic hero.
 *
 * Repo-owned, copied into site/ by deploy.sh:apply_hero() and injected into
 * index.html. NEVER edit the copy in site/ — it is wiped on every deploy.
 *
 * Companions: hero/hero-cinema.html (markup + copy), hero/hero-cinema.css.
 *
 * WHAT IT DOES
 *   The homepage opens on a pinned stage. Scroll progress through that stage
 *   (0 to 1) builds one of George's own automation graphs on a canvas: nodes
 *   land, edges draw themselves, payloads start running the graph, and it
 *   settles into a pipeline that keeps humming while the calls to action
 *   arrive. Three text bands ride the same progress, each with its own
 *   entrance, each fully reversible on scroll up.
 *
 * WHY A CANVAS AND NOT A VIDEO
 *   The skill this hero is built to normally scrubs a generated clip. The clip
 *   the site shipped is stock footage: cold blue against a warm dark page, a
 *   loop with no journey, and words burned into the frame that fight every
 *   caption. Drawing the graph instead costs nothing per visit, is exactly the
 *   subject's own world, and stays on palette in both themes. Said out loud as
 *   the deviation it is.
 *
 * HOW IT SURVIVES A RE-EXPORT
 *   Same contract as hero-motion.js: the design-tool export has no ids and no
 *   classes and re-renders its own subtree, so the mount point is found by
 *   structure (the hero backdrop's 46px grid, which only the home view ships)
 *   and re-checked on mutation. Every section degrades to a no-op on its own.
 *
 * SECTIONS
 *   1. Environment            gates, colours, page background
 *   2. Mount                  finding the export hero, moving the block in
 *   3. Copy                   language detection, i18n, the seeded text split
 *   4. Bands                  band maths, the delta-gated writes
 *   5. Canvas                 the automation graph
 *   6. Drive                  the rAF loop that rests, scroll, gates, boot
 * ------------------------------------------------------------------------- */
(function () {
  'use strict';

  /* ==== 1. Environment =================================================== */

  /* The five static-hero gates. These strings are duplicated character for
   * character in hero-cinema.css. If one side changes and the other does not,
   * one side loads what the other hides. */
  var GATES = [
    '(max-width: 720px)',
    '(orientation: portrait) and (max-width: 1024px)',
    '(orientation: portrait) and (pointer: coarse)',
    '(orientation: landscape) and (pointer: coarse) and (max-height: 560px)',
    '(prefers-reduced-motion: reduce)'
  ];
  var MQLS = GATES.map(function (q) { return window.matchMedia(q); });
  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  var state = {
    section: null,
    stage: null,
    canvas: null,
    ctx: null,
    lane: null,
    bands: [],
    cta: null,
    cue: null,
    mounted: false,
    scrubOn: false,
    lang: null,
    split: false,
    loadStart: 0,
    hidden: false,
    onScreen: true,
    w: 0,
    h: 0,
    dpr: 1
  };

  var target = 0;   // 0..1 scroll progress, written by the scroll handler
  var shown = 0;    // what is actually displayed; eased toward target
  var rafId = null;
  var lastTick = 0;

  var colors = { ink: '#f5f2ec', body: '#a8a29a', accent: '#ff8300', line: '#2a2724', ground: '#141413' };

  /* The export's theme colours live on its own root div, and which element that
   * is depends on the export: some builds wrap it in <x-dc>, this one nests it
   * under #dc-root > .sc-host. Walking up from our own section to the nearest
   * ancestor that actually paints a background finds it in either shape, and
   * keeps the veil in step with the light/dark switch. */
  function themeGround() {
    var el = state.section && state.section.parentElement;
    while (el && el !== document.documentElement) {
      var bg = getComputedStyle(el).backgroundColor;
      if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') return bg;
      el = el.parentElement;
    }
    return '';
  }

  function readColors() {
    var probe = state.section || document.body;
    var cs = getComputedStyle(probe);
    function pick(name, fallback) {
      var v = cs.getPropertyValue(name);
      return (v && v.trim()) || fallback;
    }
    colors.ink = pick('--ink', colors.ink);
    colors.body = pick('--body', colors.body);
    colors.accent = pick('--accent', colors.accent);
    colors.line = pick('--cardBorder', colors.line);

    var bg = themeGround();
    if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') {
      colors.ground = bg;
      var rgb = bg.match(/\d+(\.\d+)?/g);
      if (rgb && rgb.length >= 3) {
        var base = rgb[0] + ', ' + rgb[1] + ', ' + rgb[2];
        document.documentElement.style.setProperty('--gc-veil', 'rgba(' + base + ', 0.93)');
        document.documentElement.style.setProperty('--gc-veil-soft', 'rgba(' + base + ', 0.45)');
      }
    }
  }

  /* The theme switch animates the export root's background over 300ms, so the
   * value readable on the frame the mutation lands is still the OLD theme's.
   * Read now for the common case, and once more after the transition has
   * finished for the theme case. One pending timer, never a queue. */
  var colorTimer = null;
  function refreshColors() {
    readColors();
    if (colorTimer) clearTimeout(colorTimer);
    colorTimer = setTimeout(function () {
      colorTimer = null;
      readColors();
      if (staticMode()) drawGraph(1, 0); else nudge();
    }, 450);
  }

  /* ==== 2. Mount ========================================================= */

  /* The export ships the hero backdrop as an inline-styled div carrying the
   * 46px grid, and only on the home view. Its parent is the hero wrapper, which
   * is where the cinema goes in front of. */
  function findExportHero() {
    var all = document.querySelectorAll('div[style*="46px 46px"]');
    for (var i = 0; i < all.length; i++) {
      var p = all[i].parentElement;
      if (p && p.parentElement) return p;
    }
    return null;
  }

  /* support.js compiles <x-dc>'s markup into a template ONCE and then renders
   * instances of it. Anything of ours sitting inside that subtree when the
   * compile happens becomes part of the template, and every later render stamps
   * out another copy — which is exactly how the hero ended up on the page
   * twice. Two guards, and they have to hold together:
   *   1. Never mount before the export has rendered. A rendered node carries
   *      data-dc-tpl, so that attribute is the proof the compile is behind us.
   *      After it, a re-render deletes our node instead of cloning it, and the
   *      mutation pass simply puts it back.
   *   2. Never trust that to be enough. If a copy ever appears anyway, drop
   *      every [data-ga-cinema] that is not the one this layer owns. */
  function dedupe() {
    var all = document.querySelectorAll('[data-ga-cinema]');
    for (var i = 0; i < all.length; i++) {
      if (all[i] !== state.section && all[i].parentElement) {
        all[i].parentElement.removeChild(all[i]);
      }
    }
  }

  function mount() {
    var section = state.section;
    if (!section) return;
    dedupe();
    var hero = findExportHero();
    if (hero && !hero.hasAttribute('data-dc-tpl')) return; // export not rendered yet
    if (!hero) {
      // Not the home view (or the export changed shape): stand down quietly.
      if (state.mounted) { section.style.display = 'none'; state.mounted = false; }
      return;
    }
    if (section.style.display === 'none') section.style.display = '';
    if (section.nextElementSibling !== hero || section.parentElement !== hero.parentElement) {
      hero.parentElement.insertBefore(section, hero);
      state.mounted = true;
      resize();
    }

    // Band 1 hosts the page's single <h1>. hero-motion.js also places that
    // block, and yields once it sits inside the cinema (see its placeLede).
    var lede = document.querySelector('[data-ga-lede]');
    var slot = section.querySelector('.gc__band--lede');
    if (lede && slot && lede.parentElement !== slot) {
      slot.appendChild(lede);
      lede.classList.add('ga-lede--in');
      state.split = false; // the moved title still needs its character split
    }
  }

  /* ==== 3. Copy ========================================================== */

  /* Same detection hero-motion.js uses: the export holds no language flag on
   * the DOM, but GA_SERVICES lists the testimonial headings per language and
   * exactly one of them is on the page. */
  function activeLang() {
    var svc = window.GA_SERVICES;
    var map = svc && svc.testimonials && svc.testimonials.titles;
    if (!map) return 'en';
    var body = document.body.textContent || '';
    for (var lang in map) {
      if (lang !== 'en' && map[lang] && body.indexOf(map[lang]) !== -1) return lang;
    }
    return 'en';
  }

  var copyBase = null;

  function translate() {
    var section = state.section;
    if (!section) return false;
    var raw = section.getAttribute('data-i18n');
    var nodes = section.querySelectorAll('[data-key]');
    if (!raw || !nodes.length) return false;
    if (!copyBase) {
      copyBase = {};
      for (var i = 0; i < nodes.length; i++) {
        copyBase[nodes[i].getAttribute('data-key')] = nodes[i].textContent;
      }
    }
    var all;
    try { all = JSON.parse(raw); } catch (e) { return false; }
    var lang = activeLang();
    if (lang === state.lang) return false;
    state.lang = lang;
    var copy = all[lang] || copyBase;
    for (var n = 0; n < nodes.length; n++) {
      var key = nodes[n].getAttribute('data-key');
      var text = copy[key] || copyBase[key];
      if (text != null) nodes[n].textContent = text;
    }
    section.dir = lang === 'ar' ? 'rtl' : 'ltr';
    return true; // the text changed, so the split has to be rebuilt
  }

  /* Seeded, so the "random" offsets are identical on every load. */
  function rng(seed) {
    var s = seed >>> 0;
    return function () {
      s = (s * 1664525 + 1013904223) >>> 0;
      return s / 4294967296;
    };
  }

  /* Split into word and character spans. A visually hidden copy carries the
   * full sentence for screen readers; the animated copy is aria-hidden, so no
   * assistive technology ever reads a headline one letter at a time. */
  function splitTitle(el, entrance, spread) {
    /* Once split, textContent reads the screen-reader copy AND the visual copy
     * back to back, so the cached original is the only safe source. When the
     * element is NOT split (first pass, or the language switch just rewrote its
     * innerHTML) the live text is the truth and the cache is stale. */
    var text = el.querySelector('.gc-sr')
      ? (el.getAttribute('data-gc-text') || '')
      : el.textContent;
    if (!text) return;
    el.setAttribute('data-gc-text', text);
    var words = text.split(/(\s+)/).filter(function (w) { return w.length; });
    var rand = rng(text.length * 2654435761);

    var total = 0;
    words.forEach(function (w) { if (!/^\s+$/.test(w)) total += w.length; });

    var sr = document.createElement('span');
    sr.className = 'gc-sr';
    sr.textContent = text;
    sr.style.cssText = 'position:absolute;width:1px;height:1px;overflow:hidden;' +
      'clip:rect(0 0 0 0);clip-path:inset(50%);white-space:nowrap';

    var vis = document.createElement('span');
    vis.setAttribute('aria-hidden', 'true');

    var wordIdx = 0;
    var realWords = words.filter(function (w) { return !/^\s+$/.test(w); }).length;
    var charIdx = 0;

    words.forEach(function (word) {
      var ws = document.createElement('span');
      ws.className = 'w';
      if (/^\s+$/.test(word)) {
        ws.textContent = word;
        vis.appendChild(ws);
        return;
      }
      if (entrance === 'punch') {
        ws.style.setProperty('--th', (wordIdx / Math.max(1, realWords) * 0.45).toFixed(3));
        if (/[.!?]$/.test(word)) ws.classList.add('em');
      } else if (entrance === 'rise') {
        ws.style.setProperty('--th', (wordIdx / Math.max(1, realWords) * 0.5).toFixed(3));
      }
      for (var c = 0; c < word.length; c++) {
        var cs = document.createElement('span');
        cs.className = 'c';
        cs.textContent = word[c];
        if (entrance === 'grid') {
          // Reading-order stagger, characters sliding in from the start edge.
          cs.style.setProperty('--th', (charIdx / Math.max(1, total) * spread + rand() * 0.06).toFixed(3));
          cs.style.setProperty('--jx', (-14 - rand() * 20).toFixed(1) + 'px');
        }
        ws.appendChild(cs);
        charIdx++;
      }
      vis.appendChild(ws);
      wordIdx++;
    });

    el.textContent = '';
    el.appendChild(sr);
    el.appendChild(vis);
  }

  /* hero-motion.js rewrites the <h1> block's innerHTML on a language switch,
   * which silently throws the character spans away. Cheaper to notice than to
   * coordinate: if a title has lost its spans, the split is rebuilt. */
  function needsSplit() {
    if (!state.split || !state.section) return true;
    var titles = state.section.querySelectorAll('[data-split], .ga-lede__title');
    for (var i = 0; i < titles.length; i++) {
      if (!titles[i].querySelector('.c')) return true;
    }
    return false;
  }

  function splitAll() {
    if (!state.section) return;
    state.bands.forEach(function (b) {
      var entrance = b.el.getAttribute('data-entrance') || 'rise';
      var spread = parseFloat(b.el.getAttribute('data-spread')) || 0.55;
      var titles = b.el.querySelectorAll('[data-split], .ga-lede__title');
      for (var i = 0; i < titles.length; i++) {
        splitTitle(titles[i], entrance, spread);
      }
    });
    state.split = true;
  }

  /* ==== 4. Bands ========================================================= */

  var smoothstep = function (p, e0, e1) {
    var t = Math.min(1, Math.max(0, (p - e0) / (e1 - e0)));
    return t * t * (3 - 2 * t);
  };
  var clamp = function (v, lo, hi) { return Math.min(hi, Math.max(lo, v)); };

  function collectBands() {
    var els = state.section.querySelectorAll('.gc__band');
    state.bands = [];
    for (var i = 0; i < els.length; i++) {
      var raw = (els[i].getAttribute('data-band') || '0,1').split(',');
      var a = parseFloat(raw[0]);
      var b = parseFloat(raw[1]);
      state.bands.push({
        el: els[i],
        a: a,
        b: b,
        first: i === 0,
        last: i === els.length - 1,
        ramp: parseFloat(els[i].getAttribute('data-ramp')) || Math.min(0.025, (b - a) * 0.35),
        op: -1,
        k: -1,
        vis: null
      });
    }
  }

  /* Everything here is delta-gated: per-frame DOM writes are the other half of
   * choppy, so a converged band costs nothing. */
  function updateBands(p, loadK) {
    for (var i = 0; i < state.bands.length; i++) {
      var band = state.bands[i];
      var f = Math.min(0.02, (band.b - band.a) / 3);
      var inRamp = band.first ? 1 : smoothstep(p, band.a, band.a + f);
      var outRamp = band.last ? 1 : (1 - smoothstep(p, band.b - f, band.b));
      var op = inRamp * outRamp;
      var k = clamp((p - band.a) / band.ramp, 0, 1);
      if (band.first) k = Math.max(k, loadK); // the one-time opening assembly

      if (Math.abs(op - band.op) > 0.008) {
        band.op = op;
        band.el.style.opacity = op.toFixed(3);
      }
      if (Math.abs(k - band.k) > 0.008) {
        band.k = k;
        band.el.style.setProperty('--k', k.toFixed(3));
      }
      var vis = op > 0.55;
      if (vis !== band.vis) {
        band.vis = vis;
        band.el.classList.toggle('gc__band--visible', vis);
      }
    }

    var kb = clamp((p - 0.78) * 5, 0, 1);
    if (Math.abs(kb - (state.cta._kb == null ? -1 : state.cta._kb)) > 0.008) {
      state.cta._kb = kb;
      state.cta.style.setProperty('--kb', kb.toFixed(3));
      var live = kb > 0.5 ? '1' : '0';
      if (state.cta.getAttribute('data-live') !== live) state.cta.setAttribute('data-live', live);
    }

    if (state.cue) {
      var cue = 1 - smoothstep(p, 0.02, 0.12);
      if (Math.abs(cue - (state.cue._v == null ? -1 : state.cue._v)) > 0.01) {
        state.cue._v = cue;
        state.cue.style.setProperty('--cue', cue.toFixed(3));
      }
    }
  }

  /* Pin every scroll-driven element to its finished state. Used by the static
   * hero and by a live flip into reduced motion. */
  function pinFinalStates() {
    state.bands.forEach(function (band) {
      band.op = -1; band.k = -1; band.vis = null;
      band.el.style.opacity = band.first ? '1' : '0';
      band.el.style.setProperty('--k', '1');
      band.el.classList.toggle('gc__band--visible', !!band.first);
    });
    if (state.cta) {
      state.cta._kb = -1;
      state.cta.style.setProperty('--kb', '1');
      state.cta.setAttribute('data-live', '1');
    }
    drawGraph(1, 0);
  }

  /* ==== 5. Canvas: the automation graph ================================== */

  /* Normalised layout, mapped into the graph box at paint time. Left to right:
   * what starts the work, what decides, what it delivers — the same funnel the
   * three text bands describe. It is drawn as a HUD (rings, a reticle, live
   * readouts) rather than as node cards, but the topology underneath is a real
   * workflow: three triggers, two routers, one core, four deliveries. */
  var TAU = Math.PI * 2;

  var NODES = [
    /* z is depth: 1 is the near plane, smaller sits further back and paints
     * smaller and dimmer. It is what stops the graph reading as a flat diagram.
     * The left of the field is deliberately the far plane, because that is the
     * half the text lane sits over.
     *
     * tel is an optional readout. Digits and ASCII only, on purpose: the rest
     * of the hero ships in five languages, and a HUD that spelled out words
     * would drag the canvas into that translation surface for no gain. */
    { x: 0.42, y: 0.18, t: 0.02, z: 0.52, kind: 'in',   tel: { k: 'REQ', b: 128, a: 46, u: '' } },
    { x: 0.44, y: 0.60, t: 0.06, z: 0.60, kind: 'in' },
    { x: 0.50, y: 0.88, t: 0.12, z: 0.48, kind: 'in' },
    { x: 0.72, y: 0.50, t: 0.16, z: 1,    kind: 'core', tel: { k: 'SYS', b: 96,  a: 3,  u: '%' } },
    { x: 0.60, y: 0.30, t: 0.22, z: 0.72, kind: 'hub' },
    { x: 0.62, y: 0.74, t: 0.26, z: 0.74, kind: 'hub',  tel: { k: 'LAT', b: 38,  a: 11, u: 'ms' } },
    { x: 0.87, y: 0.20, t: 0.34, z: 0.90, kind: 'out' },
    { x: 0.89, y: 0.76, t: 0.40, z: 0.88, kind: 'out',  tel: { k: 'Q',   b: 3,   a: 2,  u: '' } },
    { x: 0.96, y: 0.46, t: 0.48, z: 0.70, kind: 'out' },
    { x: 0.97, y: 0.12, t: 0.56, z: 0.58, kind: 'out' }
  ];
  var EDGES = [
    { a: 0, b: 4, t: 0.10 },
    { a: 1, b: 5, t: 0.14 },
    { a: 2, b: 5, t: 0.20 },
    { a: 4, b: 3, t: 0.24 },
    { a: 5, b: 3, t: 0.28 },
    { a: 3, b: 6, t: 0.34 },
    { a: 3, b: 7, t: 0.40 },
    { a: 6, b: 8, t: 0.46 },
    { a: 7, b: 8, t: 0.50 },
    { a: 6, b: 9, t: 0.56 }
  ];

  /* The reticle's settle. drawGraph is otherwise stateless per frame, but a
   * bracket that teleports between nodes reads as a redraw rather than as an
   * instrument tracking something, so its position is carried across frames and
   * eased. Snapped, not eased, when motion is off. */
  var hud = { rx: 0, ry: 0, rr: 0, live: false };

  /* Full bleed. The references the brief pointed at (both AiO sites) put one
   * big visual across the whole frame and lay the type over it, so the graph
   * takes the whole stage instead of sitting in a panel on the right. The text
   * stays legible because the veil in hero-cinema.css darkens the left of the
   * frame, and because the field's near plane is composed on the right. */
  function graphBox() {
    var padX = Math.min(80, state.w * 0.06);
    var padY = Math.min(90, state.h * 0.12);
    return { x: padX, y: padY, w: state.w - padX * 2, h: state.h - padY * 2 };
  }

  function nodePos(n, box) {
    return { x: box.x + n.x * box.w, y: box.y + n.y * box.h };
  }

  /* The core is the near plane and the thing everything routes through, so it
   * gets its own size class rather than sitting at the top of the depth ramp. */
  function nodeRadius(n, unit) {
    return n.kind === 'core' ? unit * 0.92 : unit * (0.30 + 0.40 * n.z);
  }

  /* A point on the edge's curve. The control points are horizontal, which is
   * what gives the graph the flat S-curve a workflow canvas actually draws. */
  function edgePoint(p0, p1, t) {
    var dx = (p1.x - p0.x) * 0.5;
    var c0 = { x: p0.x + dx, y: p0.y };
    var c1 = { x: p1.x - dx, y: p1.y };
    var u = 1 - t;
    return {
      x: u * u * u * p0.x + 3 * u * u * t * c0.x + 3 * u * t * t * c1.x + t * t * t * p1.x,
      y: u * u * u * p0.y + 3 * u * u * t * c0.y + 3 * u * t * t * c1.y + t * t * t * p1.y
    };
  }

  /* ---- HUD primitives ---------------------------------------------------
   * All four batch their geometry into a single path where they can: the field
   * paints ten nodes a frame and a stroke per tick mark would be ~500 calls. */

  function tickRing(ctx, cx, cy, r0, r1, count, rot) {
    for (var i = 0; i < count; i++) {
      var a = rot + (i / count) * TAU;
      var ca = Math.cos(a), sa = Math.sin(a);
      ctx.moveTo(cx + ca * r0, cy + sa * r0);
      ctx.lineTo(cx + ca * r1, cy + sa * r1);
    }
  }

  function gappedRing(ctx, cx, cy, r, segs, gap, rot) {
    var span = TAU / segs;
    for (var i = 0; i < segs; i++) {
      var a0 = rot + i * span;
      ctx.moveTo(cx + Math.cos(a0) * r, cy + Math.sin(a0) * r);
      ctx.arc(cx, cy, r, a0, a0 + span - gap);
    }
  }

  /* Corner brackets rather than a box: a closed rectangle around a node reads
   * as a selection in a design tool, the open corners read as an instrument. */
  function reticle(ctx, cx, cy, r, arm) {
    var sx, sy, i;
    for (i = 0; i < 4; i++) {
      sx = (i === 0 || i === 2) ? -1 : 1;
      sy = i < 2 ? -1 : 1;
      ctx.moveTo(cx + sx * r - sx * arm, cy + sy * r);
      ctx.lineTo(cx + sx * r, cy + sy * r);
      ctx.lineTo(cx + sx * r, cy + sy * r - sy * arm);
    }
  }

  /* Deterministic, never Math.random(): a readout reseeded every frame jitters
   * into noise, and the same scroll position has to paint the same frame twice
   * for the static and reduced-motion passes to agree with the live one. */
  function telemetry(tel, time) {
    var v = tel.b + tel.a * Math.sin(time * 0.00042 + tel.b);
    return tel.k + ' ' + (tel.b < 10 ? Math.max(0, Math.round(v)) : Math.round(v)) + tel.u;
  }

  function drawGraph(p, time) {
    var ctx = state.ctx;
    if (!ctx || !state.w || !state.h) return;
    ctx.clearRect(0, 0, state.w, state.h);

    var box = graphBox();
    var unit = Math.max(14, Math.min(box.w, box.h) * 0.11);
    /* One gate for every autonomous motion in the field. Scroll-driven motion
     * is left alone — the sweep and the assembly answer the user's own scroll,
     * which is not what the preference is about. */
    var t = reduceMotion.matches ? 0 : time;
    var i, n, k, pos, r, depth;

    // The environment: one soft glow in the graph's own colour, so the stage
    // reads as a place rather than a flat panel.
    var glow = ctx.createRadialGradient(
      box.x + box.w * 0.72, box.y + box.h * 0.5, 0,
      box.x + box.w * 0.72, box.y + box.h * 0.5, Math.max(box.w, box.h) * 0.75
    );
    glow.addColorStop(0, colors.accent);
    glow.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.save();
    ctx.globalAlpha = 0.09 + 0.07 * smoothstep(p, 0.3, 1);
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, state.w, state.h);
    ctx.restore();

    /* The blueprint. Every edge and every node painted at a whisper first, so
     * the frame is composed from the very first paint and the scroll reads as
     * the pipeline LIGHTING UP rather than as an empty canvas slowly filling.
     * It also keeps the right of the frame occupied at progress zero, where the
     * live build has not reached yet. */
    ctx.save();
    ctx.globalAlpha = 0.055;
    ctx.strokeStyle = colors.ink;
    ctx.lineWidth = 1;
    ctx.beginPath();
    for (var ge = 0; ge < EDGES.length; ge++) {
      var gp0 = nodePos(NODES[EDGES[ge].a], box);
      var gp1 = nodePos(NODES[EDGES[ge].b], box);
      for (var gs = 0; gs <= 24; gs++) {
        var gpt = edgePoint(gp0, gp1, gs / 24);
        if (gs === 0) ctx.moveTo(gpt.x, gpt.y); else ctx.lineTo(gpt.x, gpt.y);
      }
    }
    for (var gn = 0; gn < NODES.length; gn++) {
      var gpos = nodePos(NODES[gn], box);
      var gr = nodeRadius(NODES[gn], unit);
      ctx.moveTo(gpos.x + gr, gpos.y);
      ctx.arc(gpos.x, gpos.y, gr, 0, TAU);
    }
    ctx.stroke();
    ctx.restore();

    // Edges, drawn as a reveal from source to target. Two traces, not one: a
    // solid line plus a dimmer copy a couple of pixels below it. The doubling
    // is the whole difference between "a diagram" and "an instrument".
    for (var e = 0; e < EDGES.length; e++) {
      var edge = EDGES[e];
      var g = clamp((p - edge.t) / 0.12, 0, 1);
      if (g <= 0) continue;
      var p0 = nodePos(NODES[edge.a], box);
      var p1 = nodePos(NODES[edge.b], box);
      depth = (NODES[edge.a].z + NODES[edge.b].z) / 2;
      var steps = 26;
      var lit = Math.floor(steps * g);

      ctx.save();
      /* --cardBorder is nearly the canvas itself, so an edge drawn in it
       * disappears. The ink at low alpha, scaled by depth, is what actually
       * reads as wiring on both themes. */
      ctx.strokeStyle = colors.ink;
      ctx.lineWidth = depth > 0.85 ? 1.25 : 1;
      var off, pass, pt, s;
      for (pass = 0; pass < 2; pass++) {
        off = pass === 0 ? 0 : 2 * depth;
        ctx.globalAlpha = (pass === 0 ? 0.10 + 0.26 * depth : 0.05 + 0.10 * depth);
        ctx.beginPath();
        for (s = 0; s <= lit; s++) {
          pt = edgePoint(p0, p1, s / steps);
          if (s === 0) ctx.moveTo(pt.x, pt.y + off); else ctx.lineTo(pt.x, pt.y + off);
        }
        ctx.stroke();
      }
      ctx.restore();

      // Payloads. They start once the graph is wired and keep running after it
      // settles: the pipeline is supposed to still be working when you stop
      // scrolling. This is the hero's one living element.
      var flow = smoothstep(p, 0.55, 0.8);
      if (flow > 0 && g >= 1 && t) {
        var phase = ((t * 0.00016) + e * 0.37) % 1;
        // Head plus a short trail, so a payload has a direction of travel.
        for (var tr = 0; tr < 3; tr++) {
          var tp = phase - tr * 0.035;
          if (tp < 0) continue;
          var dot = edgePoint(p0, p1, tp);
          ctx.save();
          ctx.globalAlpha = flow * depth * (0.35 + 0.65 * Math.sin(Math.PI * tp)) * (1 - tr * 0.32);
          ctx.fillStyle = colors.accent;
          ctx.beginPath();
          ctx.arc(dot.x, dot.y, unit * 0.075 * (0.6 + 0.4 * depth) * (1 - tr * 0.22), 0, TAU);
          ctx.fill();
          ctx.restore();
        }
      }
    }

    /* The sweep. One scanline per band, so it fires exactly at the three
     * moments the copy changes underneath it and never on its own schedule.
     * It has to stay a LINE: widened into a band it stops reading as a pass
     * over the field and starts reading as a flat panel sitting on top of it,
     * which is exactly what the first cut of this did. Hence the narrow trail,
     * and the fade that spends the sweep well before the far edge. */
    var sPhase = (p * 3) % 1;
    var sweepAt = box.x + box.w * sPhase;
    var sweepFade = smoothstep(p, 0.04, 0.18) * (1 - smoothstep(sPhase, 0.15, 0.75));
    if (sweepFade > 0.01) {
      var trail = unit * 0.9;
      var sg = ctx.createLinearGradient(sweepAt - trail, 0, sweepAt, 0);
      sg.addColorStop(0, 'rgba(0,0,0,0)');
      sg.addColorStop(1, colors.accent);
      ctx.save();
      ctx.globalAlpha = 0.10 * sweepFade;
      ctx.fillStyle = sg;
      ctx.fillRect(sweepAt - trail, box.y, trail, box.h);
      ctx.globalAlpha = 0.28 * sweepFade;
      ctx.fillStyle = colors.accent;
      ctx.fillRect(sweepAt, box.y, 1, box.h);
      ctx.restore();
    }

    // Nodes, and the reticle's target picked out along the way.
    var bestBusy = 0, bestNode = null;
    for (i = 0; i < NODES.length; i++) {
      n = NODES[i];
      k = clamp((p - n.t) / 0.10, 0, 1);
      if (k <= 0) continue;
      pos = nodePos(n, box);
      r = nodeRadius(n, unit) * (0.82 + 0.18 * k);
      depth = n.z;
      var core = n.kind === 'core';
      var dir = n.kind === 'out' ? -1 : 1;

      /* The working ring: the node the graph is busy with right now. Narrow on
       * purpose — the accent is supposed to be rare, and a wider window lit two
       * nodes at once at the opening frame. */
      var busy = clamp(1 - Math.abs(p - (n.t + 0.08)) / 0.09, 0, 1);
      if (busy > bestBusy) { bestBusy = busy; bestNode = { x: pos.x, y: pos.y, r: r }; }

      ctx.save();
      ctx.globalAlpha = k;

      // Ring body.
      ctx.strokeStyle = busy > 0.05 ? colors.accent : colors.ink;
      ctx.lineWidth = core ? 1.5 : 1;
      ctx.globalAlpha = k * (core ? 0.55 : 0.18 + 0.34 * depth) * (1 + busy);
      ctx.beginPath();
      ctx.arc(pos.x, pos.y, r, 0, TAU);
      ctx.stroke();

      // Graduations. The core carries a full instrument ring; the satellites
      // get a dozen ticks, enough to read as calibrated without becoming lace.
      ctx.globalAlpha = k * (0.10 + 0.22 * depth) * (1 + busy * 0.8);
      ctx.lineWidth = 1;
      ctx.beginPath();
      tickRing(ctx, pos.x, pos.y, r * 1.10, r * (core ? 1.26 : 1.20),
               core ? 60 : 12, t * 0.00007 * dir + i);
      ctx.stroke();

      if (core) {
        // Counter-rotating gapped arcs, and a disc that breathes.
        ctx.globalAlpha = k * 0.42;
        ctx.strokeStyle = colors.accent;
        ctx.lineWidth = 1.5;
        ctx.beginPath();
        gappedRing(ctx, pos.x, pos.y, r * 0.72, 3, 0.7, -t * 0.00019);
        ctx.stroke();

        ctx.globalAlpha = k * 0.30;
        ctx.strokeStyle = colors.ink;
        ctx.lineWidth = 1;
        ctx.beginPath();
        gappedRing(ctx, pos.x, pos.y, r * 0.52, 5, 0.45, t * 0.00031);
        ctx.stroke();

        ctx.globalAlpha = k * (0.26 + 0.14 * Math.sin(t * 0.0011));
        ctx.fillStyle = colors.accent;
        ctx.beginPath();
        ctx.arc(pos.x, pos.y, r * 0.20, 0, TAU);
        ctx.fill();
      } else {
        // The mark inside: a dot for a trigger, a cross for a router, a pair of
        // lanes for a delivery. Different per kind so the field reads as a real
        // pipeline rather than a ring of identical instruments.
        ctx.globalAlpha = k * (0.25 + 0.5 * depth) * (1 + busy);
        ctx.fillStyle = busy > 0.05 ? colors.accent : colors.ink;
        if (n.kind === 'in') {
          ctx.beginPath();
          ctx.arc(pos.x, pos.y, r * 0.22, 0, TAU);
          ctx.fill();
        } else if (n.kind === 'hub') {
          ctx.fillRect(pos.x - r * 0.34, pos.y - r * 0.04, r * 0.68, r * 0.08);
          ctx.fillRect(pos.x - r * 0.04, pos.y - r * 0.34, r * 0.08, r * 0.68);
        } else {
          ctx.fillRect(pos.x - r * 0.34, pos.y - r * 0.18, r * 0.68, r * 0.075);
          ctx.fillRect(pos.x - r * 0.34, pos.y + r * 0.06, r * 0.48, r * 0.075);
        }
      }

      // Readout, hung under the ring once the field is past its opening build.
      if (n.tel) {
        var telFade = smoothstep(p, 0.22, 0.45) * k;
        if (telFade > 0) {
          ctx.globalAlpha = telFade * (0.22 + 0.26 * depth);
          ctx.fillStyle = colors.body;
          ctx.font = Math.max(9, Math.round(unit * 0.17)) + 'px "JetBrains Mono", ui-monospace, monospace';
          ctx.textAlign = 'center';
          ctx.textBaseline = 'top';
          ctx.fillText(telemetry(n.tel, t), pos.x, pos.y + r * 1.42);
        }
      }

      ctx.restore();
    }

    /* The reticle. One per field: an instrument tracks one thing at a time, and
     * two brackets on screen would just read as more decoration. */
    if (bestNode && bestBusy > 0.02) {
      var rr = bestNode.r * 1.5;
      if (!hud.live || !t) {
        hud.rx = bestNode.x; hud.ry = bestNode.y; hud.rr = rr; hud.live = true;
      } else {
        hud.rx += (bestNode.x - hud.rx) * 0.18;
        hud.ry += (bestNode.y - hud.ry) * 0.18;
        hud.rr += (rr - hud.rr) * 0.18;
      }
      ctx.save();
      ctx.globalAlpha = 0.30 + 0.45 * bestBusy;
      ctx.strokeStyle = colors.accent;
      ctx.lineWidth = 1.25;
      ctx.beginPath();
      reticle(ctx, hud.rx, hud.ry, hud.rr, hud.rr * 0.42);
      ctx.stroke();
      ctx.restore();
    } else {
      hud.live = false;
    }
  }

  function resize() {
    if (!state.canvas || !state.stage) return;
    var rect = state.stage.getBoundingClientRect();
    if (!rect.width || !rect.height) return;
    state.dpr = Math.min(2, window.devicePixelRatio || 1);
    state.w = rect.width;
    state.h = rect.height;
    state.canvas.width = Math.round(rect.width * state.dpr);
    state.canvas.height = Math.round(rect.height * state.dpr);
    state.ctx = state.canvas.getContext('2d');
    state.ctx.setTransform(state.dpr, 0, 0, state.dpr, 0, 0);
    if (staticMode()) drawGraph(1, 0); else drawGraph(shown, performance.now());
  }

  /* ==== 6. Drive ========================================================= */

  function staticMode() {
    return MQLS.some(function (m) { return m.matches; });
  }

  function heroProgress() {
    if (!state.section) return 0;
    var rect = state.section.getBoundingClientRect();
    var range = state.section.offsetHeight - window.innerHeight;
    if (range <= 0) return 0;
    return clamp(-rect.top / range, 0, 1);
  }

  function loadRamp(now) {
    if (!state.loadStart) return 0;
    var t = clamp((now - state.loadStart) / 900, 0, 1);
    return t * t * (3 - 2 * t);
  }

  function tick(now) {
    var dt = Math.min(100, now - (lastTick || now));
    lastTick = now;
    var k = 0.16;
    shown += (target - shown) * (1 - Math.pow(1 - k, dt / 16.667));
    var converged = Math.abs(target - shown) < 0.0005;
    if (converged) shown = target;

    var lk = loadRamp(now);
    updateBands(shown, lk);
    /* The graph gets the same opening courtesy the first text band does: it
     * assembles its first few nodes on load, so the hero never opens on an
     * empty right half waiting for a scroll that may not come. */
    drawGraph(Math.max(shown, lk * 0.30), now);

    // The loop keeps running only while there is something to move: the ease
    // has not converged, the opening assembly is still playing, or payloads are
    // in flight on a stage that is actually on screen and visible.
    var flowing = shown > 0.55 && !reduceMotion.matches;
    var alive = !converged || lk < 1 || flowing;
    if (alive && state.onScreen && !state.hidden && state.scrubOn) {
      rafId = requestAnimationFrame(tick);
    } else {
      rafId = null;
      lastTick = 0;
    }
  }

  function nudge() {
    if (rafId === null && state.scrubOn && state.onScreen && !state.hidden) {
      rafId = requestAnimationFrame(tick);
    }
  }

  function onScroll() {
    target = heroProgress();
    nudge();
  }

  function enableScrub() {
    if (state.scrubOn) return;
    state.scrubOn = true;
    state.loadStart = performance.now();
    state.bands.forEach(function (b) { b.op = -1; b.k = -1; b.vis = null; });
    if (state.cta) state.cta._kb = -1;
    window.addEventListener('scroll', onScroll, { passive: true });
    resize();
    onScroll();
  }

  function disableScrub() {
    if (!state.scrubOn) return;
    state.scrubOn = false;
    window.removeEventListener('scroll', onScroll);
    if (rafId !== null) { cancelAnimationFrame(rafId); rafId = null; }
    lastTick = 0;
  }

  function applyHeroMode() {
    if (!state.section) return;
    if (staticMode()) {
      disableScrub();
      pinFinalStates();
    } else {
      enableScrub();
    }
  }

  function observeStage() {
    if (!('IntersectionObserver' in window) || !state.stage) return;
    new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        state.onScreen = entry.isIntersecting;
        if (state.onScreen) nudge();
      });
    }, { rootMargin: '10% 0px' }).observe(state.stage);
  }

  /* The block is injected before </body> for crawlers; everything below moves
   * it into the page and wires it up. Any missing piece stands the layer down
   * rather than taking the page with it. */
  function boot() {
    var section = document.querySelector('[data-ga-cinema]');
    if (!section) return;
    state.section = section;
    state.stage = section.querySelector('.gc__stage');
    state.canvas = section.querySelector('.gc__canvas');
    state.lane = section.querySelector('.gc__lane');
    state.cta = section.querySelector('.gc__cta');
    state.cue = section.querySelector('.gc__cue');
    if (!state.stage || !state.canvas || !state.cta) return;

    document.documentElement.classList.add('gc-on');

    collectBands();
    readColors();
    mount();
    translate();
    if (needsSplit()) splitAll();
    observeStage();
    applyHeroMode();

    MQLS.forEach(function (m) { m.addEventListener('change', applyHeroMode); });

    window.addEventListener('resize', function () {
      readColors();
      resize();
      nudge();
    }, { passive: true });

    /* The theme switch is the one change the mutation pass keeps missing: the
     * export swaps the palette without touching a style attribute we can see on
     * the frame it happens, so the veil ends up painted for the outgoing theme.
     * The background-color transition ending IS the event, and it is rare
     * enough to listen for directly. */
    document.addEventListener('transitionend', function (e) {
      if (e.propertyName === 'background-color') refreshColors();
    }, true);

    document.addEventListener('visibilitychange', function () {
      state.hidden = document.hidden;
      if (!state.hidden) nudge();
    });

    /* The export re-renders its own subtree on every state change (language,
     * theme, route), which can move the cinema out of place, restore the <h1>
     * to the old hero, or repaint the theme underneath the canvas. One
     * coalesced pass handles all three. */
    var queued = false;
    new MutationObserver(function () {
      if (queued) return;
      queued = true;
      requestAnimationFrame(function () {
        queued = false;
        mount();
        refreshColors();
        translate();
        if (needsSplit()) splitAll();
        if (!state.scrubOn && staticMode()) pinFinalStates(); else nudge();
      });
      /* Attributes as well as children: the light/dark switch only rewrites the
       * export root's inline style, so a childList-only observer never hears
       * about it and the veil stays painted for the old theme. Every pass is
       * coalesced into one frame, so the extra traffic costs nothing. */
    }).observe(document.body, {
      childList: true,
      subtree: true,
      attributes: true,
      attributeFilter: ['style']
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
