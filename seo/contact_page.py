#!/usr/bin/env python3
"""Contact page repairs, applied by apply_content.py after fix_lying_forms.

What the export ships on the contact page, and what this changes:

- The booking form's name / email / message / service fields are unbound:
  a visitor fills them in and the mailto handoff ignores them. They are now
  real controlled fields and land in the email body.
- The chosen day is keyed with toISOString() after a *local* midnight, so
  for every visitor east of UTC (all of Germany) the key is the previous
  day and the confirmation names a different date than the chip that was
  pressed. Keys are now built from local date parts.
- "Your email is open." was shown even when no mail client exists. The
  confirmation now shows the composed request with copy / re-open / WhatsApp
  fallbacks, so the enquiry can always leave the page.
- Day and time chips were <span onClick>: no keyboard, no state for screen
  readers. They are <button aria-pressed> now; inputs get <label>s; the
  message is a <textarea>; validation is an inline role="alert", never a
  disabled-looking button.
- A "what happens next" sequence carries the trust signals the page lacked
  (30-minute call, written proposal, pilot in about two weeks, one person in
  five languages).
- The page becomes addressable at /#contact: nav() mirrors the SPA page into
  the URL hash, hashchange drives nav(), and every "Contact" navigation
  control is a real <a href="#contact">.

Every edit asserts the exact shape it expects and raises PatchError on
drift, so a changed export fails the deploy loudly instead of shipping a
half-repaired page. Idempotent: the markup carries class="ga-contact" and
the script a _syncHash method; both short-circuit a second run.
"""

from __future__ import annotations

import json
import re

CT_KEYS = (
    "eyebrow", "title", "lead", "infoTitle", "phoneL", "emailL", "locationL",
    "location", "hoursL", "hours", "personal", "nextTitle", "step1T", "step1D",
    "step2T", "step2D", "step3T", "step3D", "bookTitle", "serviceL", "servicePh",
    "dateL", "timeL", "nameL", "emailFieldL", "msgL", "optional", "submit",
    "submitHint", "missing", "fieldDay", "fieldTime", "fieldName", "fieldEmail",
    "doneTitle", "doneMsg", "copy", "copied", "openMail", "edit", "mailSubject",
    "mailGreeting", "mailSlot", "mailSign", "mailService", "mailName", "mailEmail",
)
LANGS = ("en", "de", "fr", "ro", "ar")
HASH_PAGES = ("services", "about", "contact", "news", "config")


class PatchError(Exception):
    pass


# ---------------------------------------------------------------------------
# markup
# ---------------------------------------------------------------------------
MARKUP_START = '  <sc-if value="{{ isContact }}">\n'
MARKUP_END = "  <!-- NEWS PAGE -->"

_MONO = "font-family:'JetBrains Mono','Noto Sans Arabic',monospace;"
_LABEL = _MONO + "font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--muted);display:block;margin-bottom:8px"
_FIELD = (
    "width:100%;box-sizing:border-box;padding:13px 14px;border-radius:8px;border:1px solid var(--cardBorder);"
    "background:var(--surface);color:var(--ink);font-size:15px;font-family:inherit;line-height:1.4"
)
_BTN2 = (
    "font:inherit;font-size:14px;font-weight:500;padding:11px 16px;border-radius:8px;cursor:pointer;"
    "background:var(--surface);color:var(--ink);border:1px solid var(--cardBorder);text-decoration:none;display:inline-flex;align-items:center;gap:8px"
)

