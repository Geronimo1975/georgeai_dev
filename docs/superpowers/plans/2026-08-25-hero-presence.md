# Hero Presence Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the georgeai.dev hero read as a running system rather than a printed diagram, by fixing resting motion, contrast, and above-the-fold action.

**Architecture:** Three independent edits to the existing repo-owned hero layer. Payload flow is decoupled from node arrival so the field can move at rest without spending the whole graph; four alpha expressions are raised above the contrast floor; the CTA reveal is moved from the tail of the scrub to the landing state. No new files, no new dependencies, no renderer change. Everything ships through the existing `apply_hero` layer in `deploy.sh`.

**Tech Stack:** Vanilla ES5-style JS on Canvas2D (`hero/hero-cinema.js`), plain CSS (`hero/hero-cinema.css`), Python 3 stdlib for the regression test, bash `deploy.sh` for delivery.

**Spec:** `docs/superpowers/specs/2026-08-25-hero-presence-design.md`

## Global Constraints

- **Never edit `site/`.** It is wiped and regenerated on every deploy. All hero edits go in `hero/`.
- **Stdlib only in `tests/`.** No pytest-only constructs, no third-party imports. The suite must run as `python3 tests/<file>.py` and exit 0/1.
- **Preserve the depth gradient.** Far-plane nodes stay dimmer than near-plane ones; raise the floor, never flatten `n.z`.
- **`prefers-reduced-motion: reduce` must still suppress all flow and assembly.** The existing `reduceMotion` guards stay intact.
- **Ground colour is `#141413`** (`colors.ground`, hero-cinema.js:84); ink `#f5f2ec`, body `#a8a29a`, accent `#ff8300`.
- **Contrast floor is 4.5:1** for text against the ground.
- **The hero keeps exactly one `<h1>`.** Do not add or move heading elements.

---

### Task 1: Contrast regression test

A deterministic guard that reads the alpha expressions out of `hero-cinema.js` and computes the resulting contrast ratio. This exists first so Tasks 2-4 have something that fails before they start. It also survives re-exports, since `hero/` is repo-owned.

**Files:**
- Create: `tests/test_hero_contrast.py`

**Interfaces:**
- Consumes: nothing.
- Produces: `composite(fg_hex, alpha, bg_hex) -> str`, `contrast(hex_a, hex_b) -> float`, `alpha_at(expr_base, expr_slope, z) -> float`. Later tasks only need the test to pass; they do not import it.

- [ ] **Step 1: Write the failing test**

