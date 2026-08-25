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
  var idleId = null;
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
      /* will-change is scoped to bands that are actually on screen. A split
       * title is ~40 inline-block spans, so promoting all three bands for the
       * whole session pins compositor memory for two bands that are not
       * moving. The threshold is deliberately far below --visible's 0.55: the
       * layer has to exist before the assembly starts, not halfway through
       * it, or the promotion itself lands mid-animation. */
      var warm = op > 0.004;
      if (warm !== band.warm) {
        band.warm = warm;
        band.el.classList.toggle('gc__band--warm', warm);
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

  /* The field is a workflow canvas, drawn the way the real editor draws one:
   * a dot grid, node cards carrying a coloured icon tile, the node's name set
   * underneath it, solid connectors with an arrow at the midpoint for the main
   * path and dashed ones for the model / memory / tool ports that hang off an
   * agent, and a "+" stub where an output has not been wired yet.
   *
   * The names are product names — HTTP Request, AI Agent, Airtable — and those
   * stay in English in every locale the rest of the hero ships in, so putting
   * words on the canvas does not drag it into the translation surface.
   *
   * Two things survive from the instrument pass this replaced, because neither
   * fights the register: the payloads that travel the wires, and the reticle
   * that brackets whichever node the progress is working on. */
  var TAU = Math.PI * 2;

  /* The sanctioned secondary hues from DESIGN-claude.md. A real n8n canvas is
   * multicoloured and a monochrome one stops reading as one, but the palette is
   * the site's own — nothing invented, and the orange accent stays reserved for
   * the trigger and the agent, which are the two nodes the eye should land on. */
  var HUES = { teal: '#5db8a6', amber: '#e8a55a' };

  /* x/y are normalised into the graph box. t is when the node joins during the
   * build. z is depth: the left of the field is the far plane, because that is
   * the half the text lane sits over. */
  var NODES = [
    { x: 0.05, y: 0.16, t: 0.02, z: 0.66, kind: 'card', icon: 'bolt',  hue: 'accent',
      label: 'Webhook',      sub: 'form submitted' },
    { x: 0.05, y: 0.48, t: 0.08, z: 0.70, kind: 'card', icon: 'globe', hue: 'teal',
      label: 'HTTP Request', sub: 'GET:' },
    { x: 0.36, y: 0.30, t: 0.16, z: 1,    kind: 'wide', icon: 'spark', hue: 'accent',
      label: 'AI Agent',     sub: 'Tools Agent' },
    { x: 0.72, y: 0.16, t: 0.26, z: 0.9,  kind: 'card', icon: 'branch', hue: 'amber',
      label: 'If',           sub: '' },
    { x: 1.00, y: 0.14, t: 0.34, z: 0.86, kind: 'card', icon: 'mail',  hue: 'teal',
      label: 'Gmail',        sub: 'send:' },
    { x: 0.86, y: 0.50, t: 0.40, z: 0.84, kind: 'card', icon: 'table', hue: 'amber',
      label: 'Airtable',     sub: 'create: row' },
    /* The sub-nodes. In the editor these hang below an agent on dashed ports,
     * which is the shape that makes a canvas unmistakably n8n. */
    { x: 0.22, y: 0.68, t: 0.48, z: 0.7,  kind: 'sub', icon: 'spark', hue: 'ink',
      label: 'OpenAI Chat',  sub: 'Model' },
    { x: 0.42, y: 0.74, t: 0.52, z: 0.72, kind: 'sub', icon: 'db',    hue: 'ink',
      label: 'Postgres',     sub: 'Memory' },
    { x: 0.62, y: 0.68, t: 0.56, z: 0.7,  kind: 'sub', icon: 'code',  hue: 'ink',
      label: 'Vector Store', sub: 'Tool' }
  ];
  /* d marks a port connection: drawn dashed and without an arrow, the way the
   * editor distinguishes what an agent USES from what it PASSES ON. */
  var EDGES = [
    { a: 0, b: 2, t: 0.10 },
    { a: 1, b: 2, t: 0.14 },
    { a: 2, b: 3, t: 0.24 },
    { a: 3, b: 4, t: 0.32 },
    { a: 3, b: 5, t: 0.38 },
    { a: 6, b: 2, t: 0.46, d: 1 },
    { a: 7, b: 2, t: 0.50, d: 1 },
    { a: 8, b: 2, t: 0.54, d: 1 }
  ];

  /* The reticle's settle. drawGraph is otherwise stateless per frame, but a
   * bracket that teleports between nodes reads as a redraw rather than as
   * something tracking the run, so its position is carried across frames and
   * eased. Snapped, not eased, when motion is off. */
  var hud = { rx: 0, ry: 0, rw: 0, rh: 0, live: false };

  /* Set once per frame, read by nodePos. The narrow box a phone gives the
   * canvas cannot take the wide composition, so the field is re-spread rather
   * than merely scaled down — at 390px the desktop layout would pile the whole
   * flow into the right edge. */
  var compact = false;

  function graphBox() {
    var padX = Math.min(80, state.w * 0.06);
    var padY = Math.min(90, state.h * 0.12);
    return { x: padX, y: padY, w: state.w - padX * 2, h: state.h - padY * 2 };
  }

  /* Wide layout keeps the flow on the right, clear of the text lane. Compact
   * hands it the whole box. */
  function nodePos(n, box) {
    /* The wide layout starts at 0.44 rather than hard against the text lane:
     * the veil is near-opaque out to 30% and still heavy at 40%, and a card
     * with a name under it does not survive that the way a bare ring did — it
     * just looks like something failed to load. */
    var nx = compact ? 0.06 + n.x * 0.88 : 0.44 + n.x * 0.54;
    return { x: box.x + nx * box.w, y: box.y + n.y * box.h };
  }

  /* Small on purpose. A real canvas is dense — a dozen modest nodes, not four
   * billboards — and the first pass at this drew cards wide enough that the
   * names under them collided and the flow ran off the frame. */
  function cardSize(n, box) {
    var w = box.w * (compact ? 0.155 : 0.062);
    if (n.kind === 'wide') w *= 1.5;
    if (n.kind === 'sub') return { w: w * 0.62, h: w * 0.62, r: w * 0.31 };
    return { w: w, h: w * 0.60, r: Math.min(8, w * 0.14) };
  }

  function roundRect(ctx, x, y, w, h, r) {
    ctx.moveTo(x + r, y);
    ctx.lineTo(x + w - r, y);
    ctx.quadraticCurveTo(x + w, y, x + w, y + r);
    ctx.lineTo(x + w, y + h - r);
    ctx.quadraticCurveTo(x + w, y + h, x + w - r, y + h);
    ctx.lineTo(x + r, y + h);
    ctx.quadraticCurveTo(x, y + h, x, y + h - r);
    ctx.lineTo(x, y + r);
    ctx.quadraticCurveTo(x, y, x + r, y);
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

  function hueOf(name) {
    if (name === 'accent') return colors.accent;
    if (name === 'ink') return colors.ink;
    return HUES[name] || colors.ink;
  }

  /* ---- Glyphs -----------------------------------------------------------
   * Drawn rather than fetched: an icon font or a sprite sheet would be another
   * request in the hero's critical path, and at tile size these are a dozen
   * segments each. s is the tile's inner size; every glyph is centred on 0,0. */
  function glyph(ctx, name, cx, cy, s) {
    var u = s * 0.5;
    ctx.beginPath();
    if (name === 'bolt') {
      ctx.moveTo(cx + u * 0.25, cy - u);
      ctx.lineTo(cx - u * 0.55, cy + u * 0.12);
      ctx.lineTo(cx + u * 0.02, cy + u * 0.12);
      ctx.lineTo(cx - u * 0.22, cy + u);
      ctx.lineTo(cx + u * 0.6, cy - u * 0.16);
      ctx.lineTo(cx - u * 0.02, cy - u * 0.16);
      ctx.closePath();
      ctx.fill();
      return;
    }
    if (name === 'spark') {
      // The site's own four-point star, the mark already in the wordmark.
      ctx.moveTo(cx, cy - u);
      ctx.quadraticCurveTo(cx + u * 0.16, cy - u * 0.16, cx + u, cy);
      ctx.quadraticCurveTo(cx + u * 0.16, cy + u * 0.16, cx, cy + u);
      ctx.quadraticCurveTo(cx - u * 0.16, cy + u * 0.16, cx - u, cy);
      ctx.quadraticCurveTo(cx - u * 0.16, cy - u * 0.16, cx, cy - u);
      ctx.fill();
      return;
    }
    if (name === 'globe') {
      ctx.arc(cx, cy, u * 0.9, 0, TAU);
      ctx.moveTo(cx - u * 0.9, cy);
      ctx.lineTo(cx + u * 0.9, cy);
      ctx.moveTo(cx, cy - u * 0.9);
      ctx.bezierCurveTo(cx + u * 0.62, cy - u * 0.3, cx + u * 0.62, cy + u * 0.3, cx, cy + u * 0.9);
      ctx.bezierCurveTo(cx - u * 0.62, cy + u * 0.3, cx - u * 0.62, cy - u * 0.3, cx, cy - u * 0.9);
      ctx.stroke();
      return;
    }
    if (name === 'branch') {
      /* Two sliders, the way the editor draws a routing node. A literal fork
       * was the first choice and it collapsed into an ambiguous chevron at
       * tile size — twenty-four pixels does not carry three diverging lines. */
      ctx.moveTo(cx - u * 0.85, cy - u * 0.42);
      ctx.lineTo(cx + u * 0.85, cy - u * 0.42);
      ctx.moveTo(cx - u * 0.85, cy + u * 0.42);
      ctx.lineTo(cx + u * 0.85, cy + u * 0.42);
      ctx.stroke();
      ctx.beginPath();
      ctx.arc(cx + u * 0.3, cy - u * 0.42, u * 0.26, 0, TAU);
      ctx.fill();
      ctx.beginPath();
      ctx.arc(cx - u * 0.3, cy + u * 0.42, u * 0.26, 0, TAU);
      ctx.fill();
      return;
    }
    if (name === 'mail') {
      ctx.rect(cx - u * 0.9, cy - u * 0.65, u * 1.8, u * 1.3);
      ctx.moveTo(cx - u * 0.9, cy - u * 0.65);
      ctx.lineTo(cx, cy + u * 0.15);
      ctx.lineTo(cx + u * 0.9, cy - u * 0.65);
      ctx.stroke();
      return;
    }
    if (name === 'table') {
      ctx.rect(cx - u * 0.9, cy - u * 0.8, u * 1.8, u * 1.6);
      ctx.moveTo(cx - u * 0.9, cy - u * 0.24);
      ctx.lineTo(cx + u * 0.9, cy - u * 0.24);
      ctx.moveTo(cx - u * 0.9, cy + u * 0.28);
      ctx.lineTo(cx + u * 0.9, cy + u * 0.28);
      ctx.moveTo(cx - u * 0.16, cy - u * 0.8);
      ctx.lineTo(cx - u * 0.16, cy + u * 0.8);
      ctx.stroke();
      return;
    }
    if (name === 'db') {
      ctx.ellipse(cx, cy - u * 0.55, u * 0.85, u * 0.32, 0, 0, TAU);
      ctx.moveTo(cx - u * 0.85, cy - u * 0.55);
      ctx.lineTo(cx - u * 0.85, cy + u * 0.55);
      ctx.moveTo(cx + u * 0.85, cy - u * 0.55);
      ctx.lineTo(cx + u * 0.85, cy + u * 0.55);
      ctx.moveTo(cx - u * 0.85, cy + u * 0.55);
      ctx.bezierCurveTo(cx - u * 0.85, cy + u * 0.9, cx + u * 0.85, cy + u * 0.9, cx + u * 0.85, cy + u * 0.55);
      ctx.stroke();
      return;
    }
    // code
    ctx.moveTo(cx - u * 0.3, cy - u * 0.8);
    ctx.lineTo(cx - u * 0.85, cy);
    ctx.lineTo(cx - u * 0.3, cy + u * 0.8);
    ctx.moveTo(cx + u * 0.3, cy - u * 0.8);
    ctx.lineTo(cx + u * 0.85, cy);
    ctx.lineTo(cx + u * 0.3, cy + u * 0.8);
    ctx.stroke();
  }

  /* Corner brackets rather than a box: a closed rectangle around a node reads
   * as a selection in a design tool, the open corners read as a run in flight. */
  function reticle(ctx, x, y, w, h, arm) {
    var i, sx, sy, cx, cy;
    for (i = 0; i < 4; i++) {
      sx = (i === 0 || i === 2) ? -1 : 1;
      sy = i < 2 ? -1 : 1;
      cx = x + sx * w / 2;
      cy = y + sy * h / 2;
      ctx.moveTo(cx - sx * arm, cy);
      ctx.lineTo(cx, cy);
      ctx.lineTo(cx, cy - sy * arm);
    }
  }

  function drawGraph(p, time) {
    var ctx = state.ctx;
    if (!ctx || !state.w || !state.h) return;
    ctx.clearRect(0, 0, state.w, state.h);

    var box = graphBox();
    /* Absolute width, not aspect ratio. The phone band is 343x184 once padded,
     * which is a 1.86 ratio and sailed past an aspect test — leaving the whole
     * flow squeezed into the right-hand third of a canvas that had no text lane
     * to keep clear. What actually decides this is whether there is room. */
    compact = box.w < 640;
    /* One gate for every autonomous motion in the field. Scroll-driven motion
     * is left alone — the build answers the user's own scroll, which is not
     * what the preference is about. */
    var t = reduceMotion.matches ? 0 : time;
    var i, n, k, pos, sz, e;

    // The environment: one soft glow in the accent, so the canvas reads as a
    // place rather than a flat panel.
    var glow = ctx.createRadialGradient(
      box.x + box.w * 0.72, box.y + box.h * 0.5, 0,
      box.x + box.w * 0.72, box.y + box.h * 0.5, Math.max(box.w, box.h) * 0.75
    );
    glow.addColorStop(0, colors.accent);
    glow.addColorStop(1, 'rgba(0,0,0,0)');
    ctx.save();
    ctx.globalAlpha = 0.07 + 0.05 * smoothstep(p, 0.3, 1);
    ctx.fillStyle = glow;
    ctx.fillRect(0, 0, state.w, state.h);
    ctx.restore();

    /* The dot grid. It is the single strongest cue that this is a node editor
     * and not a diagram, and it costs one path. */
    var step = Math.max(16, Math.min(box.w, box.h) * 0.032);
    ctx.save();
    ctx.globalAlpha = 0.07 + 0.05 * smoothstep(p, 0.1, 0.6);
    ctx.fillStyle = colors.ink;
    ctx.beginPath();
    for (var gx = box.x; gx <= box.x + box.w; gx += step) {
      for (var gy = box.y; gy <= box.y + box.h; gy += step) {
        ctx.moveTo(gx + 0.9, gy);
        ctx.arc(gx, gy, 0.9, 0, TAU);
      }
    }
    ctx.fill();
    ctx.restore();

    // Connectors, revealed source to target as the build reaches them.
    for (e = 0; e < EDGES.length; e++) {
      var edge = EDGES[e];
      var g = clamp((p - edge.t) / 0.12, 0, 1);
      if (g <= 0) continue;
      var na = NODES[edge.a], nb = NODES[edge.b];
      var pa = nodePos(na, box), pb = nodePos(nb, box);
      var sa = cardSize(na, box), sb = cardSize(nb, box);
      /* Leave from the right port and arrive at the left one, except for a
       * port connection, which rises out of the sub-node's top into the
       * agent's underside the way the editor routes them. */
      var p0 = edge.d
        ? { x: pa.x, y: pa.y - sa.h / 2 }
        : { x: pa.x + sa.w / 2, y: pa.y };
      var p1 = edge.d
        ? { x: pb.x + (edge.a - 7) * sb.w * 0.22, y: pb.y + sb.h / 2 }
        : { x: pb.x - sb.w / 2, y: pb.y };
      var depth = (na.z + nb.z) / 2;
      var steps = 26;
      var lit = Math.floor(steps * g);
      var s, pt;

      ctx.save();
      ctx.strokeStyle = colors.ink;
      ctx.globalAlpha = (edge.d ? 0.10 : 0.16) + 0.24 * depth;
      ctx.lineWidth = depth > 0.85 ? 1.25 : 1;
      if (edge.d) ctx.setLineDash([4, 4]);
      ctx.beginPath();
      for (s = 0; s <= lit; s++) {
        pt = edgePoint(p0, p1, s / steps);
        if (s === 0) ctx.moveTo(pt.x, pt.y); else ctx.lineTo(pt.x, pt.y);
      }
      ctx.stroke();
      ctx.setLineDash([]);

      // Direction arrow at the midpoint, main path only — the editor does not
      // put one on a port connection, and neither should this.
      if (!edge.d && g >= 1) {
        var m0 = edgePoint(p0, p1, 0.46), m1 = edgePoint(p0, p1, 0.54);
        var ang = Math.atan2(m1.y - m0.y, m1.x - m0.x);
        var ah = Math.max(3.5, sa.h * 0.13);
        ctx.globalAlpha = 0.20 + 0.3 * depth;
        ctx.fillStyle = colors.ink;
        ctx.beginPath();
        ctx.moveTo(m1.x, m1.y);
        ctx.lineTo(m1.x - Math.cos(ang - 0.5) * ah, m1.y - Math.sin(ang - 0.5) * ah);
        ctx.lineTo(m1.x - Math.cos(ang + 0.5) * ah, m1.y - Math.sin(ang + 0.5) * ah);
        ctx.closePath();
        ctx.fill();
      }
      ctx.restore();

      // Payloads. They start once the graph is wired and keep running after it
      // settles: the workflow is supposed to still be working when you stop
      // scrolling. This is the hero's one living element.
      /* Flow used to ride the same axis as node arrival, which forced a choice
       * between a moving field and a scroll that still had something to reveal.
       * Wires now carry traffic as soon as there is a wire to carry it on, so
       * the resting progress is free to sit below the last node's arrival. */
      var flow = smoothstep(p, 0.18, 0.42);
      if (flow > 0 && g >= 1 && t) {
        var phase = ((t * 0.00016) + e * 0.37) % 1;
        for (var tr = 0; tr < 3; tr++) {
          var tp = phase - tr * 0.035;
          if (tp < 0) continue;
          var dot = edgePoint(p0, p1, tp);
          ctx.save();
          ctx.globalAlpha = flow * depth * (0.35 + 0.65 * Math.sin(Math.PI * tp)) * (1 - tr * 0.32) * (edge.d ? 0.5 : 1);
          ctx.fillStyle = colors.accent;
          ctx.beginPath();
          ctx.arc(dot.x, dot.y, Math.max(1.6, sa.h * 0.07) * (1 - tr * 0.22), 0, TAU);
          ctx.fill();
          ctx.restore();
        }
      }
    }

    // Nodes, and the reticle's target picked out along the way.
    var bestBusy = 0, bestNode = null;
    for (i = 0; i < NODES.length; i++) {
      n = NODES[i];
      k = clamp((p - n.t) / 0.10, 0, 1);
      if (k <= 0) continue;
      pos = nodePos(n, box);
      sz = cardSize(n, box);
      var isSub = n.kind === 'sub';
      var scale = 0.88 + 0.12 * k;
      var w = sz.w * scale, h = sz.h * scale;
      var busy = clamp(1 - Math.abs(p - (n.t + 0.08)) / 0.09, 0, 1);
      if (busy > bestBusy) { bestBusy = busy; bestNode = { x: pos.x, y: pos.y, w: w, h: h }; }

      ctx.save();
      ctx.globalAlpha = k;

      // Card body: the page's own background, lifted a touch by its own ink so
      // the card separates from the canvas on either theme without a hard-coded
      // surface colour that would be wrong on one of them.
      ctx.beginPath();
      if (isSub) ctx.arc(pos.x, pos.y, w / 2, 0, TAU);
      else roundRect(ctx, pos.x - w / 2, pos.y - h / 2, w, h, sz.r);
      ctx.fillStyle = colors.ground;
      ctx.fill();
      /* The card is filled with the page's own ground, then lifted by its own
       * ink so it separates on either theme without a hard-coded surface
       * colour. At 0.05 that lift was invisible and the card read as a hole.
       * 0.08 is the smallest value that gives it a plane at the near depth. */
      ctx.globalAlpha = k * 0.08;
      ctx.fillStyle = colors.ink;
      ctx.fill();

      // Border. The active node borrows the accent, which is how the editor
      // shows you which step a run is on.
      ctx.globalAlpha = k * (0.28 + 0.30 * n.z) * (1 + busy * 1.6);
      ctx.strokeStyle = busy > 0.05 ? colors.accent : colors.ink;
      ctx.lineWidth = busy > 0.05 ? 1.5 : 1;
      ctx.stroke();

      // Ports: the little dots the editor puts on a node's edges.
      if (!isSub) {
        ctx.globalAlpha = k * (0.20 + 0.25 * n.z);
        ctx.fillStyle = colors.ink;
        ctx.beginPath();
        ctx.arc(pos.x - w / 2, pos.y, Math.max(1.4, h * 0.055), 0, TAU);
        ctx.arc(pos.x + w / 2, pos.y, Math.max(1.4, h * 0.055), 0, TAU);
        ctx.fill();
      }

      // Icon tile, then the glyph on it.
      var tile = isSub ? w * 0.5 : h * 0.52;
      var tx = isSub ? pos.x : pos.x - w / 2 + h * 0.42;
      var hue = hueOf(n.hue);
      if (!isSub) {
        ctx.globalAlpha = k * 0.16;
        ctx.fillStyle = hue;
        ctx.beginPath();
        roundRect(ctx, tx - tile * 0.72, pos.y - tile * 0.72, tile * 1.44, tile * 1.44, tile * 0.42);
        ctx.fill();
      }
      ctx.globalAlpha = k * (0.55 + 0.35 * n.z);
      ctx.fillStyle = hue;
      ctx.strokeStyle = hue;
      ctx.lineWidth = Math.max(1, tile * 0.09);
      ctx.lineJoin = 'round';
      glyph(ctx, n.icon, tx, pos.y, tile);

      // The name, set under the node the way the editor sets it.
      var fs = Math.max(9, Math.round(h * (isSub ? 0.34 : 0.26)));
      ctx.textAlign = 'center';
      ctx.textBaseline = 'top';
      ctx.globalAlpha = k * (0.34 + 0.34 * n.z);
      ctx.fillStyle = colors.ink;
      ctx.font = '600 ' + fs + 'px Inter, system-ui, sans-serif';
      ctx.fillText(n.label, pos.x, pos.y + h / 2 + fs * 0.55);
      /* Ink, not body, and the token change is the point: body needs alpha
       * 0.74 to clear 4.5:1 over the ground, which pins the sub-line near
       * opaque and erases its depth cue. Ink clears the same floor at 0.48.
       * The label above stays brighter still, so the hierarchy holds.
       * tests/test_hero_contrast.py recomputes this and fails if it slips. */
      if (n.sub) {
        ctx.globalAlpha = k * (0.36 + 0.18 * n.z);
        ctx.fillStyle = colors.ink;
        ctx.font = Math.max(8, fs - 1) + 'px Inter, system-ui, sans-serif';
        ctx.fillText(n.sub, pos.x, pos.y + h / 2 + fs * 1.85);
      }

      /* The unwired output. Every canvas anyone has actually built has one, and
       * it is the detail that stops the field looking like an illustration. */
      if (n.kind === 'card' && (i === 4 || i === 5) && k > 0.9) {
        var px = pos.x + w / 2 + h * 0.55, ps = h * 0.26;
        ctx.globalAlpha = k * 0.22;
        ctx.strokeStyle = colors.ink;
        ctx.lineWidth = 1;
        ctx.beginPath();
        roundRect(ctx, px - ps / 2, pos.y - ps / 2, ps, ps, ps * 0.28);
        ctx.moveTo(px - ps * 0.22, pos.y);
        ctx.lineTo(px + ps * 0.22, pos.y);
        ctx.moveTo(px, pos.y - ps * 0.22);
        ctx.lineTo(px, pos.y + ps * 0.22);
        ctx.stroke();
      }

      ctx.restore();
    }

    /* The reticle. One per field: a run is on one node at a time, and two
     * brackets on screen would just read as more decoration. */
    if (bestNode && bestBusy > 0.02) {
      var rw = bestNode.w * 1.28, rh = bestNode.h * 1.55;
      if (!hud.live || !t) {
        hud.rx = bestNode.x; hud.ry = bestNode.y; hud.rw = rw; hud.rh = rh; hud.live = true;
      } else {
        hud.rx += (bestNode.x - hud.rx) * 0.18;
        hud.ry += (bestNode.y - hud.ry) * 0.18;
        hud.rw += (rw - hud.rw) * 0.18;
        hud.rh += (rh - hud.rh) * 0.18;
      }
      ctx.save();
      ctx.globalAlpha = 0.28 + 0.42 * bestBusy;
      ctx.strokeStyle = colors.accent;
      ctx.lineWidth = 1.25;
      ctx.beginPath();
      reticle(ctx, hud.rx, hud.ry, hud.rw, hud.rh, Math.min(hud.rw, hud.rh) * 0.3);
      ctx.stroke();
      ctx.restore();
    } else {
      hud.live = false;
    }
  }

  function resize() {
    if (!state.canvas || !state.stage) return;
    /* The canvas's own rect, not the stage's. On a wide screen it is absolutely
     * positioned over the whole stage and the two are the same box; on a phone
     * it is a band in the flow below the copy, and measuring the stage there
     * would size the drawing surface to the text as well. */
    var rect = state.canvas.getBoundingClientRect();
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

  /* Static mode pins the copy and drops the scroll choreography, which is right
   * on a phone: a 3600px scrub track is not something to hand a thumb. It used
   * to also mean the canvas painted once and stopped. It now idles instead —
   * the rings turn, the payloads run — so the workflow reads as running rather
   * than as a screenshot of one. Gated on the same IntersectionObserver the
   * scrub loop uses, so it costs nothing while it is off screen, and skipped
   * entirely under reduced motion. */
  function idleTick(now) {
    drawGraph(1, now);
    if (idleAlive()) {
      idleId = requestAnimationFrame(idleTick);
    } else {
      idleId = null;
    }
  }

  function idleAlive() {
    return staticMode() && !reduceMotion.matches && state.onScreen && !state.hidden;
  }

  function startIdle() {
    if (idleId !== null) return;
    if (!idleAlive()) { drawGraph(1, 0); return; }
    idleId = requestAnimationFrame(idleTick);
  }

  function stopIdle() {
    if (idleId !== null) { cancelAnimationFrame(idleId); idleId = null; }
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
    /* 0.46 rests the field just past Airtable (t=0.40) and short of the dashed
     * port cluster (t=0.48-0.56), so six of nine nodes are present at full flow
     * and the sub-nodes stay the scroll's payoff. */
    drawGraph(Math.max(shown, lk * 0.46), now);

    // The loop keeps running only while there is something to move: the ease
    // has not converged, the opening assembly is still playing, or payloads are
    // in flight on a stage that is actually on screen and visible.
    var flowing = shown > 0.20 && !reduceMotion.matches;
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
    if (idleAlive()) startIdle();
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
      startIdle();
    } else {
      stopIdle();
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