NEW_MARKUP = """  <sc-if value="{{ isContact }}">
  <div class="ga-contact" style="padding:{{ heroPadY }} {{ padX }} {{ sectionPadY }}">
    <div style="__MONO__font-size:12px;letter-spacing:2px;text-transform:uppercase;color:var(--accent);margin-bottom:18px">{{ ct.eyebrow }}</div>
    <h1 style="font-family:{{ fontDisplay }};font-weight:400;font-size:{{ heroTitleSize }};line-height:1.04;letter-spacing:-1.5px;color:var(--ink);max-width:740px;text-wrap:balance">{{ ct.title }}</h1>
    <p style="font-size:18px;line-height:1.6;color:var(--body);max-width:540px;margin-top:22px">{{ ct.lead }}</p>

    <div style="display:grid;grid-template-columns:{{ contactCols }};gap:48px;margin-top:48px;align-items:start">
      <div>
        <div style="display:flex;flex-direction:column;gap:22px">
          <div style="__MONO__font-size:11px;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted)">{{ ct.infoTitle }}</div>
          <a href="tel:+491604155546" style="text-decoration:none;color:inherit;align-self:flex-start">
            <div style="__MONO__font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--muted)">{{ ct.phoneL }}</div>
            <div style="font-size:17px;color:var(--ink);margin-top:4px">+49 160 4155546</div>
          </a>
          <a href="mailto:contact@georgeai.dev" style="text-decoration:none;color:inherit;align-self:flex-start">
            <div style="__MONO__font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--muted)">{{ ct.emailL }}</div>
            <div style="font-size:17px;color:var(--ink);margin-top:4px">contact@georgeai.dev</div>
          </a>
          <div>
            <div style="__MONO__font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--muted)">{{ ct.locationL }}</div>
            <div style="font-size:17px;color:var(--ink);margin-top:4px">{{ ct.location }}</div>
          </div>
          <div>
            <div style="__MONO__font-size:11px;letter-spacing:1px;text-transform:uppercase;color:var(--muted)">{{ ct.hoursL }}</div>
            <div style="font-size:17px;color:var(--ink);margin-top:4px">{{ ct.hours }}</div>
          </div>
          <a href="https://wa.me/491604155546" target="_blank" rel="noopener" style="text-decoration:none;display:inline-flex;align-items:center;gap:8px;color:var(--accent);font-weight:500;font-size:15px;margin-top:4px;align-self:flex-start"><span style="width:7px;height:7px;background:#cc785c;clip-path:polygon(50% 0,61% 39%,100% 50%,61% 61%,50% 100%,39% 61%,0 50%,39% 39%)"></span>WhatsApp</a>
        </div>

        <div style="margin-top:44px;padding-top:32px;border-top:1px solid var(--hairline)">
          <div style="__MONO__font-size:11px;letter-spacing:1.5px;text-transform:uppercase;color:var(--muted);margin-bottom:6px">{{ ct.nextTitle }}</div>
          <ol style="list-style:none;margin:0;padding:0">
            <sc-for list="{{ nextSteps }}" as="st" hint-placeholder-count="3">
              <li style="display:grid;grid-template-columns:34px 1fr;gap:14px;padding:18px 0;border-bottom:1px solid var(--hairline)">
                <span style="__MONO__font-size:12px;color:var(--accent);padding-top:3px">{{ st.n }}</span>
                <span>
                  <span style="display:block;font-size:16px;font-weight:500;color:var(--ink);line-height:1.35">{{ st.t }}</span>
                  <span style="display:block;font-size:14px;line-height:1.55;color:var(--muted);margin-top:4px;max-width:46ch">{{ st.d }}</span>
                </span>
              </li>
            </sc-for>
          </ol>
          <p style="font-size:14px;line-height:1.55;color:var(--body);margin:20px 0 0;max-width:46ch">{{ ct.personal }}</p>
        </div>
      </div>

      <div style="background:var(--card);border:1px solid var(--cardBorder);border-radius:16px;padding:{{ contactCardPad }};order:{{ contactFormOrder }}">
        <sc-if value="{{ bookOpen }}" hint-placeholder-val="{{ true }}">
          <form onSubmit="{{ submitBooking }}" noValidate="true">
            <h2 style="font-family:{{ fontDisplay }};font-weight:400;font-size:26px;letter-spacing:-.4px;color:var(--ink);margin:0 0 22px">{{ ct.bookTitle }}</h2>

            <label for="ga-ct-service" style="__LABEL__">{{ ct.serviceL }}</label>
            <select id="ga-ct-service" name="service" value="{{ bkService }}" onChange="{{ setBkService }}" style="__FIELD__;margin-bottom:22px">
              <option value="">{{ ct.servicePh }}</option>
              <sc-for list="{{ serviceNames }}" as="n" hint-placeholder-count="6">
                <option value="{{ n }}">{{ n }}</option>
              </sc-for>
            </select>

            <div role="group" aria-labelledby="ga-ct-dayL" style="margin-bottom:22px">
              <div id="ga-ct-dayL" style="__LABEL__;margin-bottom:10px">{{ ct.dateL }}</div>
              <div style="display:flex;gap:8px;flex-wrap:wrap">
                <sc-for list="{{ days }}" as="d" hint-placeholder-count="8">
                  <button type="button" onClick="{{ d.onClick }}" aria-pressed="{{ d.pressed }}" aria-label="{{ d.label }}" style="{{ d.style }}">
                    <span style="font-family:'JetBrains Mono',monospace;font-size:10px;text-transform:uppercase;opacity:.8">{{ d.dn }}</span>
                    <span style="font-family:{{ fontDisplay }};font-size:20px;line-height:1.1">{{ d.dnum }}</span>
                    <span style="font-family:'JetBrains Mono',monospace;font-size:10px;opacity:.8">{{ d.mon }}</span>
                  </button>
                </sc-for>
              </div>
            </div>

            <div role="group" aria-labelledby="ga-ct-timeL" style="margin-bottom:22px">
              <div id="ga-ct-timeL" style="__LABEL__;margin-bottom:10px">{{ ct.timeL }}</div>
              <div style="display:flex;gap:8px;flex-wrap:wrap">
                <sc-for list="{{ slots }}" as="s" hint-placeholder-count="6">
                  <button type="button" onClick="{{ s.onClick }}" aria-pressed="{{ s.pressed }}" style="{{ s.style }}">{{ s.tm }}</button>
                </sc-for>
              </div>
            </div>

            <div style="display:grid;grid-template-columns:{{ contactFieldCols }};gap:12px;margin-bottom:16px">
              <div>
                <label for="ga-ct-name" style="__LABEL__">{{ ct.nameL }}</label>
                <input id="ga-ct-name" name="name" type="text" autoComplete="name" value="{{ bkName }}" onChange="{{ setBkName }}" style="__FIELD__">
              </div>
              <div>
                <label for="ga-ct-email" style="__LABEL__">{{ ct.emailFieldL }}</label>
                <input id="ga-ct-email" name="email" type="email" autoComplete="email" inputMode="email" value="{{ bkEmail }}" onChange="{{ setBkEmail }}" style="__FIELD__">
              </div>
            </div>
            <label for="ga-ct-msg" style="__LABEL__">{{ ct.msgL }} <span style="text-transform:none;letter-spacing:0;font-family:inherit;opacity:.8">({{ ct.optional }})</span></label>
            <textarea id="ga-ct-msg" name="message" rows="3" value="{{ bkMsg }}" onChange="{{ setBkMsg }}" style="__FIELD__;resize:vertical;min-height:84px;margin-bottom:18px"></textarea>

            <button type="submit" style="{{ submitStyle }}">{{ ct.submit }}</button>
            <sc-if value="{{ bookError }}">
              <p role="alert" style="font-size:14px;line-height:1.5;color:var(--accent);margin:12px 0 0">{{ bookError }}</p>
            </sc-if>
            <p style="font-size:13px;line-height:1.5;color:var(--muted);margin:14px 0 0">{{ ct.submitHint }}</p>
          </form>
        </sc-if>
        <sc-if value="{{ bookDone }}">
          <div>
            <img src="/logo-mark.png" alt="" width="28" height="28" style="display:block;width:28px;height:28px;margin-bottom:18px">
            <h2 style="font-family:{{ fontDisplay }};font-weight:400;font-size:26px;letter-spacing:-.4px;color:var(--ink);margin:0">{{ ct.doneTitle }}</h2>
            <p style="font-size:16px;line-height:1.55;color:var(--body);margin:10px 0 0">{{ chosen }} · {{ chosenTime }}</p>
            <p style="font-size:14px;line-height:1.55;color:var(--muted);margin:8px 0 0;max-width:52ch">{{ ct.doneMsg }}</p>
            <div style="white-space:pre-wrap;font-size:14px;line-height:1.6;color:var(--body);background:var(--surface);border:1px solid var(--cardBorder);border-radius:10px;padding:16px 18px;margin-top:20px">{{ bookBody }}</div>
            <div style="display:flex;gap:10px;flex-wrap:wrap;margin-top:16px">
              <button type="button" onClick="{{ copyBooking }}" style="__BTN2__">{{ copyLabel }}</button>
              <a href="{{ mailtoHref }}" style="__BTN2__">{{ ct.openMail }}</a>
              <a href="{{ waHref }}" target="_blank" rel="noopener" style="__BTN2__"><span style="width:7px;height:7px;background:#cc785c;clip-path:polygon(50% 0,61% 39%,100% 50%,61% 61%,50% 100%,39% 61%,0 50%,39% 39%)"></span>WhatsApp</a>
            </div>
            <button type="button" onClick="{{ editBooking }}" style="background:none;border:none;padding:0;margin-top:22px;font:inherit;font-size:14px;color:var(--accent);cursor:pointer;text-decoration:underline;text-underline-offset:3px">{{ ct.edit }}</button>
          </div>
        </sc-if>
      </div>
    </div>
  </div>
  </sc-if>

""".replace("__MONO__", _MONO).replace("__LABEL__", _LABEL).replace("__FIELD__", _FIELD).replace("__BTN2__", _BTN2)


