#!/usr/bin/env python3
"""
gen_mockups.py — generate the on-brand dark-UI mockup SVGs for georgeai.dev.

The design-tool export leaves empty placeholder slots (diagonal-hatch divs with
a `[ label ]`) on the About page, the News cards and every service-detail view.
This script draws a distinct, self-contained SVG "product mockup" for each one,
all from the same palette / type / window-chrome primitives so they read as one
visual system.

Output: images/mock/*.svg  (committed; apply_images.py copies them into site/).
Regenerate after a palette change:  python3 images/gen_mockups.py

Pure stdlib, no deps. Deterministic (no randomness) so re-runs are byte-stable.
"""
import math
import os

# --- palette (from DESIGN-claude.md, dark surfaces) -------------------------
BG       = "#181715"   # surface-dark
PANEL    = "#1f1e1b"   # surface-dark-soft
ELEV     = "#252320"   # surface-dark-elevated
LINE     = "#34302b"   # hairline on dark
LINE2    = "#413b34"   # brighter hairline
ACCENT   = "#ff6b1a"   # neon orange
ACCENT2  = "#c2410c"   # deep orange, for text on light surfaces
INK      = "#faf9f5"   # on-dark
SOFT     = "#a09d96"   # on-dark-soft
MUTE     = "#6c6a64"   # muted
TEAL     = "#5db8a6"
AMBER    = "#e8a55a"
GREEN    = "#5db872"

MONO  = "'JetBrains Mono','SFMono-Regular',ui-monospace,monospace"
SERIF = "'Newsreader',Georgia,'Times New Roman',serif"

OUT = os.path.join(os.path.dirname(__file__), "mock")


# --- low-level helpers ------------------------------------------------------
def rect(x, y, w, h, r=0, fill=PANEL, stroke=None, sw=1, op=1, dash=None):
    s = f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{r}" fill="{fill}"'
    if op != 1:
        s += f' fill-opacity="{op}"'
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{sw}"'
        if dash:
            s += f' stroke-dasharray="{dash}"'
    return s + "/>"


def line(x1, y1, x2, y2, stroke=LINE, sw=1, dash=None, op=1):
    s = (f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
         f'stroke="{stroke}" stroke-width="{sw}"')
    if dash:
        s += f' stroke-dasharray="{dash}"'
    if op != 1:
        s += f' stroke-opacity="{op}"'
    return s + ' stroke-linecap="round"/>'


def circle(cx, cy, r, fill=ACCENT, stroke=None, sw=1, op=1):
    # when a stroke is given, treat the circle as an outline (fill:none) unless a
    # non-default fill was explicitly requested — never emit `fill` twice.
    face = "none" if (stroke and fill is ACCENT) else fill
    s = f'<circle cx="{cx:.1f}" cy="{cy:.1f}" r="{r:.1f}" fill="{face}"'
    if op != 1:
        s += f' fill-opacity="{op}"'
    if stroke:
        s += f' stroke="{stroke}" stroke-width="{sw}"'
    return s + "/>"


def text(x, y, s, size=13, fill=INK, family=MONO, weight=400, anchor="start", ls=0):
    extra = f' letter-spacing="{ls}"' if ls else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{family}" font-size="{size}" '
            f'font-weight="{weight}" fill="{fill}" text-anchor="{anchor}"{extra}>'
            f'{_esc(s)}</text>')


def path(d, fill="none", stroke=ACCENT, sw=2, op=1, dash=None):
    s = f'<path d="{d}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"'
    if op != 1:
        s += f' stroke-opacity="{op}"'
    if dash:
        s += f' stroke-dasharray="{dash}"'
    return s + ' stroke-linecap="round" stroke-linejoin="round"/>'


