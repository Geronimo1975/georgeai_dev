# Generates the 5 pages of /cinematic/ from shared fragments. Not shipped.
import os, re, json
from merge_frag import TOPBAR, MARQ, HOW, WORK4, WORK_HEAD, SVCGRID, FAQ, FAQ_LD, NEWSLETTER, LEGAL_BODY
FRAG = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frag')
OUT = '/Users/Geronimo/Projects/georgeai_dev/pages/cinematic'
BASE = '/cinematic/'
def frag(n): return open(f'{FRAG}/{n}.html', encoding='utf-8').read()

SRI = {
 'gsap': 'sha384-g4NTh/Iv5PPU4xPyhEWqPcwtNXOvdaDI8LLnyYfyNZOjKJeYQyjzQ9X5275eBjpt',
 'st': 'sha384-Z3REaz79l2IaAZqJsSABtTbhjgOUYyV3p90XNnAPCSHg3EMTz1fouunq9WZRtj3d',
 'lenis': 'sha384-tKsJDT6PlUI0pSBt9/sBKJluKgA19/a6mBrDsZaXotLB4ZYfMGM6xt6/WgGpYhTm',
}
NAV = [('services/','Services'),('assistant/','Assistant'),('work/','Work'),('about/','About'),('/blog/','Blog'),('pricing/','Pricing'),('contact/','Contact')]

def head(title, desc, path, og_img='assets/george.jpg', extra_js=''):
    url = f'https://georgeai.dev{BASE}{path}'
    return f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="theme-color" content="#02060a">
<link rel="canonical" href="{url}">
<!-- DEPLOY STEP: og:url / og:image carry the live absolute URLs -->
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="https://georgeai.dev{BASE}{og_img}">
<link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%2302060a'/%3E%3Cpath d='M10 7h12l-5 9 5 9H10l5-9z' fill='none' stroke='%23fb5e31' stroke-width='2.2' stroke-linejoin='round'/%3E%3C/svg%3E">
<link rel="preload" href="/assets/fonts/plusjakartasans-var-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/fonts.css">
<link rel="stylesheet" href="{BASE}style.css?v=5">
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/gsap.min.js" integrity="{SRI['gsap']}" crossorigin="anonymous" defer></script>
<script src="https://cdn.jsdelivr.net/npm/gsap@3.12.5/dist/ScrollTrigger.min.js" integrity="{SRI['st']}" crossorigin="anonymous" defer></script>
<script src="https://cdn.jsdelivr.net/npm/lenis@1.1.18/dist/lenis.min.js" integrity="{SRI['lenis']}" crossorigin="anonymous" defer></script>
<script src="{BASE}script.js?v=5" defer></script>
{extra_js}</head>
<body data-page="{path.strip('/') or 'home'}">
<a class="skip" href="#main">Skip to content</a>
<div class="env" aria-hidden="true"></div>
<div class="grain" aria-hidden="true"></div>
'''

def nav(active):
    links = ''.join(f'<a href="{h if h.startswith("/") else BASE+h}"{" aria-current=\"page\"" if h==active else ""}>{t}</a>' for h,t in NAV)
    sheet = ''.join(f'<a href="{h if h.startswith("/") else BASE+h}">{t}</a>' for h,t in NAV)
    return TOPBAR + f'''<header class="nav" id="nav">
  <a class="wordmark" href="{BASE}" aria-label="GeorgeAI home">
    <svg width="26" height="26" viewBox="0 0 32 32" aria-hidden="true"><path d="M10 7h12l-5 9 5 9H10l5-9z" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linejoin="round"/></svg>
    George<b>AI</b>
  </a>
  <nav aria-label="Primary">{links}</nav>
  <a class="btn btn-nav" href="{BASE}contact/" data-audit>Free audit</a>
  <button class="burger" aria-label="Open menu" aria-expanded="false" aria-controls="sheet"><span></span><span></span></button>
</header>
<div class="sheet" id="sheet" hidden>
  {sheet}
  <a class="btn" href="{BASE}contact/" data-audit>Get your free visibility audit</a>
</div>

<main id="main" tabindex="-1">
'''

SAND = '''<svg class="sand" viewBox="0 0 100 3000" preserveAspectRatio="none" aria-hidden="true">
  <path id="sandpath" d="M50 0 C50 200 50 300 50 420 C50 560 30 620 50 760 C70 900 50 980 50 1120 C50 1260 20 1300 20 1440 M50 1120 C50 1260 50 1300 50 1440 M50 1120 C50 1260 80 1300 80 1440 M20 1440 C20 1600 50 1700 50 1880 M80 1440 C80 1600 50 1700 50 1880 M50 1440 C50 1600 50 1700 50 1880 C50 2060 50 2200 50 2400 C50 2600 50 2800 50 3000"/>