def patch_markup(html: str) -> str:
    start = html.find(MARKUP_START)
    end = html.find(MARKUP_END)
    if start < 0 or end < 0 or end < start:
        raise PatchError("contact page block not found between isContact and the NEWS PAGE marker")
    old = html[start:end]
    if old.count("<sc-if") != old.count("</sc-if>") or "{{ ct.bookTitle }}" not in old:
        raise PatchError("contact page block is not the shape this patch expects")
    return html[:start] + NEW_MARKUP + html[end:]


# ---------------------------------------------------------------------------
# booking logic inside the render function
# ---------------------------------------------------------------------------
JS_START = '    const chipBase = "display:flex;flex-direction:column;align-items:center;gap:2px;min-width:62px;padding:10px;border-radius:10px;cursor:pointer;";\n'
JS_END_HEAD = "    const chosen = this.state.bookDate\n"
JS_END_TAIL = '      : "";\n'

NEW_JS = r'''    const chipBase = "display:flex;flex-direction:column;align-items:center;gap:2px;min-width:62px;padding:10px;border-radius:10px;cursor:pointer;font:inherit;line-height:1;transition:background-color .15s ease,border-color .15s ease;";
    const chipOn = "background:var(--accentBtn);color:#fff;border:1px solid var(--accentBtn)";
    const chipOff = "background:var(--surface);color:var(--body);border:1px solid var(--cardBorder)";
    const slotBase = "padding:11px 16px;border-radius:9999px;cursor:pointer;font-size:14px;font-family:'JetBrains Mono',monospace;line-height:1;transition:background-color .15s ease,border-color .15s ease;";
    const bkLocale = { en: "en-GB", de: "de-DE", fr: "fr-FR", ro: "ro-RO", ar: "ar-EG" }[lang] || "en-GB";
    const ctT = t.ct || {};
    const localKey = (d) => d.getFullYear() + "-" + String(d.getMonth() + 1).padStart(2, "0") + "-" + String(d.getDate()).padStart(2, "0");
    const fromKey = (k) => { const p = k.split("-"); return new Date(+p[0], +p[1] - 1, +p[2]); };
    const longDay = new Intl.DateTimeFormat(bkLocale, { weekday: "long", day: "numeric", month: "long" });
    const days = [];
    const _dt = new Date(); _dt.setHours(0, 0, 0, 0);
    let _added = 0, _guard = 0;
    while (_added < 10 && _guard < 40) {
      _dt.setDate(_dt.getDate() + 1); _guard++;
      const dow = _dt.getDay();
      if (dow === 0 || dow === 6) continue;
      const key = localKey(_dt);
      const d2 = new Date(_dt);
      const act = this.state.bookDate === key;
      days.push({
        key,
        dn: new Intl.DateTimeFormat(bkLocale, { weekday: "short" }).format(d2),
        dnum: new Intl.DateTimeFormat(bkLocale, { day: "numeric" }).format(d2),
        mon: new Intl.DateTimeFormat(bkLocale, { month: "short" }).format(d2),
        label: longDay.format(d2),
        pressed: act,
        style: chipBase + (act ? chipOn : chipOff),
        onClick: () => this.setState({ bookDate: key, bookDone: false, bookError: "" }),
      });
      _added++;
    }
    const slots = ["09:00", "10:30", "12:00", "14:00", "15:30", "17:00"].map((tm) => {
      const act = this.state.bookTime === tm;
      return { tm, pressed: act, style: slotBase + (act ? chipOn : chipOff), onClick: () => this.setState({ bookTime: tm, bookDone: false, bookError: "" }) };
    });
    const bk = this.state.booking || {};
    const setBk = (k) => (e) => this.setState({ booking: Object.assign({}, this.state.booking || {}, { [k]: e.target.value }), bookError: "" });
    const chosen = this.state.bookDate ? longDay.format(fromKey(this.state.bookDate)) : "";
    const emailOk = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test((bk.email || "").trim());
    const bookReady = !!(this.state.bookDate && this.state.bookTime && (bk.name || "").trim() && emailOk);
    const submitStyle = "width:100%;text-align:center;padding:15px;border-radius:8px;font-size:15px;font-weight:500;border:none;margin-top:4px;font-family:inherit;cursor:pointer;background:var(--accentBtn);color:#fff;transition:opacity .15s ease;" + (bookReady ? "" : "opacity:.82");
    const when = (chosen ? chosen + ", " : "") + (this.state.bookTime || "");
    const bookBody = (ctT.mailGreeting || "Hi George,") + "\n\n"
      + (ctT.mailSlot || "Requested slot:") + " " + when + "\n"
      + (ctT.serviceL || "Service") + " " + (bk.service || "–") + "\n"
      + (ctT.nameL || "Name") + " " + (bk.name || "").trim() + "\n"
      + (ctT.emailFieldL || "Email") + " " + (bk.email || "").trim()
      + ((bk.msg || "").trim() ? "\n\n" + (bk.msg || "").trim() : "")
      + "\n\n" + (ctT.mailSign || "Thanks,") + "\n" + (bk.name || "").trim();
    const subject = ctT.mailSubject ? ctT.mailSubject + ": " + when : "Booking request: " + when;
    const mailtoHref = "mailto:contact@georgeai.dev?subject=" + encodeURIComponent(subject) + "&body=" + encodeURIComponent(bookBody);
    const waHref = "https://wa.me/491604155546?text=" + encodeURIComponent(bookBody);
    const submitBooking = (e) => {
      if (e && e.preventDefault) e.preventDefault();
      const missing = [];
      if (!this.state.bookDate) missing.push(ctT.fieldDay || "a day");
      if (!this.state.bookTime) missing.push(ctT.fieldTime || "a time");
      if (!(bk.name || "").trim()) missing.push(ctT.fieldName || "your name");
      if (!emailOk) missing.push(ctT.fieldEmail || "a valid email");
      if (missing.length) { this.setState({ bookError: (ctT.missing || "Still needed:") + " " + missing.join(", ") }); return; }
      this.setState({ bookDone: true, bookError: "", copied: false });
      try { window.location.href = mailtoHref; } catch (err) {}
    };
    const editBooking = () => this.setState({ bookDone: false });
    const copyBooking = () => {
      const done = () => { this.setState({ copied: true }); clearTimeout(this._cp); this._cp = setTimeout(() => this.setState({ copied: false }), 2200); };
      try { navigator.clipboard.writeText(bookBody).then(done, () => {}); } catch (err) {}
    };
    const nextSteps = [1, 2, 3].map((i) => ({ n: "0" + i, t: ctT["step" + i + "T"] || "", d: ctT["step" + i + "D"] || "" }));
'''

