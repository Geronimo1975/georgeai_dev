# Merged-content fragments (phase 1 of combining the classic site with the cinematic one).
# Imported by gen.py. Copy comes from the classic export (services-data.js GA_EXTRA, T().en) with the
# skill's copy rules applied (no em dashes, plain voice).
import json, re
BASE = '/cinematic/'

TOPBAR = '''<div class="topbar" aria-label="Contact details">
  <a href="tel:+491604155546"><span class="dot"></span>+49 160 4155546</a>
  <a href="mailto:contact@GeorgeAI.dev">contact@GeorgeAI.dev</a>
  <span class="tb-social">
    <a href="https://wa.me/491604155546" rel="noopener" target="_blank" aria-label="WhatsApp"><svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 2a10 10 0 0 0-8.6 15.1L2 22l5-1.3A10 10 0 1 0 12 2zm0 18a8 8 0 0 1-4.1-1.1l-.3-.2-3 .8.8-2.9-.2-.3A8 8 0 1 1 12 20zm4.4-6c-.2-.1-1.4-.7-1.6-.8s-.4-.1-.5.1-.6.8-.8 1-.3.2-.5.1a6.5 6.5 0 0 1-3.2-2.8c-.2-.4.2-.4.7-1.2.1-.2 0-.3 0-.4l-.7-1.7c-.2-.5-.4-.4-.5-.4h-.5a1 1 0 0 0-.7.3 2.8 2.8 0 0 0-.9 2.1 4.9 4.9 0 0 0 1 2.6c.1.2 1.8 2.7 4.3 3.8 1.6.7 2.2.7 3 .6.5-.1 1.4-.6 1.6-1.1s.2-1 .2-1.1-.3-.2-.5-.3z"/></svg></a>
    <a href="https://linkedin.com/in/georgesebastian-c-212b7455" rel="me noopener" target="_blank" aria-label="LinkedIn"><svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M4.98 3.5C4.98 4.88 3.87 6 2.5 6S0 4.88 0 3.5 1.12 1 2.5 1s2.48 1.12 2.48 2.5zM.2 8h4.6v14H.2V8zm7.4 0h4.4v1.9h.1c.6-1.1 2.1-2.3 4.3-2.3 4.6 0 5.5 3 5.5 7V22h-4.6v-6.5c0-1.6 0-3.6-2.2-3.6s-2.5 1.7-2.5 3.5V22H7.6V8z"/></svg></a>
    <a href="https://github.com/Geronimo1975" rel="me noopener" target="_blank" aria-label="GitHub"><svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><path d="M12 .5A11.5 11.5 0 0 0 .5 12c0 5.1 3.3 9.4 7.9 10.9.6.1.8-.3.8-.6v-2c-3.2.7-3.9-1.5-3.9-1.5-.5-1.3-1.3-1.7-1.3-1.7-1-.7.1-.7.1-.7 1.2.1 1.8 1.2 1.8 1.2 1 1.8 2.7 1.3 3.4 1 .1-.8.4-1.3.7-1.6-2.6-.3-5.3-1.3-5.3-5.7 0-1.3.5-2.3 1.2-3.1-.1-.3-.5-1.5.1-3.1 0 0 1-.3 3.2 1.2a11 11 0 0 1 5.8 0c2.2-1.5 3.2-1.2 3.2-1.2.6 1.6.2 2.8.1 3.1.8.8 1.2 1.8 1.2 3.1 0 4.4-2.7 5.4-5.3 5.7.4.4.8 1.1.8 2.2v3.3c0 .3.2.7.8.6A11.5 11.5 0 0 0 23.5 12 11.5 11.5 0 0 0 12 .5z"/></svg></a>
  </span>
  <span class="tb-right"><a href="/cinematic/configurator/">Configurator</a><a href="/cinematic/account/">Account</a><span class="tb-lang mono">EN</span></span>
</div>
'''

_MQ = ['n8n', 'OpenAI', 'Claude Code', 'RAG', 'GEO', 'AIO', 'SEO Automation', 'Phone AI', 'Django', 'PostgreSQL', 'Docker', 'KNX', 'Home Assistant', 'ElevenLabs']
MARQ = '<div class="marquee" aria-hidden="true"><div class="track">' + ''.join(f'<span>{x}</span>' for x in _MQ * 3) + '</div></div>\n'

