/*
 * georgeai.dev — free visibility audit widget
 *
 * Floating CTA button + modal lead form. Submissions go to the n8n webhook,
 * which runs an automated SEO/AEO/AIO/GEO audit of the submitted URL and
 * emails the report to the prospect.
 *
 * Kept out of the design export (same rationale as auth.js) so it survives
 * re-exports. Copied into site/ and injected into index.html by deploy.sh.
 */
(function () {
  "use strict";

  var WEBHOOK = "https://n8n.rotocon.world/webhook/georgeai-free-audit";
  var CONTACT = "contact@georgeai.dev";

  // ---- copy ----------------------------------------------------------------
  // The target market is German; the site itself is multilingual and stores the
  // visitor's choice in localStorage under ga_lang (see the export's setLang).
  // Follow that, then the browser, then fall back to English. Add fr/ro/ar here
  // when they are needed — missing keys fall through to English, never blank.
  var COPY = {
    en: {
      fab: "Free visibility check", badge: "Free \u00b7 2 minutes",
      title: "Free visibility check",
      sub: "See how your website shows up in Google and inside AI assistants " +
           "like ChatGPT, Claude and Perplexity \u2014 a short report, straight to your inbox.",
      first: "First name", last: "Surname", email: "E-mail address",
      phone: "Phone (optional)", url: "Website to check",
      phFirst: "Jane", phLast: "Doe", phEmail: "jane@company.com",
      phPhone: "+49 170 1234567", phUrl: "yourcompany.com",
      submit: "Send me the report", sending: "Starting the check\u2026",
      fine: "Free and without obligation. Your details are used only to send you this " +
            "report \u2014 never passed to third parties. Ask me to delete them any time at ",
      errName: "Please fill in your name.",
      errEmail: "Please enter a valid e-mail address.",
      errUrl: "Please enter a valid website address.",
      errSend: "Something went wrong sending your request. Please try again, or email",
      doneTitle: "On its way", doneA: "I am checking your website now. The report will reach ",
      doneB: " in a few minutes."
    },
    de: {
      fab: "Kostenloser Sichtbarkeits-Check", badge: "Kostenlos \u00b7 2 Minuten",
      title: "Kostenloser Sichtbarkeits-Check",
      sub: "Sehen Sie, wie Ihre Website bei Google und in KI-Assistenten wie ChatGPT, " +
           "Claude und Perplexity auftaucht \u2014 ein kurzer Bericht, direkt in Ihr Postfach.",
      first: "Vorname", last: "Nachname", email: "E-Mail-Adresse",
      phone: "Telefon (optional)", url: "Zu pr\u00fcfende Website",
      phFirst: "Max", phLast: "Mustermann", phEmail: "max@firma.de",
      phPhone: "+49 170 1234567", phUrl: "ihrefirma.de",
      submit: "Bericht anfordern", sending: "Check l\u00e4uft\u2026",
      fine: "Kostenlos und unverbindlich. Ihre Angaben verwende ich ausschlie\u00dflich, um Ihnen " +
            "diesen Bericht zu senden \u2014 keine Weitergabe an Dritte. L\u00f6schung jederzeit m\u00f6glich unter ",
      errName: "Bitte tragen Sie Ihren Namen ein.",
      errEmail: "Bitte geben Sie eine g\u00fcltige E-Mail-Adresse ein.",
      errUrl: "Bitte geben Sie eine g\u00fcltige Website-Adresse ein.",
      errSend: "Beim Senden ist etwas schiefgelaufen. Bitte erneut versuchen oder mailen an",
      doneTitle: "Unterwegs", doneA: "Ich pr\u00fcfe Ihre Website jetzt. Der Bericht erreicht ",
      doneB: " in wenigen Minuten."
    }
  };

  function T() {
    var code = "";
    try { code = localStorage.getItem("ga_lang") || ""; } catch (e) {}
    if (!code && navigator.language) code = navigator.language;
    var lang = COPY[String(code).slice(0, 2).toLowerCase()] ? String(code).slice(0, 2).toLowerCase() : "en";
    var base = COPY.en, pick = COPY[lang], out = {};
    for (var k in base) out[k] = pick[k] !== undefined ? pick[k] : base[k];
    return out;
  }

  var SERIF = '"Copernicus","Tiempos Headline",Georgia,"Times New Roman",serif';
  var SANS = '"StyreneB",Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif';

  // ---- styles ------------------------------------------------------------
  var css =
    "#ga-audit-fab{position:fixed;right:20px;bottom:calc(20px + env(safe-area-inset-bottom));z-index:99990;display:flex;" +
    "align-items:center;gap:8px;background:#cc785c;color:#fff;border:none;cursor:pointer;" +
    "border-radius:9999px;padding:12px 20px;font:500 14px/1 " + SANS + ";" +
    "box-shadow:0 6px 24px rgba(20,20,19,.25)}" +
    "#ga-audit-fab:active{background:#a9583e}" +
    "#ga-audit-overlay{position:fixed;inset:0;z-index:99995;background:rgba(20,20,19,.55);" +
    "display:flex;align-items:center;justify-content:center;padding:20px;overflow-y:auto}" +
    "#ga-audit-modal{background:#faf9f5;border-radius:16px;padding:32px;max-width:440px;" +
    "width:100%;max-height:92vh;overflow-y:auto;position:relative;" +
    "font-family:" + SANS + ";color:#141413}" +
    ".ga-audit-badge{display:inline-block;background:#cc785c;color:#fff;border-radius:9999px;" +
    "padding:4px 12px;font:500 12px/1.4 " + SANS + ";letter-spacing:1.5px;text-transform:uppercase}" +
    ".ga-audit-title{font:400 28px/1.2 " + SERIF + ";letter-spacing:-.3px;margin:14px 0 8px}" +
    ".ga-audit-sub{font:400 14px/1.55 " + SANS + ";color:#3d3d3a;margin:0 0 20px}" +
    ".ga-audit-close{position:absolute;top:14px;right:14px;width:36px;height:36px;" +
    "border-radius:9999px;border:1px solid #e6dfd8;background:#faf9f5;color:#141413;" +
    "cursor:pointer;font:400 18px/1 " + SANS + "}" +
    ".ga-audit-label{display:block;font:500 13px/1.4 " + SANS + ";color:#3d3d3a;" +
    "margin:0 0 4px}" +
    ".ga-audit-field{margin-bottom:14px}" +
    ".ga-audit-row{display:flex;gap:12px}.ga-audit-row .ga-audit-field{flex:1;min-width:0}" +
    ".ga-audit-input{width:100%;box-sizing:border-box;height:40px;background:#fff;" +
    "color:#141413;border:1px solid #e6dfd8;border-radius:8px;padding:10px 14px;" +
    "font:400 15px/1.4 " + SANS + ";outline:none}" +
    ".ga-audit-input:focus{border-color:#cc785c;box-shadow:0 0 0 3px rgba(204,120,92,.15)}" +
    ".ga-audit-submit{width:100%;height:44px;border:none;border-radius:8px;background:#cc785c;" +
    "color:#fff;font:500 15px/1 " + SANS + ";cursor:pointer;margin-top:6px}" +
    ".ga-audit-submit:active{background:#a9583e}" +
    ".ga-audit-submit[disabled]{background:#e6dfd8;color:#6c6a64;cursor:default}" +
    ".ga-audit-msg{margin-top:12px;font:400 13px/1.5 " + SANS + ";border-radius:8px;" +
    "padding:10px 12px;display:none}" +
    ".ga-audit-msg a{color:#cc785c}" +
    ".ga-audit-fine{margin:14px 0 0;font:400 12px/1.5 " + SANS + ";color:#8e8b82;text-align:center}" +
    ".ga-audit-hp{position:absolute;left:-9999px;top:-9999px;height:1px;width:1px;overflow:hidden}" +
    ".ga-audit-done{text-align:center;padding:24px 0}" +
    ".ga-audit-done-mark{width:56px;height:56px;border-radius:9999px;background:#5db872;" +
    "color:#fff;font:400 28px/56px " + SANS + ";margin:0 auto 16px}" +
    "@media (max-width:520px){.ga-audit-row{display:block}#ga-audit-modal{padding:24px}}";

  var style = document.createElement("style");
  style.textContent = css;
  document.head.appendChild(style);

  // ---- helpers -----------------------------------------------------------
  function el(tag, attrs, children) {
    var n = document.createElement(tag);
    Object.keys(attrs || {}).forEach(function (k) {
      if (k === "text") n.textContent = attrs[k];
      else n.setAttribute(k, attrs[k]);
    });
    (children || []).forEach(function (c) { n.appendChild(c); });
    return n;
  }

  function field(label, name, type, placeholder, autocomplete) {
    var input = el("input", {
      class: "ga-audit-input",
      name: name,
      type: type,
      placeholder: placeholder,
      autocomplete: autocomplete || "on",
    });
    return {
      wrap: el("div", { class: "ga-audit-field" }, [
        el("label", { class: "ga-audit-label", text: label }),
        input,
      ]),
      input: input,
    };
  }

  function normalizeUrl(v) {
    v = v.trim();
    if (!v) return "";
    if (!/^https?:\/\//i.test(v)) v = "https://" + v;
    try {
      var u = new URL(v);
      if (!/\./.test(u.hostname)) return "";
      return u.href;
    } catch (e) {
      return "";
    }
  }

  // ---- modal -------------------------------------------------------------
  var overlay = null;

  function close() {
    if (overlay) { overlay.remove(); overlay = null; }
    document.removeEventListener("keydown", onKey);
  }

  function onKey(e) { if (e.key === "Escape") close(); }

  function setMsg(box, text, isError, asHtml) {
    box.style.display = text ? "block" : "none";
    box.style.background = isError ? "rgba(198,69,69,.08)" : "rgba(93,184,114,.12)";
    box.style.color = isError ? "#c64545" : "#3d7a4a";
    if (asHtml) {
      box.textContent = text + " ";
      var a = el("a", { href: "mailto:" + CONTACT, text: CONTACT });
      box.appendChild(a);
      box.appendChild(document.createTextNode("."));
    } else {
      box.textContent = text;
    }
  }

  function showSuccess(modal, email) {
    var t = T();
    modal.replaceChildren(
      el("button", { class: "ga-audit-close", "aria-label": "Close", text: "×" }),
      el("div", { class: "ga-audit-done" }, [
        el("div", { class: "ga-audit-done-mark", text: "✓" }),
        el("div", { class: "ga-audit-title", text: t.doneTitle }),
        el("p", { class: "ga-audit-sub", text: t.doneA + email + t.doneB }),
      ])
    );
  }

  function open() {
    if (overlay) return;

    var t = T();
    var fFirst = field(t.first, "first_name", "text", t.phFirst, "given-name");
    var fLast = field(t.last, "surname", "text", t.phLast, "family-name");
    var fEmail = field(t.email, "email", "email", t.phEmail, "email");
    var fPhone = field(t.phone, "phone", "tel", t.phPhone, "tel");
    var fUrl = field(t.url, "website", "text", t.phUrl, "url");

    // honeypot — humans never see it; bots that fill it are dropped in n8n
    var hp = el("input", { class: "ga-audit-input", name: "company", type: "text",
      tabindex: "-1", autocomplete: "off", "aria-hidden": "true" });

    var msg = el("div", { class: "ga-audit-msg" });
    var submit = el("button", { class: "ga-audit-submit", type: "submit",
      text: t.submit });

    var fine = el("p", { class: "ga-audit-fine", text: t.fine });
    fine.appendChild(el("a", { href: "mailto:" + CONTACT, text: CONTACT }));
    fine.appendChild(document.createTextNode("."));

    var form = el("form", { novalidate: "novalidate" }, [
      el("div", { class: "ga-audit-row" }, [fFirst.wrap, fLast.wrap]),
      fEmail.wrap,
      fPhone.wrap,
      fUrl.wrap,
      el("div", { class: "ga-audit-hp" }, [hp]),
      submit,
      msg,
      fine,
    ]);

    var modal = el("div", { id: "ga-audit-modal", role: "dialog", "aria-modal": "true" }, [
      el("button", { class: "ga-audit-close", "aria-label": "Close", text: "×" }),
      el("span", { class: "ga-audit-badge", text: t.badge }),
      el("div", { class: "ga-audit-title", text: t.title }),
      el("p", {
        class: "ga-audit-sub",
        text: t.sub,
      }),
      form,
    ]);

    overlay = el("div", { id: "ga-audit-overlay" }, [modal]);
    overlay.addEventListener("click", function (e) { if (e.target === overlay) close(); });
    modal.addEventListener("click", function (e) {
      if (e.target.closest && e.target.closest(".ga-audit-close")) close();
    });
    document.addEventListener("keydown", onKey);

    form.addEventListener("submit", function (e) {
      e.preventDefault();
      var payload = {
        first_name: fFirst.input.value.trim(),
        surname: fLast.input.value.trim(),
        email: fEmail.input.value.trim(),
        phone: fPhone.input.value.trim(),
        website: normalizeUrl(fUrl.input.value),
        company: hp.value, // honeypot
        page: location.href,
      };

      if (!payload.first_name || !payload.surname) {
        setMsg(msg, t.errName, true); return;
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(payload.email)) {
        setMsg(msg, t.errEmail, true); return;
      }
      if (!payload.website) {
        setMsg(msg, t.errUrl, true); return;
      }

      setMsg(msg, "", false);
      submit.disabled = true;
      submit.textContent = t.sending;

      fetch(WEBHOOK, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
        .then(function (r) {
          if (!r.ok) throw new Error("HTTP " + r.status);
          showSuccess(modal, payload.email);
        })
        .catch(function () {
          submit.disabled = false;
          submit.textContent = t.submit;
          setMsg(msg, t.errSend, true, true);
        });
    });

    document.body.appendChild(overlay);
    fFirst.input.focus();
  }

  // ---- floating button ---------------------------------------------------
  // The consent banner owns the bottom of the viewport until it is dismissed.
  // The export records consent as localStorage ga_cookie === "done"
  // (site/index.html:1403-1405); mounting before that puts this button on top of
  // the banner's "Accept all" target on a phone.
  function consentSettled() {
    try { return localStorage.getItem("ga_cookie") === "done"; }
    catch (e) { return true; }  // storage blocked: never withhold the button
  }

  function mountWhenConsentSettled() {
    if (consentSettled()) { mount(); return; }
    var tries = 0;
    var timer = setInterval(function () {
      if (consentSettled()) { clearInterval(timer); mount(); }
      else if (++tries > 600) { clearInterval(timer); mount(); }  // 5 min, then show anyway
    }, 500);
  }

  function mount() {
    if (document.getElementById("ga-audit-fab")) return;
    var fab = el("button", { id: "ga-audit-fab", type: "button" });
    // radar-blip glyph, drawn inline so there is no asset dependency
    var NS = "http://www.w3.org/2000/svg";
    var svg = document.createElementNS(NS, "svg");
    svg.setAttribute("width", "16");
    svg.setAttribute("height", "16");
    svg.setAttribute("viewBox", "0 0 16 16");
    svg.setAttribute("fill", "none");
    svg.setAttribute("aria-hidden", "true");
    var ring = document.createElementNS(NS, "circle");
    ring.setAttribute("cx", "8"); ring.setAttribute("cy", "8"); ring.setAttribute("r", "6.5");
    ring.setAttribute("stroke", "#fff"); ring.setAttribute("stroke-width", "1.4");
    var dot = document.createElementNS(NS, "circle");
    dot.setAttribute("cx", "8"); dot.setAttribute("cy", "8"); dot.setAttribute("r", "2");
    dot.setAttribute("fill", "#fff");
    svg.appendChild(ring);
    svg.appendChild(dot);
    fab.appendChild(svg);
    fab.appendChild(document.createTextNode(T().fab));
    fab.addEventListener("click", open);
    document.body.appendChild(fab);
  }

  window.gaAudit = { open: open, close: close };

  if (document.readyState !== "loading") mountWhenConsentSettled();
  else document.addEventListener("DOMContentLoaded", mountWhenConsentSettled);
})();