</svg>
'''

SAND_SUB = '''<svg class="sand" viewBox="0 0 100 3000" preserveAspectRatio="none" aria-hidden="true"><path id="sandpath" d="M50 0 V3000"/></svg>
'''

def page_head(kicker, h1, lede, img=None):
    fig = f'<figure class="ph-fig" aria-hidden="true"><img src="{BASE}assets/{img}" alt="" loading="eager" width="1600" height="900"></figure>' if img else ''
    return f'''<section class="page-head reveal">
  <p class="kicker mono">{kicker}</p>
  <h1>{h1}</h1>
  <p class="lede">{lede}</p>
  {fig}
</section>
'''

TEASER = f'''<!-- ===================== TEASER ===================== -->
<section class="teaser" aria-labelledby="teaser-h">
  <header class="sec-head reveal">
    <p class="kicker mono">What we build</p>
    <h2 id="teaser-h">Three things. Done properly.</h2>
  </header>
  <div class="teaser-row">
    <a class="teaser-card reveal" href="{BASE}services/#automation"><p class="mono idx">01</p><h3>AI Automation</h3><p>Connect every tool. Kill the busywork.</p><span class="more">See how <span aria-hidden="true">→</span></span></a>
    <a class="teaser-card reveal" href="{BASE}services/#visibility"><p class="mono idx">02</p><h3>AI Visibility</h3><p>Be found by people and by AI.</p><span class="more">See how <span aria-hidden="true">→</span></span></a>
    <a class="teaser-card reveal" href="{BASE}services/#web"><p class="mono idx">03</p><h3>Web Systems</h3><p>The site and the backend behind it.</p><span class="more">See how <span aria-hidden="true">→</span></span></a>
  </div>
  <div class="teaser-links reveal">
    <a class="more" href="{BASE}about/">Meet the person behind the machine <span aria-hidden="true">→</span></a>
    <a class="more" href="{BASE}work/">Systems we have shipped <span aria-hidden="true">→</span></a>
    <a class="more" href="{BASE}assistant/">Try the Jarvis-style assistant <span aria-hidden="true">→</span></a>
  </div>
</section>
'''

def cta_strip(h, p, primary='Get your free visibility audit'):
    return f'''<!-- ===================== CTA STRIP ===================== -->
<section class="final reveal" id="cta">
  <h2>{h}</h2>
  <p class="lede">{p}</p>
  <div class="cta-row">
    <a class="btn btn-lg" href="{BASE}contact/" data-audit>{primary}</a>
    <a class="more" href="{BASE}pricing/">Or see fixed packages <span aria-hidden="true">→</span></a>
  </div>
  <p class="mono trust">Built and hosted in Germany · GDPR by default · Replies in EN, DE, FR, RO</p>
