/* GeorgeAI Console — no-build SPA (prompts 04.03–04.12).
   Talks to /api/console/v1/*; replies stream as SSE over a POST fetch. */
(() => {
  "use strict";

  const API = "/api/console/v1";
  const $ = (id) => document.getElementById(id);
  const els = {
    app: $("app"), main: $("main"), convList: $("convList"), search: $("searchInput"),
    thread: $("thread"), inner: $("threadInner"), input: $("input"), composer: $("composer"),
    send: $("sendBtn"), modelBtn: $("modelBtn"), styleBtn: $("styleBtn"), styleName: $("styleName"), modelName: $("modelName"), greeting: $("greeting"),
    chips: $("chips"), title: $("convTitle"), actions: $("convActions"), star: $("starBtn"),
    del: $("deleteBtn"), demo: $("demoPill"), menu: $("menu"), toast: $("toast"), jump: $("jumpBtn"),
    userBtn: $("userBtn"), userName: $("userName"), userAvatar: $("userAvatar"), scrim: $("scrim"),
  };

  const ICON = {
    copy: '<svg viewBox="0 0 24 24"><rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/></svg>',
    check: '<svg viewBox="0 0 24 24"><path d="m5 12 5 5 9-10"/></svg>',
    retry: '<svg viewBox="0 0 24 24"><path d="M3 12a9 9 0 0 1 15.5-6.2L21 8M21 3v5h-5M21 12a9 9 0 0 1-15.5 6.2L3 16M3 21v-5h5"/></svg>',
    more: '<svg viewBox="0 0 24 24"><circle cx="5" cy="12" r="1.2"/><circle cx="12" cy="12" r="1.2"/><circle cx="19" cy="12" r="1.2"/></svg>',
    star: '<svg viewBox="0 0 24 24"><path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1-4.4-4.3 6.1-.9z"/></svg>',
    edit: '<svg viewBox="0 0 24 24"><path d="M4 20h4L19 9l-4-4L4 16z"/></svg>',
    trash: '<svg viewBox="0 0 24 24"><path d="M4 7h16M6 7l1 12a2 2 0 0 0 2 2h6a2 2 0 0 0 2-2l1-12M9 7V4h6v3"/></svg>',
    code: '<svg viewBox="0 0 24 24"><path d="m8 7-5 5 5 5M16 7l5 5-5 5"/></svg>',
    flow: '<svg viewBox="0 0 24 24"><circle cx="6" cy="6" r="2.5"/><circle cx="18" cy="18" r="2.5"/><path d="M8.5 6H14a4 4 0 0 1 4 4v5.5"/></svg>',
    search: '<svg viewBox="0 0 24 24"><circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/></svg>',
    spark: '<svg viewBox="0 0 24 24"><path d="M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5 18 18M6 18l2.5-2.5M15.5 8.5 18 6"/></svg>',
    sun: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="4"/><path d="M12 2v2M12 20v2M4.9 4.9l1.4 1.4M17.7 17.7l1.4 1.4M2 12h2M20 12h2M4.9 19.1l1.4-1.4M17.7 6.3l1.4-1.4"/></svg>',
    shield: '<svg viewBox="0 0 24 24"><path d="M12 3 4 6v6c0 4.5 3.4 8.3 8 9 4.6-.7 8-4.5 8-9V6z"/></svg>',
    out: '<svg viewBox="0 0 24 24"><path d="M15 4h3a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-3M10 17l5-5-5-5M15 12H3"/></svg>',
    ok: '<svg viewBox="0 0 24 24" class="check"><path d="m5 12 5 5 9-10"/></svg>',
    up: '<svg viewBox="0 0 24 24"><path d="M7 11v9H4v-9zM7 11l4-8a2 2 0 0 1 2 2v4h5.5a2 2 0 0 1 2 2.3l-1.2 7A2 2 0 0 1 17.3 20H7"/></svg>',
    down: '<svg viewBox="0 0 24 24"><path d="M7 13V4H4v9zM7 13l4 8a2 2 0 0 0 2-2v-4h5.5a2 2 0 0 0 2-2.3l-1.2-7A2 2 0 0 0 17.3 4H7"/></svg>',
    gear: '<svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/></svg>',
    plus: '<svg viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>',
    prev: '<svg viewBox="0 0 24 24"><path d="m15 18-6-6 6-6"/></svg>',
    next: '<svg viewBox="0 0 24 24"><path d="m9 18 6-6-6-6"/></svg>',
  };

  const SUGGESTIONS = [
    { icon: "code", text: "Plan a Django + PostgreSQL app", prompt: "Help me plan a Django 5 + PostgreSQL web app. Ask me 3 short questions about the business first, then propose the data model and the first sprint." },
    { icon: "flow", text: "Automate a workflow with n8n", prompt: "I want to automate a business process with n8n. Ask me what the process is, then sketch the workflow node by node." },
    { icon: "search", text: "Audit my site for SEO & GEO", prompt: "Give me a checklist to audit a company website for classic SEO and for visibility in AI answers (GEO/AIO), ordered by impact." },
    { icon: "spark", text: "Find AI quick wins", prompt: "What are 5 realistic AI quick wins for a small B2B services company in Germany? Keep each to two sentences with expected effort." },
  ];

  const state = {
    user: null, models: [], provider: "fake", defaultModel: "",
    conversations: [], currentId: null, messages: [],
    model: null, stream: null, filter: "", stick: true,
    searchResults: null, editing: null,
    prefs: {}, styles: [], style: null,
  };

  // ------------------------------------------------------------------ utils
  const csrf = () => (document.cookie.match(/(?:^|; )csrftoken=([^;]+)/) || [])[1] || "";
  const store = {
    get(k, d) { try { return localStorage.getItem(k) ?? d; } catch { return d; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch {} },
  };
  const esc = (s) => s.replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));

  async function api(path, opts = {}) {
    const res = await fetch(API + path, {
      method: opts.method || "GET",
      headers: { "Content-Type": "application/json", "X-CSRFToken": csrf() },
      body: opts.body ? JSON.stringify(opts.body) : undefined,
      credentials: "same-origin",
    });
    if (res.status === 401) { location.href = "/console/login/?next=" + encodeURIComponent(location.pathname); throw new Error("auth"); }
    if (res.status === 204) return null;
    const data = await res.json().catch(() => ({}));
    if (!res.ok) { const err = new Error(data?.error?.message || `Request failed (${res.status})`); err.data = data; throw err; }
    return data;
  }

  let toastTimer;
  function toast(msg) {
    els.toast.textContent = msg; els.toast.hidden = false;
    clearTimeout(toastTimer); toastTimer = setTimeout(() => (els.toast.hidden = true), 2200);
  }

  function renderMarkdown(text) {
    if (!window.marked || !window.DOMPurify) return `<p>${esc(text).replace(/\n/g, "<br>")}</p>`;
    const html = marked.parse(text, { gfm: true, breaks: false });
    // Block remote images: a reply must not be able to beacon data out via <img src>.
    return DOMPurify.sanitize(html, { FORBID_TAGS: ["img", "style", "iframe", "form"], ADD_ATTR: ["target"] });
  }

  function enhanceCode(root) {
    root.querySelectorAll("pre").forEach((pre) => {
      if (pre.parentElement.classList.contains("code")) return;
      const lang = (pre.querySelector("code")?.className.match(/language-(\S+)/) || [])[1] || "text";
      const wrap = document.createElement("div");
      wrap.className = "code";
      wrap.innerHTML = `<div class="code-head"><span>${esc(lang)}</span><button type="button">${ICON.copy}<span>Copy</span></button></div>`;
      pre.replaceWith(wrap); wrap.appendChild(pre);
      wrap.querySelector("button").addEventListener("click", (e) => copy(pre.innerText, e.currentTarget));
    });
    root.querySelectorAll("a[href]").forEach((a) => { a.target = "_blank"; a.rel = "noopener noreferrer"; });
  }

  async function copy(text, btn) {
    try { await navigator.clipboard.writeText(text); } catch { return toast("Copy failed"); }
    if (btn) {
      const prev = btn.innerHTML;
      btn.innerHTML = ICON.check + (btn.querySelector("span") ? "<span>Copied</span>" : "");
      setTimeout(() => (btn.innerHTML = prev), 1400);
    } else toast("Copied");
  }

  // ------------------------------------------------------------------ menu
  function openMenu(anchor, items, align = "start") {
    const m = els.menu;
    m.innerHTML = "";
    items.forEach((it) => {
      if (it === "-") return m.insertAdjacentHTML("beforeend", '<div class="menu-sep"></div>');
      if (it.label) return m.insertAdjacentHTML("beforeend", `<div class="menu-label">${esc(it.label)}</div>`);
      const b = document.createElement("button");
      b.type = "button"; b.className = "menu-item" + (it.danger ? " danger" : ""); b.setAttribute("role", "menuitem");
      b.innerHTML = (it.icon ? ICON[it.icon] : "") + `<span>${esc(it.text)}${it.desc ? `<span class="desc">${esc(it.desc)}</span>` : ""}</span>` + (it.checked ? ICON.ok : "");
      b.addEventListener("click", () => { closeMenu(); it.onClick(); });
      m.appendChild(b);
    });
    m.hidden = false;
    anchor.setAttribute("aria-expanded", "true");
    m._anchor = anchor;
    const r = anchor.getBoundingClientRect(), mr = m.getBoundingClientRect();
    let top = r.bottom + 6;
    if (top + mr.height > innerHeight - 8) top = r.top - mr.height - 6;
    let left = align === "end" ? r.right - mr.width : r.left;
    left = Math.max(8, Math.min(left, innerWidth - mr.width - 8));
    m.style.top = `${Math.max(8, top)}px`; m.style.left = `${left}px`;
    m.querySelector(".menu-item")?.focus();
  }
  function closeMenu() {
    if (els.menu.hidden) return;
    els.menu.hidden = true;
    els.menu._anchor?.setAttribute("aria-expanded", "false");
  }
  document.addEventListener("click", (e) => {
    if (!els.menu.hidden && !els.menu.contains(e.target) && !els.menu._anchor?.contains(e.target)) closeMenu();
  });

  // ------------------------------------------------------------------ sidebar
  function groupOf(c) {
    if (c.is_starred) return "Starred";
    const d = new Date(c.updated_at), now = new Date();
    const day = (x) => new Date(x.getFullYear(), x.getMonth(), x.getDate()).getTime();
    const diff = (day(now) - day(d)) / 86400000;
    if (diff < 1) return "Today";
    if (diff < 2) return "Yesterday";
    if (diff < 7) return "Previous 7 days";
    if (diff < 30) return "Previous 30 days";
    return "Older";
  }

  // Full-text search (02.09): title filter is instant and local; from 2 chars
  // the server also searches message content and returns highlighted snippets.
  const snippetHtml = (s) => esc(s).replace(/\x02/g, "<mark>").replace(/\x03/g, "</mark>");
  let searchTimer, searchSeq = 0;
  function runSearch() {
    clearTimeout(searchTimer);
    const q = state.filter.trim();
    if (q.length < 2) { state.searchResults = null; return renderSidebar(); }
    renderSidebar();
    searchTimer = setTimeout(async () => {
      const seq = ++searchSeq;
      const data = await api(`/search?q=${encodeURIComponent(q)}`).catch(() => null);
      if (seq !== searchSeq || state.filter.trim() !== q || !data) return;
      state.searchResults = data.results;
      renderSidebar();
    }, 220);
  }

  function renderSearchResults() {
    els.convList.innerHTML = "";
    const sec = document.createElement("div");
    sec.className = "sb-group";
    sec.innerHTML = `<div class="sb-group-title">Search results</div>`;
    if (!state.searchResults.length) {
      els.convList.innerHTML = '<p class="sb-empty">No chats or messages match your search.</p>';
      return;
    }
    state.searchResults.forEach((r) => {
      const c = r.conversation, a = document.createElement("a");
      a.className = "sb-result" + (c.id === state.currentId ? " is-active" : "");
      a.href = `/console/chat/${c.id}`; a.dataset.link = "";
      a.innerHTML = `<span class="sb-result-title">${esc(c.title || "New chat")}</span>` +
        (r.snippet ? `<span class="sb-result-snippet">${snippetHtml(r.snippet)}</span>` : "");
      sec.appendChild(a);
    });
    els.convList.appendChild(sec);
  }

  function renderSidebar(newId) {
    if (state.searchResults && state.filter.trim().length >= 2) return renderSearchResults();
    const order = ["Starred", "Today", "Yesterday", "Previous 7 days", "Previous 30 days", "Older"];
    const q = state.filter.toLowerCase();
    const list = state.conversations.filter((c) => !q || (c.title || "New chat").toLowerCase().includes(q));
    const groups = {};
    list.forEach((c) => (groups[groupOf(c)] ||= []).push(c));
    els.convList.innerHTML = "";
    if (!list.length) {
      els.convList.innerHTML = `<p class="sb-empty">${q ? "No chats match your search." : "Your chats will show up here."}</p>`;
      return;
    }
    order.filter((g) => groups[g]).forEach((g) => {
      const sec = document.createElement("div");
      sec.className = "sb-group";
      sec.innerHTML = `<div class="sb-group-title">${g}</div>`;
      groups[g].forEach((c) => {
        const item = document.createElement("div");
        item.className = "sb-item" + (c.id === state.currentId ? " is-active" : "") + (c.id === newId ? " is-new" : "");
        item.dataset.id = c.id;
        item.innerHTML = `<a href="/console/chat/${c.id}" data-link title="${esc(c.title || "New chat")}">${esc(c.title || "New chat")}</a>
          <button class="icon-btn more" type="button" aria-label="Chat options" aria-haspopup="menu">${ICON.more}</button>`;
        item.querySelector(".more").addEventListener("click", (e) => {
          e.stopPropagation();
          openMenu(e.currentTarget, [
            { icon: "star", text: c.is_starred ? "Unstar" : "Star", onClick: () => toggleStar(c.id) },
            { icon: "edit", text: "Rename", onClick: () => renameInline(item, c) },
            "-",
            { icon: "trash", text: "Delete", danger: true, onClick: () => deleteConv(c.id) },
          ], "end");
        });
        sec.appendChild(item);
      });
      els.convList.appendChild(sec);
    });
  }

  function renameInline(item, c) {
    const input = document.createElement("input");
    input.value = c.title || ""; input.setAttribute("aria-label", "Chat title");
    item.replaceChildren(input); input.focus(); input.select();
    let done = false;
    const finish = (save) => {
      if (done) return; done = true;
      if (save && input.value.trim() && input.value.trim() !== c.title) rename(c.id, input.value.trim());
      else renderSidebar();
    };
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") finish(true); if (e.key === "Escape") finish(false); });
    input.addEventListener("blur", () => finish(true));
  }

  const conv = (id) => state.conversations.find((c) => c.id === id);

  async function rename(id, title) {
    const updated = await api(`/conversations/${id}`, { method: "PATCH", body: { title } }).catch((e) => toast(e.message));
    if (updated) Object.assign(conv(id), { title: updated.title });
    renderSidebar(); renderHeader();
  }

  async function toggleStar(id) {
    const c = conv(id); if (!c) return;
    c.is_starred = !c.is_starred; renderSidebar(); renderHeader();
    await api(`/conversations/${id}`, { method: "PATCH", body: { is_starred: c.is_starred } })
      .catch((e) => { c.is_starred = !c.is_starred; renderSidebar(); renderHeader(); toast(e.message); });
  }

  async function deleteConv(id) {
    const c = conv(id);
    if (!confirm(`Delete “${c?.title || "New chat"}”? This can’t be undone.`)) return;
    await api(`/conversations/${id}`, { method: "DELETE" }).catch((e) => toast(e.message));
    state.conversations = state.conversations.filter((x) => x.id !== id);
    if (state.currentId === id) navigate("/console/new"); else renderSidebar();
    toast("Chat deleted");
  }

  // ------------------------------------------------------------------ header / models
  function renderHeader() {
    const c = conv(state.currentId);
    els.title.hidden = els.actions.hidden = !c;
    if (c) {
      els.title.textContent = c.title || "New chat";
      els.star.classList.toggle("is-on", c.is_starred);
      els.star.setAttribute("aria-label", c.is_starred ? "Unstar" : "Star");
      document.title = `${c.title || "New chat"} · GeorgeAI Console`;
    } else document.title = "GeorgeAI Console";
    // Demo pill follows the selected model: Claude may be live while DeepSeek is not.
    const info = modelInfo(state.model);
    els.demo.hidden = info ? info.live !== false : state.provider !== "fake";
  }

  function modelInfo(id) { return state.models.find((m) => m.id === id) || state.models[0]; }
  function setModel(id) {
    state.model = id; store.set("gai-model", id);
    els.modelName.textContent = modelInfo(id)?.name || id;
    renderHeader();
  }
  // PATCHes are chained so an older pick can never land after a newer one.
  let modelSave = Promise.resolve();
  function saveModel(convId, model) {
    modelSave = modelSave.then(() => api(`/conversations/${convId}`, { method: "PATCH", body: { model } })).catch(() => {});
  }
  const knownModel = (id) => state.models.some((m) => m.id === id);
  // New chat: the default from Settings wins; the last-used model is only the
  // fallback when no default is set.
  function applyDefaults() {
    const pref = state.prefs.default_model, saved = store.get("gai-model", state.defaultModel);
    setModel(knownModel(pref) ? pref : knownModel(saved) ? saved : state.defaultModel);
    setStyle(state.prefs.default_style_id || null);
  }

  // Grouped by vendor once more than one is configured (Claude / DeepSeek).
  els.modelBtn.addEventListener("click", (e) => {
    const items = [], vendors = [...new Set(state.models.map((m) => m.vendor_name || ""))];
    vendors.forEach((v, i) => {
      if (vendors.length > 1) { if (i) items.push("-"); items.push({ label: v }); }
      state.models.filter((m) => (m.vendor_name || "") === v).forEach((m) => items.push({
        text: m.name, checked: m.id === state.model,
        desc: [m.description, m.data_note, m.live === false ? "Demo mode" : ""].filter(Boolean).join(" · "),
        onClick: () => {
          setModel(m.id);
          if (state.currentId) saveModel(state.currentId, m.id);
        },
      }));
    });
    openMenu(e.currentTarget, items, "end");
  });

  // ------------------------------------------------------------------ thread
  function greeting() {
    const h = new Date().getHours();
    const part = h < 5 ? "Working late" : h < 12 ? "Good morning" : h < 18 ? "Good afternoon" : "Good evening";
    return `${part}, ${state.user?.name || "there"}`;
  }

  function renderChips() {
    els.chips.innerHTML = "";
    SUGGESTIONS.forEach((s) => {
      const b = document.createElement("button");
      b.type = "button"; b.className = "chip"; b.innerHTML = ICON[s.icon] + esc(s.text);
      b.addEventListener("click", () => { els.input.value = s.prompt; autosize(); updateSend(); els.input.focus(); });
      els.chips.appendChild(b);
    });
  }

  function renderThread(scroll = true) {
    const empty = !state.currentId && !state.messages.length;
    els.main.classList.toggle("is-empty", empty);
    if (empty) { els.greeting.textContent = greeting(); return; }
    els.inner.innerHTML = "";
    state.messages.forEach((m, i) => els.inner.appendChild(messageEl(m, i === state.messages.length - 1)));
    if (scroll) scrollToBottom(true);
  }

  function messageEl(m, isLast) {
    const el = document.createElement("div");
    el.className = `msg ${m.role}` + (isLast ? " is-last" : "") + (m.streaming ? " streaming" : "");
    el.dataset.id = m.id;
    if (m.role === "user") {
      if (state.editing === m.id) return editorEl(el, m);
      el.innerHTML = `<div class="bubble"></div><div class="msg-actions"></div>`;
      el.querySelector(".bubble").textContent = m.content;
      branchNav(el, m);
      addAction(el, "copy", "Copy", (btn) => copy(m.content, btn));
      if (!state.stream && !String(m.id).startsWith("tmp-")) addAction(el, "edit", "Edit", () => startEdit(m.id));
      return el;
    }
    el.innerHTML = `<div class="mark" aria-hidden="true"></div><div class="msg-body"><div class="md"></div></div><div class="msg-actions"></div>`;
    paintAssistant(el, m);
    return el;
  }

  // "< 2/3 >" between edits of a user turn or regenerations of a reply (02.07).
  function branchNav(el, m) {
    const sibs = m.siblings || [];
    if (sibs.length < 2) return;
    const i = sibs.indexOf(m.id);
    const nav = document.createElement("div");
    nav.className = "branch-nav";
    nav.setAttribute("role", "group"); nav.setAttribute("aria-label", "Response versions");
    nav.innerHTML = `<button type="button" class="icon-btn" aria-label="Previous version" ${i <= 0 ? "disabled" : ""}>${ICON.prev}</button>` +
      `<span aria-live="polite">${i + 1} / ${sibs.length}</span>` +
      `<button type="button" class="icon-btn" aria-label="Next version" ${i >= sibs.length - 1 ? "disabled" : ""}>${ICON.next}</button>`;
    const [prev, next] = nav.querySelectorAll("button");
    prev.addEventListener("click", () => switchBranch(sibs[i - 1]));
    next.addEventListener("click", () => switchBranch(sibs[i + 1]));
    if (state.stream) prev.disabled = next.disabled = true;
    el.querySelector(".msg-actions").appendChild(nav);
  }

  async function switchBranch(messageId) {
    if (state.stream || !messageId) return;
    const id = state.currentId;
    const data = await api(`/conversations/${id}/branch`, { method: "POST", body: { message_id: messageId } })
      .catch((e) => { toast(e.message); return null; });
    if (!data || state.currentId !== id) return;
    const keep = els.thread.scrollTop;
    state.messages = data.messages; state.editing = null;
    renderThread(); els.thread.scrollTop = keep; scrollToBottom();
  }

  function startEdit(id) {
    if (state.stream) return;
    state.editing = id;
    renderThread(false);
    const ta = els.inner.querySelector(".msg-edit textarea");
    if (ta) { ta.focus(); ta.setSelectionRange(ta.value.length, ta.value.length); }
  }

  function editorEl(el, m) {
    el.classList.add("is-editing");
    el.innerHTML = `<form class="msg-edit"><textarea rows="1" aria-label="Edit message"></textarea>
      <div class="msg-edit-bar"><span class="msg-edit-hint">Editing creates a new branch — the original stays available.</span>
      <button type="button" class="btn-ghost">Cancel</button><button type="submit" class="btn-accent">Save</button></div></form>`;
    const form = el.querySelector("form"), ta = el.querySelector("textarea");
    ta.value = m.content;
    const size = () => { ta.style.height = "auto"; ta.style.height = Math.min(ta.scrollHeight, innerHeight * 0.4) + "px"; };
    requestAnimationFrame(size);
    const cancel = () => { state.editing = null; renderThread(false); };
    ta.addEventListener("input", () => { size(); form.querySelector("[type=submit]").disabled = !ta.value.trim(); });
    ta.addEventListener("keydown", (e) => {
      if (e.key === "Escape") { e.stopPropagation(); cancel(); }
      if (e.key === "Enter" && !e.shiftKey && !e.isComposing) { e.preventDefault(); form.requestSubmit(); }
    });
    form.querySelector(".btn-ghost").addEventListener("click", cancel);
    form.addEventListener("submit", (e) => {
      e.preventDefault();
      const content = ta.value.trim();
      if (!content || state.stream) return;
      if (content === m.content) return cancel();
      const at = state.messages.findIndex((x) => x.id === m.id);
      state.editing = null;
      state.messages = state.messages.slice(0, at);
      state.messages.push({ id: "tmp-" + Date.now(), role: "user", content });
      runStream({ content, edit_of: m.id, model: state.model });
    });
    return el;
  }

  // 👍/👎 (04.08): toggle, aria-pressed; 👎 asks for an optional comment.
  function rateButton(el, m, value, icon, label) {
    addAction(el, icon, label, () => rate(m, m.rating === value ? 0 : value));
    const b = el.querySelector(".msg-actions").lastElementChild;
    b.setAttribute("aria-pressed", String(m.rating === value));
    b.classList.toggle("is-on", m.rating === value);
  }

  // Requests per message run one after another, so the server applies them in
  // click order; only the newest click's outcome is painted.
  const rateQueue = new Map();
  function rate(m, value, comment = "") {
    const seq = (m.rateSeq = (m.rateSeq || 0) + 1);
    const prev = m.rating || 0;
    m.rating = value; repaint(m);
    const run = (rateQueue.get(m.id) || Promise.resolve()).then(async () => {
      let res;
      try { res = await api(`/messages/${m.id}/feedback`, { method: "POST", body: { rating: value, comment } }); }
      catch (e) { if (seq === m.rateSeq) { m.rating = prev; repaint(m); } return toast(e.message); }
      if (seq !== m.rateSeq) return;
      m.rating = res.rating; repaint(m);
      if (value === -1 && !comment) askFeedback(m);
      else if (value) toast(comment ? "Thanks — feedback sent" : "Thanks for the feedback");
    });
    rateQueue.set(m.id, run);
    return run;
  }

  function repaint(m) {
    const el = els.inner.querySelector(`.msg[data-id="${m.id}"]`);
    if (el && m.role === "assistant") paintAssistant(el, m);
  }

  const feedbackDlg = $("feedbackDialog");
  function askFeedback(m) {
    $("feedbackText").value = "";
    feedbackDlg._msg = m;
    feedbackDlg.showModal();
  }
  $("feedbackForm").addEventListener("submit", (e) => {
    e.preventDefault();
    const m = feedbackDlg._msg, text = $("feedbackText").value.trim();
    feedbackDlg.close();
    if (m && text) rate(m, -1, text);
  });

  function addAction(el, icon, label, fn) {
    const b = document.createElement("button");
    b.type = "button"; b.className = "icon-btn"; b.innerHTML = ICON[icon];
    b.setAttribute("aria-label", label); b.title = label;
    b.addEventListener("click", () => fn(b));
    el.querySelector(".msg-actions").appendChild(b);
  }

  function paintAssistant(el, m) {
    const md = el.querySelector(".md"), body = el.querySelector(".msg-body");
    el.classList.toggle("streaming", !!m.streaming);
    if (m.streaming && !m.content) md.innerHTML = '<span class="thinking-dots" aria-label="Thinking"><i></i><i></i><i></i></span>';
    else { md.innerHTML = renderMarkdown(m.content); enhanceCode(md); }
    body.querySelectorAll(".msg-note, .msg-error").forEach((n) => n.remove());
    if (m.stop_reason === "user_cancelled") body.insertAdjacentHTML("beforeend", '<div class="msg-note">Stopped by you.</div>');
    if (m.stop_reason === "error" && !m.error && !m.streaming) m.error = "This response failed to generate.";
    if (m.error) {
      body.insertAdjacentHTML("beforeend", `<div class="msg-error" role="alert"><span>${esc(m.error)}</span><button type="button">Retry</button></div>`);
      body.querySelector(".msg-error button").addEventListener("click", regenerate);
    }
    const actions = el.querySelector(".msg-actions");
    actions.innerHTML = "";
    if (!m.streaming) branchNav(el, m);
    if (!m.streaming) {
      addAction(el, "copy", "Copy", (btn) => copy(m.content, btn));
      if (!String(m.id).startsWith("pending") && m.content) {
        rateButton(el, m, 1, "up", "Good response");
        rateButton(el, m, -1, "down", "Bad response");
      }
      if (state.messages[state.messages.length - 1] === m && !state.stream) addAction(el, "retry", "Retry", regenerate);
    }
  }

  function nearBottom() { const t = els.thread; return t.scrollHeight - t.scrollTop - t.clientHeight < 80; }
  function scrollToBottom(force) {
    if (force || state.stick) els.thread.scrollTop = els.thread.scrollHeight;
    els.jump.hidden = nearBottom();
  }
  els.thread.addEventListener("scroll", () => { state.stick = nearBottom(); els.jump.hidden = state.stick; }, { passive: true });
  els.jump.addEventListener("click", () => { state.stick = true; els.thread.scrollTo({ top: els.thread.scrollHeight, behavior: "smooth" }); });

  // ------------------------------------------------------------------ composer
  function autosize() {
    const t = els.input; t.style.height = "auto"; t.style.height = Math.min(t.scrollHeight, innerHeight * 0.4) + "px";
  }
  function updateSend() {
    const streaming = !!state.stream;
    els.send.classList.toggle("is-stop", streaming);
    els.send.disabled = !streaming && !els.input.value.trim();
    els.send.setAttribute("aria-label", streaming ? "Stop response" : "Send message");
  }
  const draftKey = () => `gai-draft:${state.currentId || "new"}`;
  els.input.addEventListener("input", () => { autosize(); updateSend(); store.set(draftKey(), els.input.value); });
  els.input.addEventListener("keydown", (e) => {
    if (e.key !== "Enter" || e.shiftKey || e.isComposing) return;
    const mod = e.metaKey || e.ctrlKey;
    if (state.prefs.send_with_enter === false && !mod) return; // newline; ⌘/Ctrl+Enter sends
    e.preventDefault(); if (!state.stream) submit();
  });
  els.composer.addEventListener("submit", (e) => { e.preventDefault(); state.stream ? stop() : submit(); });

  async function submit() {
    const content = els.input.value.trim();
    if (!content || state.stream) return;
    store.set(draftKey(), ""); // clear before currentId changes, or the "new" draft lingers
    if (!state.currentId) {
      let c;
      try { c = await api("/conversations", { method: "POST", body: { model: state.model, style_id: state.style } }); }
      catch (e) { return toast(e.message); }
      state.conversations.unshift(c);
      state.currentId = c.id; state.messages = [];
      history.pushState({}, "", `/console/chat/${c.id}`);
      renderSidebar(); renderHeader();
    }
    els.input.value = ""; autosize();
    state.messages.push({ id: "tmp-" + Date.now(), role: "user", content });
    runStream({ content, model: state.model });
  }

  function regenerate() {
    if (state.stream) return;
    const last = state.messages[state.messages.length - 1];
    if (last?.role === "assistant") state.messages.pop();
    runStream({ regenerate: true, model: state.model });
  }

  function stop() { state.stream?.controller.abort(); }

  async function runStream(payload) {
    if (state.style) payload = { ...payload, style_id: state.style }; // never races the style PATCH
    const convId = state.currentId;
    const assistant = { id: "pending", role: "assistant", content: "", streaming: true };
    state.messages.push(assistant);
    state.stick = true;
    renderThread();
    const el = () => els.inner.lastElementChild;
    const controller = new AbortController();
    state.stream = { controller, convId };
    updateSend();

    let raf = 0;
    const paint = () => { raf = 0; if (state.currentId === convId && el()) { paintAssistant(el(), assistant); scrollToBottom(); } };
    const schedule = () => { if (!raf) raf = requestAnimationFrame(paint); };

    try {
      const res = await fetch(`${API}/conversations/${convId}/messages`, {
        method: "POST", signal: controller.signal, credentials: "same-origin",
        headers: { "Content-Type": "application/json", "X-CSRFToken": csrf(), Accept: "text/event-stream" },
        body: JSON.stringify(payload),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.error?.message || `Request failed (${res.status})`);
      }
      const reader = res.body.getReader(), dec = new TextDecoder();
      let buf = "";
      for (;;) {
        const { value, done } = await reader.read();
        if (done) break;
        buf += dec.decode(value, { stream: true });
        let idx;
        while ((idx = buf.indexOf("\n\n")) >= 0) {
          const raw = buf.slice(0, idx); buf = buf.slice(idx + 2);
          const ev = (raw.match(/^event: (.*)$/m) || [])[1];
          const dataLine = (raw.match(/^data: (.*)$/m) || [])[1];
          if (!ev || !dataLine) continue;
          handleEvent(ev, JSON.parse(dataLine), assistant, convId);
          schedule();
        }
      }
    } catch (e) {
      if (e.name === "AbortError") assistant.stop_reason = "user_cancelled";
      else assistant.error = e.message || "Network error — check your connection and retry.";
    } finally {
      assistant.streaming = false;
      state.stream = null;
      updateSend();
      if (raf) cancelAnimationFrame(raf);
      if (state.currentId === convId) { renderThread(); els.input.focus(); refreshPath(convId); }
      const c = conv(convId);
      if (c) { c.updated_at = new Date().toISOString(); state.conversations.sort((a, b) => b.updated_at.localeCompare(a.updated_at)); renderSidebar(); }
    }
  }

  // The server is the source of truth for the tree: re-read the active path
  // after a turn so "< n/m >" counts and ids match what was saved.
  async function refreshPath(convId) {
    const data = await api(`/conversations/${convId}`).catch(() => null);
    if (!data || state.currentId !== convId || state.stream) return;
    const errors = new Map(state.messages.filter((m) => m.error).map((m) => [m.id, m.error]));
    state.messages = data.messages.map((m) => (errors.has(m.id) ? { ...m, error: errors.get(m.id) } : m));
    const keep = els.thread.scrollTop;
    renderThread(false); els.thread.scrollTop = keep;
  }

  function handleEvent(ev, data, assistant, convId) {
    switch (ev) {
      case "user_message": {
        const tmp = [...state.messages].reverse().find((m) => m.role === "user" && String(m.id).startsWith("tmp-"));
        if (tmp) Object.assign(tmp, data);
        break;
      }
      case "message_start": assistant.id = data.id; assistant.model = data.model; break;
      case "delta": assistant.content += data.text; break;
      case "error": assistant.error = data.message; break;
      case "message_stop": if (data.stop_reason) assistant.stop_reason = data.stop_reason; break;
      case "conversation_title": {
        const c = conv(data.id);
        if (c) { c.title = data.title; renderSidebar(data.id); if (state.currentId === convId) renderHeader(); }
        break;
      }
    }
  }

  // ------------------------------------------------------------------ routing
  async function route() {
    closeMenu(); closeMobileSidebar();
    const m = location.pathname.match(/^\/console\/chat\/([0-9a-f-]{36})/);
    const id = m ? m[1] : null;
    if (state.stream && state.stream.convId !== id) stop();
    state.currentId = id; state.messages = []; state.editing = null;
    renderSidebar(); renderHeader();
    if (!id) {
      if (location.pathname !== "/console/new") history.replaceState({}, "", "/console/new");
      applyDefaults();
      renderThread();
    } else {
      els.main.classList.remove("is-empty");
      els.inner.innerHTML = "";
      try {
        const data = await api(`/conversations/${id}`);
        if (state.currentId !== id) return;
        state.messages = data.messages;
        if (data.model && state.models.some((x) => x.id === data.model)) setModel(data.model);
        setStyle(data.style_id || null);
        renderThread();
      } catch (e) {
        if (e.message === "auth") return;
        toast("That chat could not be found");
        return navigate("/console/new");
      }
    }
    els.input.value = store.get(draftKey(), ""); autosize(); updateSend();
    if (matchMedia("(pointer: fine)").matches) els.input.focus();
  }

  function navigate(path) { if (location.pathname !== path) history.pushState({}, "", path); route(); }
  addEventListener("popstate", route);
  document.addEventListener("click", (e) => {
    const a = e.target.closest("a[data-link]");
    if (!a || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return;
    e.preventDefault(); navigate(a.getAttribute("href"));
  });

  // ------------------------------------------------------------------ chrome
  const mobile = () => matchMedia("(max-width: 860px)").matches;
  function closeMobileSidebar() { delete els.app.dataset.mobileOpen; els.scrim.hidden = true; }
  $("collapseBtn").addEventListener("click", () => {
    if (mobile()) return closeMobileSidebar();
    els.app.dataset.sidebar = "closed"; store.set("gai-sidebar", "closed");
  });
  $("openSidebarBtn").addEventListener("click", () => {
    if (mobile()) { els.app.dataset.mobileOpen = ""; els.scrim.hidden = false; return; }
    els.app.dataset.sidebar = "open"; store.set("gai-sidebar", "open");
  });
  els.scrim.addEventListener("click", closeMobileSidebar);
  els.search.addEventListener("input", () => { state.filter = els.search.value; runSearch(); });
  els.search.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && els.search.value) { e.stopPropagation(); els.search.value = ""; state.filter = ""; runSearch(); }
  });
  els.title.addEventListener("click", () => {
    const c = conv(state.currentId); if (!c) return;
    const input = document.createElement("input");
    input.className = "conv-title-input"; input.value = c.title || ""; input.setAttribute("aria-label", "Chat title");
    els.title.hidden = true; els.title.after(input); input.focus(); input.select();
    let done = false;
    const finish = (save) => {
      if (done) return; done = true; input.remove(); els.title.hidden = false;
      if (save && input.value.trim() && input.value.trim() !== c.title) rename(c.id, input.value.trim());
    };
    input.addEventListener("keydown", (e) => { if (e.key === "Enter") finish(true); if (e.key === "Escape") finish(false); });
    input.addEventListener("blur", () => finish(true));
  });
  els.star.addEventListener("click", () => state.currentId && toggleStar(state.currentId));
  els.del.addEventListener("click", () => state.currentId && deleteConv(state.currentId));

  // Theme lives in the server preferences (02.10); localStorage mirrors it so
  // base.html can paint the right theme before the bootstrap call returns.
  const lightQuery = matchMedia("(prefers-color-scheme: light)");
  function setTheme(t, persist = true) {
    const prev = state.prefs.theme || store.get("gai-theme", "dark");
    store.set("gai-theme", t);
    document.documentElement.dataset.theme = t === "system" ? (lightQuery.matches ? "light" : "dark") : t;
    if (persist && state.prefs.theme !== t) {
      state.prefs.theme = t;
      api("/me/preferences", { method: "PATCH", body: { theme: t } }).catch((e) => {
        if (state.prefs.theme !== t) return; // a newer pick already replaced it
        state.prefs.theme = prev; setTheme(prev, false);
        toast(`Theme not saved: ${e.message}`);
      });
    }
  }
  lightQuery.addEventListener("change", () => { if (store.get("gai-theme", "dark") === "system") setTheme("system", false); });
  els.userBtn.addEventListener("click", (e) => {
    const theme = store.get("gai-theme", "dark");
    const items = [
      { label: state.user.email },
      { icon: "gear", text: "Settings", onClick: () => openSettings() },
      "-",
      { icon: "sun", text: "Dark", checked: theme === "dark", onClick: () => setTheme("dark") },
      { icon: "sun", text: "Light", checked: theme === "light", onClick: () => setTheme("light") },
      { icon: "sun", text: "Match system", checked: theme === "system", onClick: () => setTheme("system") },
      "-",
    ];
    if (state.user.is_staff) items.push({ icon: "shield", text: "Admin dashboard", onClick: () => window.open("/admin/", "_blank") });
    items.push({ icon: "out", text: "Log out", onClick: () => $("logoutForm").submit() });
    openMenu(e.currentTarget, items);
  });

  document.addEventListener("keydown", (e) => {
    const mod = e.metaKey || e.ctrlKey;
    if (mod && e.key.toLowerCase() === "k") { e.preventDefault(); if (mobile()) { els.app.dataset.mobileOpen = ""; els.scrim.hidden = false; } els.search.focus(); }
    else if (mod && e.shiftKey && e.key.toLowerCase() === "o") { e.preventDefault(); navigate("/console/new"); }
    else if (mod && e.key === ",") { e.preventDefault(); openSettings(); }
    else if (e.key === "Escape" && document.querySelector("dialog[open]")) { /* the dialog closes itself */ }
    else if (e.key === "Escape") { if (!els.menu.hidden) closeMenu(); else if (state.stream) stop(); else closeMobileSidebar(); }
  });

  // ------------------------------------------------------------------ styles (02.11)
  const styleById = (id) => state.styles.find((x) => x.id === id);
  // Parse one of the static ICON strings into an SVG node (no HTML sink).
  const iconNode = (name) => document.importNode(
    new DOMParser().parseFromString(ICON[name].replace("<svg", '<svg xmlns="http://www.w3.org/2000/svg"'), "image/svg+xml").documentElement, true);
  function setStyle(id) {
    const st = styleById(id);
    state.style = st ? st.id : null;
    const custom = st && st.key !== "normal";
    els.styleName.textContent = custom ? st.name : "";
    els.styleBtn.classList.toggle("is-set", !!custom);
    els.styleBtn.setAttribute("aria-label", `Response style: ${st ? st.name : "Normal"}`);
  }
  function chooseStyle(id) {
    const prev = state.style, convId = state.currentId;
    setStyle(id);
    if (convId) {
      const c = conv(convId); if (c) c.style_id = state.style;
      const picked = state.style;
      api(`/conversations/${convId}`, { method: "PATCH", body: { style_id: picked } }).catch((e) => {
        if (c) c.style_id = prev;
        if (state.currentId === convId && state.style === picked) setStyle(prev);
        toast(`Style not saved: ${e.message}`);
      });
    }
  }
  els.styleBtn.addEventListener("click", (e) => {
    const presets = state.styles.filter((x) => x.is_preset), mine = state.styles.filter((x) => !x.is_preset);
    const item = (x) => ({ text: x.name, desc: x.description, checked: (state.style || presetId("normal")) === x.id, onClick: () => chooseStyle(x.id) });
    const items = [{ label: "Response style" }, ...presets.map(item)];
    if (mine.length) items.push("-", { label: "Your styles" }, ...mine.map(item));
    items.push("-", { icon: "plus", text: "Create & edit styles", onClick: () => openStyles() });
    openMenu(e.currentTarget, items, "end");
  });
  const presetId = (key) => state.styles.find((x) => x.key === key && x.is_preset)?.id;

  const styleDlg = $("styleDialog");
  let editingStyle = null;
  function fieldError(prefix, field, msg) {
    const el = $(`${prefix}-${field}`); if (!el) return;
    el.textContent = msg || ""; el.hidden = !msg;
    const input = el.closest(".field")?.querySelector("input, textarea, select");
    if (input) { input.toggleAttribute("aria-invalid", !!msg); if (msg) input.setAttribute("aria-errormessage", el.id); }
  }
  function renderStyleList() {
    const list = $("styleList"), mine = state.styles.filter((x) => !x.is_preset);
    list.replaceChildren();
    if (!mine.length) {
      const empty = document.createElement("li");
      empty.className = "style-empty"; empty.textContent = "No custom styles yet — create one below.";
      list.append(empty);
    }
    mine.forEach((st) => {
      const li = document.createElement("li");
      li.className = "style-row" + (editingStyle === st.id ? " is-editing" : "");
      const text = document.createElement("span"), b = document.createElement("b");
      b.textContent = st.name; text.append(b);
      if (st.description) {
        const d = document.createElement("span"); d.className = "field-help"; d.textContent = st.description; text.append(d);
      }
      const iconButton = (icon, label) => {
        const btn = document.createElement("button");
        btn.type = "button"; btn.className = "icon-btn"; btn.setAttribute("aria-label", label);
        btn.append(iconNode(icon));
        return btn;
      };
      const edit = iconButton("edit", `Edit ${st.name}`), del = iconButton("trash", `Delete ${st.name}`);
      li.append(text, edit, del);
      edit.addEventListener("click", () => fillStyle(st));
      del.addEventListener("click", () => deleteStyle(st));
      list.appendChild(li);
    });
  }
  function fillStyle(st) {
    editingStyle = st ? st.id : null;
    $("styleNameInput").value = st?.name || ""; $("styleDescInput").value = st?.description || ""; $("stylePromptInput").value = st?.prompt || "";
    $("styleSave").textContent = st ? "Save changes" : "Create style";
    ["name", "prompt"].forEach((f) => fieldError("serr", f, ""));
    $("styleState").textContent = "";
    renderStyleList();
    $("styleNameInput").focus();
  }
  function openStyles() { fillStyle(null); styleDlg.showModal(); }
  $("styleReset").addEventListener("click", () => fillStyle(null));
  async function deleteStyle(st) {
    if (!confirm(`Delete the style “${st.name}”? Chats using it go back to Normal.`)) return;
    try { await api(`/styles/${st.id}`, { method: "DELETE" }); } catch (e) { return toast(e.message); }
    state.styles = state.styles.filter((x) => x.id !== st.id);
    if (state.style === st.id) setStyle(null);
    if (state.prefs.default_style_id === st.id) state.prefs.default_style_id = null;
    if (editingStyle === st.id) fillStyle(null); else renderStyleList();
    toast("Style deleted");
  }
  let styleBusy = false;
  $("styleForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = { name: $("styleNameInput").value.trim(), description: $("styleDescInput").value.trim(), prompt: $("stylePromptInput").value.trim() };
    const local = {};
    if (!body.name) local.name = "Give the style a name.";
    if (!body.prompt) local.prompt = "Describe how GeorgeAI should write.";
    ["name", "prompt"].forEach((f) => fieldError("serr", f, local[f]));
    if (Object.keys(local).length) return $(local.name ? "styleNameInput" : "stylePromptInput").focus();
    if (styleBusy) return;
    styleBusy = true; $("styleSave").disabled = true;
    $("styleState").textContent = "Saving…";
    let saved;
    try {
      saved = editingStyle
        ? await api(`/styles/${editingStyle}`, { method: "PATCH", body })
        : await api("/styles", { method: "POST", body });
    } catch (err) {
      styleBusy = false; $("styleSave").disabled = false;
      $("styleState").textContent = "";
      const f = err.data?.error?.fields || {};
      Object.entries(f).forEach(([k, v]) => fieldError("serr", k, v));
      return toast(err.message);
    }
    styleBusy = false; $("styleSave").disabled = false;
    const i = state.styles.findIndex((x) => x.id === saved.id);
    if (i >= 0) state.styles[i] = saved; else state.styles.push(saved);
    const created = !editingStyle;
    fillStyle(saved);
    $("styleState").textContent = created ? "Created" : "Saved";
    if (created) chooseStyle(saved.id);
    else if (state.style === saved.id) setStyle(saved.id);
  });

  // ------------------------------------------------------------------ settings (02.10 / 04.13)
  const settingsDlg = $("settingsDialog");
  const tabs = [...settingsDlg.querySelectorAll('[role="tab"]')];
  function showTab(tab, focus) {
    tabs.forEach((t) => {
      const on = t === tab;
      t.setAttribute("aria-selected", String(on)); t.tabIndex = on ? 0 : -1;
      $(t.getAttribute("aria-controls")).hidden = !on;
    });
    if (focus) tab.focus();
  }
  tabs.forEach((t, i) => {
    t.addEventListener("click", () => showTab(t));
    t.addEventListener("keydown", (e) => {
      const d = { ArrowDown: 1, ArrowRight: 1, ArrowUp: -1, ArrowLeft: -1 }[e.key];
      if (d) { e.preventDefault(); showTab(tabs[(i + d + tabs.length) % tabs.length], true); }
    });
  });
  const counter = () => { $("count-instructions").textContent = `${$("setInstructions").value.length.toLocaleString()} / 4,000`; };
  $("setInstructions").addEventListener("input", counter);
  function openSettings() {
    closeMenu();
    const p = state.prefs;
    $("setName").value = p.name || "";
    $("setInstructions").value = p.personal_instructions || ""; counter();
    settingsDlg.querySelectorAll('input[name="theme"]').forEach((r) => (r.checked = r.value === (p.theme || "dark")));
    $("setModel").replaceChildren(new Option("Automatic (recommended)", ""),
      ...state.models.map((m) => new Option((m.vendor_name ? m.vendor_name + " · " : "") + m.name, m.id)));
    $("setModel").value = knownModel(p.default_model) ? p.default_model : "";
    $("setStyle").replaceChildren(...state.styles.map((x) => new Option(x.name, x.key === "normal" ? "" : x.id)));
    $("setStyle").value = p.default_style_id && styleById(p.default_style_id) ? p.default_style_id : "";
    $("setEnter").checked = p.send_with_enter !== false;
    ["name", "personal_instructions", "default_model", "default_style_id"].forEach((f) => fieldError("err", f, ""));
    $("settingsErrors").hidden = true; $("settingsState").textContent = "";
    showTab(tabs[0]);
    settingsDlg.showModal();
    $("setName").focus();
  }
  document.querySelectorAll("dialog [data-close]").forEach((b) => b.addEventListener("click", () => b.closest("dialog").close()));
  document.querySelectorAll("dialog").forEach((d) => d.addEventListener("click", (e) => { if (e.target === d) d.close(); }));
  $("settingsForm").addEventListener("submit", async (e) => {
    e.preventDefault();
    const body = {
      name: $("setName").value.trim(),
      personal_instructions: $("setInstructions").value,
      theme: settingsDlg.querySelector('input[name="theme"]:checked')?.value || "dark",
      default_model: $("setModel").value,
      default_style_id: $("setStyle").value || null,
      send_with_enter: $("setEnter").checked,
    };
    $("settingsSave").disabled = true; $("settingsState").textContent = "Saving…";
    let saved;
    try { saved = await api("/me/preferences", { method: "PATCH", body }); }
    catch (err) {
      $("settingsSave").disabled = false; $("settingsState").textContent = "";
      const fields = err.data?.error?.fields || {};
      Object.entries(fields).forEach(([k, v]) => fieldError("err", k, v));
      const sum = $("settingsErrors");
      const head = document.createElement("b"); head.textContent = "Couldn’t save.";
      sum.replaceChildren(head, " " + (Object.values(fields).join(" ") || err.message));
      sum.hidden = false; sum.focus();
      return;
    }
    $("settingsSave").disabled = false;
    state.prefs = saved;
    state.user.name = saved.name || state.user.email.split("@")[0];
    els.userName.textContent = state.user.name;
    els.userAvatar.textContent = state.user.name.slice(0, 1).toUpperCase();
    setTheme(saved.theme, false);
    if (!state.currentId) applyDefaults();
    settingsDlg.close();
    toast("Settings saved");
  });

  // ------------------------------------------------------------------ boot
  async function boot() {
    if (store.get("gai-sidebar", "open") === "closed") els.app.dataset.sidebar = "closed";
    let data;
    try { data = await api("/bootstrap"); } catch (e) { if (e.message !== "auth") toast(e.message); return; }
    Object.assign(state, { user: data.user, models: data.models, provider: data.provider, defaultModel: data.default_model,
      conversations: data.conversations, prefs: data.preferences || {}, styles: data.styles || [] });
    if (state.prefs.name) state.user.name = state.prefs.name;
    if (state.prefs.theme) setTheme(state.prefs.theme, false);
    els.userName.textContent = state.user.name;
    els.userAvatar.textContent = (state.user.name || "?").slice(0, 1).toUpperCase();
    const saved = store.get("gai-model", data.default_model);
    setModel(state.models.some((m) => m.id === saved) ? saved : data.default_model);
    renderChips();
    route();
  }
  boot();
})();
