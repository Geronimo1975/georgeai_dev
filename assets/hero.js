export function hero() {
  const root = document.querySelector("[data-hero-panels]");
  if (!root) return;
  const panels = Array.from(root.querySelectorAll("[data-panel]"));
  const buttons = panels.map((p) => p.querySelector(".panel__hit"));
  const reduced = matchMedia("(prefers-reduced-motion: reduce)").matches;
  let idx = 0, timer = null;
  const activate = (i) => {
    idx = i;
    panels.forEach((p, j) => { p.classList.toggle("is-active", j === i); buttons[j].setAttribute("aria-pressed", String(j === i)); });
  };
  const start = () => { if (reduced || timer) return; timer = setInterval(() => activate((idx + 1) % panels.length), 6000); };
  const stop = () => { clearInterval(timer); timer = null; };
  buttons.forEach((b, i) => b.addEventListener("click", () => { activate(i); stop(); }));
  root.addEventListener("pointerenter", stop);
  root.addEventListener("pointerleave", start);
  root.addEventListener("focusin", stop);
  root.addEventListener("focusout", (e) => { if (!root.contains(e.relatedTarget)) start(); });
  activate(0);
  start();
}
