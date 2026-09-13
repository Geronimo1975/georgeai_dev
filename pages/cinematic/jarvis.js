/* Jarvis-style assistant demo. Runs entirely in the browser: a small intent parser drives a live
   device panel, speaks back with speechSynthesis, and listens with webkitSpeechRecognition where
   available. ponytail: rule-based intents; swap `understand()` for a fetch to the n8n webhook when
   the real assistant goes live. */
(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const root = $('#jarvis'); if (!root) return;
  const log = $('#transcript'), form = $('#ask'), input = $('#q'), mic = $('#mic'), wave = $('#wave'), lat = $('#lat');
  const rmq = matchMedia('(prefers-reduced-motion: reduce)');

  /* ---------- state ---------- */
  const state = { lights: false, fan: false, music: false, temp: 21, security: false, calendar: null };
  const devEl = n => $(`.dev[data-dev="${n}"]`);
  const V = { en: ['On', 'Off', 'Playing', 'Paused', 'Armed', 'Disarmed', 'None'], de: ['An', 'Aus', 'Läuft', 'Pausiert', 'Scharf', 'Deaktiviert', 'Keiner'], fr: ['Allumé', 'Éteint', 'En lecture', 'En pause', 'Armée', 'Désarmée', 'Aucun'], ro: ['Pornit', 'Oprit', 'Redă', 'Pauză', 'Armată', 'Dezarmată', 'Niciuna'], ar: ['يعمل', 'متوقف', 'تعمل', 'متوقفة', 'مفعّل', 'معطّل', 'لا شيء'] }[(document.documentElement.lang || 'en').slice(0, 2)] || ['On', 'Off', 'Playing', 'Paused', 'Armed', 'Disarmed', 'None'];
  function render() {
    set('lights', state.lights, state.lights ? V[0] : V[1]);
    set('fan', state.fan, state.fan ? V[0] : V[1]);
    set('music', state.music, state.music ? V[2] : V[3]);
    set('temp', true, state.temp + '°C');
    const s = devEl('security'); s.classList.toggle('alert', state.security); s.classList.toggle('on', false);
    $('.val', s).textContent = state.security ? V[4] : V[5];
    set('calendar', !!state.calendar, state.calendar || V[6]);
  }
  function set(n, on, val) { const el = devEl(n); if (!el) return; el.classList.toggle('on', on); const v = $('.val', el); if (v.textContent !== val) v.textContent = val; }

  /* ---------- waveform (whisper level, louder while listening/speaking) ---------- */
  const bars = []; for (let i = 0; i < 28; i++) { const b = document.createElement('i'); wave.appendChild(b); bars.push(b); }
  let level = 0.15, wRaf = null, t0 = performance.now();
  function waveTick(now) {
    const t = (now - t0) / 1000;
    bars.forEach((b, i) => { const h = 4 + Math.abs(Math.sin(t * 3 + i * .55) * Math.cos(t * 1.3 + i * .2)) * 28 * level; b.style.height = h.toFixed(1) + 'px'; });
    wRaf = document.hidden || rmq.matches ? null : requestAnimationFrame(waveTick);
  }
  if (!rmq.matches) wRaf = requestAnimationFrame(waveTick);
  document.addEventListener('visibilitychange', () => { if (!document.hidden && wRaf === null && !rmq.matches) wRaf = requestAnimationFrame(waveTick); });

  /* ---------- clock ---------- */
  const clock = $('#clock');
  const tickClock = () => { clock.textContent = new Date().toLocaleTimeString('de-DE', { hour: '2-digit', minute: '2-digit' }); };
  tickClock(); setInterval(tickClock, 15000);

  /* ---------- transcript ---------- */
  function say(text, who) {
    const m = document.createElement('div'); m.className = 'msg ' + who;
    const tag = document.createElement('span'); tag.className = 'mono'; tag.textContent = who === 'you' ? ({ en: 'You', de: 'Sie', fr: 'Vous', ro: 'Dvs.', ar: 'أنت' }[L]) : 'Jarvis';
    const body = document.createElement('span'); m.append(tag, body); log.appendChild(m);
    log.scrollTop = log.scrollHeight;
    if (who === 'you' || rmq.matches) { body.textContent = text; return Promise.resolve(); }
    return new Promise(res => { let i = 0; const step = () => { body.textContent = text.slice(0, ++i); log.scrollTop = log.scrollHeight; if (i < text.length) setTimeout(step, 14); else res(); }; step(); });
  }

  /* ---------- voice out ---------- */
  let voiceOn = 'speechSynthesis' in window;
  function speak(text) {
    if (!voiceOn) return;
    try {
      speechSynthesis.cancel();
      const VL = { en: 'en-GB', de: 'de-DE', fr: 'fr-FR', ro: 'ro-RO', ar: 'ar-SA' }[L];
      const u = new SpeechSynthesisUtterance(text); u.lang = VL; u.rate = 1.02; u.pitch = .9;
      const vs = speechSynthesis.getVoices().filter(v => v.lang.replace('_', '-').startsWith(VL.slice(0, 2)));
      const v = vs.find(v => /Daniel|Arthur|Google UK English Male|Markus|Thomas|Andrei|Majed/.test(v.name)) || vs[0];
      if (v) u.voice = v;
      u.onstart = () => { level = .9; root.classList.add('thinking'); }; u.onend = u.onerror = () => { level = .15; root.classList.remove('thinking'); };
      speechSynthesis.speak(u);
    } catch (_) { voiceOn = false; }
  }

  /* ---------- the brain (rule-based, five languages) ---------- */
  const LANG = (document.documentElement.lang || 'en').slice(0, 2);
  const L = ['en', 'de', 'fr', 'ro', 'ar'].includes(LANG) ? LANG : 'en';
  // keyword families shared across languages (accent-insensitive: input is folded below)
  const K = {
    on: /\b(on|an|ein|einschalten|mach|allume|allumer|activer|aprinde|porneste|deschide|شغل|فعل)\b/,
    off: /\b(off|aus|ausschalten|eteins|eteindre|desactiver|stinge|opreste|inchide|اطفئ|أطفئ|اوقف|أوقف)\b/,
    light: /light|licht|lumi|lampe|lampa|ضوء|اضاءة|إضاءة|النور/,
    fan: /\bfan\b|air|luft|ventil|مروحة|هواء/,
    music: /music|musik|musique|muzic|song|lied|chanson|play|spiel|joue|canta|cânta|موسيقى|شغل اغنية/,
    temp: /temp|grad|degr|degre|warm|kalt|cold|froid|chaud|heat|heiz|cool|frig|cald|rece|حرارة|درجة|دفئ|برد/,
    security: /secur|alarm|lock|arm|sicher|verriegel|schloss|serrure|incuie|încuie|امان|أمان|انذار|إنذار|اقفل|أقفل/,
    disarm: /\b(dis|off|unlock|open|aus|entsch|deaktiv|desactiv|desarm|dezarm|descuie|deschide|الغ|ألغ|افتح)\b/,
    book: /book|schedule|meeting|call|appointment|remind|calendar|termin|buch|besprech|anruf|erinner|kalender|reserv|rendez|reunion|appel|programe|programa|intalnir|întâlnir|calendar|احجز|موعد|اجتماع|مكالمة|ذكرني/,
    status: /status|report|how (are|is)|everything|bericht|wie geht|alles|etat|état|rapport|tout|stare|raport|cum (e|este)|totul|الحالة|تقرير|كل شيء/,
    time: /\btime\b|clock|uhr|zeit|heure|\bora\b|ceas|الوقت|الساعة/,
    who: /who are you|what are you|your name|wer bist|was bist|dein name|qui es|que es|ton nom|cine esti|cine ești|ce esti|من انت|من أنت|ما اسمك/,
    price: /price|cost|how much|package|preis|kost|wie viel|paket|prix|combien|offre|pret|preț|cat costa|cât costă|pachet|سعر|تكلف|كم|باقة/,
    thanks: /thank|dank|merci|multumesc|mulțumesc|mersi|شكر/,
    hello: /hello|\bhi\b|\bhey\b|good (morning|evening|afternoon)|hallo|guten|moin|bonjour|salut|bonsoir|buna|bună|مرحبا|اهلا|أهلا|صباح|مساء/,
    stop: /stop|pause|off|aus|arret|arrêt|opreste|oprește|اوقف|أوقف/,
    up: /warm|heat|up|hoch|waerm|chaud|plus|cald|mai mult|ادفأ|أدفأ|ارفع/,
    down: /cold|cool|down|runter|kalt|kuhl|froid|moins|rece|mai putin|ابرد|أبرد|اخفض/,
  };
  const DAYS = {
    en: ['monday','tuesday','wednesday','thursday','friday','saturday','sunday','tomorrow','today'],
    de: ['montag','dienstag','mittwoch','donnerstag','freitag','samstag','sonntag','morgen','heute'],
    fr: ['lundi','mardi','mercredi','jeudi','vendredi','samedi','dimanche','demain',"aujourd'hui"],
    ro: ['luni','marti','miercuri','joi','vineri','sambata','duminica','maine','azi'],
    ar: ['الاثنين','الثلاثاء','الاربعاء','الخميس','الجمعة','السبت','الاحد','غدا','اليوم'],
  };
  const R = {
    en: { empty: 'Say it again, Sir. I did not catch that.', lightsOn: 'Sure, Sir. Turning on the lights.', lightsOff: 'Lights off. Enjoy the dark.', fanOn: 'Fan is on.', fanOff: 'Fan is off.', musicOn: 'Playing something calm. Focus mode.', musicOff: 'Music paused.', temp: t => `Temperature set to ${t} degrees.`, armed: 'Security armed. All doors locked.', disarmed: 'Security disarmed. Welcome back, Sir.', booked: w => `Booked. ${w}, thirty minutes, invite sent. Anything else?`, status: (t, on, cal) => `All systems operational. ${t} degrees. ${on.length ? on.join(', ') + '.' : 'Everything is off.'} ${cal ? 'Next meeting ' + cal + '.' : 'Calendar is clear.'}`, time: t => `It is ${t}.`, who: 'A demo of the assistant GeorgeAI builds for businesses. The real one answers phones, books jobs and never sleeps.', price: 'Fixed prices. The phone assistant is 690 euros a month plus setup. Full list on the pricing page.', thanks: 'Always, Sir.', hello: 'Good to see you. What shall we automate today?', fallback: 'I can control lights, fan, music, temperature and security, book meetings, or report status. Try "turn on the lights".', greet: 'Online. All systems operational. Type a command or pick one below.', listening: 'Listening', placeholder: 'Hey Jarvis, turn on the lights', micErr: 'Microphone not available here. Type instead.', names: { lights: 'lights on', fan: 'fan on', music: 'music on', security: 'security armed' }, tomorrow: 'Tomorrow' },
    de: { empty: 'Bitte noch einmal. Das habe ich nicht verstanden.', lightsOn: 'Gern. Ich schalte das Licht ein.', lightsOff: 'Licht aus.', fanOn: 'Lüfter ist an.', fanOff: 'Lüfter ist aus.', musicOn: 'Ich spiele etwas Ruhiges. Fokus-Modus.', musicOff: 'Musik pausiert.', temp: t => `Temperatur auf ${t} Grad gesetzt.`, armed: 'Sicherheit scharf. Alle Türen verriegelt.', disarmed: 'Sicherheit deaktiviert. Willkommen zurück.', booked: w => `Gebucht. ${w}, dreißig Minuten, Einladung verschickt. Noch etwas?`, status: (t, on, cal) => `Alle Systeme laufen. ${t} Grad. ${on.length ? on.join(', ') + '.' : 'Alles ist aus.'} ${cal ? 'Nächster Termin ' + cal + '.' : 'Der Kalender ist frei.'}`, time: t => `Es ist ${t} Uhr.`, who: 'Eine Demo des Assistenten, den GeorgeAI für Unternehmen baut. Der echte geht ans Telefon, bucht Aufträge und schläft nie.', price: 'Festpreise. Der Telefonassistent kostet 690 Euro im Monat plus Einrichtung. Die ganze Liste steht auf der Preisseite.', thanks: 'Immer gern.', hello: 'Schön, Sie zu sehen. Was automatisieren wir heute?', fallback: 'Ich steuere Licht, Lüfter, Musik, Temperatur und Sicherheit, buche Termine oder melde den Status. Versuchen Sie „mach das Licht an“.', greet: 'Online. Alle Systeme laufen. Tippen Sie einen Befehl oder wählen Sie unten einen aus.', listening: 'Ich höre', placeholder: 'Hey Jarvis, mach das Licht an', micErr: 'Mikrofon hier nicht verfügbar. Bitte tippen.', names: { lights: 'Licht an', fan: 'Lüfter an', music: 'Musik an', security: 'Sicherheit scharf' }, tomorrow: 'Morgen' },
    fr: { empty: 'Répétez, je vous prie. Je n\'ai pas compris.', lightsOn: 'Bien sûr. J\'allume les lumières.', lightsOff: 'Lumières éteintes.', fanOn: 'Ventilateur allumé.', fanOff: 'Ventilateur éteint.', musicOn: 'Je lance quelque chose de calme. Mode concentration.', musicOff: 'Musique en pause.', temp: t => `Température réglée à ${t} degrés.`, armed: 'Sécurité armée. Toutes les portes verrouillées.', disarmed: 'Sécurité désarmée. Bon retour.', booked: w => `Réservé. ${w}, trente minutes, invitation envoyée. Autre chose ?`, status: (t, on, cal) => `Tous les systèmes fonctionnent. ${t} degrés. ${on.length ? on.join(', ') + '.' : 'Tout est éteint.'} ${cal ? 'Prochain rendez-vous ' + cal + '.' : 'L\'agenda est libre.'}`, time: t => `Il est ${t}.`, who: 'Une démo de l\'assistant que GeorgeAI construit pour les entreprises. Le vrai répond au téléphone, réserve les interventions et ne dort jamais.', price: 'Prix fixes. L\'assistant téléphonique coûte 690 euros par mois plus la mise en place. La liste complète est sur la page tarifs.', thanks: 'Toujours.', hello: 'Ravi de vous voir. Qu\'automatisons-nous aujourd\'hui ?', fallback: 'Je contrôle les lumières, le ventilateur, la musique, la température et la sécurité, je réserve des réunions ou je donne le statut. Essayez « allume les lumières ».', greet: 'En ligne. Tous les systèmes fonctionnent. Tapez une commande ou choisissez-en une ci-dessous.', listening: 'J\'écoute', placeholder: 'Hey Jarvis, allume les lumières', micErr: 'Micro indisponible ici. Tapez plutôt.', names: { lights: 'lumières allumées', fan: 'ventilateur allumé', music: 'musique en cours', security: 'sécurité armée' }, tomorrow: 'Demain' },
    ro: { empty: 'Repetați, vă rog. Nu am înțeles.', lightsOn: 'Sigur. Aprind lumina.', lightsOff: 'Lumina stinsă.', fanOn: 'Ventilatorul e pornit.', fanOff: 'Ventilatorul e oprit.', musicOn: 'Pun ceva liniștit. Mod concentrare.', musicOff: 'Muzica e pe pauză.', temp: t => `Temperatura setată la ${t} grade.`, armed: 'Securitate armată. Toate ușile încuiate.', disarmed: 'Securitate dezarmată. Bine ați revenit.', booked: w => `Programat. ${w}, treizeci de minute, invitația e trimisă. Altceva?`, status: (t, on, cal) => `Toate sistemele funcționează. ${t} grade. ${on.length ? on.join(', ') + '.' : 'Totul e oprit.'} ${cal ? 'Următoarea întâlnire ' + cal + '.' : 'Calendarul e liber.'}`, time: t => `Este ora ${t}.`, who: 'Un demo al asistentului pe care GeorgeAI îl construiește pentru firme. Cel real răspunde la telefon, programează lucrări și nu doarme niciodată.', price: 'Prețuri fixe. Asistentul telefonic costă 690 de euro pe lună plus configurarea. Lista completă e pe pagina de prețuri.', thanks: 'Oricând.', hello: 'Mă bucur să vă văd. Ce automatizăm azi?', fallback: 'Pot controla lumina, ventilatorul, muzica, temperatura și securitatea, pot programa întâlniri sau raporta starea. Încercați „aprinde lumina”.', greet: 'Online. Toate sistemele funcționează. Scrieți o comandă sau alegeți una de mai jos.', listening: 'Ascult', placeholder: 'Hey Jarvis, aprinde lumina', micErr: 'Microfonul nu e disponibil aici. Scrieți în schimb.', names: { lights: 'lumina aprinsă', fan: 'ventilator pornit', music: 'muzică pornită', security: 'securitate armată' }, tomorrow: 'Mâine' },
    ar: { empty: 'أعد من فضلك. لم أفهم ذلك.', lightsOn: 'بالتأكيد. أشغّل الإضاءة.', lightsOff: 'أُطفئت الإضاءة.', fanOn: 'المروحة تعمل.', fanOff: 'المروحة متوقفة.', musicOn: 'أشغّل شيئًا هادئًا. وضع التركيز.', musicOff: 'الموسيقى متوقفة مؤقتًا.', temp: t => `ضُبطت الحرارة على ${t} درجة.`, armed: 'الأمان مفعّل. كل الأبواب مقفلة.', disarmed: 'الأمان معطّل. أهلًا بعودتك.', booked: w => `تم الحجز. ${w}، ثلاثون دقيقة، أُرسلت الدعوة. هل من شيء آخر؟`, status: (t, on, cal) => `كل الأنظمة تعمل. ${t} درجة. ${on.length ? on.join('، ') + '.' : 'كل شيء متوقف.'} ${cal ? 'الاجتماع التالي ' + cal + '.' : 'التقويم فارغ.'}`, time: t => `الساعة الآن ${t}.`, who: 'عرض للمساعد الذي يبنيه GeorgeAI للشركات. النسخة الحقيقية ترد على الهاتف وتحجز الأعمال ولا تنام أبدًا.', price: 'أسعار ثابتة. المساعد الهاتفي بـ 690 يورو شهريًا زائد الإعداد. القائمة الكاملة في صفحة الأسعار.', thanks: 'دائمًا في الخدمة.', hello: 'سعيد برؤيتك. ماذا نؤتمت اليوم؟', fallback: 'أستطيع التحكم بالإضاءة والمروحة والموسيقى والحرارة والأمان، وحجز الاجتماعات، أو عرض الحالة. جرّب «شغّل الإضاءة».', greet: 'متصل. كل الأنظمة تعمل. اكتب أمرًا أو اختر واحدًا أدناه.', listening: 'أستمع', placeholder: 'يا جارفيس، شغّل الإضاءة', micErr: 'الميكروفون غير متاح هنا. اكتب بدلًا من ذلك.', names: { lights: 'الإضاءة مشغّلة', fan: 'المروحة تعمل', music: 'الموسيقى تعمل', security: 'الأمان مفعّل' }, tomorrow: 'غدًا' },
  }[L];
  const fold = s => s.toLowerCase().normalize('NFD').replace(/[\u0300-\u036f\u064b-\u065f\u0670]/g, '').replace(/[إأآ]/g, 'ا').replace(/(hey |يا )?jarvis[,.]?\s*|جارفيس[،,.]?\s*/g, '').trim();
  function understand(raw) {
    const s = fold(raw);
    if (!s) return R.empty;
    const on = K.on.test(s), off = K.off.test(s);
    if (K.light.test(s)) { state.lights = on || !off && !state.lights; return state.lights ? R.lightsOn : R.lightsOff; }
    if (K.fan.test(s)) { state.fan = on || !off && !state.fan; return state.fan ? R.fanOn : R.fanOff; }
    if (K.music.test(s)) { state.music = !K.stop.test(s); return state.music ? R.musicOn : R.musicOff; }
    const deg = s.match(/(-?\d{1,2})\s*(°|degrees|grad|degr|درجة|c\b)?/);
    if (K.temp.test(s)) {
      if (deg) state.temp = Math.max(15, Math.min(28, +deg[1]));
      else if (K.up.test(s)) state.temp = Math.min(28, state.temp + 1);
      else if (K.down.test(s)) state.temp = Math.max(15, state.temp - 1);
      return R.temp(state.temp);
    }
    if (K.security.test(s)) { state.security = !K.disarm.test(s); return state.security ? R.armed : R.disarmed; }
    if (K.book.test(s)) {
      const day = DAYS[L].concat(DAYS.en).find(d => s.includes(fold(d)));
      const time = (s.match(/\b(\d{1,2})(?::(\d{2}))?\s*(am|pm|o'clock|uhr|h)?\b/) || []);
      const when = [day ? day[0].toUpperCase() + day.slice(1) : R.tomorrow, time[1] ? `${time[1].padStart(2, '0')}:${time[2] || '00'}` : '10:00'].join(' ');
      state.calendar = when; return R.booked(when);
    }
    if (K.status.test(s)) return R.status(state.temp, ['lights', 'fan', 'music', 'security'].filter(k => state[k]).map(k => R.names[k]), state.calendar);
    if (K.time.test(s)) return R.time(clock.textContent);
    if (K.who.test(s)) return R.who;
    if (K.price.test(s)) return R.price;
    if (K.thanks.test(s)) return R.thanks;
    if (K.hello.test(s)) return R.hello;
    return R.fallback;
  }

  let busy = false;
  async function handle(text) {
    if (busy || !text.trim()) return; busy = true;
    await say(text.trim(), 'you');
    root.classList.add('thinking'); level = .5;
    const t0 = performance.now();
    await new Promise(r => setTimeout(r, rmq.matches ? 0 : 420 + Math.random() * 380));
    // several orders in one breath: "set 24 degrees and book Tuesday at 10"
    const parts = text.split(/\s+(?:and then|and also|and|then|und dann|und|dann|et puis|et|puis|si apoi|și apoi|si|și|apoi|ثم)\s+|\s+و(?=\S)|;\s*/i).filter(p => p.trim());
    const reply = (parts.length > 1 ? parts.map(understand) : [understand(text)]).join(' ');
    lat.textContent = Math.round(performance.now() - t0) + ' ms';
    render();
    speak(reply);
    await say(reply, 'ai');
    root.classList.remove('thinking'); if (!speechSynthesis?.speaking) level = .15;
    busy = false;
  }

  form.addEventListener('submit', e => { e.preventDefault(); const v = input.value; input.value = ''; handle(v); });
  document.querySelectorAll('.chip').forEach(c => c.addEventListener('click', () => handle(c.dataset.say)));

  /* ---------- voice in (Chrome, Safari, Edge) ---------- */
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (SR) {
    mic.hidden = false;
    let rec = null, listening = false;
    mic.addEventListener('click', () => {
      if (listening) { rec && rec.stop(); return; }
      rec = new SR(); rec.lang = { en: 'en-GB', de: 'de-DE', fr: 'fr-FR', ro: 'ro-RO', ar: 'ar-SA' }[L]; rec.interimResults = true; rec.maxAlternatives = 1;
      rec.onstart = () => { listening = true; mic.setAttribute('aria-pressed', 'true'); root.classList.add('listening'); level = 1; input.placeholder = R.listening + '…'; };
      rec.onresult = e => { const r = e.results[e.results.length - 1]; input.value = r[0].transcript; if (r.isFinal) { const v = input.value; input.value = ''; handle(v); } };
      rec.onerror = () => { say(R.micErr, 'ai'); };
      rec.onend = () => { listening = false; mic.setAttribute('aria-pressed', 'false'); root.classList.remove('listening'); level = .15; input.placeholder = R.placeholder; };
      try { rec.start(); } catch (_) { rec.onend(); }
    });
  }

  /* ---------- the command room: globe (globe.js) + ticking tiles ---------- */
  if (window.mountGlobe) mountGlobe($('#globe'));
  // tiles that tick upward like a live counter
  document.querySelectorAll('[data-tick]').forEach(el => {
    let v = +el.dataset.tick; const rate = +el.dataset.rate;
    if (rmq.matches) return;
    setInterval(() => { if (Math.random() < rate) { v++; el.textContent = v.toLocaleString('en-US'); el.animate([{ color: '#19c39a' }, { color: '#fff' }], { duration: 900 }); } }, 1000);
  });

  /* ---------- opening line ---------- */
  render();
  const greet = () => say(R.greet, 'ai');
  const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { greet(); io.disconnect(); } }, { threshold: .3 });
  io.observe(root);
})();