HOW = '''<!-- ===================== HOW ===================== -->
<section class="how" id="how" aria-labelledby="how-h">
  <header class="sec-head reveal"><p class="kicker mono">How it works</p><h2 id="how-h">From bottleneck to running system. In weeks, not months.</h2><p>A simple, proven path from your first call to a system that quietly does the work every day.</p></header>
  <ol class="how-grid">
    <li class="how-card reveal"><div class="mock mock-flow" aria-hidden="true"><span>trigger</span><span>openai : decide</span><span>update CRM</span></div><p class="mono">01 / Discover</p><h3>We map the bottleneck</h3><p>A short call to find the repetitive, costly work, and the fastest place to automate it.</p></li>
    <li class="how-card reveal"><div class="mock mock-code" aria-hidden="true"><i># build and test</i><i>pipe = Pipeline()</i><i>pipe.add(handler)</i><i>pipe.test(real_data)  ok</i></div><p class="mono">02 / Build</p><h3>I build and harden it</h3><p>Custom n8n + Python with error handling, tested against your real data until it is reliable.</p></li>
    <li class="how-card reveal"><div class="mock mock-int" aria-hidden="true"><span>CRM</span><span>Email</span><span>Sheets</span><span>WhatsApp</span><span>Phone</span><span>Slack</span></div><p class="mono">03 / Connect</p><h3>It plugs into your stack</h3><p>CRM, email, sheets, WhatsApp, phone: your tools, talking to each other automatically.</p></li>
    <li class="how-card reveal"><div class="mock mock-dash" aria-hidden="true"><i style="--h:35%"></i><i style="--h:50%"></i><i style="--h:42%"></i><i style="--h:64%"></i><i style="--h:58%"></i><i style="--h:78%"></i><i style="--h:70%"></i><i style="--h:92%" class="hot"></i></div><p class="mono">04 / Run</p><h3>It runs. You watch it work</h3><p>Deployed, monitored and handed over, with dashboards so you always see what it is doing.</p></li>
  </ol>
</section>
'''

_TILES = [
    ('work-medical.jpg', 1600, 900, 'Medical professional using an AI assistant on a laptop', 'AI / RAG / 2024', 'Medical AI Agent', 'An OpenAI + Python + RAG assistant for medical data processing and query automation.'),
    ('work-building.jpg', 1600, 894, 'Smart building at dusk with a control app', 'IoT / BMS / 2024', 'Smart Facility Automation', 'n8n, OpenAI (RAG) and Python for smart-building monitoring and operational control.'),
    ('work-infra.jpg', 1600, 1074, 'Cloud infrastructure hologram over a laptop', 'Infra / Cloud / 2025', 'Containerized Infrastructure', 'Scalable infrastructure with Docker, PostgreSQL, Redis and Nginx, built for high availability.'),
    ('work-web.jpg', 1600, 934, 'Web development interface with connected icons', 'Django / AI / 2025', 'Full-stack Web Platform', 'A scalable Django platform with WordPress integration, AI services and API automations.'),
]
WORK_HEAD = '<header class="sec-head reveal"><p class="kicker mono">Selected work</p><h2>Systems we have shipped.</h2></header>'
WORK4 = '<!-- ===================== WORK ===================== -->\n<section class="work" id="work">\n  ' + WORK_HEAD + '\n  <div class="work-grid four">' + ''.join(
    f'<article class="tile reveal"><img src="{BASE}assets/{img}" alt="{alt}" loading="lazy" width="{w}" height="{h}"><div class="tile-text"><p class="mono">{tag}</p><h3>{t}</h3><p>{d}</p></div></article>'
    for img, w, h, alt, tag, t, d in _TILES) + '</div>\n</section>\n'