</section>
'''

def footer():
    f = frag('footer')
    f = f.replace('    <p>Practical AI automation for the German Mittelstand.</p>\n  </div>', '    <p>AI automation, Python backend and infrastructure. Hanstedt, Germany, working remotely.</p>\n' + NEWSLETTER + '  </div>')
    f = f.replace('<a href="/blog/">Blog</a>', '<a href="/blog/">Blog</a><a href="/index.html">Classic site</a>')
    f = f.replace('<a class="wordmark" href="/">', f'<a class="wordmark" href="{BASE}">')
    f = f.replace('<a href="/services/">Automation</a><a href="/services/">AI Visibility</a><a href="/services/">Web Systems</a>',
                  f'<a href="{BASE}services/#automation">Automation</a><a href="{BASE}services/#visibility">AI Visibility</a><a href="{BASE}services/#web">Web Systems</a>')
    f = f.replace('<a href="#story">About</a>', f'<a href="{BASE}about/">About</a>').replace('<a href="#audit" data-audit>Contact</a>', f'<a href="{BASE}contact/">Contact</a>')
    f = f.replace('<a href="/#impressum">Impressum</a><a href="/#datenschutz">Datenschutz</a>', f'<a href="{BASE}legal/#imprint">Impressum</a><a href="{BASE}legal/#privacy">Datenschutz</a><a href="{BASE}legal/#terms">Terms</a><a href="{BASE}legal/#cookies">Cookies</a>')
    return f + '</body>\n</html>\n'

def fix(html):
    # relative asset paths -> absolute under /cinematic/, in-page anchors -> real pages
    html = html.replace('src="assets/', f'src="{BASE}assets/')
    html = html.replace('href="#audit"', f'href="{BASE}contact/"')
    html = html.replace('href="#pillars"', f'href="{BASE}services/"').replace('href="#story"', f'href="{BASE}about/"').replace('href="#work"', f'href="{BASE}work/"')
    html = html.replace('href="/services/">How it works', f'href="{BASE}services/">How it works')
    html = html.replace('href="/pricing/', f'href="{BASE}pricing/')
    return html

pages = {}
# ---- HOME
home = frag('hero') + SAND + frag('stats') + MARQ + HOW + SVCGRID + WORK4 + FAQ + FAQ_LD + cta_strip('Find out what AI can automate in your business. Free.', 'Enter your website. In a few minutes you get a report: where you lose enquiries, what AI could handle, and what it would cost. No call required.')
pages['index.html'] = head('GeorgeAI: Your business, running while you sleep', 'Practical AI automation for German trades, clinics and service firms. n8n workflows, AI agents, AI visibility and web systems. Live in about two weeks. Free visibility audit.', '', extra_js=f'<script src="{BASE}globe.js?v=5" defer></script>\n') + nav(None) + fix(home) + '\n</main>\n\n' + footer()

# ---- SERVICES
pil = frag('pillars').replace('<article class="pillar reveal" data-tilt>', '<article class="pillar reveal" data-tilt id="automation">', 1)
pil = pil.replace('<article class="pillar reveal" data-tilt>\n      <figure><img src="assets/pillar-visibility', '<article class="pillar reveal" data-tilt id="visibility">\n      <figure><img src="assets/pillar-visibility')
pil = pil.replace('<article class="pillar reveal" data-tilt>\n      <figure><img src="assets/pillar-web', '<article class="pillar reveal" data-tilt id="web">\n      <figure><img src="assets/pillar-web')
pil = re.sub(r'<a class="more" href="/services/">How it works <span aria-hidden="true">→</span></a>', '', pil)
pil = pil.replace('<header class="sec-head reveal">\n    <p class="kicker mono">What we build</p>\n    <h2>Three things. Done properly.</h2>\n  </header>', '')
svc = page_head('Services', 'Three things. Done properly.', 'Automation, visibility and the web systems underneath. Each one starts with one process and one number to move.') + SAND_SUB + pil + SVCGRID + HOW + frag('packages').replace('href="/pricing/#', f'href="{BASE}pricing/#').replace('href="/pricing/"', f'href="{BASE}pricing/"') + cta_strip('Not sure which one you need?', 'The free audit looks at your website and your enquiry flow and tells you where AI pays off first.')
pages['services/index.html'] = head('Services: AI Automation, AI Visibility, Web Systems | GeorgeAI', 'n8n and AI agent automation, SEO and AI visibility, Django web systems. Fixed prices, live in about two weeks, built in Germany.', 'services/') + nav('services/') + fix(svc) + '\n</main>\n\n' + footer()

# ---- ABOUT
story = frag('story').replace('<div class="story-head reveal">\n    <p class="kicker mono">The person behind the machine</p>\n    <h2>Twenty years of making systems work. Now they run on AI.</h2>', '<div class="story-head reveal">\n    <p class="kicker mono">The path</p>\n    <h2>Every role was the same job: make the system run without me.</h2>')
about = page_head('About', 'Twenty years of making systems work. Now they run on AI.', 'George Sebastian. Head of infrastructure, agency founder, plant manager, finance lead. One person, four languages, near Hamburg.') + SAND_SUB + frag('mission') + story + FAQ + cta_strip('Want to talk to the person, not a sales team?', 'Start with the free audit. The report comes from me, and so does the reply.')
pages['about/index.html'] = head('About George Sebastian | GeorgeAI', 'Twenty years in infrastructure, automation and SEO. Certified AI engineer and Python developer near Hamburg. The person behind GeorgeAI.', 'about/') + nav('about/') + fix(about) + '\n</main>\n\n' + footer()

# ---- WORK
work = frag('work').replace('<header class="sec-head reveal">\n    <p class="kicker mono">Proof</p>\n    <h2>Systems we have shipped.</h2>\n  </header>', '')
wk = page_head('Work', 'Systems we have shipped.', 'Anonymised by sector. Names appear only with written permission.') + SAND_SUB + WORK4.replace(WORK_HEAD,'') + cta_strip('Your business could be the next tile.', 'Tell me where the hours go. The free audit is the first step.')
pages['work/index.html'] = head('Work: systems shipped | GeorgeAI', 'Smart-building infrastructure for a medical university, AI voice agents for trades and clinics, SEO and lead generation for small businesses.', 'work/') + nav('work/') + fix(wk) + '\n</main>\n\n' + footer()

# ---- CONTACT
final = frag('final').replace('<section class="final reveal" id="audit">', '<section class="final reveal" id="audit">')
final = final.replace(f'href="#audit" data-audit>Get my free visibility audit', 'href="#audit" data-audit>Get my free visibility audit')
contact_extra = '''<!-- ===================== DIRECT ===================== -->
<section class="direct reveal" aria-labelledby="direct-h">
  <p class="kicker mono">Prefer a person?</p>
  <h2 id="direct-h">Write to George directly.</h2>
  <div class="direct-grid">
    <a class="direct-card" href="https://linkedin.com/in/georgesebastian-c-212b7455" rel="me noopener" target="_blank"><p class="mono">LinkedIn</p><h3>Message on LinkedIn</h3><p>Replies within one working day, in EN, DE, FR or RO.</p></a>
    <a class="direct-card" href="/pricing/"><p class="mono">Fixed prices</p><h3>Order a package</h3><p>Seven packages, prices shown, nothing added at checkout.</p></a>
    <div class="direct-card"><p class="mono">Where</p><h3>Hanstedt, near Hamburg</h3><p>Working with companies across Germany and the DACH region.</p></div>
  </div>