OLD_VALS = (
    "      days, slots, bookReady, submitStyle, bookDone: this.state.bookDone, bookOpen: !this.state.bookDone, "
    "submitBooking, chosen, chosenTime: this.state.bookTime, serviceNames,\n"
)
NEW_VALS = (
    "      days, slots, bookReady, submitStyle, bookDone: this.state.bookDone, bookOpen: !this.state.bookDone, "
    "submitBooking, chosen, chosenTime: this.state.bookTime, serviceNames,\n"
    '      bookError: this.state.bookError || "", bkService: bk.service || "", bkName: bk.name || "", '
    'bkEmail: bk.email || "", bkMsg: bk.msg || "",\n'
    '      setBkService: setBk("service"), setBkName: setBk("name"), setBkEmail: setBk("email"), setBkMsg: setBk("msg"),\n'
    "      bookBody, mailtoHref, waHref, copyBooking, editBooking, nextSteps, "
    "copyLabel: this.state.copied ? (ctT.copied || \"Copied\") : (ctT.copy || \"Copy request\"),\n"
    '      contactFieldCols: isNarrow ? "1fr" : "1fr 1fr", contactFormOrder: isMobile ? "-1" : "0", '
    'contactCardPad: isNarrow ? "22px 18px" : "32px",\n'
)