```python
#!/usr/bin/env python3
"""Contrast floors for the hero canvas.

The hero field draws its text with globalAlpha over the page ground, so the
effective contrast is not visible in any colour token — it only exists once
the alpha is composited. This suite recomputes that composite from the alpha
expressions in hero-cinema.js and asserts the result clears WCAG AA.

Stdlib only, exit 0/1, same contract as tests/test_payments_pipeline.py.
"""
import re
import sys
from pathlib import Path

SRC = Path(__file__).resolve().parent.parent / "hero" / "hero-cinema.js"

GROUND = "#141413"
INK = "#f5f2ec"
BODY = "#a8a29a"  # kept for reference; the sub-line moved to ink

# The near-plane depth. Nodes sit between z=0.66 and z=1.0; the floor has to
# hold at the dimmest of them, which is the 0.66 plane.
NEAR_Z = 0.66

FLOOR = 4.5


def _rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def composite(fg_hex, alpha, bg_hex):
    """Flatten fg at `alpha` over bg, the way canvas globalAlpha does."""
    fg, bg = _rgb(fg_hex), _rgb(bg_hex)
    out = tuple(round(alpha * f + (1 - alpha) * b) for f, b in zip(fg, bg))
    return "#%02x%02x%02x" % out


def _lum(h):
    def chan(c):
        c = c / 255.0
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (chan(c) for c in _rgb(h))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    la, lb = _lum(a), _lum(b)
    hi, lo = max(la, lb), min(la, lb)
    return (hi + 0.05) / (lo + 0.05)


def alpha_at(base, slope, z):
    return base + slope * z


def find_alpha(label, pattern):
    """Pull (base, slope) out of a `k * (BASE + SLOPE * n.z)` expression."""
    src = SRC.read_text(encoding="utf-8")
    m = re.search(pattern, src)
    if not m:
        raise AssertionError(
            "%s: could not find the alpha expression in %s. If the line was "
            "reworded, update the pattern here rather than deleting the check."
            % (label, SRC.name)
        )
    return float(m.group(1)), float(m.group(2))


def check(label, fg, base, slope):
    a = alpha_at(base, slope, NEAR_Z)
    ratio = contrast(composite(fg, a, GROUND), GROUND)
    ok = ratio >= FLOOR
    print("%-14s alpha=%.3f contrast=%.2f:1 %s" % (label, a, ratio, "OK" if ok else "FAIL"))
    return ok


def main():
    results = []

    # The sub-line is the only draw inside `if (n.sub)`, which is what anchors
    # it. It is drawn in ink, same as the label, so a colour-based anchor would
    # be ambiguous.
    base, slope = find_alpha(
        "sub-label",
        r"if \(n\.sub\) \{\s*\n\s*ctx\.globalAlpha = k \* \(([\d.]+) \+ ([\d.]+) \* n\.z\);")
    results.append(check("sub-label", INK, base, slope))

    # Anchored on the `'600 '` font weight, which only the label sets. Two other
    # draws combine a `k * (base + slope * n.z)` alpha with colors.ink, and a
    # bare search would silently measure one of those instead.
    base, slope = find_alpha(
        "label",
        r"ctx\.globalAlpha = k \* \(([\d.]+) \+ ([\d.]+) \* n\.z\);\s*\n\s*ctx\.fillStyle = colors\.ink;\s*\n\s*ctx\.font = '600 '")
    results.append(check("label", INK, base, slope))

    if all(results):
        print("\nhero contrast: all floors clear")
        return 0
    print("\nhero contrast: below the %.1f:1 floor" % FLOOR)
    return 1


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 2: Run it to verify the sub-label fails**

Run: `python3 tests/test_hero_contrast.py`
Expected: exit 1. `sub-label` prints roughly `alpha=0.332 contrast=1.87:1 FAIL`; `label` prints roughly `alpha=0.564 contrast=5.86:1 OK`.

If `find_alpha` raises instead, the regex did not match the current source — fix the pattern against the real line before continuing. Do not loosen the floor.

- [ ] **Step 3: Commit the failing test**

```bash
git add tests/test_hero_contrast.py
git commit -m "Add a contrast floor test for the hero canvas

The field's text contrast only exists after globalAlpha composites it over
the ground, so no colour token shows it. Recompute it from the source and
hold it to 4.5:1. Fails today on the sub-label at 1.9:1."
```

---

### Task 2: Raise the contrast floors

**Files:**
- Modify: `hero/hero-cinema.js:836` (card surface), `:842` (card border), `:884-885` (sub-label)
- Test: `tests/test_hero_contrast.py`

**Interfaces:**
- Consumes: the test from Task 1.
- Produces: nothing later tasks depend on.

- [ ] **Step 1: Raise the sub-label alpha**

At hero-cinema.js:884, change:

```js
        ctx.globalAlpha = k * (0.20 + 0.20 * n.z);
        ctx.fillStyle = colors.body;
```

to:

```js
        /* Ink, not body, and the token change is the point: body needs alpha
         * 0.74 to clear 4.5:1 over the ground, which pins the sub-line near
         * opaque and erases its depth cue. Ink clears the same floor at 0.48.
         * The label above stays brighter still, so the hierarchy holds.
         * tests/test_hero_contrast.py recomputes this and fails if it slips. */
        ctx.globalAlpha = k * (0.36 + 0.18 * n.z);
        ctx.fillStyle = colors.ink;
```

- [ ] **Step 2: Give the card a surface**

At hero-cinema.js:836, change:

```js
      ctx.globalAlpha = k * 0.05;
      ctx.fillStyle = colors.ink;
