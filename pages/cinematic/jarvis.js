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
  function render() {
    set('lights', state.lights, state.lights ? 'On' : 'Off');
    set('fan', state.fan, state.fan ? 'On' : 'Off');
    set('music', state.music, state.music ? 'Playing' : 'Paused');
    set('temp', true, state.temp + '°C');
    const s = devEl('security'); s.classList.toggle('alert', state.security); s.classList.toggle('on', false);
    $('.val', s).textContent = state.security ? 'Armed' : 'Disarmed';
    set('calendar', !!state.calendar, state.calendar || 'None');
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
    const tag = document.createElement('span'); tag.className = 'mono'; tag.textContent = who === 'you' ? 'You' : 'Jarvis';
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
      const u = new SpeechSynthesisUtterance(text); u.lang = 'en-GB'; u.rate = 1.02; u.pitch = .9;
      const v = speechSynthesis.getVoices().find(v => /en-GB|en_GB/.test(v.lang) && /Daniel|Google UK English Male|Arthur/.test(v.name)) || speechSynthesis.getVoices().find(v => /en-GB/.test(v.lang));
      if (v) u.voice = v;
      u.onstart = () => { level = .9; root.classList.add('thinking'); }; u.onend = u.onerror = () => { level = .15; root.classList.remove('thinking'); };
      speechSynthesis.speak(u);
    } catch (_) { voiceOn = false; }
  }

  /* ---------- the brain (rule-based) ---------- */
  const rx = (s, ...alts) => alts.some(a => a.test(s));
  function understand(raw) {
    const s = raw.toLowerCase().replace(/hey jarvis[,.]?\s*/, '').trim();
    if (!s) return 'Say it again, Sir. I did not catch that.';
    const on = /\b(on|start|enable|activate|switch on|turn on)\b/.test(s), off = /\b(off|stop|disable|deactivate|switch off|turn off)\b/.test(s);
    if (/light/.test(s)) { state.lights = on || !off && !state.lights; return state.lights ? 'Sure, Sir. Turning on the lights.' : 'Lights off. Enjoy the dark.'; }
    if (/\bfan\b|air/.test(s)) { state.fan = on || !off && !state.fan; return state.fan ? 'Fan is on.' : 'Fan is off.'; }
    if (/music|song|play|spotify/.test(s)) { state.music = !/stop|pause|off/.test(s); return state.music ? 'Playing something calm. Focus mode.' : 'Music paused.'; }
    const deg = s.match(/(-?\d{1,2})\s*(°|degrees|grad|c\b)?/);
    if (/temp|degree|warm|cold|heat|cool/.test(s)) {
      if (deg && /temp|degree|°|set/.test(s)) state.temp = Math.max(15, Math.min(28, +deg[1]));
      else if (/warm|heat|up/.test(s)) state.temp = Math.min(28, state.temp + 1);
      else if (/cold|cool|down/.test(s)) state.temp = Math.max(15, state.temp - 1);
      return `Temperature set to ${state.temp} degrees.`;
    }
    if (/secur|alarm|lock|arm/.test(s)) { state.security = !/dis|off|unlock|open/.test(s); return state.security ? 'Security armed. All doors locked.' : 'Security disarmed. Welcome back, Sir.'; }
    if (/book|schedule|meeting|call|appointment|remind|calendar/.test(s)) {
      const day = (s.match(/\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday|tomorrow|today)\b/) || [])[1];
      const time = (s.match(/\b(\d{1,2})(?::(\d{2}))?\s*(am|pm|o'clock|uhr)?\b/) || []);
      const when = [day ? day[0].toUpperCase() + day.slice(1) : 'Tomorrow', time[1] ? `${time[1].padStart(2, '0')}:${time[2] || '00'}` : '10:00'].join(' ');
      state.calendar = when; return `Booked. ${when}, thirty minutes, invite sent. Anything else?`;
    }
    if (/status|report|how (are|is)|everything/.test(s)) {
      const onList = ['lights', 'fan', 'music', 'security'].filter(k => state[k]).map(k => k === 'security' ? 'security armed' : k + ' on');
      return `All systems operational. ${state.temp} degrees. ${onList.length ? onList.join(', ') + '.' : 'Everything is off.'} ${state.calendar ? 'Next meeting ' + state.calendar + '.' : 'Calendar is clear.'}`;
    }
    if (/time|clock/.test(s)) return `It is ${clock.textContent}.`;
    if (/who are you|what are you|your name/.test(s)) return 'A demo of the assistant GeorgeAI builds for businesses. The real one answers phones, books jobs and never sleeps.';
    if (/price|cost|how much|package/.test(s)) return 'Fixed prices. The phone assistant is 690 euros a month plus setup. Full list on the pricing page.';
    if (/thank/.test(s)) return 'Always, Sir.';
    if (/hello|hi\b|hey\b|good (morning|evening|afternoon)/.test(s)) return 'Good to see you. What shall we automate today?';
    return 'I can control lights, fan, music, temperature and security, book meetings, or report status. Try "turn on the lights".';
  }

  let busy = false;
  async function handle(text) {
    if (busy || !text.trim()) return; busy = true;
    await say(text.trim(), 'you');
    root.classList.add('thinking'); level = .5;
    const t0 = performance.now();
    await new Promise(r => setTimeout(r, rmq.matches ? 0 : 420 + Math.random() * 380));
    // several orders in one breath: "set 24 degrees and book Tuesday at 10"
    const parts = text.split(/\s+(?:and then|and also|and|then)\s+|;\s*/i).filter(p => p.trim());
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
      rec = new SR(); rec.lang = 'en-GB'; rec.interimResults = true; rec.maxAlternatives = 1;
      rec.onstart = () => { listening = true; mic.setAttribute('aria-pressed', 'true'); root.classList.add('listening'); level = 1; input.placeholder = 'Listening…'; };
      rec.onresult = e => { const r = e.results[e.results.length - 1]; input.value = r[0].transcript; if (r.isFinal) { const v = input.value; input.value = ''; handle(v); } };
      rec.onerror = () => { say('Microphone not available here. Type instead.', 'ai'); };
      rec.onend = () => { listening = false; mic.setAttribute('aria-pressed', 'false'); root.classList.remove('listening'); level = .15; input.placeholder = 'Hey Jarvis, turn on the lights'; };
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
  const greet = () => say('Online. All systems operational. Type a command or pick one below.', 'ai');
  const io = new IntersectionObserver(([e]) => { if (e.isIntersecting) { greet(); io.disconnect(); } }, { threshold: .3 });
  io.observe(root);
})();