def patch_logic(html: str) -> str:
    start = html.find(JS_START)
    if start < 0:
        raise PatchError("booking chip styles not found; the export's contact logic changed shape")
    head = html.find(JS_END_HEAD, start)
    if head < 0:
        raise PatchError("`const chosen` not found after the booking chips")
    end = html.find(JS_END_TAIL, head)
    if end < 0:
        raise PatchError("`const chosen` does not end the way this patch expects")
    end += len(JS_END_TAIL)
    old = html[start:end]
    if "Booking request: " not in old or "const submitBooking" not in old:
        raise PatchError("contact_page must run after fix_lying_forms")
    html = html[:start] + NEW_JS + html[end:]
    if OLD_VALS not in html:
        raise PatchError("renderVals booking line not found")
    return html.replace(OLD_VALS, NEW_VALS, 1)


# ---------------------------------------------------------------------------
# copy — one flat `ct: { ... }` literal per language block of T()
# ---------------------------------------------------------------------------
_CT_OBJ = re.compile(r"(?<![A-Za-z])ct:\s*\{[^{}]*\}")


def patch_copy(html: str, copy: dict) -> str:
    for lang in LANGS:
        if lang not in copy:
            raise PatchError(f"contact.json has no '{lang}' block")
        missing = [k for k in CT_KEYS if not copy[lang].get(k)]
        if missing:
            raise PatchError(f"contact.json[{lang}] missing {', '.join(missing)}")
        for k, v in copy[lang].items():
            if "—" in v:
                raise PatchError(f"contact.json[{lang}].{k} contains an em dash")
        block = re.search(r"^ {6}%s: \{" % lang, html, re.M)
        if not block:
            raise PatchError(f"no '{lang}: {{' language block found")
        obj = _CT_OBJ.search(html, block.end())
        if not obj:
            raise PatchError(f"no ct object inside the {lang} block")
        fields = ", ".join(
            "%s: %s" % (k, json.dumps(copy[lang][k], ensure_ascii=False)) for k in CT_KEYS
        )
        html = html[: obj.start()] + "ct: { " + fields + " }" + html[obj.end():]
    return html