</section>
'''
ct = page_head('Contact', 'Find out what AI can automate in your business. Free.', 'Enter your website. In a few minutes you get a report: where you lose enquiries, what AI could handle, and what it would cost. No call required.') + SAND_SUB + frag('hold') + '''<section class="final reveal" id="audit">
  <h2>Start with the free visibility audit.</h2>
  <p class="lede">One field, your website address. The report lands in your inbox.</p>
  <div class="cta-row">
    <a class="btn btn-lg" href="#audit" data-audit>Get my free visibility audit</a>
    <a class="more" href="{BASE}pricing/">Or see fixed packages <span aria-hidden="true">→</span></a>
  </div>
  <p class="mono trust">Built and hosted in Germany · GDPR by default · Replies in EN, DE, FR, RO</p>
</section>
''' + contact_extra
pages['contact/index.html'] = head('Contact: free visibility audit | GeorgeAI', 'Get a free AI visibility audit of your website, or write to George directly. Replies in English, German, French and Romanian.', 'contact/') + nav('contact/') + fix(ct) + '\n</main>\n\n' + footer()


# ---- ASSISTANT (Jarvis-style demo, front-end only)
ICON = {
 'light': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M9 18h6M10 21h4M12 3a6 6 0 0 1 3.6 10.8c-.6.5-.9 1.2-.9 2V16H9.3v-.2c0-.8-.3-1.5-.9-2A6 6 0 0 1 12 3z"/></svg>',
 'fan': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><circle cx="12" cy="12" r="2"/><path d="M12 10c0-4 2-7 4-7s2 4-1 6M14 12c4 0 7 2 7 4s-4 2-6-1M12 14c0 4-2 7-4 7s-2-4 1-6M10 12c-4 0-7-2-7-4s4-2 6 1"/></svg>',
 'music': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M9 18V5l12-2v13"/><circle cx="6" cy="18" r="3"/><circle cx="18" cy="16" r="3"/></svg>',
 'temp': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M14 14.8V5a2 2 0 1 0-4 0v9.8a4 4 0 1 0 4 0z"/></svg>',
 'lock': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="4" y="11" width="16" height="10" rx="2"/><path d="M8 11V7a4 4 0 0 1 8 0v4"/></svg>',
 'cal': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M3 10h18M8 3v4M16 3v4"/></svg>',
 'mic': '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" aria-hidden="true"><rect x="9" y="3" width="6" height="11" rx="3"/><path d="M5 11a7 7 0 0 0 14 0M12 18v3"/></svg>',
}
OPS = f'''<!-- ===================== OPS ROOM ===================== -->
<section class="ops" aria-label="Command room">
  <canvas class="globe" id="globe" aria-hidden="true"></canvas>
  <div class="ops-scan" aria-hidden="true"></div>
  <div class="ops-grid" aria-hidden="true">
    <div class="hud-tile t1"><span class="name">Systems</span><b><span class="dot"></span>Online</b><small>12 / 12 services</small></div>
    <div class="hud-tile t2"><span class="name">Workflows today</span><b data-tick="1284" data-rate="0.4">1,284</b><small>n8n · auto</small></div>
    <div class="hud-tile t3"><span class="name">Calls answered</span><b data-tick="317" data-rate="0.08">317</b><small>24/7 · 4 languages</small></div>
    <div class="hud-tile t4"><span class="name">Bookings</span><b data-tick="46" data-rate="0.02">46</b><small>calendar synced</small></div>
    <div class="hud-tile t5"><span class="name">Avg. response</span><b>1.8 s</b><small>voice to action</small></div>
    <div class="hud-tile t6"><span class="name">Radar</span><svg class="radar" viewBox="0 0 100 100"><circle cx="50" cy="50" r="46"/><circle cx="50" cy="50" r="30"/><circle cx="50" cy="50" r="14"/><path d="M50 50 L50 4"/><path d="M4 50 H96"/><path class="sweep" d="M50 50 L50 4 A46 46 0 0 1 96 50 Z"/></svg></div>
  </div>
  <div class="ops-copy">
    <p class="kicker mono">Your world. Your voice. One intelligence.</p>
    <h1><span class="w1">JARVIS</span><span class="w2">for your business.</span></h1>
    <p class="lede">Thinks. Understands. Acts. The assistant we build answers the phone, books the job and switches the building, in the caller's language. Try the demo below.</p>
    <div class="cta-row"><a class="btn" href="#jarvis">Try it now</a><a class="btn btn-ghost" href="{BASE}contact/" data-audit>Put it on my phone line</a></div>
  </div>
