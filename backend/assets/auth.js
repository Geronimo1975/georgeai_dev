/*
 * georgeai.dev — auth bridge
 *
 * Wires the static design-export signin/signup modal to the Django session
 * auth API (/api/auth/*). The export is regenerated on every deploy and its
 * form fields have no ids, so this script hooks by structure (input type +
 * position) via event delegation — surviving the design runtime's re-renders.
 *
 * It degrades gracefully: if /api/auth/* is unavailable (e.g. the current
 * nginx-only production), nothing happens and the form stays decorative.
 *
 * Injected into index.html by deploy.sh.
 */
(function () {
  "use strict";

  var API = "/api/auth";
  var ORANGE = "rgb(204, 120, 92)"; // #cc785c — the primary CTA colour

  // ---- helpers ----------------------------------------------------------
  function getCookie(name) {
    var m = document.cookie.match("(^|;)\\s*" + name + "\\s*=\\s*([^;]+)");
    return m ? decodeURIComponent(m.pop()) : "";
  }

  function api(path, body) {
    return fetch(API + path, {
      method: body === undefined ? "GET" : "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRFToken": getCookie("csrftoken"),
      },
      credentials: "same-origin",
      body: body === undefined ? undefined : JSON.stringify(body),
    }).then(function (r) {
      return r.json().then(function (data) {
        return { ok: r.ok, status: r.status, data: data };
      });
    });
  }

  function visible(el) {
    if (!el) return false;
    if (typeof el.checkVisibility === "function") return el.checkVisibility();
    return !!(el.offsetWidth || el.offsetHeight || el.getClientRects().length);
  }

  // The auth modal is any ancestor that contains a password input.
  function authModalFor(el) {
    for (var n = el; n && n !== document.body; n = n.parentElement) {
      if (n.querySelector && n.querySelector('input[type="password"]')) return n;
    }
    return null;
  }

  function isPrimaryCta(btn, modal) {
    if (btn.tagName !== "BUTTON" || !modal.contains(btn)) return false;
    var cs = getComputedStyle(btn);
    // full-width orange button = the submit CTA, not the small tab/switch links
    return cs.backgroundColor === ORANGE && btn.offsetWidth > 180;
  }

  // Collect the form fields from a modal by type + DOM order.
  function readForm(modal) {
    var inputs = Array.prototype.filter.call(
      modal.querySelectorAll("input"),
      visible
    );
    var passwords = inputs.filter(function (i) {
      return i.type === "password";
    });
    var texts = inputs.filter(function (i) {
      return i.type === "text" || i.type === "email" || i.type === "";
    });
    var checkbox = modal.querySelector('input[type="checkbox"]');

    var signup = passwords.length >= 2; // confirm field visible => signup
    // email is the last text input before the first password (name precedes it)
    var emailInput = texts.length ? texts[texts.length - 1] : null;
    var nameInput = signup && texts.length >= 2 ? texts[0] : null;

    return {
      signup: signup,
      name: nameInput ? nameInput.value.trim() : "",
      email: emailInput ? emailInput.value.trim() : "",
      password: passwords[0] ? passwords[0].value : "",
      confirm: passwords[1] ? passwords[1].value : "",
      remember: checkbox ? checkbox.checked : false,
    };
  }

  // ---- inline feedback inside the modal ---------------------------------
  function setMessage(modal, text, isError) {
    var box = modal.querySelector("[data-auth-msg]");
    if (!box) {
      box = document.createElement("div");
      box.setAttribute("data-auth-msg", "");
      box.style.cssText =
        "margin-top:14px;font-size:13px;text-align:center;border-radius:8px;padding:8px 10px";
      var pwd = modal.querySelector('input[type="password"]');
      (pwd && pwd.parentElement ? pwd.parentElement : modal).appendChild(box);
    }
    box.textContent = text || "";
    box.style.display = text ? "block" : "none";
    box.style.color = isError ? "#ff9b87" : "#9fd6a3";
  }

  function closeModal(modal) {
    // try the export's own close affordance, else just hide the overlay
    var overlay = modal;
    for (var n = modal; n && n !== document.body; n = n.parentElement) {
      var cs = getComputedStyle(n);
      if (cs.position === "fixed") {
        overlay = n;
        break;
      }
    }
    overlay.style.display = "none";
  }

  // ---- signed-in badge (self-contained; independent of the export) ------
  function renderBadge(state) {
    var badge = document.getElementById("ga-auth-badge");
    if (!state.authenticated) {
      if (badge) badge.remove();
      document.body.removeAttribute("data-user");
      return;
    }
    document.body.setAttribute("data-user", state.email);
    if (!badge) {
      badge = document.createElement("div");
      badge.id = "ga-auth-badge";
      badge.style.cssText =
        "position:fixed;right:16px;bottom:16px;z-index:99999;display:flex;gap:10px;" +
        "align-items:center;background:#201f1c;color:#faf9f5;border:1px solid #2f2c28;" +
        "border-radius:12px;padding:10px 14px;font:13px/1.2 system-ui,sans-serif;" +
        "box-shadow:0 6px 24px rgba(0,0,0,.35)";
      document.body.appendChild(badge);
    }
    badge.replaceChildren();
    var who = document.createElement("span");
    who.textContent = state.name || state.email;
    var out = document.createElement("button");
    out.textContent = "Log out";
    out.style.cssText =
      "cursor:pointer;border:none;border-radius:8px;background:#cc785c;color:#fff;" +
      "padding:6px 10px;font:600 12px system-ui,sans-serif";
    out.addEventListener("click", function () {
      api("/logout", {}).then(refreshState);
    });
    badge.appendChild(who);
    badge.appendChild(out);
  }

  function refreshState() {
    return api("/me").then(function (res) {
      renderBadge(res.data || { authenticated: false });
      return res.data;
    });
  }

  // ---- submit handling --------------------------------------------------
  function errorText(data, status) {
    if (data && data.detail && data.detail.length) return data.detail[0];
    var map = {
      invalid_credentials: "Wrong email or password.",
      email_taken: "That email is already registered.",
      email_and_password_required: "Email and password are required.",
      weak_password: "Please choose a stronger password.",
    };
    return (data && map[data.error]) || "Something went wrong (" + status + ").";
  }

  function submit(modal) {
    var f = readForm(modal);
    if (!f.email || !f.password) {
      setMessage(modal, "Email and password are required.", true);
      return;
    }
    if (f.signup && f.confirm && f.password !== f.confirm) {
      setMessage(modal, "Passwords don't match.", true);
      return;
    }
    setMessage(modal, "…", false);

    var req = f.signup
      ? api("/signup", { name: f.name, email: f.email, password: f.password })
      : api("/login", { email: f.email, password: f.password, remember: f.remember });

    req
      .then(function (res) {
        if (res.ok) {
          renderBadge(res.data);
          setMessage(modal, "Signed in.", false);
          setTimeout(function () {
            closeModal(modal);
          }, 500);
        } else {
          setMessage(modal, errorText(res.data, res.status), true);
        }
      })
      .catch(function () {
        // API absent (e.g. nginx-only prod) — stay quiet, leave form decorative
        setMessage(modal, "", false);
      });
  }

  // ---- wire up (event delegation survives runtime re-renders) -----------
  document.addEventListener(
    "click",
    function (e) {
      var btn = e.target.closest && e.target.closest("button");
      if (!btn) return;
      var modal = authModalFor(btn);
      if (!modal || !isPrimaryCta(btn, modal)) return;
      e.preventDefault();
      submit(modal);
    },
    true
  );

  // submit on Enter inside a password field
  document.addEventListener("keydown", function (e) {
    if (e.key !== "Enter") return;
    var t = e.target;
    if (!t || t.tagName !== "INPUT" || t.type !== "password") return;
    var modal = authModalFor(t);
    if (modal) {
      e.preventDefault();
      submit(modal);
    }
  });

  // reflect existing session on load
  if (document.readyState !== "loading") refreshState();
  else document.addEventListener("DOMContentLoaded", refreshState);
})();
