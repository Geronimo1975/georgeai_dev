/* ---------------------------------------------------------------------------
 * hero-motion.js — motion layer for the homepage hero.
 *
 * Repo-owned, copied into site/ by deploy.sh:apply_hero() and injected into
 * index.html. NEVER edit the copy in site/ — it is wiped on every deploy.
 *
 * Why JS at all: the design-tool export renders the hero client-side from
 * support.js with inline styles and no ids or classes, and re-renders the panel
 * subtree on every state change. So — same approach as backend/assets/auth.js —
 * we hook it *by structure*, re-tag on mutation, and degrade to a no-op if the
 * export ever stops shipping the accordion.
 *
 * Everything visual lives in hero-motion.css; this file only tags nodes, drives
 * the autoplay timer, and writes parallax offsets as CSS variables.
 * ------------------------------------------------------------------------- */
(function () {
  'use strict';

  var DWELL = 5200; // must match --ga-dwell in hero-motion.css
  var VIDEO_SRC = '/assets/hero.mp4';

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var finePointer = window.matchMedia('(hover: hover) and (pointer: fine)');
  var wideEnough = window.matchMedia('(min-width: 900px)');

  var state = {
    root: null,
    row: null,
    progress: null,
    videoWrap: null,
    activeIdx: -1,
    timer: null,
    autoplay: true, // false once the visitor picks a panel themselves
    paused: false,
    entered: false,
    selfAdvancing: false,
  };

  /* --------------------------------------------------------------------
   * Discovery — the accordion panels are the only nodes in the export
   * carrying `transition:flex` inline. The panel row lives in two places
   * (hero showcase, and the "Featured" section that renders only in video
   * mode), so we confirm the hero by its beam/grid backdrop.
   * ------------------------------------------------------------------ */
  function findHero() {
    // The browser re-serialises inline styles ("transition: flex 0.6s ..."), and
    // support.js rewrites them on every render — so match with a whitespace-
    // tolerant regex rather than a brittle [style*=] attribute selector.
    var candidates = document.querySelectorAll('div[style*="transition"]');
    var panels = [];
    for (var c = 0; c < candidates.length; c++) {
      if (/transition:\s*flex\b/.test(candidates[c].getAttribute('style') || '')) {
        panels.push(candidates[c]);
      }
    }
    if (!panels.length) return null;

    var row = panels[0].parentElement;
    if (!row) return null;
    var root = row.parentElement;
    if (!root) return null;

    var bg = null;
    for (var i = 0; i < root.children.length; i++) {
      var s = root.children[i].getAttribute('style') || '';
      if (s.indexOf('46px 46px') !== -1) { bg = root.children[i]; break; }
    }
    if (!bg) return null; // panel row without the hero backdrop → Featured section

    return { root: root, row: row, bg: bg, panels: Array.prototype.slice.call(row.children) };
  }

  /* The framework re-renders panels rather than mutating them, so "active" is
   * re-derived each pass instead of held as a reference.
   *
   * Deliberately NOT measured from layout: offsetWidth during the 420ms flex
   * transition still reports the outgoing panel, which silently pins every
   * downstream read (detail tagging, progress) one step behind. The detail
   * block is only rendered inside the active panel, so its presence is exact
   * and available on the same frame as the re-render. */
  function activeIndex(panels) {
    for (var i = 0; i < panels.length; i++) {
      if (panels[i].querySelector('h3')) return i;
    }
    // Detail block not painted yet — fall back to the authored flex-grow in the
    // style attribute (the authored value, unaffected by the running transition).
    var best = 0, bestF = -1;
    for (var j = 0; j < panels.length; j++) {
      var m = /flex:\s*([\d.]+)/.exec(panels[j].getAttribute('style') || '');
      var f = m ? parseFloat(m[1]) : 0;
      if (f > bestF) { bestF = f; best = j; }
    }
    return best;
  }

  function detailBlock(panel) {
    var kids = panel.children;
    for (var i = kids.length - 1; i >= 0; i--) {
      if (kids[i].querySelector && kids[i].querySelector('h3')) return kids[i];
    }
    return null;
  }

  /* --------------------------------------------------------------------
   * Tagging — idempotent, re-run after every re-render.
   * ------------------------------------------------------------------ */
  /* --------------------------------------------------------------------
   * Design-review fixes (2026-08-19) — see .jez/artifacts/design-review.md
   * ------------------------------------------------------------------ */

  /* A. Hero lede. deploy.sh injects the block before </body> so the <h1> is in
   * the raw HTML for crawlers; here it is moved to the top of the hero, above
   * the panel row. Idempotent — sync() runs on every mutation. */
  function placeLede(hero) {
    var lede = document.querySelector('[data-ga-lede]');
    if (!lede) return;
    if (lede.parentElement !== hero.root || lede.nextElementSibling !== hero.row) {
      hero.root.insertBefore(lede, hero.row);
    }
    if (!lede.classList.contains('ga-lede--in')) {
      requestAnimationFrame(function () { lede.classList.add('ga-lede--in'); });
    }
  }

  /* B. The consent banner and the audit FAB both own the bottom-right corner;
   * the FAB was winning the hit test over "Accept all". Tag <html> while the
   * banner is up so CSS can stand the FAB down. Structural, not text-matched —
   * the banner copy ships in five languages. */
  var consentTitles = null;

  /* The consent bar carries no id, class or href, is not always position:fixed
   * (mobile drops it back into flow), and its copy ships in five languages — so
   * neither a selector nor a geometry test holds. window.GA_LEGAL.cookie is
   * repo-owned (site/legal-data.js) and lists the exact title in every
   * language, which makes an exact-text match the one reliable handle. */
  function consentTitleSet() {
    if (consentTitles) return consentTitles;
    var cookie = window.GA_LEGAL && window.GA_LEGAL.cookie;
    if (!cookie) return null; // legal-data.js not in yet — retry next pass
    consentTitles = [];
    for (var lang in cookie) {
      if (cookie[lang] && cookie[lang].title) consentTitles.push(cookie[lang].title);
    }
    return consentTitles;
  }

  function consentOpen() {
    var titles = consentTitleSet();
    if (!titles || !titles.length) return false;
    var nodes = document.querySelectorAll('#dc-root h3, #dc-root h4, #dc-root div, #dc-root span, #dc-root p');
    for (var i = 0; i < nodes.length; i++) {
      var n = nodes[i];
      if (n.children.length) continue; // leaf only — ancestors carry the text too
      var t = n.textContent.trim();
      if (!t) continue;
      for (var j = 0; j < titles.length; j++) {
        if (t === titles[j] && n.getBoundingClientRect().height > 0) return true;
      }
    }
    return false;
  }

  function syncConsent() {
    document.documentElement.classList.toggle('ga-consent-open', consentOpen());
  }

  /* D. Services grid: four group cards in a 2-col grid, wildly uneven item
   * counts. Tag it so CSS can flow it as balanced columns. Matched by shape
   * (a 2-col grid whose every child carries an h3) because the group names are
   * localised. No match → no class → the export's grid stands unchanged. */
  function tagServicesGrid() {
    if (document.querySelector('.ga-svc-grid')) return;
    var grids = document.querySelectorAll('div[style*="grid"]');
    for (var i = 0; i < grids.length; i++) {
      var g = grids[i];
      if (!/grid-template-columns:\s*repeat\(2/.test(g.getAttribute('style') || '')) continue;
      var kids = g.children;
      if (kids.length < 3) continue;
      var all = true;
      for (var k = 0; k < kids.length; k++) {
        if (!kids[k].querySelector('h3')) { all = false; break; }
      }
      if (all) { g.classList.add('ga-svc-grid'); return; }
    }
  }

  /* E. Mobile chrome + touch targets.
   *
   * The top bar stacked three rows into 163px before any content — 20% of an
   * 844px screen — and its 7 social icons render at 17px, well under the 44px
   * minimum. The same seven links sit in the footer verbatim, so on phones the
   * header row is dropped rather than enlarged, which fixes the height and the
   * tap size in one move. The footer copies stay and get grown to 44px there.
   *
   * Both rows are found the same way: a flex row of five or more sibling
   * anchors pointing at social hosts. Nothing else on the site has that shape.
   */
  var SOCIAL_HOST = /(whatsapp|wa\.me|facebook|instagram|tiktok|youtube|linkedin|github|x\.com|twitter)/i;

  function socialRows() {
    var rows = [], divs = document.querySelectorAll('#dc-root div');
    for (var i = 0; i < divs.length; i++) {
      var kids = divs[i].children, hits = 0;
      if (kids.length < 5) continue;
      for (var k = 0; k < kids.length; k++) {
        if (kids[k].tagName === 'A' && SOCIAL_HOST.test(kids[k].getAttribute('href') || '')) hits++;
      }
      if (hits >= 5) rows.push(divs[i]);
    }
    return rows;
  }

  /* The footer is the full-bleed band the second social row lives in. Walking
   * up to viewport width beats guessing at the export's nesting depth; bail if
   * the walk overshoots into something that also holds the hero. */
  function footerFor(row) {
    var n = row;
    while (n && n !== document.body) {
      if (Math.round(n.getBoundingClientRect().width) >= document.documentElement.clientWidth - 1) {
        return n.querySelector('.ga-hero') ? null : n;
      }
      n = n.parentElement;
    }
    return null;
  }

  /* The utility row (contact + language + sign-up + theme) and the logo/nav bar
   * share one sticky wrapper, so 167px of chrome stayed pinned on a 844px
   * screen. Pulling the wrapper up by exactly the utility row's height lets
   * that row scroll away while the nav bar still pins at the top — the phone
   * number and the controls stay on the page, they just stop occupying a fifth
   * of every screen. The height is measured rather than assumed because the
   * row rewraps with the language (Arabic runs taller). */
  function measureTopbar() {
    var bar = document.querySelector('.ga-topbar');
    var header = document.querySelector('.ga-header');
    if (!bar || !header) return;
    header.style.setProperty('--ga-topbar-h', bar.offsetHeight + 'px');
  }

  function tagChrome() {
    if (document.querySelector('.ga-soc-row--foot')) return;
    var rows = socialRows();
    if (rows.length < 2) return; // export changed shape — leave everything alone
    rows[0].classList.add('ga-soc-row', 'ga-soc-row--head');
    var topbar = rows[0].parentElement;
    if (topbar) {
      topbar.classList.add('ga-topbar');
      var sticky = topbar;
      while (sticky && sticky !== document.body &&
             getComputedStyle(sticky).position !== 'sticky') {
        sticky = sticky.parentElement;
      }
      if (sticky && sticky !== document.body) {
        sticky.classList.add('ga-header');
        measureTopbar();
      }
    }
    var foot = rows[rows.length - 1];
    foot.classList.add('ga-soc-row', 'ga-soc-row--foot');
    var f = footerFor(foot);
    if (f) f.classList.add('ga-footer');
  }

  /* C. Under 900px the panel row is a horizontal scroller. Autoplay only moved
   * the active index, leaving the visitor parked on an uncaptioned slide while
   * the caption rendered off-screen. Keep the scroller and the active panel in
   * step — gated on state.autoplay, which stopAutoplay() clears the moment
   * the visitor drives the hero themselves, so this never fights a finger. */
  function scrollActiveIntoView(hero, idx) {
    if (wideEnough.matches) return;
    var row = hero.row, panel = hero.panels[idx];
    if (!row || !panel || row.scrollWidth <= row.clientWidth + 4) return;
    var target = panel.offsetLeft - row.offsetLeft;
    if (Math.abs(row.scrollLeft - target) < 8) return;
    if (row.scrollTo) {
      row.scrollTo({ left: target, behavior: reduceMotion.matches ? 'auto' : 'smooth' });
    } else {
      row.scrollLeft = target;
    }
  }


  function sync() {
    var hero = findHero();
    if (!hero) { teardown(); return; }

    state.root = hero.root;
    state.row = hero.row;
    hero.root.classList.add('ga-hero');
    hero.bg.classList.add('ga-hero-bg');

    // Beams sit between the bottom glow (first child) and the two closing
    // gradient strips (last two children). They already animate themselves
    // (the export sets `animation:` inline), so tagging them buys exactly one
    // thing: a hook the reduced-motion block can use to stop that animation.
    var bgKids = hero.bg.children;
    for (var b = 1; b < bgKids.length - 2; b++) {
      bgKids[b].classList.add('ga-hero-beam');
    }

    var idx = activeIndex(hero.panels);
    for (var i = 0; i < hero.panels.length; i++) {
      var p = hero.panels[i];
      p.classList.add('ga-hero-panel');
      p.classList.toggle('ga-hero-panel--active', i === idx);
      if (i === idx) {
        var d = detailBlock(p);
        if (d) d.classList.add('ga-hero-detail');
      }
    }

    // The CTA row is the sibling after the panel row.
    var cta = hero.row.nextElementSibling;
    if (cta && cta !== state.progress) cta.classList.add('ga-hero-cta');

    placeLede(hero);
    tagServicesGrid();
    tagChrome();

    ensureProgress(hero);
    ensureVideo(hero);

    if (idx !== state.activeIdx) {
      state.activeIdx = idx;
      paintProgress(hero.panels.length, idx);
      restartTimer();
      if (state.autoplay) scrollActiveIntoView(hero, idx);
    }

    if (!state.entered) {
      state.entered = true;
      hero.root.classList.add('ga-hero--enter');
      requestAnimationFrame(function () {
        requestAnimationFrame(function () {
          hero.root.classList.add('ga-hero--ready');
        });
      });
    }
  }

  /* --------------------------------------------------------------------
   * Autoplay progress indicator
   * ------------------------------------------------------------------ */
  function ensureProgress(hero) {
    if (state.progress && state.progress.parentElement === hero.root) return;
    var bar = document.createElement('div');
    bar.className = 'ga-hero-progress';
    bar.setAttribute('aria-hidden', 'true');
    hero.row.insertAdjacentElement('afterend', bar);
    state.progress = bar;
    paintProgress(hero.panels.length, state.activeIdx);
  }

  function paintProgress(count, idx) {
    var bar = state.progress;
    if (!bar) return;
    bar.hidden = !state.autoplay;
    bar.textContent = '';
    for (var i = 0; i < count; i++) {
      var seg = document.createElement('div');
      seg.className =
        'ga-hero-progress-seg' +
        (i === idx ? ' ga-hero-progress-seg--active' : i < idx ? ' ga-hero-progress-seg--done' : '');
      seg.appendChild(document.createElement('i'));
      bar.appendChild(seg);
    }
  }

  /* --------------------------------------------------------------------
   * Video backdrop — showcase mode only, and only where it is not a
   * bandwidth or motion imposition.
   * ------------------------------------------------------------------ */
  function videoAllowed() {
    if (reduceMotion.matches) return false;
    if (!wideEnough.matches) return false;
    var c = navigator.connection;
    if (c && (c.saveData || /2g/.test(c.effectiveType || ''))) return false;
    return true;
  }

  function ensureVideo(hero) {
    if (!videoAllowed()) return;
    if (state.videoWrap && state.videoWrap.parentElement === hero.root) return;
    // Video mode already ships its own <video>; do not stack a second one.
    if (hero.root.querySelector('video')) return;

    var wrap = document.createElement('div');
    wrap.className = 'ga-hero-video';
    wrap.setAttribute('aria-hidden', 'true');

    var v = document.createElement('video');
    v.src = VIDEO_SRC;
    v.muted = true;
    v.loop = true;
    v.playsInline = true;
    v.autoplay = true;
    v.preload = 'metadata';
    v.setAttribute('muted', '');
    v.setAttribute('playsinline', '');
    wrap.appendChild(v);

    hero.root.insertBefore(wrap, hero.root.firstChild);
    state.videoWrap = wrap;

    v.addEventListener('canplay', function () {
      wrap.classList.add('ga-hero-video--in');
      hero.root.classList.add('ga-hero--video-bg');
    });
    v.addEventListener('error', function () {
      wrap.remove();
      hero.root.classList.remove('ga-hero--video-bg');
      state.videoWrap = null;
    });

    var play = v.play();
    if (play && play.catch) play.catch(function () { /* autoplay blocked — fine */ });

    // Don't decode frames the visitor cannot see.
    if ('IntersectionObserver' in window) {
      new IntersectionObserver(function (entries) {
        entries.forEach(function (e) {
          if (e.isIntersecting) { var p = v.play(); if (p && p.catch) p.catch(function () {}); }
          else v.pause();
        });
      }, { threshold: 0.05 }).observe(hero.root);
    }
  }

  /* --------------------------------------------------------------------
   * Autoplay timer
   * ------------------------------------------------------------------ */
  function restartTimer() {
    clearTimeout(state.timer);
    if (!state.autoplay || state.paused || reduceMotion.matches) return;
    state.timer = setTimeout(advance, DWELL);
  }

  function advance() {
    var hero = findHero();
    if (!hero || !state.autoplay || state.paused) return;
    var next = (activeIndex(hero.panels) + 1) % hero.panels.length;
    state.selfAdvancing = true;
    hero.panels[next].click();
    // Cleared on a microtask so the synthetic click's own pointer/click
    // handlers don't read as visitor intent.
    setTimeout(function () { state.selfAdvancing = false; }, 0);
    restartTimer();
  }

  function stopAutoplay() {
    state.autoplay = false;
    clearTimeout(state.timer);
    if (state.progress) state.progress.hidden = true;
  }

  function setPaused(p) {
    if (state.paused === p) return;
    state.paused = p;
    if (state.root) state.root.classList.toggle('ga-hero--paused', p);
    if (p) clearTimeout(state.timer);
    else restartTimer();
  }

  /* --------------------------------------------------------------------
   * Pointer parallax — rAF lerp toward the pointer, so the backdrop has
   * momentum instead of tracking the cursor 1:1 (which reads as artificial).
   * ------------------------------------------------------------------ */
  var px = 0, py = 0, tx = 0, ty = 0, rafId = 0;

  function tick() {
    px += (tx - px) * 0.08;
    py += (ty - py) * 0.08;
    if (state.root) {
      var bg = state.root.querySelector('.ga-hero-bg');
      if (bg) {
        bg.style.setProperty('--ga-px', px.toFixed(2) + 'px');
        bg.style.setProperty('--ga-py', py.toFixed(2) + 'px');
      }
      if (state.videoWrap) {
        state.videoWrap.style.setProperty('--ga-px', (px * 1.8).toFixed(2) + 'px');
        state.videoWrap.style.setProperty('--ga-py', (py * 1.8).toFixed(2) + 'px');
      }
    }
    if (Math.abs(tx - px) > 0.1 || Math.abs(ty - py) > 0.1) rafId = requestAnimationFrame(tick);
    else rafId = 0;
  }

  function nudge() { if (!rafId) rafId = requestAnimationFrame(tick); }

  function onPointerMove(e) {
    if (!state.root || reduceMotion.matches || !finePointer.matches) return;
    var r = state.root.getBoundingClientRect();
    tx = ((e.clientX - r.left) / r.width - 0.5) * -12;
    ty = ((e.clientY - r.top) / r.height - 0.5) * -8;
    nudge();
  }

  function onPointerLeave() { tx = 0; ty = 0; nudge(); }

  /* --------------------------------------------------------------------
   * Wiring
   * ------------------------------------------------------------------ */
  function teardown() {
    clearTimeout(state.timer);
    state.root = null;
    state.row = null;
    state.progress = null;
    state.videoWrap = null;
    state.activeIdx = -1;
    state.entered = false;
  }

  document.addEventListener('pointerdown', function (e) {
    if (!e.isTrusted || state.selfAdvancing) return;
    if (state.row && state.row.contains(e.target)) stopAutoplay();
  }, true);

  document.addEventListener('pointerover', function (e) {
    if (state.root && state.root.contains(e.target)) setPaused(true);
  }, true);
  document.addEventListener('pointerout', function (e) {
    if (state.root && !state.root.contains(e.relatedTarget)) setPaused(false);
  }, true);
  document.addEventListener('focusin', function (e) {
    if (state.root && state.root.contains(e.target)) setPaused(true);
  });
  document.addEventListener('visibilitychange', function () {
    setPaused(document.hidden);
  });

  document.addEventListener('pointermove', onPointerMove, { passive: true });
  document.addEventListener('pointerleave', onPointerLeave, { passive: true });

  reduceMotion.addEventListener('change', function () {
    if (reduceMotion.matches) { stopAutoplay(); tx = ty = 0; nudge(); }
  });

  // The export renders asynchronously and re-renders on every state change,
  // so re-tagging is driven by mutations, coalesced into one rAF.
  var queued = false;
  function schedule() {
    syncConsent();
    if (queued) return;
    queued = true;
    requestAnimationFrame(function () { queued = false; sync(); });
  }

  window.addEventListener('resize', measureTopbar);

  function boot() {
    syncConsent();
    sync();
    new MutationObserver(schedule).observe(document.body, { childList: true, subtree: true });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot);
  } else {
    boot();
  }
})();