</section>
'''
jv = OPS + SAND_SUB + f'''
<!-- ===================== JARVIS ===================== -->
<section class="jarvis reveal" id="jarvis" aria-labelledby="jv-h">
  <div class="hud">
    <h2 id="jv-h" class="sr">Assistant console</h2>
    <div class="core" aria-hidden="true">
      <span class="pulse"></span>
      <svg viewBox="0 0 200 200"><circle class="r1" cx="100" cy="100" r="96"/><circle class="r2" cx="100" cy="100" r="80"/><circle class="r3" cx="100" cy="100" r="62"/><circle cx="100" cy="100" r="46" fill="none" stroke="rgba(255,255,255,.12)"/></svg>
      <span class="label">JARVIS</span>
    </div>
    <div class="wave" id="wave" aria-hidden="true"></div>
    <div class="transcript" id="transcript" role="log" aria-live="polite" aria-relevant="additions"></div>
    <form class="ask" id="ask" autocomplete="off">
      <label class="sr" for="q">Ask the assistant</label>
      <input id="q" name="q" type="text" placeholder="Hey Jarvis, turn on the lights" maxlength="140">
      <button class="mic" id="mic" type="button" aria-pressed="false" aria-label="Speak" hidden>{ICON['mic']}</button>
      <button class="btn" type="submit">Send</button>
    </form>
    <div class="chips" aria-label="Try one">
      <button class="chip" type="button" data-say="Turn on the lights">Lights on</button>
      <button class="chip" type="button" data-say="Set the temperature to 22 degrees">22 degrees</button>
      <button class="chip" type="button" data-say="Play some music">Play music</button>
      <button class="chip" type="button" data-say="Book a call for Tuesday at 10">Book Tuesday 10:00</button>
      <button class="chip" type="button" data-say="Arm the security">Arm security</button>
      <button class="chip" type="button" data-say="What is the status?">Status</button>
    </div>
  </div>
  <aside class="panel">
    <h3>Live state</h3>
    <ul class="devices">
      <li class="dev" data-dev="lights">{ICON['light']}<div><div class="name">Lights</div><div class="val">Off</div></div></li>
      <li class="dev" data-dev="fan">{ICON['fan']}<div><div class="name">Fan</div><div class="val">Off</div></div></li>
      <li class="dev" data-dev="music">{ICON['music']}<div><div class="name">Music</div><div class="val">Paused</div></div></li>
      <li class="dev on" data-dev="temp">{ICON['temp']}<div><div class="name">Temperature</div><div class="val">21°C</div></div></li>
      <li class="dev" data-dev="security">{ICON['lock']}<div><div class="name">Security</div><div class="val">Disarmed</div></div></li>
      <li class="dev" data-dev="calendar">{ICON['cal']}<div><div class="name">Next meeting</div><div class="val">None</div></div></li>
    </ul>
    <h3>System</h3>
    <div class="sys">
      <div><div class="name">Status</div><div class="val"><span class="dot"></span>Online</div></div>
      <div><div class="name">Local time</div><div class="val" id="clock">--:--</div></div>
      <div><div class="name">Response</div><div class="val" id="lat">-- ms</div></div>
    </div>
    <p class="lede" style="font-size:1rem;margin-top:6px">This demo runs entirely in your browser. In production the same commands drive real systems through n8n: phones, calendars, CRM, smart buildings. <a class="more" href="{BASE}services/#automation">How we build it <span aria-hidden="true">→</span></a></p>
  </aside>
