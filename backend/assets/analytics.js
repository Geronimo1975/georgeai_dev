/* Google Analytics 4 (gtag.js) — consent-gated loader.
 *
 * Kept out of the design-tool export (like auth.js / audit.js) so it survives
 * a re-export, copied into site/ by deploy.sh's apply_assets and injected on
 * every page by apply_analytics.
 *
 * WHY THIS IS NOT THE RAW gtag SNIPPET
 * The vanilla snippet Google hands you loads googletagmanager.com and fires a
 * page_view — shipping the visitor's IP to Google — the instant the page
 * parses, before anyone touches the consent banner. On a German site with a
 * Datenschutzerklärung that is exactly the Abmahnung exposure this repo already
 * engineers around for Google Fonts (see seo/apply_content.py, LG München I
 * 3 O 17493/20). So GA here loads ONLY after explicit "Accept all" consent.
 *
 * The export's cookie banner (GeorgeAI.dc.html) writes localStorage.ga_cookie:
 *   "all"       -> visitor accepted optional/analytics cookies
 *   "essential" -> visitor declined; load nothing
 *   (unset)     -> banner not answered yet; wait, do not load
 * The banner updates localStorage without a reload, so we poll until the
 * choice is settled (mirrors audit.js), then load gtag the moment it is "all".
 */
(function () {
  "use strict";

  var MEASUREMENT_ID = "G-RF1QM0Q149";
  var loaded = false;

  function consentGranted() {
    try { return localStorage.getItem("ga_cookie") === "all"; }
    catch (e) { return false; } // private mode / storage blocked -> no consent
  }

  function loadGA() {
    if (loaded) return;
    loaded = true;

    var s = document.createElement("script");
    s.async = true;
    s.src = "https://www.googletagmanager.com/gtag/js?id=" + MEASUREMENT_ID;
    document.head.appendChild(s);

    window.dataLayer = window.dataLayer || [];
    function gtag() { window.dataLayer.push(arguments); }
    window.gtag = gtag;
    gtag("js", new Date());
    // GA4 anonymises IPs by default; no analytics cookie is read or written
    // until this point, so nothing fires before "Accept all".
    gtag("config", MEASUREMENT_ID);
  }

  if (consentGranted()) {
    loadGA();
    return;
  }

  // Not granted yet (unset, or "essential"). Poll and load the moment the value
  // becomes "all" — this also covers a later upgrade from "essential" via the
  // "Cookie settings" reopen, on any page (the cinematic banner or the export's
  // own React banner), with no reload. The idle timer is a no-op if the visitor
  // keeps "essential".
  var timer = setInterval(function () {
    if (consentGranted()) { clearInterval(timer); loadGA(); }
  }, 800);
})();