# ---------------------------------------------------------------------------
# /#contact — hash routing and real links for every "Contact" control
# ---------------------------------------------------------------------------
OLD_NAV = """  nav(page, idx) {
    this.setState({ page, svcIdx: idx == null ? this.state.svcIdx : idx, menuOpen: false });
    try { window.scrollTo(0, 0); } catch (e) {}
  }
  nav2(page, legalDoc) {
    this.setState({ page, legalDoc: legalDoc || this.state.legalDoc, menuOpen: false });
    try { window.scrollTo(0, 0); } catch (e) {}
  }
"""
NEW_NAV = """  _syncHash(page) {
    try {
      const h = %s.indexOf(page) >= 0 ? "#" + page : "";
      if (h) { if (window.location.hash !== h) window.location.hash = h; }
      else if (window.location.hash) history.pushState(null, "", window.location.pathname + window.location.search);
    } catch (e) {}
  }
  _pageFromHash() {
    const p = (window.location.hash || "").slice(1);
    return %s.indexOf(p) >= 0 ? p : (p ? null : "home");
  }
  nav(page, idx) {
    this.setState({ page, svcIdx: idx == null ? this.state.svcIdx : idx, menuOpen: false });
    try { window.scrollTo(0, 0); } catch (e) {}
    this._syncHash(page);
  }
  nav2(page, legalDoc) {
    this.setState({ page, legalDoc: legalDoc || this.state.legalDoc, menuOpen: false });
    try { window.scrollTo(0, 0); } catch (e) {}
    this._syncHash(page);
  }
""" % (json.dumps(list(HASH_PAGES)), json.dumps(list(HASH_PAGES)))