```

to:

```js
      /* The card is filled with the page's own ground, then lifted by its own
       * ink so it separates on either theme without a hard-coded surface
       * colour. At 0.05 that lift was invisible and the card read as a hole.
       * 0.08 is the smallest value that gives it a plane at the near depth. */
      ctx.globalAlpha = k * 0.08;
      ctx.fillStyle = colors.ink;
```

- [ ] **Step 3: Strengthen the card border**

At hero-cinema.js:842, change:

```js
      ctx.globalAlpha = k * (0.16 + 0.30 * n.z) * (1 + busy * 1.6);
```

to:

```js
      ctx.globalAlpha = k * (0.28 + 0.30 * n.z) * (1 + busy * 1.6);
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `python3 tests/test_hero_contrast.py`
Expected: exit 0. `sub-label` prints roughly `alpha=0.479 contrast=4.55:1 OK`.

- [ ] **Step 5: Commit**

```bash
git add hero/hero-cinema.js
git commit -m "Lift the hero card and its sub-line off the ground

The sub-label composited to about 1.9:1 and the card was filled with the
page background, so only the accent-tiled agent read as a node. Raise the
sub-label to clear 4.5:1, give the card a surface, and firm up the border.
The depth gradient is untouched: the floor moves, the slope does not."```

---

### Task 3: Decouple payload flow from node arrival

**Files:**
- Modify: `hero/hero-cinema.js:793` (flow ramp), `:1015` (resting progress), `:1020` (rAF keep-alive)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: nothing later tasks depend on.

The hero lands as a still image because payload opacity is `smoothstep(p, 0.5, 0.78)` (hero-cinema.js:793) while the last node arrives at `t = 0.56`. Any resting progress high enough to show movement also spends the entire graph. Move the flow ramp earlier so the two are independent.

- [ ] **Step 1: Re-ramp the payload flow**

At hero-cinema.js:793, change:

```js
      var flow = smoothstep(p, 0.5, 0.78);
```

to:

```js
      /* Flow used to ride the same axis as node arrival, which forced a choice
       * between a moving field and a scroll that still had something to reveal.
       * Wires now carry traffic as soon as there is a wire to carry it on, so
       * the resting progress is free to sit below the last node's arrival. */
      var flow = smoothstep(p, 0.18, 0.42);
```

- [ ] **Step 2: Raise the resting progress**

At hero-cinema.js:1015, change:

```js
    drawGraph(Math.max(shown, lk * 0.30), now);
```

to:

```js
    /* 0.46 rests the field just past Airtable (t=0.40) and short of the dashed
     * port cluster (t=0.48-0.56), so six of nine nodes are present at full flow
     * and the sub-nodes stay the scroll's payoff. */
    drawGraph(Math.max(shown, lk * 0.46), now);
```

- [ ] **Step 3: Lower the rAF keep-alive to match**

At hero-cinema.js:1020, change:

```js
    var flowing = shown > 0.55 && !reduceMotion.matches;
```

to:

```js
    var flowing = shown > 0.20 && !reduceMotion.matches;
```

- [ ] **Step 4: Verify in the browser**

```bash
./deploy.sh --no-content
```

Then load the homepage at 1440x900 and confirm, WITHOUT scrolling:

- Six node cards are present: Webhook, HTTP Request, AI Agent, If, Gmail, Airtable.
- The three dashed-port sub-nodes (OpenAI Chat, Postgres, Vector Store) are NOT present.
- Payload dots visibly travel the connectors and keep travelling — the frame is not static after the 900ms assembly.

Then scroll and confirm the three sub-nodes still arrive on their dashed ports.

- [ ] **Step 5: Verify the reduced-motion path**

In DevTools, Rendering panel, force `prefers-reduced-motion: reduce`, then reload. Expected: no assembly, no payload travel, a single static frame with the field pinned to its finished state. If anything moves, `reduceMotion` was bypassed — stop and fix before committing.

- [ ] **Step 6: Verify the loop still parks**

With the page open, scroll the hero fully off screen, then open DevTools Performance and record 3 seconds. Expected: no sustained rAF callbacks from hero-cinema.js. Repeat with the tab backgrounded. The `state.onScreen` and `state.hidden` guards already exist; this confirms the lower `flowing` threshold did not defeat them.