</section>

<!-- ===================== HOW IT WORKS ===================== -->
<section class="flow reveal" aria-labelledby="flow-h">
  <p class="kicker mono">How it works</p>
  <h2 id="flow-h">Voice in. Action out.</h2>
  <ol>
    <li><h3>Voice input</h3><p>Speech to text, in the caller's language.</p></li>
    <li><h3>AI brain</h3><p>Understands intent, keeps context, decides.</p></li>
    <li><h3>Action engine</h3><p>n8n runs the workflow: book, send, switch, log.</p></li>
    <li><h3>Systems</h3><p>Calendar, CRM, phone line, KNX and building automation.</p></li>
    <li><h3>Voice output</h3><p>Answers back, confirms, and records the outcome.</p></li>
  </ol>
  <div class="stack" aria-label="Technology"><span>Claude</span><span>OpenAI</span><span>n8n</span><span>Python</span><span>ElevenLabs</span><span>Home Assistant</span><span>KNX / DALI</span><span>Ollama (local)</span></div>
</section>
''' + cta_strip('Want this answering your phone?', 'The 24/7 phone package puts this assistant on your line in about two weeks. The free audit tells you what else it could take over.', 'Get your free visibility audit')
pages['assistant/index.html'] = head('Assistant: Jarvis-style AI for your business | GeorgeAI', 'Try a Jarvis-style AI assistant in your browser: voice and text commands that switch devices, book meetings and report status. Built with n8n for real businesses.', 'assistant/', extra_js=f'<script src="{BASE}globe.js?v=5" defer></script>\n<script src="{BASE}jarvis.js?v=5" defer></script>\n') + nav('assistant/') + fix(jv) + '\n</main>\n\n' + footer()

# ---- PRICING: cards parsed from the live pricing page so prices and Stripe links have one source of truth
SRC = open('/Users/Geronimo/Projects/georgeai_dev/pages/pricing/index.html', encoding='utf-8').read()
def cards(section_id):
    sec = SRC[SRC.index(f'id="{section_id}"'):]; sec = sec[:sec.index('</section>')]
    out = []
    for m in re.finditer(r'<div class="card( featured)?" id="([^"]+)">(.*?)</div>\s*(?=<div class="card|\s*</div>)', sec, re.S):
        feat, slug, body = m.group(1), m.group(2), m.group(3)
        g = lambda rx: (re.search(rx, body, re.S) or [None, ''])[1]
        price = g(r'<p class="price">(.*?)</p>').replace('<span style="color:var(--muted)">', '<small>').replace('</span>', '</small>')
        out.append(dict(slug=slug, feat=bool(feat), h3=g(r'<h3>(.*?)</h3>').replace(' — ', ', '), price=price, first=g(r'<p class="first">(.*?)</p>'),
            promise=g(r'<p class="promise">(.*?)</p>').replace(' — ', ', ').replace('—', ','), incl=re.findall(r'<li>(.*?)</li>', body), deliv=g(r'<p class="deliv">(.*?)</p>'),
            href=g(r'<a class="buy" data-product="[^"]+" href="([^"]+)"'), label=g(r'<a class="buy"[^>]*>(.*?)</a>').replace('Order — ', 'Order ')))
    return out
def card_html(c):
    incl = ''.join(f'<li>{x.replace(" — ", ": ").replace("—", ",")}</li>' for x in c['incl'])
    return f'''<article class="pack reveal{' featured' if c['feat'] else ''}" id="{c['slug']}">
      {'<p class="mono">Start here</p>' if c['feat'] else ''}
      <h3>{c['h3']}</h3>
      <p class="price">{c['price']}</p>
      <p class="first">{c['first'].replace(' — ', ', ')}</p>
      <p>{c['promise']}</p>
      <ul class="ticks">{incl}</ul>
      <p class="mono deliv">{c['deliv']}</p>
      <a class="btn buy" data-product="{c['slug']}" href="{c['href']}">{c['label']}</a>
    </article>'''
one = cards('one-off'); mon = cards('monthly')
assert len(one) == 3 and len(mon) == 4, (len(one), len(mon))
PR = page_head('Pricing', 'Fixed prices. No surprises.', 'Pick a package, pay once, it goes live. No VAT is charged under § 19 UStG, so the price you see is the price you pay. Stripe checkout, card or SEPA.') + SAND_SUB + f'''
<!-- ===================== ONE-TIME ===================== -->
<section class="packages" id="one-off">
  <header class="sec-head reveal"><p class="kicker mono">Buy once, delivered</p><h2>Fixed scope. Fixed price. A deadline in days.</h2><p>Nothing renews and there is nothing to cancel.</p></header>
  <div class="pack-grid pack-full">{''.join(card_html(c) for c in one)}</div>