def _esc(s):
    return (s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def dot_row(x, y, gap=9):
    """macOS-style window dots."""
    return "".join(circle(x + i * gap, y, 3.2, c) for i, c in
                   enumerate(["#4a453e", "#4a453e", "#4a453e"]))


def pill(x, y, w, h, label, fill=ELEV, fg=SOFT, size=10, stroke=LINE):
    return (rect(x, y, w, h, r=h / 2, fill=fill, stroke=stroke, sw=1) +
            text(x + w / 2, y + h / 2 + size * 0.35, label, size=size, fill=fg, anchor="middle"))


def bar_h(x, y, w, h, fill=LINE2, r=3, op=1):
    return rect(x, y, w, h, r=r, fill=fill, op=op)


def window(cw, ch, pad, title, body, chrome=True):
    """A framed app window filling the content box; `body` is inner markup."""
    parts = [rect(pad, pad, cw, ch, r=16, fill=PANEL, stroke=LINE, sw=1.5)]
    if chrome:
        parts.append(dot_row(pad + 20, pad + 22))
        parts.append(rect(pad + 54, pad + 13, cw - 74, 18, r=9, fill=ELEV))
        parts.append(text(pad + 66, pad + 25, title, size=9.5, fill=MUTE, ls=0.5))
        parts.append(line(pad, pad + 40, pad + cw, pad + 40, stroke=LINE, sw=1))
    return "".join(parts) + body


# --- document scaffold ------------------------------------------------------
def svg(w, h, inner, label=None):
    grad = (
        f'<defs>'
        f'<linearGradient id="bg" x1="0" y1="0" x2="0" y2="1">'
        f'<stop offset="0" stop-color="#1c1b18"/><stop offset="1" stop-color="{BG}"/>'
        f'</linearGradient>'
        f'<radialGradient id="glow" cx="0.78" cy="0.12" r="0.9">'
        f'<stop offset="0" stop-color="{ACCENT}" stop-opacity="0.14"/>'
        f'<stop offset="0.5" stop-color="{ACCENT}" stop-opacity="0"/>'
        f'</radialGradient>'
        f'</defs>'
    )
    tag = ""
    if label:
        tag = text(w - 16, h - 14, label, size=10, fill=MUTE, anchor="end", ls=1)
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" '
        f'width="{w}" height="{h}" role="img">'
        f'{grad}'
        f'{rect(0, 0, w, h, r=0, fill="url(#bg)")}'
        f'{rect(0, 0, w, h, r=0, fill="url(#glow)")}'
        f'{inner}{tag}</svg>'
    )


# ============================================================================
# SERVICE SCENES  (content area, 4:3 → 800×600, drawn inside a padded window)
# ============================================================================
SW, SH = 800, 600           # service canvas
NW, NH = 800, 450           # news canvas (16:9)
AW, AH = 640, 800           # about canvas (4:5)


def sc_automation():
    """workflow canvas — node graph."""
    b = []
    nodes = [(150, 200, "trigger", ACCENT), (150, 380, "webhook", TEAL),
             (400, 290, "n8n", INK), (620, 200, "OpenAI", AMBER),
             (620, 380, "CRM", GREEN)]
    edges = [(0, 2), (1, 2), (2, 3), (2, 4)]
    for a, c in edges:
        x1, y1 = nodes[a][0], nodes[a][1]
        x2, y2 = nodes[c][0], nodes[c][1]
        mx = (x1 + x2) / 2
        b.append(path(f"M{x1+46} {y1} C{mx} {y1},{mx} {y2},{x2-46} {y2}",
                      stroke=LINE2, sw=2))
        b.append(circle((x1 + x2) / 2, (y1 + y2) / 2, 2.5, fill=ACCENT, op=.8))
    for x, y, lab, col in nodes:
        b.append(rect(x - 46, y - 26, 92, 52, r=12, fill=ELEV, stroke=LINE2, sw=1.5))
        b.append(circle(x - 28, y, 5, fill=col))
        b.append(text(x - 14, y + 4, lab, size=11, fill=INK))
    return window(SW - 96, SH - 96, 48, "flow · automation.json", "".join(b))


def sc_chatbot():
    """chat widget — bubbles."""
    b = []
    msgs = [("Hi! How can I help?", False), ("Do you ship to Germany?", True),
            ("Yes — 2–3 business days.", False), ("What's the return window?", True),
            ("30 days, free returns.", False)]
    y = 130
    for m, user in msgs:
        w = 40 + len(m) * 6.6
        x = SW - 96 - w if user else 96
        col = ACCENT if user else ELEV
        fg = "#fff" if user else INK
        b.append(rect(x, y, w, 40, r=13, fill=col, stroke=None if user else LINE2, sw=1))
        b.append(text(x + 16, y + 25, m, size=12, fill=fg))
        y += 58
    b.append(rect(96, SH - 150, SW - 192, 44, r=22, fill=PANEL, stroke=LINE2, sw=1.5))
    b.append(text(120, SH - 122, "Type a message…", size=12, fill=MUTE))
    b.append(circle(SW - 132, SH - 128, 15, fill=ACCENT))
    b.append(path(f"M{SW-138} {SH-128} l12 0 M{SW-131} {SH-134} l7 6 -7 6",
                  stroke="#fff", sw=2))
    return window(SW - 96, SH - 96, 48, "chat · assistant", "".join(b))