OLD_MOUNT = "    this._set = set;\n"
NEW_MOUNT = """    this._set = set;
    try {
      const p0 = this._pageFromHash();
      if (p0 && p0 !== "home") this.setState({ page: p0 });
      this._onHash = () => { const p = this._pageFromHash(); if (p && p !== this.state.page) this.nav(p); };
      window.addEventListener("hashchange", this._onHash);
    } catch (e) {}
"""
OLD_UNMOUNT = '  componentWillUnmount() { window.removeEventListener("resize", this._set); if (this._gi) clearInterval(this._gi); }'
NEW_UNMOUNT = '  componentWillUnmount() { window.removeEventListener("resize", this._set); if (this._onHash) window.removeEventListener("hashchange", this._onHash); if (this._gi) clearInterval(this._gi); if (this._cp) clearTimeout(this._cp); }'

# Every control that navigates to the contact page is a <span onClick> in the
# export (header nav, header CTA, mobile menu, hero CTA, CTA band, service and
# about page CTAs, footer). A span cannot be focused, crawled or opened in a
# new tab. Each becomes <a href="#contact"> with its inline style kept, so the
# layout is unchanged; onClick stays so a click on the current page still
# scrolls to the top and closes the mobile menu. The <button> form is accepted
# too, for a page that was hand-repaired before this layer existed.
_CONTACT_CTRL = re.compile(
    r'<(span|button)(?: type="button")? onClick="\{\{ goContact \}\}" style="([^"]*)">([^<]*)</\1>'
)


def _as_link(m: re.Match) -> str:
    style = m.group(2).rstrip(";")
    if "color:" not in style:
        style += ";color:inherit"
    style = style.lstrip(";") + ";text-decoration:none"
    return '<a href="#contact" onClick="{{ goContact }}" style="%s">%s</a>' % (style, m.group(3))


def patch_routing(html: str) -> str:
    if "_syncHash" not in html:
        for old, label in ((OLD_NAV, "nav()/nav2()"), (OLD_MOUNT, "componentDidMount"), (OLD_UNMOUNT, "componentWillUnmount")):
            if html.count(old) != 1:
                raise PatchError(f"{label} not found exactly once; the export's logic class changed shape")
        html = html.replace(OLD_NAV, NEW_NAV, 1).replace(OLD_MOUNT, NEW_MOUNT, 1).replace(OLD_UNMOUNT, NEW_UNMOUNT, 1)
    html, n = _CONTACT_CTRL.subn(_as_link, html)
    links = html.count('<a href="#contact" onClick="{{ goContact }}"')
    leftover = html.count('onClick="{{ goContact }}"') - links
    if links < 5 or leftover:
        raise PatchError(
            f"contact controls: {links} linked, {leftover} still not links (converted {n} this run)"
        )
    return html


def patch_contact_page(html: str, copy: dict) -> str:
    if 'class="ga-contact"' not in html:
        html = patch_markup(html)
        html = patch_logic(html)
    html = patch_copy(html, copy)
    return patch_routing(html)