</section>
<!-- ===================== MONTHLY ===================== -->
<section class="packages" id="monthly">
  <header class="sec-head reveal"><p class="kicker mono">Runs every day, without you</p><h2>A system I build, hand over and keep running.</h2><p>Setup is charged once, on the first invoice. Cancel with one month's notice.</p></header>
  <div class="pack-grid pack-full four">{''.join(card_html(c) for c in mon)}</div>
</section>
<!-- ===================== AFTER ===================== -->
<section class="flow reveal" aria-labelledby="after-h">
  <p class="kicker mono">After you click</p>
  <h2 id="after-h">What happens after you buy.</h2>
  <ol>
    <li><h3>Checkout</h3><p>Stripe, card or SEPA. Invoice in your inbox within a minute.</p></li>
    <li><h3>Kick-off</h3><p>A short form and, if useful, a 20-minute call. Same day.</p></li>
    <li><h3>Build</h3><p>I build it. You get a progress note every few days.</p></li>
    <li><h3>Live</h3><p>Delivered on the stated date. You test it with me.</p></li>
    <li><h3>Keep running</h3><p>Monthly packages include tuning and monitoring.</p></li>
  </ol>
</section>
''' + cta_strip('Not sure which package fits?', 'The free audit looks at your website and enquiry flow and tells you where AI pays off first.')
pages['pricing/index.html'] = head('Pricing: fixed-price AI packages | GeorgeAI', 'Fixed-price AI automation packages: verified lead lists from 299 euros, AI visibility audit 490 euros, 24/7 AI phone answering, website chatbots and business automation. GDPR-first, built for the German market.', 'pricing/') + nav('pricing/') + fix(PR) + '\n</main>\n\n' + footer()

# ---- LEGAL: rendered client-side from the deployed /legal-data.js (identity applied by apply_legal at deploy)
lg = page_head('Legal', 'Imprint, privacy, terms, cookies.', 'The legal documents for georgeai.dev, in five languages. Pick a document below.') + SAND_SUB + LEGAL_BODY
pages['legal/index.html'] = head('Legal: Imprint, Privacy, Terms, Cookies | GeorgeAI', 'Impressum, Datenschutzerklaerung, AGB and cookie policy for georgeai.dev in EN, DE, FR, RO and AR.', 'legal/', extra_js=f'<script src="/legal-data.js" defer></script>\n<script src="{BASE}legal.js?v=5" defer></script>\n') + nav(None) + fix(lg) + '\n</main>\n\n' + footer()

# ---- CONFIGURATOR: services from georgeai_services.json, rules from its configurator block
_cfg = json.load(open('/Users/Geronimo/Projects/georgeai_dev/georgeai_services.json'))
_svcs, _conf = _cfg['services'], _cfg['configurator']
_grp = {}
for _x in _svcs: _grp.setdefault(_x.get('group') or _x.get('category'), []).append(_x)
def _svc_boxes():
    out = ''
    for g in ['Automation & AI', 'Growth & Marketing', 'Software & Data', 'Web']:
        items = ''.join(f'<label class="chk"><input type="checkbox" name="svc"><span>{x["name"]}</span><small>{x.get("tagline","")}</small></label>' for x in _grp.get(g, []))
        out += f'<fieldset class="cfg-group"><legend>{g}</legend>{items}</fieldset>'
    return out
_scales = ''.join(f'<label class="chk radio"><input type="radio" name="scale" data-index="{i}" data-weeks="{sc["scale_base_weeks"]}"{" checked" if i == 0 else ""}><b>{sc["name"]}</b><small>{sc["desc"]} About {sc["scale_base_weeks"]} weeks base.</small></label>' for i, sc in enumerate(_conf['scales']))
_addons = ''.join(f'<label class="chk"><input type="checkbox" name="addon"><span>{a}</span></label>' for a in _conf['addons'])
CFG = page_head('Configurator', 'Outline your project. See the timeline before the first call.', 'Pick the services you need, the scale and the add-ons. The estimate updates as you go. Send it and I reply with a tailored quote within 48 hours.') + SAND_SUB + f'''
<section class="cfg-wrap">
<form id="cfg" class="cfg" novalidate>
  <div class="cfg-steps">
    <div class="cfg-step reveal"><p class="kicker mono">01 / Services</p><h2>What should it do?</h2>{_svc_boxes()}</div>
    <div class="cfg-step reveal"><p class="kicker mono">02 / Scale</p><h2>How big is it?</h2><div class="cfg-scales">{_scales}</div></div>
    <div class="cfg-step reveal"><p class="kicker mono">03 / Add-ons</p><h2>Anything on top?</h2><div class="cfg-addons">{_addons}</div></div>
    <div class="cfg-step reveal"><p class="kicker mono">04 / You</p><h2>Where should the quote go?</h2>
      <div class="cfg-you"><label>Your name<input id="cfg-name" type="text" autocomplete="name"></label><label>Your email<input id="cfg-email" type="email" autocomplete="email" required></label><label class="wide">A line about your project<textarea id="cfg-notes" rows="3"></textarea></label></div>
    </div>
  </div>
  <aside class="cfg-sum reveal">
    <p class="kicker mono">Your estimate</p>
    <p id="cfg-empty" class="lede">Pick at least one service to see a timeline.</p>
    <div class="sum-row" hidden><span class="mono">Timeline</span><b id="cfg-weeks"></b></div>
    <div class="sum-row" hidden><span class="mono">Complexity</span><b id="cfg-cx"></b></div>
    <p class="mono sum-count"><span id="cfg-count">0</span> services selected</p>
    <ul id="cfg-list" class="sum-list"></ul>
    <button id="cfg-submit" class="btn btn-lg" type="submit" disabled>Request a quote</button>
    <p id="cfg-done" class="nl-note" hidden>Your email app opened with the summary. Send it and I reply within 48 hours.</p>
    <p class="nl-note">Opens your email app with the summary; nothing is stored on this page. Prices are quoted per project, fixed packages are on the <a href="{BASE}pricing/">pricing page</a>.</p>
  </aside>
