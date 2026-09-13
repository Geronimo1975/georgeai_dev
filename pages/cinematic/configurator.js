/* Project configurator: pick services, scale and add-ons; the timeline and complexity follow the
   rules in georgeai_services.json (configurator.logic). The request goes out as an email with the
   summary prefilled, so nothing is stored on the page. Signed-in visitors get their name and email
   prefilled from /api/auth/me. */
(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const root = $('#cfg'); if (!root) return;
  const L = (document.documentElement.lang || 'en').slice(0, 2);
  const T = {
    en: { weeks: 'weeks', low: 'Low', medium: 'Medium', high: 'High', none: 'Pick at least one service to see a timeline.', subject: 'Project request from the configurator', body: 'Hello George,\n\nI configured a project on georgeai.dev:\n\nServices: %s\nScale: %S\nAdd-ons: %a\nEstimated timeline: %t weeks\nComplexity: %c\n\nMy notes:\n%n\n\nName: %N\nEmail: %E\n' },
    de: { weeks: 'Wochen', low: 'Niedrig', medium: 'Mittel', high: 'Hoch', none: 'Wählen Sie mindestens eine Leistung, um einen Zeitplan zu sehen.', subject: 'Projektanfrage aus dem Konfigurator', body: 'Hallo George,\n\nich habe auf georgeai.dev ein Projekt konfiguriert:\n\nLeistungen: %s\nUmfang: %S\nZusätze: %a\nGeschätzter Zeitrahmen: %t Wochen\nKomplexität: %c\n\nMeine Notizen:\n%n\n\nName: %N\nE-Mail: %E\n' },
    fr: { weeks: 'semaines', low: 'Faible', medium: 'Moyenne', high: 'Élevée', none: 'Choisissez au moins un service pour voir un calendrier.', subject: 'Demande de projet depuis le configurateur', body: 'Bonjour George,\n\nJ\'ai configuré un projet sur georgeai.dev :\n\nServices : %s\nÉchelle : %S\nOptions : %a\nDélai estimé : %t semaines\nComplexité : %c\n\nMes notes :\n%n\n\nNom : %N\nE-mail : %E\n' },
    ro: { weeks: 'săptămâni', low: 'Scăzută', medium: 'Medie', high: 'Ridicată', none: 'Alegeți cel puțin un serviciu ca să vedeți un calendar.', subject: 'Cerere de proiect din configurator', body: 'Bună George,\n\nAm configurat un proiect pe georgeai.dev:\n\nServicii: %s\nScară: %S\nExtra: %a\nTermen estimat: %t săptămâni\nComplexitate: %c\n\nNotele mele:\n%n\n\nNume: %N\nE-mail: %E\n' },
    ar: { weeks: 'أسابيع', low: 'منخفضة', medium: 'متوسطة', high: 'عالية', none: 'اختر خدمة واحدة على الأقل لعرض الجدول الزمني.', subject: 'طلب مشروع من المُهيّئ', body: 'مرحبًا جورج،\n\nقمت بتهيئة مشروع على georgeai.dev:\n\nالخدمات: %s\nالنطاق: %S\nالإضافات: %a\nالمدة المقدرة: %t أسابيع\nالتعقيد: %c\n\nملاحظاتي:\n%n\n\nالاسم: %N\nالبريد: %E\n' },
  }[L] || {};
  const out = { weeks: $('#cfg-weeks'), cx: $('#cfg-cx'), list: $('#cfg-list'), count: $('#cfg-count'), submit: $('#cfg-submit'), empty: $('#cfg-empty') };
  function calc() {
    const svc = $$('input[name="svc"]:checked', root).map(i => i.parentElement.querySelector('span').textContent.trim());
    const scaleEl = $('input[name="scale"]:checked', root);
    const scaleIdx = +scaleEl.dataset.index, base = +scaleEl.dataset.weeks, scale = scaleEl.parentElement.querySelector('b').textContent.trim();
    const addons = $$('input[name="addon"]:checked', root).map(i => i.parentElement.querySelector('span').textContent.trim());
    const n = svc.length;
    const min = base + n, max = min + Math.ceil(min * 0.4);
    const score = n + scaleIdx * 2, cx = score <= 3 ? T.low : score <= 7 ? T.medium : T.high;
    out.count.textContent = n;
    out.empty.hidden = n > 0; out.weeks.parentElement.hidden = n === 0; out.cx.parentElement.hidden = n === 0;
    out.weeks.textContent = n ? `${min} – ${max} ${T.weeks}` : '';
    out.cx.textContent = n ? cx : ''; out.cx.dataset.level = n ? (score <= 3 ? 'low' : score <= 7 ? 'medium' : 'high') : '';
    out.list.innerHTML = svc.map(s => `<li>${s}</li>`).join('');
    out.submit.disabled = n === 0;
    return { svc, scale, addons, min, max, cx };
  }
  root.addEventListener('change', calc);
  root.addEventListener('submit', e => {
    e.preventDefault();
    const r = calc(); if (!r.svc.length) return;
    const name = $('#cfg-name').value.trim(), email = $('#cfg-email').value.trim(), notes = $('#cfg-notes').value.trim();
    const body = T.body.replace('%s', r.svc.join(', ')).replace('%S', r.scale).replace('%a', r.addons.join(', ') || '-').replace('%t', `${r.min}-${r.max}`).replace('%c', r.cx).replace('%n', notes || '-').replace('%N', name || '-').replace('%E', email || '-');
    location.href = 'mailto:contact@GeorgeAI.dev?subject=' + encodeURIComponent(T.subject) + '&body=' + encodeURIComponent(body);
    $('#cfg-done').hidden = false;
  });
  // prefill from the account, when signed in
  fetch('/api/auth/me', { credentials: 'same-origin' }).then(r => r.ok ? r.json() : null).then(d => {
    const u = d && (d.user || d); if (!u || !u.email) return;
    if (!$('#cfg-email').value) $('#cfg-email').value = u.email; if (!$('#cfg-name').value && u.name) $('#cfg-name').value = u.name;
  }).catch(() => {});
  calc();
})();