def sc_phone():
    """call agent — waveform + call card."""
    b = []
    cx = SW / 2
    b.append(circle(cx, 210, 46, fill=ELEV, stroke=ACCENT, sw=2))
    b.append(path(f"M{cx-13} {195} q-3 14 10 22 q13 8 20 -4 l-6 -9 q-8 6 -12 1 "
                  f"q-4 -5 2 -12 z", fill=ACCENT, stroke="none"))
    b.append(text(cx, 300, "Incoming — AI agent", size=14, fill=INK, anchor="middle"))
    b.append(text(cx, 324, "connected · 00:42", size=11, fill=MUTE, anchor="middle"))
    # waveform
    base = 420
    bars = [18, 34, 52, 30, 44, 66, 40, 58, 24, 48, 70, 36, 54, 28, 44, 60, 32, 46,
            22, 38, 56, 30, 50, 40]
    n = len(bars)
    total = SW - 200
    step = total / n
    for i, hgt in enumerate(bars):
        x = 100 + i * step
        col = ACCENT if i % 3 == 0 else SOFT
        b.append(rect(x, base - hgt / 2, step * 0.5, hgt, r=3, fill=col,
                      op=.5 + 0.5 * (i % 2)))
    b.append(rect(cx - 70, base + 60, 140, 44, r=22, fill=ACCENT))
    b.append(text(cx, base + 88, "Book a call", size=13, fill="#fff", anchor="middle"))
    return window(SW - 96, SH - 96, 48, "phone · voice-agent", "".join(b))


def sc_seo():
    """rankings dashboard — bars + rank list."""
    b = []
    b.append(text(96, 120, "Keyword rankings", size=13, fill=INK))
    b.append(pill(SW - 210, 100, 114, 24, "▲ +38% · 30d", fill=ELEV, fg=GREEN, size=10))
    # bar chart
    vals = [40, 58, 52, 74, 68, 92, 120, 110, 150]
    bw = 44
    gap = ((SW - 192) - len(vals) * bw) / (len(vals) - 1)
    base = 340
    for i, v in enumerate(vals):
        x = 96 + i * (bw + gap)
        col = ACCENT if i >= len(vals) - 2 else LINE2
        b.append(rect(x, base - v, bw, v, r=5, fill=col))
    b.append(line(96, base, SW - 96, base, stroke=LINE, sw=1))
    # rank rows
    rows = [("ai automation agency", "#3", ACCENT), ("n8n consultant", "#1", GREEN),
            ("rag chatbot developer", "#5", SOFT)]
    y = 400
    for name, rk, col in rows:
        b.append(rect(96, y, SW - 192, 46, r=10, fill=ELEV, stroke=LINE, sw=1))
        b.append(text(118, y + 29, name, size=12, fill=INK))
        b.append(text(SW - 120, y + 29, rk, size=13, fill=col, anchor="end", weight=500))
        y += 56
    return window(SW - 96, SH - 96, 48, "seo · rankings", "".join(b))


def sc_email():
    """campaign flow — sequence steps."""
    b = []
    steps = [("Signup", ACCENT), ("Welcome", TEAL), ("Wait 2d", MUTE),
             ("Offer", AMBER), ("Convert", GREEN)]
    y = 200
    x = 130
    dx = (SW - 260) / (len(steps) - 1)
    for i, (lab, col) in enumerate(steps):
        cx = x + i * dx
        if i:
            b.append(line(cx - dx + 30, y, cx - 30, y, stroke=LINE2, sw=2, dash="2 6"))
        b.append(circle(cx, y, 30, fill=ELEV, stroke=col, sw=2))
        b.append(circle(cx, y, 6, fill=col))
        b.append(text(cx, y + 60, lab, size=11, fill=SOFT, anchor="middle"))
    # metric tiles
    tiles = [("Sent", "12,480"), ("Open", "41%"), ("Click", "9.2%"), ("Rev.", "€6.1k")]
    tw = (SW - 192 - 3 * 16) / 4
    ty = 360
    for i, (k, v) in enumerate(tiles):
        tx = 96 + i * (tw + 16)
        b.append(rect(tx, ty, tw, 90, r=12, fill=ELEV, stroke=LINE, sw=1))
        b.append(text(tx + 16, ty + 32, k.upper(), size=9, fill=MUTE, ls=1))
        b.append(text(tx + 16, ty + 66, v, size=22, fill=INK, family=SERIF))
    return window(SW - 96, SH - 96, 48, "email · sequence", "".join(b))


def sc_leads():
    """lead pipeline — kanban."""
    b = []
    cols = [("New", 3, ACCENT), ("Qualified", 2, TEAL), ("Won", 2, GREEN)]
    cw = (SW - 192 - 2 * 20) / 3
    x = 96
    for title, n, col in cols:
        b.append(text(x + 6, 120, title.upper(), size=10, fill=MUTE, ls=1))
        b.append(circle(x + 6 + len(title) * 6.4 + 14, 116, 8, fill=ELEV, stroke=col, sw=1.5))
        b.append(text(x + 6 + len(title) * 6.4 + 14, 120, str(n), size=9, fill=col, anchor="middle"))
        cy = 145
        for j in range(n):
            b.append(rect(x, cy, cw, 84, r=12, fill=ELEV, stroke=LINE, sw=1))
            b.append(circle(x + 22, cy + 26, 11, fill=PANEL, stroke=col, sw=1.5))
            b.append(rect(x + 40, cy + 20, 80, 9, r=4, fill=LINE2))
            b.append(rect(x + 40, cy + 36, 52, 8, r=4, fill=LINE))
            b.append(rect(x + 16, cy + 58, cw - 32, 8, r=4, fill=LINE, op=.7))
            cy += 96
        x += cw + 20
    return window(SW - 96, SH - 96, 48, "crm · leads", "".join(b))