</form>
</section>
''' + cta_strip('Prefer to start smaller?', 'The free visibility audit shows where AI pays off first, before you configure anything.')
pages['configurator/index.html'] = head('Configurator: outline your AI project | GeorgeAI', 'Pick services, scale and add-ons, see the estimated timeline and complexity, and request a tailored quote within 48 hours.', 'configurator/', extra_js=f'<script src="{BASE}configurator.js?v=5" defer></script>\n') + nav('configurator/') + fix(CFG) + '\n</main>\n\n' + footer()

# ---- ACCOUNT: sign up / log in on the Django session API
ACC = page_head('Account', 'Log in or create your account.', 'Save configurations and track your requests. One email, one password, nothing else.') + SAND_SUB + f'''
<section class="acct" id="account">
  <div class="acct-card reveal">
    <div class="acct-tabs" role="tablist"><button type="button" data-tab="login" role="tab" aria-selected="true">Log in</button><button type="button" data-tab="signup" role="tab" aria-selected="false">Sign up</button></div>
    <p id="acct-msg" class="acct-msg" hidden></p>
    <form id="login" class="acct-form" novalidate>
      <label>Email<input name="email" type="email" autocomplete="email" required></label>
      <label>Password<input name="password" type="password" autocomplete="current-password" required></label>
      <label class="row"><input name="remember" type="checkbox" value="1"> Remember me</label>
      <button class="btn" type="submit">Log in</button>
    </form>
    <form id="signup" class="acct-form" hidden novalidate>
      <label>Full name<input name="name" type="text" autocomplete="name"></label>
      <label>Email<input name="email" type="email" autocomplete="email" required></label>
      <label>Password<input name="password" type="password" autocomplete="new-password" minlength="8" required></label>
      <button class="btn" type="submit">Create account</button>
      <p class="nl-note">By continuing you agree to the <a href="{BASE}legal/#terms">terms</a> and the <a href="{BASE}legal/#privacy">privacy policy</a>.</p>
    </form>
    <div id="signed" class="acct-in" hidden>
      <p id="who" class="lede"></p>
      <div class="cta-row"><a class="btn" href="{BASE}configurator/">Open the configurator</a><button id="logout" class="btn btn-ghost" type="button">Log out</button></div>
    </div>
  </div>
</section>
'''
pages['account/index.html'] = head('Account: log in or sign up | GeorgeAI', 'Log in or create your GeorgeAI account to save configurations and track your requests.', 'account/', extra_js=f'<script src="{BASE}account.js?v=5" defer></script>\n') + nav(None) + fix(ACC) + '\n</main>\n\n' + footer()

for path, html in pages.items():
    full = os.path.join(OUT, path); os.makedirs(os.path.dirname(full), exist_ok=True)
    open(full, 'w', encoding='utf-8').write(html)
    print(path, len(html))