_svc = json.load(open('/Users/Geronimo/Projects/georgeai_dev/georgeai_services.json'))['services']
def _slug(n): return {'SEO / AIO / GEO': 'seo-aio-geo'}.get(n, re.sub(r'[^a-z0-9]+', '-', n.lower()).strip('-'))
_groups = {}
for _x in _svc: _groups.setdefault(_x.get('group') or _x.get('category'), []).append(_x)
_order = ['Automation & AI', 'Growth & Marketing', 'Software & Data', 'Web']
def _grp(i, g):
    items = ''.join(f'<li><a href="/services/{_slug(x["name"])}/"><span>{x["name"]}</span><small>{x.get("tagline", "")}</small><i aria-hidden="true">→</i></a></li>' for x in _groups.get(g, []))
    return f'<div class="svc-group reveal"><p class="mono">0{i}</p><h3>{g}</h3><ul>{items}</ul></div>'
SVCGRID = '''<!-- ===================== SERVICES GRID ===================== -->
<section class="svcs" id="services" aria-labelledby="svc-h">
  <header class="sec-head reveal"><p class="kicker mono">Services</p><h2 id="svc-h">What I build for you.</h2><p>Fifteen services in four areas. Pick one or combine them; every one links to its own page with scope, process and outcome.</p></header>
  <div class="svc-grid">''' + ''.join(_grp(i + 1, g) for i, g in enumerate(_order)) + '''</div>
</section>
'''

_faq = [
    ("How long does a typical project take?", "Most automations and AI agents ship in 2 to 6 weeks, depending on scope. A focused pilot can be live in days; larger, multi-system builds take longer. You get a clear timeline after the first call."),
    ("Do you work with my existing website and tools?", "Yes. I connect to what you already use: WordPress, your CRM, email platform, sheets, WhatsApp and more. If you do not have a site yet, I can build that too."),
    ("What does it cost?", "Fixed-price packages start at 299 euros and are listed on the pricing page. Larger builds are quoted per project within 48 hours. No surprise fees."),
    ("Will the automations keep running without you?", "Yes. Everything is deployed, monitored and documented, then handed over to you. Optional ongoing support is available if you want me to keep an eye on it."),
    ("Is my data safe?", "Your data stays in your own tools and infrastructure wherever possible. I follow GDPR practices and can work within your security requirements."),
    ("Which languages and regions do you serve?", "I work remotely across Europe and the Middle East, in English, German, French, Romanian and Arabic."),
]
FAQ = '<!-- ===================== FAQ ===================== -->\n<section class="faq" id="faq" aria-labelledby="faq-h"><header class="sec-head reveal"><p class="kicker mono">FAQ</p><h2 id="faq-h">Questions and answers.</h2></header><div class="faq-list reveal">' + ''.join(
    f'<details{" open" if i == 0 else ""}><summary>{q}<i aria-hidden="true"></i></summary><p>{a}</p></details>' for i, (q, a) in enumerate(_faq)) + '</div></section>\n'
FAQ_LD = '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [{"@type": "Question", "name": q, "acceptedAnswer": {"@type": "Answer", "text": a}} for q, a in _faq]}, ensure_ascii=False) + '</script>\n'

NEWSLETTER = '''    <form class="news" action="mailto:contact@GeorgeAI.dev?subject=Subscribe%20to%20GeorgeAI%20notes" method="post" enctype="text/plain">
      <label for="nl">Stay in the loop.</label>
      <p class="nl-sub">Occasional notes on AI automation, new projects and the odd build log. No spam.</p>
      <div class="nl-row"><input id="nl" name="email" type="email" placeholder="Your email" required autocomplete="email"><button class="btn" type="submit">Subscribe</button></div>
      <p class="nl-note">Opens your email app with a subscribe message; nothing is stored on this page.</p>
    </form>
'''

LEGAL_BODY = '''<section class="legal" id="legal-root">
  <nav class="legal-tabs mono" aria-label="Documents"><a href="#imprint">Imprint</a><a href="#privacy">Privacy</a><a href="#terms">Terms</a><a href="#cookies">Cookies</a><span class="lang"><label for="lg-lang">Language</label><select id="lg-lang"><option value="en">EN</option><option value="de">DE</option><option value="fr">FR</option><option value="ro">RO</option><option value="ar">AR</option></select></span></nav>
  <div id="legal-docs" class="legal-docs"><p class="lede">Loading the documents.</p></div>
  <noscript><p class="lede">These documents need JavaScript to render here. They are also in the footer of the <a href="/index.html">classic site</a>.</p></noscript>
</section>
'''
