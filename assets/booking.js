export function booking() {
  const form = document.querySelector("form[data-booking]");
  if (!form) return;
  const d = form.dataset;
  const days = form.querySelector("[data-booking-days]");
  const slots = form.querySelector("[data-booking-slots]");
  const err = form.querySelector("[data-booking-error]");
  const done = form.parentElement.querySelector("[data-booking-done]");
  const fields = { service: form.querySelector("#ga-ct-service"), name: form.querySelector("#ga-ct-name"), email: form.querySelector("#ga-ct-email"), msg: form.querySelector("#ga-ct-msg") };
  const longDay = new Intl.DateTimeFormat(d.locale, { weekday: "long", day: "numeric", month: "long" });
  const state = { date: null, time: null };

  const key = (dt) => dt.getFullYear() + "-" + String(dt.getMonth() + 1).padStart(2, "0") + "-" + String(dt.getDate()).padStart(2, "0");
  const fromKey = (k) => { const p = k.split("-"); return new Date(+p[0], +p[1] - 1, +p[2]); };

  // next 10 weekdays, keyed by local date (never toISOString: it shifts a day east of UTC)
  const dt = new Date(); dt.setHours(0, 0, 0, 0);
  let added = 0, guard = 0;
  while (added < 10 && guard < 40) {
    dt.setDate(dt.getDate() + 1); guard++;
    if (dt.getDay() === 0 || dt.getDay() === 6) continue;
    const k = key(dt), copy = new Date(dt);
    const b = document.createElement("button");
    b.type = "button"; b.className = "chip chip--day"; b.dataset.day = k;
    b.setAttribute("aria-pressed", "false"); b.setAttribute("aria-label", longDay.format(copy));
    b.innerHTML = `<span class="chip__dn">${new Intl.DateTimeFormat(d.locale, { weekday: "short" }).format(copy)}</span>` +
      `<span class="chip__num">${new Intl.DateTimeFormat(d.locale, { day: "numeric" }).format(copy)}</span>` +
      `<span class="chip__mon">${new Intl.DateTimeFormat(d.locale, { month: "short" }).format(copy)}</span>`;
    days.appendChild(b); added++;
  }
  const press = (group, attr, value) => group.querySelectorAll("button").forEach((b) => b.setAttribute("aria-pressed", String(b.dataset[attr] === value)));
  days.addEventListener("click", (e) => { const b = e.target.closest("[data-day]"); if (!b) return; state.date = b.dataset.day; press(days, "day", state.date); clear(); });
  slots.addEventListener("click", (e) => { const b = e.target.closest("[data-slot]"); if (!b) return; state.time = b.dataset.slot; press(slots, "slot", state.time); clear(); });
  Object.values(fields).forEach((f) => f.addEventListener("input", clear));

  function clear() { err.hidden = true; err.textContent = ""; }
  const emailOk = () => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(fields.email.value.trim());
  const when = () => (state.date ? longDay.format(fromKey(state.date)) + ", " : "") + (state.time || "");
  const body = () => [d.mailGreeting, "", d.mailSlot + " " + when(), d.mailService + " " + (fields.service.value || "-"),
    d.mailName + " " + fields.name.value.trim(), d.mailEmail + " " + fields.email.value.trim(),
    ...(fields.msg.value.trim() ? ["", fields.msg.value.trim()] : []), "", d.mailSign, fields.name.value.trim()].join("\n");
  const mailto = () => "mailto:" + d.email + "?subject=" + encodeURIComponent(d.mailSubject + ": " + when()) + "&body=" + encodeURIComponent(body());

  form.addEventListener("submit", (e) => {
    e.preventDefault();
    const missing = [];
    if (!state.date) missing.push(d.fieldDay);
    if (!state.time) missing.push(d.fieldTime);
    if (!fields.name.value.trim()) missing.push(d.fieldName);
    if (!emailOk()) missing.push(d.fieldEmail);
    if (missing.length) { err.textContent = d.missing + " " + missing.join(", "); err.hidden = false; return; }
    done.querySelector("[data-booking-summary]").textContent = when();
    done.querySelector("[data-booking-body]").textContent = body();
    done.querySelector("[data-booking-mail]").href = mailto();
    done.querySelector("[data-booking-wa]").href = d.whatsapp + "?text=" + encodeURIComponent(body());
    form.hidden = true; done.hidden = false;
    done.querySelector("h2").focus?.();
    try { window.location.href = mailto(); } catch (x) {}
  });
  done.querySelector("[data-booking-edit]").addEventListener("click", () => { done.hidden = true; form.hidden = false; fields.name.focus(); });
  const copyBtn = done.querySelector("[data-booking-copy]");
  copyBtn.addEventListener("click", () => {
    navigator.clipboard?.writeText(body()).then(() => { copyBtn.textContent = d.copied; setTimeout(() => { copyBtn.textContent = d.copy; }, 2200); }, () => {});
  });
}
