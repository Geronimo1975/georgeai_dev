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

  var WEBHOOK = "https://app.n8n-studio.com/webhook/georgeai-free-audit";
  var CONTACT = "contact@georgeai.dev";

  var SERIF = '"Copernicus","Tiempos Headline",Georgia,"Times New Roman",serif';
  var SANS = '"StyreneB",Inter,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif';

  // ---- styles ------------------------------------------------------------
  var css =
    "#ga-audit-fab{position:fixed;right:20px;bottom:20px;z-index:99990;display:flex;" +
    "align-items:center;gap:8px;background:#ff8300;color:#141413;border:none;cursor:pointer;" +
    "border-radius:9999px;padding:12px 20px;font:500 14px/1 " + SANS + ";" +
    "box-shadow:0 6px 24px rgba(20,20,19,.25)}" +
    "#ga-audit-fab:active{background:#e8760a}" +
    "#ga-audit-overlay{position:fixed;inset:0;z-index:99995;background:rgba(20,20,19,.55);" +
    "display:flex;align-items:center;justify-content:center;padding:20px;overflow-y:auto}" +
    "#ga-audit-modal{background:#faf9f5;border-radius:16px;padding:32px;max-width:440px;" +
    "width:100%;max-height:92vh;overflow-y:auto;position:relative;" +
    "font-family:" + SANS + ";color:#141413}" +
    ".ga-audit-badge{display:inline-block;background:#ff8300;color:#141413;border-radius:9999px;" +
    "padding:4px 12px;font:500 12px/1.4 " + SANS + ";letter-spacing:1.5px;text-transform:uppercase}" +
    ".ga-audit-title{font:400 28px/1.2 " + SERIF + ";letter-spacing:-.3px;margin:14px 0 8px}" +
    ".ga-audit-sub{font:400 14px/1.55 " + SANS + ";color:#3d3d3a;margin:0 0 20px}" +
    ".ga-audit-close{position:absolute;top:14px;right:14px;width:36px;height:36px;" +
    "border-radius:9999px;border:1px solid #e6dfd8;background:#faf9f5;color:#141413;" +
    "cursor:pointer;font:400 18px/1 " + SANS + "}" +
    ".ga-audit-label{display:block;font:500 13px/1.4 " + SANS + ";color:#3d3d3a;" +
    "margin:0 0 4px}" +
    ".ga-audit-field{margin-bottom:14px}" +
    ".ga-audit-opt{color:#8e8b82;font-weight:400}" +
    // Toggle chips: the whole label is the hit area (>=44px tall incl. the 8px
    // gap), the checkbox itself stays in the a11y tree but is visually hidden.
    ".ga-audit-chips{display:flex;flex-wrap:wrap;gap:8px}" +
    ".ga-audit-chip{display:inline-flex;align-items:center;min-height:44px;" +
    "padding:0 14px;border:1px solid #e6dfd8;border-radius:9999px;background:#fff;" +
    "color:#3d3d3a;font:400 14px/1.2 " + SANS + ";cursor:pointer;user-select:none}" +
    ".ga-audit-chip-cb{position:absolute;opacity:0;width:1px;height:1px}" +
    ".ga-audit-chip.is-on{background:#ff8300;color:#141413;border-color:#ff8300}" +
    ".ga-audit-chip.is-focus{outline:2px solid #ff8300;outline-offset:2px}" +
    ".ga-audit-row{display:flex;gap:12px}.ga-audit-row .ga-audit-field{flex:1;min-width:0}" +
    ".ga-audit-input{width:100%;box-sizing:border-box;height:40px;background:#fff;" +
    "color:#141413;border:1px solid #e6dfd8;border-radius:8px;padding:10px 14px;" +
    "font:400 15px/1.4 " + SANS + ";outline:none}" +
    ".ga-audit-input:focus{border-color:#ff8300;box-shadow:0 0 0 3px rgba(255,131,0,.18)}" +
    ".ga-audit-submit{width:100%;height:44px;border:none;border-radius:8px;background:#ff8300;" +
    "color:#141413;font:500 15px/1 " + SANS + ";cursor:pointer;margin-top:6px}" +
    ".ga-audit-submit:active{background:#e8760a}" +
    ".ga-audit-submit[disabled]{background:#e6dfd8;color:#6c6a64;cursor:default}" +
    ".ga-audit-msg{margin-top:12px;font:400 13px/1.5 " + SANS + ";border-radius:8px;" +
    "padding:10px 12px;display:none}" +
    ".ga-audit-msg a{color:#c2410c}" +
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

  function field(label, name, type, placeholder, autocomplete, optional) {
    var id = "ga-audit-" + name;
    var input = el("input", {
      class: "ga-audit-input",
      id: id,
      name: name,
      type: type,
      placeholder: placeholder,
      autocomplete: autocomplete || "on",
    });
    var lab = el("label", { class: "ga-audit-label", for: id, text: label });
    if (optional) {
      lab.appendChild(el("span", { class: "ga-audit-opt", text: " (optional)" }));
    }
    return {
      wrap: el("div", { class: "ga-audit-field" }, [lab, input]),
      input: input,
    };
  }

  // Service interests — names mirror georgeai_services.json so the lead data
  // lines up with the service pages. Rendered as toggle chips: six stacked
  // checkbox rows would double the height of an already long modal.
  var SERVICES = [
    "SEO / AIO / GEO",
    "AI Chatbot",
    "Automation",
    "AI Phone Calls",
    "Web Design",
    "Lead Generation",
  ];

  function interestChips() {
    var inputs = [];
    var chips = SERVICES.map(function (name, i) {
      var id = "ga-audit-svc-" + i;
      var cb = el("input", { type: "checkbox", id: id, value: name, class: "ga-audit-chip-cb" });
      inputs.push(cb);
      var chip = el("label", { class: "ga-audit-chip", for: id }, [cb]);
      chip.appendChild(document.createTextNode(name));
      // Class toggle rather than :has() so the selected state survives on
      // browsers without :has() support.
      cb.addEventListener("change", function () {
        chip.classList.toggle("is-on", cb.checked);
      });
      // The checkbox is visually hidden, so the focus ring has to be drawn on
      // the chip itself — done in JS rather than :has() for older browsers.
      cb.addEventListener("focus", function () { chip.classList.add("is-focus"); });
      cb.addEventListener("blur", function () { chip.classList.remove("is-focus"); });
      return chip;
    });
    var wrap = el("div", { class: "ga-audit-field" }, [
      el("span", { class: "ga-audit-label", id: "ga-audit-svc-label" }, [
        el("span", { text: "Also interested in" }),
        el("span", { class: "ga-audit-opt", text: " (optional)" }),
      ]),
      el("div", { class: "ga-audit-chips", role: "group",
        "aria-labelledby": "ga-audit-svc-label" }, chips),
    ]);
    return {
      wrap: wrap,
      value: function () {
        return inputs.filter(function (c) { return c.checked; })
          .map(function (c) { return c.value; }).join(", ");
      },
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
    modal.replaceChildren(
      el("button", { class: "ga-audit-close", "aria-label": "Close", text: "×" }),
      el("div", { class: "ga-audit-done" }, [
        el("div", { class: "ga-audit-done-mark", text: "✓" }),
        el("div", { class: "ga-audit-title", text: "Request received" }),
        el("p", {
          class: "ga-audit-sub",
          // Deliberately does not promise the report itself: a repeat request
          // gets the "free audit already used" mail instead, and the webhook
          // answers before the workflow knows which branch it took.
          text:
            "We're working on it. Check " + email + " in the next few minutes — " +
            "everything comes by e-mail.",
        }),
      ])
    );
  }

  function open() {
    if (overlay) return;

    var fFirst = field("First name", "first_name", "text", "Jane", "given-name");
    var fLast = field("Surname", "surname", "text", "Doe", "family-name");
    var fEmail = field("E-mail address", "email", "email", "jane@company.com", "email");
    var fPhone = field("Contact number", "phone", "tel", "+27 82 000 0000", "tel", true);
    var fUrl = field("Website URL to audit", "website", "text", "yourcompany.com", "url");
    var fCompany = field("Company", "company_name", "text", "Acme Ltd", "organization", true);
    var interests = interestChips();

    // honeypot — humans never see it; bots that fill it are dropped in n8n
    var hp = el("input", { class: "ga-audit-input", name: "company", type: "text",
      tabindex: "-1", autocomplete: "off", "aria-hidden": "true" });

    var msg = el("div", { class: "ga-audit-msg" });
    var submit = el("button", { class: "ga-audit-submit", type: "submit",
      text: "Get my free audit" });

    var form = el("form", { novalidate: "novalidate" }, [
      el("div", { class: "ga-audit-row" }, [fFirst.wrap, fLast.wrap]),
      fEmail.wrap,
      fPhone.wrap,
      fUrl.wrap,
      fCompany.wrap,
      interests.wrap,
      el("div", { class: "ga-audit-hp" }, [hp]),
      submit,
      msg,
      el("p", {
        class: "ga-audit-fine",
        text: "Free, no obligation. Your details are only used to send the report.",
      }),
    ]);

    var modal = el("div", { id: "ga-audit-modal", role: "dialog", "aria-modal": "true" }, [
      el("button", { class: "ga-audit-close", "aria-label": "Close", text: "×" }),
      el("span", { class: "ga-audit-badge", text: "Free · 5 minutes" }),
      el("div", { class: "ga-audit-title", text: "Free Visibility Audit" }),
      el("p", {
        class: "ga-audit-sub",
        text:
          "See how your website performs in Google search and inside AI assistants " +
          "like ChatGPT, Claude and Perplexity — one report covering SEO, AEO, " +
          "AIO & GEO, straight to your inbox.",
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
        company_name: fCompany.input.value.trim(),
        interests: interests.value(),
        company: hp.value, // honeypot — must stay named "company"
        page: location.href,
      };

      if (!payload.first_name || !payload.surname) {
        setMsg(msg, "Please fill in your name.", true); return;
      }
      if (!/^[^\s@]+@[^\s@]+\.[^\s@]{2,}$/.test(payload.email)) {
        setMsg(msg, "Please enter a valid e-mail address.", true); return;
      }
      if (!payload.website) {
        setMsg(msg, "Please enter a valid website URL.", true); return;
      }

      setMsg(msg, "", false);
      submit.disabled = true;
      submit.textContent = "Starting your audit…";

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
          submit.textContent = "Get my free audit";
          setMsg(msg,
            "Something went wrong sending your request. Please try again, or email",
            true, true);
        });
    });

    document.body.appendChild(overlay);
    fFirst.input.focus();
  }

  // ---- floating button ---------------------------------------------------
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
    fab.appendChild(document.createTextNode("Free Visibility Audit"));
    fab.addEventListener("click", open);
    document.body.appendChild(fab);
  }

  window.gaAudit = { open: open, close: close };

  if (document.readyState !== "loading") mount();
  else document.addEventListener("DOMContentLoaded", mount);
})();
