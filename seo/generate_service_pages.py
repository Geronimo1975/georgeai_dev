#!/usr/bin/env python3
"""Generate static, indexable service pages + sitemap for georgeai.dev.

Called by deploy.sh on every deploy:
    python3 seo/generate_service_pages.py georgeai_services.json site/

Reads the canonical service catalog (georgeai_services.json) and writes:
    site/services/index.html          — services hub page
    site/services/<slug>/index.html   — one page per service
    site/work/index.html              — work/case-study hub (if georgeai_work.json exists)
    site/work/<slug>/index.html       — one page per project
    site/sitemap.xml                  — homepage + hubs + all generated pages

The SPA homepage stays untouched: these pages exist so every service (and,
via georgeai_work.json, every portfolio project) has a real, crawlable URL
with its own title/description/JSON-LD (the "biggest GEO/SEO win" noted in
the original sitemap). Content is English; the SPA handles i18n interactively.
"""
import html
import json
import re
import sys
from datetime import date
from pathlib import Path

BASE = "https://georgeai.dev"
OG_IMAGE = f"{BASE}/assets/SEO_AI.png"
EMAIL = "contact@georgeai.dev"
PHONE = "+49 160 4155546"
PHONE_HREF = "tel:+491604155546"

# design tokens from DESIGN-claude.md
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
body{background:#faf9f5;color:#3d3d3a;font-family:Inter,system-ui,sans-serif;line-height:1.6}
a{color:#df2700}
.wrap{max-width:840px;margin:0 auto;padding:0 24px}
header.site{border-bottom:1px solid #e6dfd8;padding:18px 0}
header.site .wrap{display:flex;align-items:center;justify-content:space-between}
.wordmark{font-family:Newsreader,Georgia,serif;font-size:22px;color:#141413;text-decoration:none}
.wordmark img{width:24px;height:24px;display:inline-block;vertical-align:-5px;margin-right:9px}
.wordmark b{color:#ff5c39;font-weight:500}
nav.crumbs{font-family:'JetBrains Mono',monospace;font-size:12px;margin:28px 0 8px;color:#8e8b82}
nav.crumbs a{color:#6c6a64;text-decoration:none}
nav.crumbs a:hover{color:#df2700}
.cat{display:inline-block;font-family:'JetBrains Mono',monospace;font-size:12px;color:#df2700;border:1px solid #e6dfd8;border-radius:9999px;padding:4px 12px;margin:14px 0 10px}
h1{font-family:Newsreader,Georgia,serif;font-weight:500;font-size:44px;color:#141413;line-height:1.15;margin:6px 0 10px}
.tagline{font-family:Newsreader,Georgia,serif;font-size:22px;color:#6c6a64;font-style:italic;margin-bottom:18px}
.intro{font-size:17px;color:#252523;margin-bottom:34px;max-width:64ch}
h2{font-family:Newsreader,Georgia,serif;font-weight:500;font-size:26px;color:#141413;margin:34px 0 12px}
ul.list{list-style:none;margin-bottom:8px}
ul.list li{padding:9px 0 9px 26px;position:relative;border-bottom:1px solid #ebe6df}
ul.list li::before{content:"";position:absolute;left:2px;top:17px;width:8px;height:8px;background:#ff5c39;clip-path:polygon(50% 0,61% 39%,100% 50%,61% 61%,50% 100%,39% 61%,0 50%,39% 39%)}
ol.steps{counter-reset:s;list-style:none}
ol.steps li{counter-increment:s;padding:9px 0 9px 38px;position:relative;border-bottom:1px solid #ebe6df}
ol.steps li::before{content:counter(s,decimal-leading-zero);position:absolute;left:0;top:11px;font-family:'JetBrains Mono',monospace;font-size:12px;color:#df2700}
.outcome{background:#181715;color:#faf9f5;border-radius:14px;padding:24px 26px;margin:36px 0;font-family:Newsreader,Georgia,serif;font-size:20px}
.outcome small{display:block;font-family:'JetBrains Mono',monospace;font-size:11px;color:#a09d96;letter-spacing:.12em;text-transform:uppercase;margin-bottom:8px}
.stack{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 30px}
.stack span{font-family:'JetBrains Mono',monospace;font-size:12px;background:#f5f0e8;border:1px solid #e6dfd8;border-radius:8px;padding:5px 11px;color:#3d3d3a}
.cta{background:#efe9de;border-radius:14px;padding:26px;margin:36px 0}
.cta h2{margin-top:0}
.cta .btn{display:inline-block;background:#df2700;color:#fff;text-decoration:none;border-radius:9999px;padding:11px 22px;font-weight:600;margin:6px 12px 0 0}
.cta .btn.alt{background:transparent;color:#141413;border:1px solid #ff5c39}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:14px;margin:18px 0 40px}
.card{background:#fff;border:1px solid #e6dfd8;border-radius:14px;padding:20px;text-decoration:none;display:block}
.card:hover{border-color:#ff5c39}
.card h3{font-family:Newsreader,Georgia,serif;font-weight:500;font-size:20px;color:#141413;margin-bottom:6px}
.card p{font-size:14px;color:#6c6a64}
.cathead{font-family:'JetBrains Mono',monospace;font-size:12px;letter-spacing:.12em;text-transform:uppercase;color:#8e8b82;margin:34px 0 4px}
footer.site{border-top:1px solid #e6dfd8;margin-top:56px;padding:26px 0 40px;font-size:14px;color:#6c6a64}
footer.site a{text-decoration:none}
article p{margin:0 0 16px;max-width:68ch}
article .lead{font-size:19px;color:#252523}
.post-meta{font-family:'JetBrains Mono',monospace;font-size:12px;color:#8e8b82;margin:4px 0 22px}
.takeaways{background:#f5f0e8;border:1px solid #e6dfd8;border-radius:14px;padding:20px 24px;margin:26px 0}
.takeaways ul{margin:10px 0 0 18px}
.takeaways li{margin-bottom:6px}
.from-practice{border-left:3px solid #ff5c39;padding:2px 0 2px 16px;color:#252523}
.faq h3{font-family:Newsreader,Georgia,serif;font-weight:500;font-size:20px;color:#141413;margin:20px 0 6px}
article code{font-family:'JetBrains Mono',monospace;font-size:.88em;background:#f5f0e8;border:1px solid #ebe6df;border-radius:5px;padding:1px 5px}
.hero-img{width:100%;aspect-ratio:3/2;object-fit:cover;border-radius:14px;border:1px solid #e6dfd8;margin:18px 0 28px;display:block}
@media(max-width:600px){h1{font-size:32px}.tagline{font-size:19px}}
"""

# Self-hosted (site/assets/fonts.css) — matches the SPA homepage, which
# vendors these same faces specifically so no visitor IP reaches
# fonts.googleapis.com / fonts.gstatic.com. Kept as one constant so every
# generated page (services, blog, work) shares the same, no-third-party head.
FONTS = '<link href="/assets/fonts.css" rel="stylesheet">'


# Service pages. Scoped to `s-*` so the work and blog pages are untouched.
#
# "Cinematic" here is native CSS only — scroll-driven animations
# (animation-timeline) plus position:sticky. No GSAP, no Framer, no CDN: this
# project deliberately ships no third-party host (see seo/vendor), and these
# are the SEO landing pages that actually take search traffic, so a JS motion
# library would cost the very thing the pages exist for.
#
# The one rule that matters: reveals MUST fail visible. Animating opacity from
# 0 would hide the page's entire content from every browser without scroll
# timelines — including crawlers. So the hidden start state lives INSIDE
# `@supports (animation-timeline: view())`, never outside it, and is disabled
# again under prefers-reduced-motion.
SERVICE_CSS = """
.s-main{max-width:none;margin:0;padding:0}
.s-in{max-width:1140px;margin:0 auto;padding:0 28px}
.s-hero{position:relative;overflow:hidden;background:#181715;color:#faf9f5;padding:104px 0 88px}
.s-hero-bg{position:absolute;inset:0;pointer-events:none;
  background-image:linear-gradient(rgba(250,249,245,.05) 1px,transparent 1px),linear-gradient(90deg,rgba(250,249,245,.05) 1px,transparent 1px);
  background-size:54px 54px;
  -webkit-mask-image:radial-gradient(120% 90% at 20% 0%,#000 30%,transparent 80%);
  mask-image:radial-gradient(120% 90% at 20% 0%,#000 30%,transparent 80%)}
.s-hero-glow{position:absolute;left:-10%;top:-30%;width:70%;height:150%;pointer-events:none;
  background:radial-gradient(ellipse 50% 40% at 50% 50%,rgba(255,92,57,.30),transparent 70%);filter:blur(40px)}
.s-hero .s-in{position:relative}
.s-crumbs{font-family:'JetBrains Mono',monospace;font-size:12px;color:#a09d96;margin-bottom:40px}
.s-crumbs a{color:#cfccc4;text-decoration:none}
.s-crumbs a:hover{color:#ff5c39}
.s-eyebrow{display:inline-block;font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.18em;
  text-transform:uppercase;color:#ff5c39;border:1px solid #2f2c28;border-radius:9999px;padding:7px 15px}
.s-title{color:#faf9f5;font-family:Newsreader,Georgia,serif;font-weight:400;font-size:clamp(44px,7vw,86px);line-height:1.02;
  letter-spacing:-.03em;margin:26px 0 0;max-width:18ch;text-wrap:balance}
.s-tagline{font-family:Newsreader,Georgia,serif;font-style:italic;font-size:clamp(21px,2.4vw,30px);
  color:#ff9e82;margin:22px 0 0;max-width:30ch}
.s-band{padding:96px 0}
.s-lede{display:grid;grid-template-columns:.36fr .64fr;gap:52px;align-items:start}
.s-lede-label{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.18em;
  text-transform:uppercase;color:#8e8b82}
.s-lede p{font-size:clamp(20px,2.1vw,27px);line-height:1.45;color:#141413;margin:0;max-width:34ch;
  font-family:Newsreader,Georgia,serif}
.s-split{display:grid;grid-template-columns:.36fr .64fr;gap:52px;align-items:start}
.s-stick{position:sticky;top:92px}
.s-h2{font-family:Newsreader,Georgia,serif;font-weight:400;font-size:clamp(28px,3.4vw,42px);
  letter-spacing:-.02em;color:#141413;margin:0;line-height:1.1}
.s-h2-on-dark{color:#faf9f5}
.s-count{font-family:'JetBrains Mono',monospace;font-size:12px;color:#8e8b82;margin-top:14px;letter-spacing:.14em}
.s-items{list-style:none;margin:0;padding:0;display:flex;flex-direction:column}
.s-item{border-top:1px solid #e6dfd8;padding:26px 0;display:grid;grid-template-columns:44px 1fr;gap:18px;align-items:baseline}
.s-item:last-child{border-bottom:1px solid #e6dfd8}
.s-item-n{font-family:'JetBrains Mono',monospace;font-size:12px;color:#ff5c39}
.s-item-t{font-size:clamp(17px,1.7vw,21px);line-height:1.4;color:#141413}
.s-steps{display:flex;flex-direction:column;gap:0}
.s-step{display:grid;grid-template-columns:.36fr .64fr;gap:52px;align-items:start;
  border-top:1px solid #2a2824;padding:46px 0}
.s-step-n{font-family:Newsreader,Georgia,serif;font-size:clamp(52px,7vw,104px);line-height:.9;
  color:transparent;-webkit-text-stroke:1px #ff5c39;text-stroke:1px #ff5c39}
.s-step-t{font-size:clamp(18px,1.9vw,24px);line-height:1.45;color:#cfccc4;max-width:32ch;padding-top:10px}
.s-dark{background:#181715;color:#faf9f5}
.s-outcome{background:#ff5c39;color:#141413;padding:96px 0}
.s-outcome p.s-outcome-label{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.2em;
  text-transform:uppercase;opacity:.72}
.s-outcome p{font-family:Newsreader,Georgia,serif;font-size:clamp(30px,5vw,62px);line-height:1.06;
  letter-spacing:-.025em;margin:20px 0 0;max-width:24ch;text-wrap:balance}
.s-stack{display:flex;flex-wrap:wrap;gap:10px;margin:26px 0 0}
.s-stack span{font-family:'JetBrains Mono',monospace;font-size:13px;color:#cfccc4;
  border:1px solid #2f2c28;border-radius:9px;padding:9px 15px;background:#1f1e1b}
.s-cta{border-top:1px solid #e6dfd8;padding:86px 0}
.s-cta-row{display:flex;flex-wrap:wrap;gap:14px;margin-top:28px}
.s-btn{display:inline-block;background:#ff5c39;color:#141413;text-decoration:none;border-radius:10px;
  padding:16px 28px;font-weight:600;font-size:15px;transition:transform .3s cubic-bezier(.16,1,.3,1)}
.s-btn:hover{transform:translateY(-2px)}
.s-btn:active{transform:translateY(1px)}
.s-btn-alt{display:inline-block;background:transparent;color:#141413;border:1px solid #e6dfd8;
  border-radius:10px;padding:16px 28px;font-weight:500;font-size:15px;text-decoration:none;
  transition:border-color .3s cubic-bezier(.16,1,.3,1)}
.s-btn-alt:hover{border-color:#ff5c39}
.s-pager{border-top:1px solid #e6dfd8;padding:24px 0 60px;display:flex;justify-content:space-between;
  gap:20px;flex-wrap:wrap;font-family:'JetBrains Mono',monospace;font-size:12px}
.s-pager a{color:#6c6a64;text-decoration:none}
.s-pager a:hover{color:#ff5c39}

/* --- motion: native scroll timelines, gated so content can never be hidden --- */
@supports (animation-timeline: view()) {
  @media (prefers-reduced-motion: no-preference) {
    /* TRANSFORM ONLY for anything carrying text. A scroll timeline that never
       advances (tall viewport, print, a crawler rendering the full page in one
       shot) would otherwise strand the copy at opacity 0 — on the very pages
       that exist to be indexed. Movement is safe; invisibility is not. */
    @keyframes s-rise{from{transform:translateY(30px)}to{transform:none}}
    @keyframes s-fade{from{opacity:.35;transform:translateY(14px)}to{opacity:1;transform:none}}
    @keyframes s-drift{from{transform:translateY(-7%) scale(1.06)}to{transform:translateY(7%) scale(1.06)}}
    .s-reveal{animation:s-rise .9s linear both;animation-timeline:view();animation-range:entry 0% entry 62%}
    /* decorative only — worst case it renders at 35% opacity, still legible */
    .s-reveal-slow{animation:s-fade 1s linear both;animation-timeline:view();animation-range:entry 0% entry 80%}
    /* the hero field drifts against the scroll — parallax without JS */
    .s-hero-bg,.s-hero-glow{animation:s-drift linear both;animation-timeline:scroll();animation-range:0 120vh}
  }
}
@media(max-width:900px){
  .s-lede,.s-split,.s-step{grid-template-columns:1fr;gap:22px}
  .s-stick{position:static}
  .s-hero{padding:76px 0 62px}
  .s-band,.s-outcome{padding:64px 0}
  .s-title{max-width:none}
  .s-step{padding:32px 0}
}
"""


# Work/case-study pages only. Scoped to `w-*` classes so the service and blog
# pages keep their existing markup byte-for-byte. Asymmetric editorial layout,
# no card containers, transform/opacity-only motion, brand palette from
# DESIGN.md (cream/coral/Newsreader) — the palette is not negotiable here.
WORK_CSS = """
.w-wrap{max-width:1140px;margin:0 auto;padding:0 24px}
.w-lede{display:grid;grid-template-columns:1.05fr .95fr;gap:56px;align-items:start;margin:8px 0 0}
.w-lede-text{padding-top:26px}
.w-idx{display:block;font-family:'JetBrains Mono',monospace;font-size:13px;letter-spacing:.18em;color:#8e8b82}
.w-lede h1{font-size:52px;margin:14px 0 0;letter-spacing:-.02em}
.w-desc{font-size:19px;color:#252523;line-height:1.55;margin:20px 0 0;max-width:46ch}
.w-stack{list-style:none;display:flex;flex-wrap:wrap;gap:0;margin:30px 0 0;border-top:1px solid #e6dfd8}
.w-stack li{font-family:'JetBrains Mono',monospace;font-size:12px;color:#3d3d3a;padding:11px 18px 11px 0;margin-right:18px;border-bottom:1px solid #ebe6df;flex:0 0 auto}
.w-shot{margin:0;border-radius:18px;overflow:hidden;border:1px solid #e6dfd8;box-shadow:0 24px 48px -28px rgba(61,45,38,.42);transform:translateY(-18px)}
.w-shot img{display:block;width:100%;height:auto;aspect-ratio:4/3;object-fit:cover}
.w-band{border-top:1px solid #e6dfd8;margin-top:76px;padding-top:34px;display:grid;grid-template-columns:.34fr .66fr;gap:40px}
.w-band-label{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:#8e8b82}
.w-band p{color:#3d3d3a;margin:0 0 18px;max-width:58ch}
.w-go{display:inline-flex;align-items:center;gap:10px;font-weight:600;color:#141413;text-decoration:none;border-bottom:1px solid #ff5c39;padding-bottom:3px;transition:gap .3s cubic-bezier(.16,1,.3,1),color .3s cubic-bezier(.16,1,.3,1)}
.w-go:hover{gap:16px;color:#df2700}
.w-go:active{transform:translateY(1px)}
.w-pager{border-top:1px solid #e6dfd8;margin-top:64px;padding-top:22px;display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap}
.w-pager a{font-family:'JetBrains Mono',monospace;font-size:12px;color:#6c6a64;text-decoration:none;transition:color .3s cubic-bezier(.16,1,.3,1)}
.w-pager a:hover{color:#df2700}
.w-hub-head{max-width:52ch;margin:6px 0 8px}
.w-rows{display:flex;flex-direction:column;gap:14px;margin:34px 0 24px}
.w-row{display:grid;grid-template-columns:1.02fr 1.28fr;gap:52px;align-items:center;padding:34px 0;border-top:1px solid #e6dfd8;text-decoration:none;color:inherit}
.w-row:last-child{border-bottom:1px solid #e6dfd8}
.w-row-shot{margin:0;border-radius:14px;overflow:hidden;border:1px solid #e6dfd8;grid-column:2;grid-row:1}
.w-row-shot img{display:block;width:100%;height:auto;aspect-ratio:3/2;object-fit:cover;transition:transform .5s cubic-bezier(.16,1,.3,1)}
.w-row:hover .w-row-shot img{transform:scale(1.04)}
.w-row-text{display:flex;flex-direction:column;gap:9px;grid-column:1;grid-row:1}
.w-row:nth-child(even){grid-template-columns:1.28fr 1.02fr}
.w-row:nth-child(even) .w-row-shot{grid-column:1}
.w-row:nth-child(even) .w-row-text{grid-column:2}
.w-row:nth-child(even) .w-row-shot img{aspect-ratio:4/3}
.w-row-meta{font-family:'JetBrains Mono',monospace;font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:#8e8b82}
.w-row h2{font-family:Newsreader,Georgia,serif;font-weight:500;font-size:31px;color:#141413;margin:0;line-height:1.18;transition:color .3s cubic-bezier(.16,1,.3,1)}
.w-row:hover h2{color:#df2700}
.w-row p{font-size:15px;color:#6c6a64;margin:0;max-width:52ch}
.w-row-go{font-family:'JetBrains Mono',monospace;font-size:12px;color:#df2700;margin-top:4px}
.w-rise{opacity:0;transform:translateY(14px);animation:wRise .7s cubic-bezier(.16,1,.3,1) forwards;animation-delay:calc(var(--i,0) * 90ms)}
@keyframes wRise{to{opacity:1;transform:none}}
a:focus-visible,button:focus-visible{outline:2px solid #df2700;outline-offset:3px;border-radius:3px}
@media(max-width:860px){
  .w-lede,.w-band,.w-row,.w-row:nth-child(even){grid-template-columns:1fr;gap:24px}
  .w-lede h1{font-size:34px}
  .w-lede-text{padding-top:4px}
  .w-shot{transform:none}
  .w-shot img{aspect-ratio:3/2}
  .w-row-shot,.w-row:nth-child(even) .w-row-shot{grid-column:1;grid-row:1}
  .w-row-text,.w-row:nth-child(even) .w-row-text{grid-column:1;grid-row:2}
  .w-row:nth-child(even) .w-row-shot img{aspect-ratio:3/2}
  .w-row h2{font-size:26px}
  .w-band{margin-top:52px}
}
@media(prefers-reduced-motion:reduce){
  .w-rise{animation:none;opacity:1;transform:none}
  .w-row-shot img,.w-go,.w-row h2{transition:none}
}
"""


def slugify(name: str) -> str:
    s = name.lower().replace("&", " ").replace("/", " ")
    return re.sub(r"-{2,}", "-", re.sub(r"[^a-z0-9]+", "-", s)).strip("-")


def meta_desc(svc: dict) -> str:
    text = f"{svc['tagline']} {svc['intro']}"
    if len(text) <= 158:
        return text
    return text[:155].rsplit(" ", 1)[0].rstrip(",.;:") + "…"


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def page_shell(title, description, canonical, body, jsonld, extra_css="", main_class="wrap") -> str:
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<meta name="robots" content="index, follow, max-image-preview:large, max-snippet:-1">
<link rel="canonical" href="{canonical}">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">
<link rel="apple-touch-icon" sizes="180x180" href="/apple-touch-icon.png">
<meta property="og:type" content="website">
<meta property="og:site_name" content="GeorgeAI">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{OG_IMAGE}">
<meta name="twitter:card" content="summary_large_image">
{FONTS}
<style>{CSS}{extra_css}</style>
<script type="application/ld+json">
{json.dumps(jsonld, ensure_ascii=False, indent=1)}
</script>
</head>
<body>
<header class="site"><div class="wrap">
<a class="wordmark" href="/"><img src="/logo-mark-ink.png" alt="" width="24" height="24" decoding="async">George<b>AI</b></a>
<a href="/" style="font-family:'JetBrains Mono',monospace;font-size:13px;text-decoration:none">← back to site</a>
</div></header>
<main class="{main_class}">
{body}
</main>
<footer class="site"><div class="wrap">
GeorgeAI — AI automation &amp; software · <a href="{PHONE_HREF}">{PHONE}</a> · <a href="mailto:{EMAIL}">{EMAIL}</a> · <a href="/pricing/">Pricing</a> · <a href="/services/">All services</a> · <a href="/blog/">Blog</a>
</div></footer>
</body>
</html>
"""


def service_jsonld(svc, slug, canonical):
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Service",
                "@id": f"{canonical}#service",
                "name": svc["name"],
                "serviceType": svc["name"],
                "category": svc["category"],
                "description": f"{svc['tagline']} {svc['intro']}",
                "url": canonical,
                "provider": {"@id": f"{BASE}/#organization"},
                "areaServed": "Worldwide",
                "availableChannel": {
                    "@type": "ServiceChannel",
                    "serviceUrl": f"{BASE}/",
                    "availableLanguage": ["en", "de", "fr", "ro", "ar"],
                },
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{canonical}#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
                    {"@type": "ListItem", "position": 2, "name": "Services", "item": f"{BASE}/services/"},
                    {"@type": "ListItem", "position": 3, "name": svc["name"]},
                ],
            },
            {
                "@type": "WebPage",
                "@id": canonical,
                "url": canonical,
                "name": f"{svc['name']} — GeorgeAI",
                "isPartOf": {"@id": f"{BASE}/#website"},
                "breadcrumb": {"@id": f"{canonical}#breadcrumb"},
                "mainEntity": {"@id": f"{canonical}#service"},
                "inLanguage": "en",
            },
        ],
    }


def service_body(svc, prev_svc=None, next_svc=None, slugs=None):
    includes = "".join(
        f'<li class="s-item s-reveal"><span class="s-item-n">{i + 1:02d}</span>'
        f'<span class="s-item-t">{esc(t)}</span></li>'
        for i, t in enumerate(svc.get("includes", []))
    )
    steps = "".join(
        f'<div class="s-step s-reveal"><div class="s-step-n">{i + 1:02d}</div>'
        f'<p class="s-step-t">{esc(s)}</p></div>'
        for i, s in enumerate(svc.get("steps", []))
    )
    stack = "".join(f"<span>{esc(t)}</span>" for t in svc.get("stack", []))
    n_inc = len(svc.get("includes", []))
    n_steps = len(svc.get("steps", []))

    pager = ""
    if slugs and (prev_svc or next_svc):
        left = (f'<a href="/services/{slugs[prev_svc["name"]]}/">&larr; {esc(prev_svc["name"])}</a>'
                if prev_svc else "<span></span>")
        right = (f'<a href="/services/{slugs[next_svc["name"]]}/">{esc(next_svc["name"])} &rarr;</a>'
                 if next_svc else "<span></span>")
        pager = f'<nav class="s-pager"><div class="s-in" style="display:flex;justify-content:space-between;gap:20px;flex-wrap:wrap;width:100%">{left}{right}</div></nav>'

    return f"""<section class="s-hero">
<div class="s-hero-bg"></div><div class="s-hero-glow"></div>
<div class="s-in">
<nav class="s-crumbs"><a href="/">Home</a> / <a href="/services/">Services</a> / {esc(svc["name"])}</nav>
<span class="s-eyebrow">{esc(svc["category"])}</span>
<h1 class="s-title">{esc(svc["name"])}</h1>
<p class="s-tagline">{esc(svc["tagline"])}</p>
</div>
</section>

<section class="s-band">
<div class="s-in s-lede s-reveal">
<p class="s-lede-label">The short version</p>
<p>{esc(svc["intro"])}</p>
</div>
</section>

<section class="s-band" style="border-top:1px solid #e6dfd8">
<div class="s-in s-split">
<div class="s-stick">
<h2 class="s-h2">What's included</h2>
<p class="s-count">{n_inc:02d} DELIVERABLES</p>
</div>
<ul class="s-items">{includes}</ul>
</div>
</section>

<section class="s-dark s-band">
<div class="s-in s-split">
<div class="s-stick">
<h2 class="s-h2 s-h2-on-dark">How it works</h2>
<p class="s-count">{n_steps:02d} STEPS &middot; PILOT IN ~2 WEEKS</p>
</div>
<div class="s-steps">{steps}</div>
</div>
</section>

<section class="s-outcome">
<div class="s-in s-reveal">
<p class="s-outcome-label">Outcome</p>
<p>{esc(svc["outcome"])}</p>
</div>
</section>

<section class="s-dark s-band">
<div class="s-in s-split">
<div class="s-stick"><h2 class="s-h2 s-h2-on-dark">Stack</h2></div>
<div class="s-stack s-reveal">{stack}</div>
</div>
</section>

<section class="s-cta">
<div class="s-in s-reveal">
<h2 class="s-h2">Get a quote</h2>
<p style="font-size:18px;color:#3d3d3a;margin-top:14px;max-width:52ch">Configure this service on the main site, or reach out directly — replies within one business day.</p>
<div class="s-cta-row">
<a class="s-btn" href="/">Open the configurator</a>
<a class="s-btn-alt" href="mailto:{EMAIL}">{EMAIL}</a>
</div>
</div>
</section>
{pager}"""


def hub_body(data, slugs):
    cats = data["categories"]
    sections = []
    for ci, cat in enumerate(cats):
        cards = "".join(
            f'<a class="card" href="/services/{slugs[s["name"]]}/">'
            f'<h3>{esc(s["name"])}</h3><p>{esc(s["tagline"])}</p></a>'
            for s in data["services"]
            if s["cat"] == ci
        )
        sections.append(f'<p class="cathead">{esc(cat)}</p><div class="grid">{cards}</div>')
    return (
        '<nav class="crumbs"><a href="/">Home</a> / Services</nav>'
        "<h1>Services</h1>"
        '<p class="intro">AI automation, chatbots, AI phone agents, growth systems and custom '
        "Python &amp; Django software — every service below has a fixed, transparent scope. "
        'Pick one to see what\'s included, or <a href="/">use the configurator</a> for a bundled quote.</p>'
        + "".join(sections)
    )


def hub_jsonld(data, slugs):
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": f"{BASE}/services/",
                "url": f"{BASE}/services/",
                "name": "Services — GeorgeAI",
                "isPartOf": {"@id": f"{BASE}/#website"},
                "inLanguage": "en",
            },
            {
                "@type": "ItemList",
                "@id": f"{BASE}/services/#list",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i + 1,
                        "name": s["name"],
                        "url": f"{BASE}/services/{slugs[s['name']]}/",
                    }
                    for i, s in enumerate(data["services"])
                ],
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{BASE}/services/#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
                    {"@type": "ListItem", "position": 2, "name": "Services"},
                ],
            },
        ],
    }


def work_jsonld(proj, slug, canonical, related_url):
    graph = [
        {
            "@type": "CreativeWork",
            "@id": f"{canonical}#work",
            "name": proj["name"],
            "genre": "Case study",
            "about": proj["category"],
            "description": proj["description"],
            "image": f"{BASE}/{proj['image']}",
            "url": canonical,
            "creator": {"@id": f"{BASE}/#organization"},
            "keywords": ", ".join(proj.get("stack", [])),
        },
        {
            "@type": "BreadcrumbList",
            "@id": f"{canonical}#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
                {"@type": "ListItem", "position": 2, "name": "Work", "item": f"{BASE}/work/"},
                {"@type": "ListItem", "position": 3, "name": proj["name"]},
            ],
        },
        {
            "@type": "WebPage",
            "@id": canonical,
            "url": canonical,
            "name": f"{proj['name']} — GeorgeAI",
            "isPartOf": {"@id": f"{BASE}/#website"},
            "breadcrumb": {"@id": f"{canonical}#breadcrumb"},
            "mainEntity": {"@id": f"{canonical}#work"},
            "inLanguage": "en",
        },
    ]
    if related_url:
        graph[0]["about"] = {"@type": "Service", "name": proj["relatedService"], "url": related_url}
    return {"@context": "https://schema.org", "@graph": graph}


def work_body(proj, related_path, position, prev_proj, next_proj, slugs):
    crumbs = (
        '<nav class="crumbs"><a href="/">Home</a> / '
        f'<a href="/work/">Work</a> / {esc(proj["name"])}</nav>'
    )
    stack = "".join(f"<li>{esc(t)}</li>" for t in proj.get("stack", []))
    if related_path:
        band = (
            '<section class="w-band w-rise" style="--i:3">'
            '<p class="w-band-label">Related service</p><div>'
            f'<p>Same approach, packaged as a service you can scope and book: '
            f'{esc(proj["relatedService"])}.</p>'
            f'<a class="w-go" href="{related_path}">See the {esc(proj["relatedService"])} service'
            '<span aria-hidden="true">&rarr;</span></a></div></section>'
        )
    else:
        band = (
            '<section class="w-band w-rise" style="--i:3">'
            '<p class="w-band-label">Similar build</p><div>'
            '<p>Infrastructure work is scoped case by case. Describe the setup and '
            'you get a written scope back within one business day.</p>'
            f'<a class="w-go" href="mailto:{EMAIL}">{EMAIL}'
            '<span aria-hidden="true">&rarr;</span></a></div></section>'
        )
    pager = ""
    if prev_proj or next_proj:
        left = (
            f'<a href="/work/{slugs[prev_proj["name"]]}/">&larr; {esc(prev_proj["name"])}</a>'
            if prev_proj else "<span></span>"
        )
        right = (
            f'<a href="/work/{slugs[next_proj["name"]]}/">{esc(next_proj["name"])} &rarr;</a>'
            if next_proj else "<span></span>"
        )
        pager = f'<nav class="w-pager">{left}{right}</nav>'
    return f"""{crumbs}
<section class="w-lede">
<div class="w-lede-text w-rise" style="--i:0">
<span class="w-idx">{position:02d} &middot; {esc(proj["category"])}</span>
<h1>{esc(proj["name"])}</h1>
<p class="w-desc">{esc(proj["description"])}</p>
<ul class="w-stack">{stack}</ul>
</div>
<figure class="w-shot w-rise" style="--i:1">
<img src="/{esc(proj["image"])}" alt="{esc(proj["name"])}" width="1200" height="900" fetchpriority="high" decoding="async">
</figure>
</section>
{band}
{pager}"""


def work_hub_body(projects, slugs):
    rows = "".join(
        f'<a class="w-row w-rise" style="--i:{i}" href="/work/{slugs[p["name"]]}/">'
        f'<figure class="w-row-shot"><img src="/{esc(p["image"])}" alt="{esc(p["name"])}" '
        f'width="900" height="{675 if i % 2 else 600}" loading="{"eager" if i == 0 else "lazy"}" '
        f'{"fetchpriority=\"high\" " if i == 0 else ""}decoding="async"></figure>'
        f'<div class="w-row-text"><span class="w-row-meta">{i + 1:02d} &middot; {esc(p["category"])}</span>'
        f'<h2>{esc(p["name"])}</h2><p>{esc(p["description"])}</p>'
        '<span class="w-row-go">View case study &rarr;</span></div></a>'
        for i, p in enumerate(projects)
    )
    return (
        '<nav class="crumbs"><a href="/">Home</a> / Work</nav>'
        '<header class="w-hub-head">'
        "<h1>Selected work</h1>"
        '<p class="intro">Five builds, up close — what each one runs on and what it does. '
        'For the full catalog of what can be scoped and booked, see '
        '<a href="/services/">Services</a>.</p>'
        "</header>"
        f'<div class="w-rows">{rows}</div>'
    )


def work_hub_jsonld(projects, slugs):
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "CollectionPage",
                "@id": f"{BASE}/work/",
                "url": f"{BASE}/work/",
                "name": "Selected work — GeorgeAI",
                "isPartOf": {"@id": f"{BASE}/#website"},
                "inLanguage": "en",
            },
            {
                "@type": "ItemList",
                "@id": f"{BASE}/work/#list",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i + 1,
                        "name": p["name"],
                        "url": f"{BASE}/work/{slugs[p['name']]}/",
                    }
                    for i, p in enumerate(projects)
                ],
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{BASE}/work/#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
                    {"@type": "ListItem", "position": 2, "name": "Work"},
                ],
            },
        ],
    }


def parse_post(path: Path):
    raw = path.read_text(encoding="utf-8")
    m = re.match(r"<!--meta\n(.*?)\n-->\n?", raw, re.S)
    if not m:
        raise ValueError(f"{path}: missing <!--meta --> header")
    meta = json.loads(m.group(1))
    meta["slug"] = path.stem
    meta["body"] = raw[m.end():]
    return meta


def post_jsonld(post, canonical):
    graph = [
        {
            "@type": "BlogPosting",
            "@id": f"{canonical}#article",
            "headline": post["title"],
            "description": post["description"],
            "datePublished": post["date"],
            "dateModified": post.get("updated", post["date"]),
            "author": {"@id": f"{BASE}/#george"},
            "publisher": {"@id": f"{BASE}/#organization"},
            "image": OG_IMAGE,
            "url": canonical,
            "mainEntityOfPage": canonical,
            "keywords": ", ".join(post.get("tags", [])),
            "inLanguage": "en",
            "isPartOf": {"@id": f"{BASE}/#website"},
        },
        {
            "@type": "BreadcrumbList",
            "@id": f"{canonical}#breadcrumb",
            "itemListElement": [
                {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
                {"@type": "ListItem", "position": 2, "name": "Blog", "item": f"{BASE}/blog/"},
                {"@type": "ListItem", "position": 3, "name": post["title"]},
            ],
        },
    ]
    if post.get("faq"):
        graph.append(
            {
                "@type": "FAQPage",
                "@id": f"{canonical}#faq",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": f["q"],
                        "acceptedAnswer": {"@type": "Answer", "text": f["a"]},
                    }
                    for f in post["faq"]
                ],
            }
        )
    return {"@context": "https://schema.org", "@graph": graph}


def post_body(post):
    faq_html = ""
    if post.get("faq"):
        items = "".join(
            f"<h3>{esc(f['q'])}</h3><p>{esc(f['a'])}</p>" for f in post["faq"]
        )
        faq_html = f'<section class="faq"><h2>Frequently asked questions</h2>{items}</section>'
    tags = " · ".join(esc(t) for t in post.get("tags", []))
    return f"""<nav class="crumbs"><a href="/">Home</a> / <a href="/blog/">Blog</a> / {esc(post["title"])}</nav>
<article>
<h1>{esc(post["title"])}</h1>
<p class="post-meta">{esc(post["date"])} · George Sebastian Cucuiet · {tags}</p>
{post["body"]}
{faq_html}
</article>"""


def blog_hub_body(posts):
    cards = "".join(
        f'<a class="card" href="/blog/{p["slug"]}/"><h3>{esc(p["title"])}</h3>'
        f'<p>{esc(p["description"])}</p>'
        f'<p class="post-meta" style="margin:10px 0 0">{esc(p["date"])}</p></a>'
        for p in posts
    )
    return (
        '<nav class="crumbs"><a href="/">Home</a> / Blog</nav>'
        "<h1>Blog</h1>"
        '<p class="intro">Practical notes on AI automation, GEO/AIO and software for small and '
        "mid-sized businesses — written from client work, with sources you can check. "
        "No news reposts, no filler.</p>"
        f'<div class="grid" style="grid-template-columns:1fr">{cards}</div>'
    )


def blog_hub_jsonld(posts):
    return {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "Blog",
                "@id": f"{BASE}/blog/",
                "url": f"{BASE}/blog/",
                "name": "GeorgeAI Blog",
                "publisher": {"@id": f"{BASE}/#organization"},
                "isPartOf": {"@id": f"{BASE}/#website"},
                "inLanguage": "en",
                "blogPost": [
                    {"@id": f"{BASE}/blog/{p['slug']}/#article"} for p in posts
                ],
            },
            {
                "@type": "BreadcrumbList",
                "@id": f"{BASE}/blog/#breadcrumb",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "Home", "item": f"{BASE}/"},
                    {"@type": "ListItem", "position": 2, "name": "Blog"},
                ],
            },
        ],
    }


def sitemap(urls, today):
    entries = "".join(
        f"\n  <url>\n    <loc>{u}</loc>\n    <lastmod>{today}</lastmod>\n"
        f"    <changefreq>{'weekly' if u.rstrip('/') == BASE.rstrip('/') else 'monthly'}</changefreq>\n"
        f"    <priority>{p}</priority>\n  </url>"
        for u, p in urls
    )
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">'
        f"{entries}\n</urlset>\n"
    )


def main():
    if len(sys.argv) not in (3, 4):
        sys.exit("usage: generate_service_pages.py <georgeai_services.json> <site_dir> [blog_dir]")
    data = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
    site = Path(sys.argv[2])
    slugs = {s["name"]: slugify(s["name"]) for s in data["services"]}
    today = date.today().isoformat()

    urls = [(f"{BASE}/", "1.0"), (f"{BASE}/pricing/", "0.9"), (f"{BASE}/services/", "0.9")]
    services = data["services"]
    for i, svc in enumerate(services):
        slug = slugs[svc["name"]]
        canonical = f"{BASE}/services/{slug}/"
        out = site / "services" / slug / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        title = f"{svc['name']} — GeorgeAI"
        out.write_text(
            page_shell(title, meta_desc(svc), canonical,
                       service_body(svc,
                                    services[i - 1] if i else None,
                                    services[i + 1] if i + 1 < len(services) else None,
                                    slugs),
                       service_jsonld(svc, slug, canonical),
                       extra_css=SERVICE_CSS, main_class="s-main"),
            encoding="utf-8",
        )
        urls.append((canonical, "0.8"))

    hub = site / "services" / "index.html"
    hub.write_text(
        page_shell(
            "Services — AI Automation, Chatbots, GEO/SEO & Software | GeorgeAI",
            "All GeorgeAI services: AI automation, chatbots, AI phone agents, SEO/AIO/GEO, "
            "email marketing, lead generation, Python, Django, ERP/CRM and web design.",
            f"{BASE}/services/",
            hub_body(data, slugs),
            hub_jsonld(data, slugs),
        ),
        encoding="utf-8",
    )

    # blog: optional third arg = directory of post fragments (blog/*.html)
    n_posts = 0
    if len(sys.argv) > 3 and Path(sys.argv[3]).is_dir():
        posts = sorted(
            (parse_post(p) for p in Path(sys.argv[3]).glob("*.html")),
            key=lambda p: p["date"],
            reverse=True,
        )
        for post in posts:
            canonical = f"{BASE}/blog/{post['slug']}/"
            out = site / "blog" / post["slug"] / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(
                page_shell(f"{post['title']} | GeorgeAI Blog", post["description"],
                           canonical, post_body(post), post_jsonld(post, canonical)),
                encoding="utf-8",
            )
            urls.append((canonical, "0.7"))
        if posts:
            (site / "blog" / "index.html").write_text(
                page_shell(
                    "Blog — AI Automation & GEO Notes | GeorgeAI",
                    "Practical, sourced articles on AI automation, GEO/AIO and software "
                    "for small and mid-sized businesses. Written from client work.",
                    f"{BASE}/blog/",
                    blog_hub_body(posts),
                    blog_hub_jsonld(posts),
                ),
                encoding="utf-8",
            )
            urls.insert(2, (f"{BASE}/blog/", "0.8"))
        n_posts = len(posts)

    # work / case-study pages: optional georgeai_work.json next to the
    # services catalog. Each project can cross-link to a real service page
    # via relatedService (matched by name against the services catalog).
    n_work = 0
    work_path = Path(sys.argv[1]).parent / "georgeai_work.json"
    if work_path.is_file():
        work_data = json.loads(work_path.read_text(encoding="utf-8"))
        projects = work_data["projects"]
        work_slugs = {p["name"]: slugify(p["name"]) for p in projects}
        for i, proj in enumerate(projects):
            slug = work_slugs[proj["name"]]
            canonical = f"{BASE}/work/{slug}/"
            out = site / "work" / slug / "index.html"
            out.parent.mkdir(parents=True, exist_ok=True)
            related_name = proj.get("relatedService")
            related_path = f"/services/{slugs[related_name]}/" if related_name in slugs else None
            related_url = f"{BASE}{related_path}" if related_path else None
            title = f"{proj['name']} — GeorgeAI"
            desc = proj["description"]
            desc = desc if len(desc) <= 158 else desc[:155].rsplit(" ", 1)[0].rstrip(",.;:") + "…"
            out.write_text(
                page_shell(
                    title, desc, canonical,
                    work_body(proj, related_path, i + 1,
                              projects[i - 1] if i else None,
                              projects[i + 1] if i + 1 < len(projects) else None,
                              work_slugs),
                    work_jsonld(proj, slug, canonical, related_url),
                    extra_css=WORK_CSS, main_class="w-wrap",
                ),
                encoding="utf-8",
            )
            urls.append((canonical, "0.7"))

        (site / "work" / "index.html").write_text(
            page_shell(
                "Selected Work — Case Studies | GeorgeAI",
                "Selected GeorgeAI projects: AI agents, automation and infrastructure work, "
                "with the stack and scope for each.",
                f"{BASE}/work/",
                work_hub_body(projects, work_slugs),
                work_hub_jsonld(projects, work_slugs),
                extra_css=WORK_CSS, main_class="w-wrap",
            ),
            encoding="utf-8",
        )
        urls.insert(3, (f"{BASE}/work/", "0.8"))
        n_work = len(projects)

    (site / "sitemap.xml").write_text(sitemap(urls, today), encoding="utf-8")
    print(f"generated {len(data['services'])} service pages + {n_posts} blog posts + "
          f"{n_work} work pages + sitemap ({len(urls)} urls)")


if __name__ == "__main__":
    main()
