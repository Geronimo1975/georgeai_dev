import { hero } from "./hero.js";
import { booking } from "./booking.js";

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
const store = {
  get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
};

function theme() {
  const btn = $("[data-theme-toggle]");
  if (!btn) return;
  const current = () => document.documentElement.getAttribute("data-theme")
    || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");
  const label = () => { btn.setAttribute("aria-label", current() === "dark" ? btn.dataset.labelLight : btn.dataset.labelDark); };
  label();
  btn.addEventListener("click", () => {
    const next = current() === "dark" ? "light" : "dark";
    document.documentElement.setAttribute("data-theme", next);
    store.set("ga_theme", next);
    label();
  });
}

function menu() {
  const btn = $("[data-menu-toggle]");
  const panel = $("#site-menu");
  if (!btn || !panel) return;
  const set = (open) => { panel.hidden = !open; btn.setAttribute("aria-expanded", String(open)); };
  btn.addEventListener("click", () => set(panel.hidden));
  document.addEventListener("keydown", (e) => { if (e.key === "Escape" && !panel.hidden) { set(false); btn.focus(); } });
  document.addEventListener("click", (e) => { if (!panel.hidden && !panel.contains(e.target) && !btn.contains(e.target)) set(false); });
}

function cookie() {
  const box = $("[data-cookie]");
  if (!box) return;
  const choice = store.get("ga_cookie");
  if (choice === "essential" || choice === "all") return;
  box.hidden = false;
  $("[data-cookie-essential]", box).addEventListener("click", () => { store.set("ga_cookie", "essential"); box.hidden = true; });
  $("[data-cookie-accept]", box).addEventListener("click", () => { store.set("ga_cookie", "all"); box.hidden = true; });
}

export { $, $$, store };
theme();
menu();
cookie();
hero();
booking();
