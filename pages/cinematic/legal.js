/* Renders the four legal documents from window.GA_LEGAL (/legal-data.js, shared with the classic
   site, identity applied by deploy.sh:apply_legal). Language from ?lang=, the select, or the browser. */
(() => {
  'use strict';
  const root = document.getElementById('legal-docs'), sel = document.getElementById('lg-lang');
  if (!root) return;
  const L = window.GA_LEGAL;
  if (!L) { root.innerHTML = '<p class="lede">The legal texts could not be loaded. They are in the footer of the <a href="/index.html">classic site</a>.</p>'; return; }
  const langs = Object.keys(L.docs);
  const pick = () => {
    const q = new URLSearchParams(location.search).get('lang');
    const d = sel && sel.dataset.default, b = (navigator.language || 'en').slice(0, 2);
    return langs.includes(q) ? q : langs.includes(d) ? d : langs.includes(b) ? b : 'en';
  };
  const esc = s => String(s).replace(/[&<>]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;' }[c]));
  const para = t => esc(t).split('\n').map(l => l.trim()).filter(Boolean).join('<br>');
  function render(lang) {
    const docs = L.docs[lang] || L.docs.en, lab = L.labels[lang] || L.labels.en;
    document.documentElement.lang = lang; document.documentElement.dir = lang === 'ar' ? 'rtl' : 'ltr';
    root.innerHTML = L.docKeys.map(k => {
      const d = docs[k]; if (!d) return '';
      const secs = (d.sections || []).map(s => `<h3>${esc(s.h)}</h3><p>${para(s.p)}</p>`).join('');
      const upd = d.updated || L.updated ? `<p class="mono upd">${esc(lab.updated || 'Last updated')}: ${esc(d.updated || L.updated)}</p>` : '';
      return `<article class="legal-doc" id="${k}"><h2>${esc(d.title)}</h2>${d.sub ? `<p class="lede">${esc(d.sub)}</p>` : ''}${upd}${secs}</article>`;
    }).join('');
    document.querySelectorAll('.legal-tabs a').forEach(a => { const k = a.getAttribute('href').slice(1); if (lab[k]) a.textContent = lab[k]; });
    if (location.hash) { const el = document.querySelector(location.hash); if (el) el.scrollIntoView(); }
  }
  const lang = pick(); if (sel) { sel.value = lang; sel.addEventListener('change', () => { history.replaceState(null, '', '?lang=' + sel.value + location.hash); render(sel.value); }); }
  render(lang);
})();