def sc_python():
    """code editor — colored code lines."""
    b = []
    b.append(rect(48, 88, 150, SH - 96 - 40, r=0, fill=ELEV, op=.5))  # gutter tint
    lines = [
        [(ACCENT, 3), (INK, 7), (TEAL, 5)],
        [(MUTE, 10)],
        [(AMBER, 4), (INK, 6)],
        [(INK, 3), (ACCENT, 5), (INK, 8), (TEAL, 4)],
        [(INK, 5), (GREEN, 9)],
        [],
        [(ACCENT, 4), (INK, 6), (AMBER, 5)],
        [(INK, 8), (TEAL, 6)],
        [(MUTE, 12)],
        [(INK, 4), (ACCENT, 7)],
    ]
    y = 128
    for i, toks in enumerate(lines):
        b.append(text(78, y + 4, str(i + 1), size=10, fill=MUTE, anchor="end"))
        x = 118
        for col, ln in toks:
            w = ln * 11
            b.append(rect(x, y - 9, w, 12, r=3, fill=col, op=.85))
            x += w + 8
        y += 34
    # cursor
    b.append(rect(118, y - 43, 2, 14, r=1, fill=ACCENT))
    return window(SW - 96, SH - 96, 48, "main.py · python", "".join(b))


def sc_django():
    """web platform — browser + layout blocks."""
    b = []
    b.append(rect(96, 110, SW - 192, 40, r=10, fill=ELEV, stroke=LINE, sw=1))
    b.append(circle(120, 130, 4, fill=MUTE))
    b.append(circle(134, 130, 4, fill=MUTE))
    b.append(rect(160, 120, SW - 300, 20, r=10, fill=PANEL))
    b.append(text(178, 134, "app.georgeai.dev/dashboard", size=10, fill=SOFT))
    # nav + content
    b.append(rect(96, 166, 150, SH - 96 - 130, r=10, fill=ELEV, stroke=LINE, sw=1))
    for i in range(5):
        c = ACCENT if i == 1 else LINE2
        b.append(rect(116, 190 + i * 40, 110, 12, r=4, fill=c, op=.9 if i == 1 else .6))
    b.append(rect(262, 166, SW - 96 - 262, 70, r=10, fill=ELEV, stroke=LINE, sw=1))
    b.append(text(284, 208, "Django + PostgreSQL", size=13, fill=INK, family=SERIF))
    gy = 252
    gw = (SW - 96 - 262 - 16) / 2
    for i in range(4):
        gx = 262 + (i % 2) * (gw + 16)
        ry = gy + (i // 2) * 84
        b.append(rect(gx, ry, gw, 70, r=10, fill=PANEL, stroke=LINE, sw=1))
        b.append(rect(gx + 16, ry + 18, 60, 9, r=4, fill=LINE2))
        b.append(rect(gx + 16, ry + 38, gw - 90, 8, r=4, fill=LINE))
        b.append(circle(gx + gw - 24, ry + 26, 10, fill=PANEL, stroke=ACCENT, sw=1.5))
    return window(SW - 96, SH - 96, 48, "django · platform", "".join(b))


def sc_erp():
    """erp modules — tile grid."""
    mods = [("Invoicing", ACCENT), ("Inventory", TEAL), ("HR", AMBER),
            ("Orders", GREEN), ("Reports", SOFT), ("Settings", MUTE)]
    b = []
    b.append(text(96, 120, "Modules", size=13, fill=INK))
    cw = (SW - 192 - 2 * 18) / 3
    ch = 120
    for i, (name, col) in enumerate(mods):
        x = 96 + (i % 3) * (cw + 18)
        y = 150 + (i // 3) * (ch + 18)
        b.append(rect(x, y, cw, ch, r=14, fill=ELEV, stroke=LINE, sw=1))
        b.append(rect(x + 20, y + 20, 34, 34, r=9, fill=PANEL, stroke=col, sw=1.5))
        b.append(circle(x + 37, y + 37, 6, fill=col))
        b.append(text(x + 20, y + 82, name, size=12, fill=INK))
        b.append(rect(x + 20, y + 96, cw * 0.5, 7, r=3, fill=LINE2))
    return window(SW - 96, SH - 96, 48, "erp · modules", "".join(b))


def sc_crm():
    """crm pipeline — stages + contact rows."""
    b = []
    stages = [("Lead", ACCENT), ("Contacted", TEAL), ("Proposal", AMBER), ("Closed", GREEN)]
    x = 96
    sw_ = (SW - 192 - 3 * 12) / 4
    for lab, col in stages:
        b.append(rect(x, 110, sw_, 34, r=8, fill=ELEV, stroke=LINE, sw=1))
        b.append(circle(x + 18, 127, 4, fill=col))
        b.append(text(x + 32, 131, lab, size=10.5, fill=SOFT))
        x += sw_ + 12
    contacts = [("Meridian GmbH", "€12,400", ACCENT), ("Nord Retail", "€8,900", TEAL),
                ("Kessler AG", "€21,000", AMBER), ("Hansa Logistik", "€5,300", GREEN)]
    y = 170
    for name, val, col in contacts:
        b.append(rect(96, y, SW - 192, 58, r=12, fill=ELEV, stroke=LINE, sw=1))
        b.append(circle(124, y + 29, 15, fill=PANEL, stroke=col, sw=1.5))
        b.append(text(120, y + 33, name[0], size=13, fill=col, anchor="middle"))
        b.append(text(154, y + 27, name, size=12.5, fill=INK))
        b.append(text(154, y + 44, "updated 2h ago", size=9.5, fill=MUTE))
        b.append(text(SW - 120, y + 35, val, size=14, fill=INK, anchor="end", family=SERIF))
        y += 70
    return window(SW - 96, SH - 96, 48, "crm · pipeline", "".join(b))


def sc_webdesign():
    """website mockup — wireframe page."""
    b = []
    m = 130
    w = SW - 2 * m
    b.append(rect(m, 110, w, 34, r=8, fill=ELEV, stroke=LINE, sw=1))
    b.append(circle(m + 22, 127, 6, fill=ACCENT))
    b.append(rect(m + w - 90, 119, 70, 16, r=8, fill=ACCENT))
    # hero
    b.append(rect(m, 158, w, 130, r=12, fill=ELEV, stroke=LINE, sw=1))
    b.append(rect(m + 30, 190, w * 0.5, 18, r=5, fill=INK, op=.85))
    b.append(rect(m + 30, 218, w * 0.62, 10, r=4, fill=LINE2))
    b.append(rect(m + 30, 236, w * 0.4, 10, r=4, fill=LINE2))
    b.append(rect(m + 30, 258, 96, 22, r=11, fill=ACCENT))
    # cards
    cy = 306
    cw = (w - 2 * 18) / 3
    for i in range(3):
        cx = m + i * (cw + 18)
        b.append(rect(cx, cy, cw, 150, r=12, fill=ELEV, stroke=LINE, sw=1))
        b.append(rect(cx + 18, cy + 18, cw - 36, 54, r=8, fill=PANEL))
        b.append(rect(cx + 18, cy + 86, cw - 60, 10, r=4, fill=LINE2))
        b.append(rect(cx + 18, cy + 104, cw - 40, 8, r=4, fill=LINE))
        b.append(rect(cx + 18, cy + 120, cw - 70, 8, r=4, fill=LINE))
    return window(SW - 96, SH - 96, 48, "figma · web-design", "".join(b))


def sc_rag():
    """rag pipeline — docs → vector → answer."""
    b = []
    midy = 250
    # stage 1 docs
    for i in range(3):
        b.append(rect(110 + i * 6, 190 + i * 6, 90, 116, r=10, fill=ELEV,
                      stroke=LINE2, sw=1.5))
    for k in range(4):
        b.append(rect(128, 214 + k * 20, 70, 7, r=3, fill=LINE2 if k else ACCENT, op=.9))
    b.append(text(150, 340, "documents", size=10, fill=MUTE, anchor="middle"))
    # arrow → vectors
    b.append(path("M230 250 L300 250", stroke=ACCENT, sw=2))
    b.append(path("M296 245 l6 5 -6 5", stroke=ACCENT, sw=2))
    # vector grid
    for r_ in range(4):
        for c_ in range(4):
            v = (r_ * 4 + c_) % 3
            col = [ACCENT, TEAL, LINE2][v]
            b.append(rect(320 + c_ * 26, 200 + r_ * 26, 20, 20, r=5, fill=col,
                          op=.85 if v < 2 else .5))
    b.append(text(372, 340, "vector index", size=10, fill=MUTE, anchor="middle"))
    # arrow → answer
    b.append(path("M448 250 L520 250", stroke=ACCENT, sw=2))
    b.append(path("M516 245 l6 5 -6 5", stroke=ACCENT, sw=2))
    b.append(rect(540, 186, SW - 96 - 540, 128, r=12, fill=ELEV, stroke=ACCENT, sw=1.5))
    b.append(text(562, 214, "Grounded answer", size=12, fill=INK, family=SERIF))
    for k in range(3):
        b.append(rect(562, 232 + k * 18, (SW - 96 - 540 - 44) - k * 14, 7, r=3,
                      fill=LINE2))
    b.append(text(562, 300, "cited · source ✓", size=9.5, fill=GREEN))
    return window(SW - 96, SH - 96, 48, "rag · retrieval", "".join(b))


def sc_cro():
    """landing optimization — A/B + uplift."""
    b = []
    for i, (lab, col, conv) in enumerate([("Variant A", MUTE, .38), ("Variant B", ACCENT, .61)]):
        x = 96 + i * ((SW - 192) / 2 + 16)
        w = (SW - 192) / 2 - 8
        b.append(rect(x, 110, w, 210, r=12, fill=ELEV, stroke=col if i else LINE, sw=1.5 if i else 1))
        b.append(text(x + 20, 138, lab, size=11, fill=col, ls=.5))
        b.append(rect(x + 20, 152, w - 40, 60, r=8, fill=PANEL))
        b.append(rect(x + 20, 224, w * 0.5, 14, r=5, fill=INK, op=.7))
        b.append(rect(x + 20, 248, 70, 20, r=10, fill=col))
        b.append(text(x + 20, 300, f"{int(conv*100)}% conv.", size=13, fill=col, family=SERIF))
    # uplift bar
    b.append(rect(96, 350, SW - 192, 100, r=12, fill=ELEV, stroke=LINE, sw=1))
    b.append(text(120, 384, "CONVERSION UPLIFT", size=10, fill=MUTE, ls=1))
    b.append(text(120, 428, "+61%", size=34, fill=GREEN, family=SERIF))
    # sparkline
    pts = [10, 22, 18, 34, 30, 48, 44, 66, 80]
    sx, sy, sw2 = 300, 430, SW - 96 - 320
    d = ""
    for i, v in enumerate(pts):
        px = sx + i * (sw2 / (len(pts) - 1))
        py = sy - v
        d += ("M" if i == 0 else "L") + f"{px:.1f} {py:.1f} "
    b.append(path(d, stroke=GREEN, sw=2.5))
    return window(SW - 96, SH - 96, 48, "cro · a/b test", "".join(b))


def sc_saas():
    """saas dashboard — stat tiles + area chart."""
    b = []
    tiles = [("MRR", "€24.8k", GREEN), ("Users", "1,204", ACCENT), ("Churn", "1.8%", AMBER)]
    tw = (SW - 192 - 2 * 16) / 3
    for i, (k, v, col) in enumerate(tiles):
        x = 96 + i * (tw + 16)
        b.append(rect(x, 110, tw, 96, r=12, fill=ELEV, stroke=LINE, sw=1))
        b.append(text(x + 18, 138, k.upper(), size=9.5, fill=MUTE, ls=1))
        b.append(text(x + 18, 176, v, size=26, fill=INK, family=SERIF))
        b.append(circle(x + tw - 24, 130, 4, fill=col))
    # area chart
    b.append(rect(96, 224, SW - 192, SH - 96 - 224 - 24, r=12, fill=ELEV, stroke=LINE, sw=1))
    cx0, cy0 = 120, 470
    cw2 = SW - 192 - 48
    pts = [30, 46, 40, 66, 58, 88, 78, 104, 96, 128, 150]
    d = f"M{cx0} {cy0} "
    dl = ""
    for i, v in enumerate(pts):
        px = cx0 + i * (cw2 / (len(pts) - 1))
        py = cy0 - v
        d += f"L{px:.1f} {py:.1f} "
        dl += ("M" if i == 0 else "L") + f"{px:.1f} {py:.1f} "
    d += f"L{cx0+cw2} {cy0} Z"
    b.append(path(d, fill=ACCENT, stroke="none", op=.14))
    b.append(path(dl, stroke=ACCENT, sw=2.5))
    for i, v in enumerate(pts):
        if i % 2 == 0:
            b.append(circle(cx0 + i * (cw2 / (len(pts) - 1)), cy0 - v, 3, fill=ACCENT))
    b.append(text(120, 254, "Revenue · last 6 months", size=11, fill=SOFT))
    return window(SW - 96, SH - 96, 48, "saas · dashboard", "".join(b))


def sc_api():
    """api integration — services + JSON."""
    b = []
    hub = (230, 250)
    b.append(circle(hub[0], hub[1], 34, fill=ELEV, stroke=ACCENT, sw=2))
    b.append(text(hub[0], hub[1] + 4, "API", size=13, fill=ACCENT, anchor="middle", weight=500))
    ends = [("REST", 120, 150, TEAL), ("n8n", 120, 350, AMBER),
            ("SQL", 340, 160, GREEN), ("CSV", 340, 340, SOFT)]
    for lab, x, y, col in ends:
        b.append(path(f"M{hub[0]} {hub[1]} L{x} {y}", stroke=LINE2, sw=1.5, dash="2 5"))
        b.append(rect(x - 40, y - 18, 80, 36, r=9, fill=ELEV, stroke=LINE2, sw=1))
        b.append(circle(x - 24, y, 4, fill=col))
        b.append(text(x - 12, y + 4, lab, size=11, fill=INK))
    # JSON panel
    px = 440
    b.append(rect(px, 130, SW - 96 - px, SH - 96 - 130 - 24, r=12, fill="#141311",
                  stroke=LINE, sw=1))
    jt = [("{", INK, 0), ('"status": ', SOFT, 1), ("200,", GREEN, 0),
          ('"rows": ', SOFT, 1), ("1240,", ACCENT, 0),
          ('"synced": ', SOFT, 1), ("true", TEAL, 0), ("}", INK, 0)]
    y = 162
    for i, (t, col, ind) in enumerate(jt):
        b.append(text(px + 20 + ind * 18, y, t, size=12, fill=col))
        y += 26
    return window(SW - 96, SH - 96, 48, "api · integration", "".join(b))


# ============================================================================
# NEWS SCENES (16:9)
# ============================================================================
def news_automation():
    b = []
    # mini node flow, editorial
    nodes = [(180, 230, ACCENT), (360, 150, TEAL), (360, 310, AMBER), (560, 230, GREEN)]
    edges = [(0, 1), (0, 2), (1, 3), (2, 3)]
    for a, c in edges:
        x1, y1 = nodes[a][:2]
        x2, y2 = nodes[c][:2]
        mx = (x1 + x2) / 2
        b.append(path(f"M{x1+30} {y1} C{mx} {y1},{mx} {y2},{x2-30} {y2}", stroke=LINE2, sw=2))
    for x, y, col in nodes:
        b.append(rect(x - 30, y - 20, 60, 40, r=10, fill=ELEV, stroke=col, sw=1.5))
        b.append(circle(x, y, 6, fill=col))
    b.append(text(NW / 2, NH - 46, "AUTOMATION", size=12, fill=SOFT, anchor="middle", ls=3))
    return "".join(b)


def news_ai():
    b = []
    msgs = [("Ask anything…", False, 280), ("Cite your sources.", True, 200),
            ("Here — 3 grounded refs ✓", False, 260)]
    y = 150
    for m, user, w in msgs:
        x = NW / 2 + 40 if user else NW / 2 - 40 - w
        col = ACCENT if user else ELEV
        fg = "#fff" if user else INK
        b.append(rect(x, y, w, 44, r=14, fill=col, stroke=None if user else LINE2, sw=1))
        b.append(text(x + 18, y + 27, m, size=13, fill=fg))
        y += 62
    b.append(text(NW / 2, NH - 46, "AI · RAG", size=12, fill=SOFT, anchor="middle", ls=3))
    return "".join(b)


def news_data():
    b = []
    # spreadsheet → chart
    gx, gy = 130, 130
    for r_ in range(4):
        for c_ in range(3):
            b.append(rect(gx + c_ * 60, gy + r_ * 34, 56, 30, r=5,
                          fill=ELEV if (r_ + c_) % 2 else PANEL, stroke=LINE, sw=1))
    b.append(path("M330 250 L400 250", stroke=ACCENT, sw=2))
    b.append(path("M396 245 l6 5 -6 5", stroke=ACCENT, sw=2))
    vals = [40, 70, 55, 96, 120]
    base = 268
    for i, v in enumerate(vals):
        x = 430 + i * 48
        col = ACCENT if i == len(vals) - 1 else LINE2
        b.append(rect(x, base - v, 34, v, r=5, fill=col))
    b.append(line(430, base, 430 + len(vals) * 48, base, stroke=LINE, sw=1))
    b.append(text(NW / 2, NH - 46, "DATA", size=12, fill=SOFT, anchor="middle", ls=3))
    return "".join(b)


# ============================================================================
# ABOUT SCENE (4:5) — non-figurative workspace
# ============================================================================
def about_scene():
    b = []
    W, H = AW, AH
    # editor window (upper)
    ex, ey, ew, eh = 70, 90, W - 140, 300
    b.append(rect(ex, ey, ew, eh, r=16, fill=PANEL, stroke=LINE, sw=1.5))
    b.append(dot_row(ex + 22, ey + 24))
    b.append(rect(ex + 56, ey + 15, ew - 78, 18, r=9, fill=ELEV))
    b.append(text(ex + 68, ey + 28, "george@dev ~ build", size=9.5, fill=MUTE, ls=.5))
    b.append(line(ex, ey + 44, ex + ew, ey + 44, stroke=LINE, sw=1))
    codelines = [
        [(ACCENT, 3), (INK, 6), (TEAL, 4)],
        [(MUTE, 9)],
        [(AMBER, 4), (INK, 5), (GREEN, 6)],
        [(INK, 3), (ACCENT, 5), (INK, 7)],
        [(INK, 6), (TEAL, 3)],
        [(ACCENT, 4), (INK, 8)],
    ]
    y = ey + 78
    for i, toks in enumerate(codelines):
        b.append(text(ex + 40, y + 4, str(i + 1), size=9, fill=MUTE, anchor="end"))
        x = ex + 54
        for col, ln in toks:
            w = ln * 12
            b.append(rect(x, y - 9, w, 12, r=3, fill=col, op=.85))
            x += w + 8
        y += 34
    b.append(rect(ex + 54, y - 43, 2, 13, r=1, fill=ACCENT))
    # terminal window (lower)
    tx, ty, tw, th = 70, 420, W - 140, 300
    b.append(rect(tx, ty, tw, th, r=16, fill="#141311", stroke=LINE, sw=1.5))
    b.append(dot_row(tx + 22, ty + 24))
    b.append(text(tx + 56, ty + 28, "terminal", size=9.5, fill=MUTE, ls=.5))
    b.append(line(tx, ty + 44, tx + tw, ty + 44, stroke=LINE, sw=1))
    term = [(GREEN, "$ ", INK, "deploy --prod"),
            (SOFT, "  ", SOFT, "building 15 services…"),
            (SOFT, "  ", TEAL, "✓ automation  ✓ rag  ✓ crm"),
            (SOFT, "  ", SOFT, "syncing to VPS…"),
            (GREEN, "  ", GREEN, "✓ live · georgeai.dev")]
    y = ty + 74
    for pre_c, pre, col, msg in term:
        b.append(text(tx + 26, y, pre, size=12, fill=pre_c, family=MONO))
        b.append(text(tx + 26 + len(pre) * 7.4, y, msg, size=12, fill=col, family=MONO))
        y += 30
    b.append(rect(tx + 26, y - 11, 8, 13, r=1, fill=ACCENT))
    # brand mark
    b.append(text(W / 2, H - 34, "GeorgeAI", size=15, fill=SOFT, anchor="middle", family=SERIF))
    return "".join(b)


# ============================================================================
# registry
# ============================================================================
SERVICES = [
    # (filename slug,   svcMeta name,                     scene fn,      label)
    ("automation",                 "Automation",                       sc_automation, "[ workflow canvas ]"),
    ("ai-chatbot",                 "AI Chatbot",                       sc_chatbot,    "[ chat widget ]"),
    ("ai-phone-calls",             "AI Phone Calls",                   sc_phone,      "[ call agent ]"),
    ("seo-aio-geo",                "SEO / AIO / GEO",                  sc_seo,        "[ rankings dashboard ]"),
    ("email-marketing",            "Email Marketing",                  sc_email,      "[ campaign flow ]"),
    ("lead-generation",            "Lead Generation",                  sc_leads,      "[ lead pipeline ]"),
    ("python-programming",         "Python Programming",               sc_python,     "[ code editor ]"),
    ("django",                     "Django",                           sc_django,     "[ web platform ]"),
    ("micro-erp",                  "Micro ERP",                        sc_erp,        "[ erp modules ]"),
    ("crm",                        "CRM",                              sc_crm,        "[ crm pipeline ]"),
    ("web-design",                 "Web Design",                       sc_webdesign,  "[ website mockup ]"),
    ("rag",                        "RAG",                              sc_rag,        "[ rag pipeline ]"),
    ("web-design-optimization",    "Web Design Optimization",          sc_cro,        "[ landing optimization ]"),
    ("saas-projects",              "SaaS Projects",                    sc_saas,       "[ saas dashboard ]"),
    ("api-integration-data-analytics", "API Integration & Data Analytics", sc_api,   "[ api integration ]"),
]

NEWS = [
    ("news-0", news_automation),
    ("news-1", news_ai),
    ("news-2", news_data),
]


def main():
    os.makedirs(OUT, exist_ok=True)
    written = []
    for slug, _name, fn, label in SERVICES:
        doc = svg(SW, SH, fn(), label=None)
        p = os.path.join(OUT, f"svc-{slug}.svg")
        open(p, "w", encoding="utf-8").write(doc)
        written.append(os.path.basename(p))
    for slug, fn in NEWS:
        doc = svg(NW, NH, fn())
        p = os.path.join(OUT, f"{slug}.svg")
        open(p, "w", encoding="utf-8").write(doc)
        written.append(os.path.basename(p))
    doc = svg(AW, AH, about_scene())
    p = os.path.join(OUT, "about.svg")
    open(p, "w", encoding="utf-8").write(doc)
    written.append(os.path.basename(p))
    print(f"wrote {len(written)} mockups to {OUT}/")
    for w in written:
        print("  ·", w)


if __name__ == "__main__":
    main()
