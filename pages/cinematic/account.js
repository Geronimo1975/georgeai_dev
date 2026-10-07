/* Account page: sign up, log in, log out against the Django session API (/api/auth/*).
   The csrftoken cookie is planted by GET /api/auth/me; every POST echoes it as X-CSRFToken. */
(() => {
  'use strict';
  const $ = (s, r = document) => r.querySelector(s);
  const page = $('#account'); if (!page) return;
  const L = (document.documentElement.lang || 'en').slice(0, 2);
  const T = {
    en: { hi: n => `Signed in as ${n}.`, out: 'You are signed out.', email_taken: 'That email already has an account. Log in instead.', weak_password: 'Pick a longer password (8+ characters, not only numbers).', invalid_credentials: 'Email or password is wrong.', email_and_password_required: 'Email and password are required.', throttled: 'Too many attempts. Wait a minute and try again.', offline: 'The account service is not reachable right now. Try again in a moment.', generic: 'Something went wrong. Try again.' },
    de: { hi: n => `Angemeldet als ${n}.`, out: 'Sie sind abgemeldet.', email_taken: 'Für diese E-Mail gibt es schon ein Konto. Bitte anmelden.', weak_password: 'Wählen Sie ein längeres Passwort (8+ Zeichen, nicht nur Ziffern).', invalid_credentials: 'E-Mail oder Passwort ist falsch.', email_and_password_required: 'E-Mail und Passwort sind erforderlich.', throttled: 'Zu viele Versuche. Bitte eine Minute warten.', offline: 'Der Kontodienst ist gerade nicht erreichbar. Bitte gleich noch einmal versuchen.', generic: 'Etwas ist schiefgelaufen. Bitte erneut versuchen.' },
    fr: { hi: n => `Connecté en tant que ${n}.`, out: 'Vous êtes déconnecté.', email_taken: 'Cet e-mail a déjà un compte. Connectez-vous.', weak_password: 'Choisissez un mot de passe plus long (8+ caractères, pas seulement des chiffres).', invalid_credentials: 'E-mail ou mot de passe incorrect.', email_and_password_required: 'E-mail et mot de passe requis.', throttled: 'Trop de tentatives. Attendez une minute.', offline: 'Le service de compte est indisponible pour le moment. Réessayez dans un instant.', generic: 'Une erreur est survenue. Réessayez.' },
    ro: { hi: n => `Autentificat ca ${n}.`, out: 'Sunteți deconectat.', email_taken: 'Acest e-mail are deja un cont. Autentificați-vă.', weak_password: 'Alegeți o parolă mai lungă (8+ caractere, nu doar cifre).', invalid_credentials: 'E-mail sau parolă greșită.', email_and_password_required: 'E-mailul și parola sunt obligatorii.', throttled: 'Prea multe încercări. Așteptați un minut.', offline: 'Serviciul de cont nu răspunde acum. Încercați din nou imediat.', generic: 'Ceva nu a mers. Încercați din nou.' },
    ar: { hi: n => `مسجّل الدخول باسم ${n}.`, out: 'تم تسجيل خروجك.', email_taken: 'هذا البريد لديه حساب بالفعل. سجّل الدخول بدلًا من ذلك.', weak_password: 'اختر كلمة مرور أطول (8 أحرف أو أكثر، وليس أرقامًا فقط).', invalid_credentials: 'البريد أو كلمة المرور غير صحيحة.', email_and_password_required: 'البريد وكلمة المرور مطلوبان.', throttled: 'محاولات كثيرة. انتظر دقيقة ثم أعد المحاولة.', offline: 'خدمة الحساب غير متاحة الآن. حاول بعد قليل.', generic: 'حدث خطأ ما. حاول مرة أخرى.' },
  }[L] || {};
  const cookie = n => (document.cookie.match('(?:^|; )' + n + '=([^;]*)') || [])[1] || '';
  const api = (path, body) => fetch('/api/auth/' + path, { method: body ? 'POST' : 'GET', credentials: 'same-origin', headers: body ? { 'Content-Type': 'application/json', 'X-CSRFToken': cookie('csrftoken') } : {}, body: body ? JSON.stringify(body) : undefined });
  const forms = { login: $('#login'), signup: $('#signup') }, signed = $('#signed'), who = $('#who'), tabs = document.querySelectorAll('.acct-tabs button'), msg = $('#acct-msg');
  function show(state, user) {
    forms.login.hidden = state !== 'login'; forms.signup.hidden = state !== 'signup'; signed.hidden = state !== 'in';
    tabs.forEach(b => b.setAttribute('aria-selected', String(b.dataset.tab === state)));
    document.querySelector('.acct-tabs').hidden = state === 'in';
    if (state === 'in') who.textContent = T.hi(user.name || user.email);
  }
  function note(text, bad) { msg.textContent = text || ''; msg.classList.toggle('bad', !!bad); msg.hidden = !text; }
  tabs.forEach(b => b.addEventListener('click', () => { note(''); show(b.dataset.tab); }));
  async function submit(kind, form) {
    const btn = form.querySelector('button[type="submit"]'); btn.disabled = true; note('');
    const data = Object.fromEntries(new FormData(form).entries()); if (kind === 'login') data.remember = !!data.remember;
    try {
      const r = await api(kind, data); const j = await r.json().catch(() => ({}));
      if (r.ok && j.authenticated) { show('in', j); form.reset(); return; }
      note(T[j.error] || (r.status === 429 ? T.throttled : T.generic), true);
    } catch (_) { note(T.offline, true); } finally { btn.disabled = false; }
  }
  forms.login.addEventListener('submit', e => { e.preventDefault(); submit('login', forms.login); });
  forms.signup.addEventListener('submit', e => { e.preventDefault(); submit('signup', forms.signup); });
  $('#logout').addEventListener('click', async () => { try { await api('logout', {}); } catch (_) {} show('login'); note(T.out); });
  // initial state (this GET also plants the csrftoken cookie)
  api('me').then(r => r.json()).then(j => show(j.authenticated ? 'in' : 'login', j)).catch(() => { show('login'); note(T.offline, true); });
})();
