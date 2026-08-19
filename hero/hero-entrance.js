/* ---------------------------------------------------------------------------
 * hero-entrance.js — entrance motion for the repo-owned homepage hero.
 *
 * Repo-owned, copied into site/ by deploy.sh:apply_hero(). NEVER edit the copy
 * in site/ — it is wiped on every deploy. The tags that load it live in
 * i18n/home.html, so all four locales (en/de/fr/ro) get it from one source.
 *
 * Not to be confused with hero-motion.js: that one hooks the *design-tool
 * export's* accordion hero by structure. This page is `pages:owned`, so
 * apply_hero deliberately skips injecting that layer here. Different hero,
 * different file.
 *
 * Anime.js v4 (vendored UMD → global `anime`, see hero/anime.umd.min.js).
 * Justified over CSS keyframes because the five hero elements share one
 * choreography with one control surface: a single timeline that can be seeked,
 * paused with the page, and reverted cleanly. Durations and curves come from
 * design/tokens.css — do not invent numbers here.
 * ------------------------------------------------------------------------- */
(function () {
  'use strict';

  if (!window.anime || !window.anime.createTimeline) return; // bundle missing → CSS failsafe reveals
  var A = window.anime;

  var root = document.documentElement;
  var READY = 'ga-motion-ready';

  /* The `ga-motion` class on <html> is what hides the hero before we paint it.
   * Whatever happens below, it comes off — an animation that fails must never
   * leave the headline invisible. */
  function reveal() {
    root.classList.add(READY);
    root.classList.remove('ga-motion');
  }

  function tokenMs(name, fallback) {
    var v = getComputedStyle(root).getPropertyValue(name).trim();
    var n = parseFloat(v);
    if (!n) return fallback;
    return /\bs$/.test(v) && !/ms$/.test(v) ? n * 1000 : n;
  }

  var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)');

  function boot() {
    var hero = document.querySelector('.hero');
    if (!hero) { reveal(); return; }

    /* The <head> guard already declines to hide anything under reduced motion,
     * but it cannot stop this file from running — and Anime.js does not honour
     * the preference for us. So bail here too, and while we are at it stop the
     * looping backdrop: an autoplaying video is itself the kind of motion the
     * preference is asking us not to impose. */
    if (reduceMotion.matches) {
      reveal();
      var still = hero.querySelector('.hero-video');
      if (still) { try { still.pause(); still.removeAttribute('autoplay'); } catch (e) {} }
      return;
    }

    // Order is the reading order: label, headline, promise, action.
    var lines = [];
    ['.eyebrow', 'h1', '.lede', '.cta-row'].forEach(function (sel) {
      var el = hero.querySelector(sel);
      if (el) lines.push(el);
    });
    var video = hero.querySelector('.hero-video');

    if (!lines.length) { reveal(); return; }

    // The backdrop's resting opacity is authored in CSS (.hero-video). Read it
    // rather than repeating it, so a stylesheet change can't silently desync.
    var videoRest = video ? parseFloat(getComputedStyle(video).opacity) || 0.18 : 0;

    // --dur-slow is the longest curve the system authorises for a UI move.
    // Four staggered elements at 420ms each still land inside a second.
    var slow = tokenMs('--dur-slow', 420);

    // --ease-out from tokens.css: cubic-bezier(.16, 1, .3, 1). Entering motion
    // decelerates — content arrives and settles, it never accelerates away.
    // Passed as a function, not the string form: v4.5 removed string easings
    // from the core and warns once per animation if you use them.
    var EASE = A.cubicBezier(0.16, 1, 0.3, 1);
    var EASE_BACKDROP = A.eases.out(2);

    reveal(); // hand the styling over to the timeline before the first frame

    var tl = A.createTimeline({
      defaults: { duration: slow, ease: EASE },
      onComplete: function (self) {
        // Inline transforms left on the headline would fight text-wrap and the
        // responsive type scale on a later resize.
        A.utils.cleanInlineStyles(self);
      },
    });

    if (video) {
      // Longer and flatter than the copy: a backdrop should resolve *behind*
      // the reading, not compete with it for attention.
      tl.add(video, { opacity: [0, videoRest], duration: 1200, ease: EASE_BACKDROP }, 0);
    }

    tl.add(
      lines,
      {
        opacity: [0, 1],
        y: [12, 0], // ~one step of the space scale; enough to read as arrival
        delay: A.stagger(90),
      },
      video ? 120 : 0
    );

    return tl;
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', boot, { once: true });
  } else {
    boot();
  }
})();
