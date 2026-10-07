# Hero presence: make the n8n field read as running, not printed

Date: 2026-08-25
Status: approved, not yet implemented
Scope: `hero/hero-cinema.js`, `hero/hero-cinema.css`

## Problem

The hero landing state reads as a brochure to a first-time visitor. Diagnosis
came from a 1440x900 capture of production plus the source, not from taste:

1. **Nothing moves at rest.** `tick()` sets the graph's resting progress to
   `lk * 0.30` (hero-cinema.js:1015) while payload flow is gated on
   `shown > 0.55` (hero-cinema.js:1020). After the 900ms load ramp the rAF loop
   converges and stops. The visitor sees a still image of a workflow.
2. **Sub-labels are below the contrast floor.** `colors.body` (#a8a29a) drawn at
   `k * (0.20 + 0.20 * n.z)` lands near alpha 0.33 on the #141413 ground, about
   1.9:1. "form submitted" and "GET:" are effectively invisible.
3. **Node cards have no surface.** The card is filled with `colors.ground` —
   the page background — then lifted by `ink` at alpha 0.05. The card does not
   read as a plane; only the accent-tiled AI Agent node has presence.
4. **No call to action above the fold.** `gc__cta` and `gc__cue` exist in
   hero-cinema.html but fall below 900px of viewport height.

Note what is NOT wrong: the field already carries a depth axis (`n.z`), pointer
parallax (hero-motion.js:565), flowing payloads, and nine nodes. The four that
look "missing" (Airtable, OpenAI Chat, Postgres, Vector Store) are gated behind
scroll by their `t` values and are meant to arrive later.

## Non-goals

- No WebGL / Three.js. Every defect above is a contrast, timing, and layout
  problem; a renderer swap would reproduce all four and add a bundle, a
  fallback path, and CSP surface.
- No new nodes. The inventory is correct.
- No new deploy layer. This ships through the existing `apply_hero`.

## Design

### 1. Resting state that runs

The blocker is that payload flow and node arrival ride the same axis. Payload
opacity is `smoothstep(p, 0.5, 0.78)` (hero-cinema.js:793) and the rAF keep-alive
is `shown > 0.55` (hero-cinema.js:1020), while the last node arrives at `t = 0.56`.
Any resting progress high enough to show movement also spends the entire graph,
leaving the scroll with nothing to reveal. The two must be decoupled.

- Re-ramp payload flow to `smoothstep(p, 0.18, 0.42)` so wires carry traffic as
  soon as there is a wire to carry it on.
- Lower the rAF keep-alive to `shown > 0.20` to match.
- Raise resting progress from `lk * 0.30` to `lk * 0.46`.

At rest that yields six of nine nodes — through Airtable (`t = 0.40`) — with
payloads at full flow. The three dashed-port sub-nodes (OpenAI Chat, Postgres,
Vector Store, `t` 0.48-0.56) stay as the scroll payoff, and they are the right
ones to hold back: the dashed port cluster is the shape that rewards a second
look rather than the one that establishes the register.

The rAF loop then runs continuously at rest. This is already the model
`idleTick` uses in static mode, and it inherits the same guards: the loop is
gated on `state.onScreen` and `!state.hidden`, so it costs nothing off screen or
in a background tab, and `reduceMotion` suppresses flow entirely.

### 2. Contrast

Measured against the #141413 ground, at the near-plane z of 0.66:

| Element | Now | Change to | Effect |
|---|---|---|---|
| Sub-label | `body x (0.20 + 0.20z)` | `ink x (0.36 + 0.18z)` | 1.87:1 -> 4.55:1 |
| Card surface | `ground`, then `ink x 0.05` | ground lightened ~4%, `ink x 0.055` | card becomes a plane |
| Card border | `ink x (0.16 + 0.30z)` | `ink x (0.28 + 0.30z)` | contour reads |
| Label | `ink x (0.34 + 0.34z)` | unchanged (~5.5:1) | already passing |

The sub-label changes token, and that is the point. Reaching 4.5:1 with `body`
(#a8a29a) requires alpha 0.74 at the z=0.66 plane, which pins the sub-line near
opaque and erases its depth cue. `ink` (#f5f2ec) clears the same floor at 0.48,
leaving room for a gradient. Hierarchy survives because the label stays brighter
still (0.56-0.68 against the sub-line's 0.48-0.54).

All ratios above are computed through sRGB relative luminance, not by scaling
the alpha. A linear estimate overstates them by roughly 1.5x at these values.

Depth is preserved: far-plane nodes stay dimmer than near-plane ones. The floor
moves up; the gradient does not flatten.

### 3. First screen

Anchor `gc__cta` and `gc__cue` inside band 1 so "See services" / "See pricing"
are visible on landing at 900px viewport height. CSS only — the HTML structure
and its single `<h1>` contract are untouched.

## Verification

Manual, at 1440x900 and at 390x844:

- At rest, without scrolling: payloads visibly move; six nodes present.
- Sub-label contrast measured at 4.5:1 or better against the ground.
- Both CTAs and the scroll cue inside the first viewport.
- With `prefers-reduced-motion: reduce`: no flow, no assembly, static frame.
- Off screen and in a background tab: no rAF activity (guards already exist).
- `./deploy.sh --no-content` re-applies cleanly and is idempotent on a second run.

## Risks

- Continuous rAF at rest raises idle CPU on the homepage. Mitigated by the
  existing visibility guards; measure before shipping.
- Raising the resting progress changes what the scroll reveals. If the remaining
  three sub-nodes feel like too small a payoff, the resting value and the flow
  ramp are two constants to retune independently.