- [ ] **Step 7: Commit**

```bash
git add hero/hero-cinema.js
git commit -m "Let the hero field run at rest

Payload flow rode the same axis as node arrival, so the only resting
progress that showed movement also spent the whole graph. Ramp flow from
0.18 and rest the field at 0.46: six nodes at full flow on landing, the
dashed port cluster still held back for the scroll."
```

---

### Task 4: Put the CTAs on the landing screen

**Files:**
- Modify: `hero/hero-cinema.js:416` (the `kb` ramp)

**Interfaces:**
- Consumes: nothing from earlier tasks.
- Produces: nothing later tasks depend on.

The CTAs are not missing from the layout — `.gc__cta` is `opacity: var(--kb, 0)` and `kb = clamp((p - 0.78) * 5, 0, 1)`, so they were deliberately held until 78% of the scrub. The spec changes that decision: a visitor who never scrolls currently has nothing to act on.

- [ ] **Step 1: Move the CTA reveal to the landing state**

At hero-cinema.js:416, change:

```js
    var kb = clamp((p - 0.78) * 5, 0, 1);
```

to:

```js
    /* The buttons used to arrive on band 3's tail. That reads well as
     * choreography and badly as commerce: a visitor who does not scroll had
     * nothing to act on. They now settle in just after the opening assembly
     * and stay, which is the one thing the landing screen was missing. */
    var kb = clamp((p - 0.06) * 6, 0, 1);
```

- [ ] **Step 2: Verify in the browser**

```bash
./deploy.sh --no-content
```

At 1440x900, without scrolling, confirm:

- "See services" and "See pricing" are visible and inside the first viewport.
- Both are clickable — `data-live` must be `1` (it flips at `kb > 0.5`; inspect the element).
- The scroll cue is visible at the bottom of the stage. If it is not, note where it actually sits; the cue is `position: absolute; bottom: 26px` on the stage, and if the stage is taller than the viewport the cue is off screen. That is a separate defect from the CTA one — record it, do not silently widen this task.

- [ ] **Step 3: Verify at 390x844**

Confirm the buttons do not collide with the field or the copy. `.gc__cta` has its own compact rules at hero-cinema.css:374; if they overlap, fix there rather than in JS.

- [ ] **Step 4: Commit**

```bash
git add hero/hero-cinema.js
git commit -m "Land the hero with something to act on

The CTAs were gated behind 78% of the scrub, so a visitor who never
scrolled saw a headline, a diagram and no action. Settle them in just
after the opening assembly instead."
```

---

### Task 5: Ship and confirm idempotence

**Files:**
- Modify: none (delivery only)

- [ ] **Step 1: Confirm the layer is idempotent**

```bash
./deploy.sh --no-content
./deploy.sh --no-content
grep -c 'hero-cinema.js' site/index.html
```

Expected: `1`. A `2` means the per-asset guard in `apply_hero` was defeated — do not deploy, fix the guard first. This repo has shipped a double-loaded `hero-motion.js` before for exactly this reason.

- [ ] **Step 2: Run the full local check**

```bash
python3 tests/test_hero_contrast.py
```

Expected: exit 0.

- [ ] **Step 3: Capture the before/after**

Screenshot the live hero at 1440x900 and put it beside the pre-change capture. The claim under review is "reads as running, not printed" — that is a visual claim and needs a visual artifact, not a green test.

- [ ] **Step 4: Deploy**

```bash
./deploy.sh --no-content
```

Then confirm on https://georgeai.dev that the six-node resting state, the moving payloads, and both CTAs are present on landing.

---

## Notes for the executor

- There is no JS test runner in this repo and this plan does not add one. Task 1 tests the one thing that can be checked deterministically — the composited contrast — and the rest is browser verification with explicit pass criteria. Do not fabricate a green result for a step whose criteria you did not actually observe.
- Every constant in Tasks 2-4 is a single number chosen against a measurement in the spec. If a value looks wrong once you see it rendered, say so and retune it rather than working around it elsewhere.
- `site/` is build output. If you find yourself editing it, stop.
