# Builds /cinematic/de/ from the generated EN pages: text nodes and alt/title/placeholder/aria-label/
# meta are mapped through de.DE (unknown strings stay EN and are reported), internal links move to
# /de/, hreflang is added on both sides, and the top bar gets the EN | DE switch.
import os, re, glob, html
import importlib, sys
LANGS = ['de', 'fr', 'ro', 'ar']
NAMES = {'en': 'EN', 'de': 'DE', 'fr': 'FR', 'ro': 'RO', 'ar': 'AR'}
ROOT = '/Users/Geronimo/Projects/georgeai_dev/pages/cinematic'
BASE = '/cinematic/'
missing = set()
D = {}; LANG = 'de'

def tr(s):
    k = ' '.join(s.split())
    if k in D: return D[k]
    if re.search('[A-Za-z]{3,}', k) and not k.startswith('http') and '©' not in k: missing.add(k)
    return None

def translate_text(seg):
    # keep surrounding whitespace, translate the trimmed content
    m = re.match(r'^(\s*)(.*?)(\s*)$', seg, re.S)
    lead, body, tail = m.groups()
    if not body: return seg
    t = tr(html.unescape(body))
    return seg if t is None else lead + html.escape(t, quote=False) + tail

ATTRS = ('alt', 'title', 'placeholder', 'aria-label', 'content', 'data-say')
def translate_tag(tag):
    if tag.startswith('<meta'):
        if not re.search(r'(name="description"|property="og:(title|description)")', tag): return tag
    def rep(m):
        name, val = m.group(1), m.group(2)
        if name == 'content' and not tag.startswith('<meta'): return m.group(0)
        t = tr(html.unescape(val)); return m.group(0) if t is None else f'{name}="{html.escape(t)}"'
    return re.sub(r'\b(' + '|'.join(ATTRS) + r')="([^"]*)"', rep, tag)

def convert(src, rel):
    out, i, skip = [], 0, None
    for m in re.finditer(r'<[^>]+>', src):
        text = src[i:m.start()]
        out.append(text if skip else translate_text(text))
        tag = m.group(0); low = tag.lower()
        if skip:
            if low.startswith('</' + skip): skip = None
            out.append(tag)
        else:
            for s in ('script', 'style', 'svg'):
                if low.startswith('<' + s) and not low.endswith('/>'): skip = s
            out.append(tag if skip else translate_tag(tag))
        i = m.end()
    out.append(src[i:])
    h = ''.join(out)
    h = h.replace('<html lang="en">', f'<html lang="{LANG}"' + (' dir="rtl"' if LANG == 'ar' else '') + '>')
    # internal links -> /de/ (assets, scripts and the classic site stay)
    h = re.sub(r'href="/cinematic/(?!assets/|de/|fr/|ro/|ar/|style\.css|script\.js|jarvis\.js|globe\.js|legal\.js)', f'href="/cinematic/{LANG}/', h)
    h = h.replace(f'https://georgeai.dev{BASE}{rel}', f'https://georgeai.dev{BASE}{LANG}/{rel}')
    h = h.replace('<span class="tb-lang mono">EN</span>', switcher(rel, LANG))
    h = h.replace('<link rel="canonical"', alternates(rel) + '<link rel="canonical"')
    h = h.replace('<body data-page=', f'<body data-lang="{LANG}" data-page=')
    h = h.replace('id="lg-lang"', f'id="lg-lang" data-default="{LANG}"')
    return h

def switcher(rel, cur):
    parts = []
    for l in ['en'] + LANGS:
        href = f'{BASE}{rel}' if l == 'en' else f'{BASE}{l}/{rel}'
        parts.append(f'<b>{NAMES[l]}</b>' if l == cur else f'<a href="{href}" hreflang="{l}" lang="{l}">{NAMES[l]}</a>')
    return '<span class="tb-lang mono">' + ' '.join(parts) + '</span>'

def alternates(rel):
    out = f'<link rel="alternate" hreflang="en" href="https://georgeai.dev{BASE}{rel}">\n'
    for l in LANGS: out += f'<link rel="alternate" hreflang="{l}" href="https://georgeai.dev{BASE}{l}/{rel}">\n'
    return out + f'<link rel="alternate" hreflang="x-default" href="https://georgeai.dev{BASE}{rel}">\n'

def en_side(src, rel):
    return src.replace('<span class="tb-lang mono">EN</span>', switcher(rel, 'en')).replace('<link rel="canonical"', alternates(rel) + '<link rel="canonical"')

pages = [p for p in glob.glob(f'{ROOT}/**/index.html', recursive=True) if not re.search(r'/(de|fr|ro|ar)/', p)]
srcs = {}
for p in pages:
    rel = os.path.relpath(os.path.dirname(p), ROOT); rel = '' if rel == '.' else rel + '/'
    src = open(p, encoding='utf-8').read()
    if 'hreflang=' in src: src = re.sub(r'<link rel="alternate" hreflang="[^"]+" href="[^"]+">\n', '', src).replace(re.search(r'<span class="tb-lang mono">.*?</span>', src, re.S).group(0), '<span class="tb-lang mono">EN</span>')
    srcs[rel] = src
    open(p, 'w', encoding='utf-8').write(en_side(src, rel))
for LANG in LANGS:
    D = importlib.import_module(LANG).T; missing = set()
    for rel, src in srcs.items():
        out_html = convert(src, rel)
        dst = os.path.join(ROOT, LANG, rel, 'index.html'); os.makedirs(os.path.dirname(dst), exist_ok=True)
        open(dst, 'w', encoding='utf-8').write(out_html)
    keep = {m for m in missing if not re.fullmatch(r'[A-Za-z0-9 /().:+=_@,-]*', m) or ' ' in m and len(m) > 22}
    print(LANG, 'pages', len(srcs), 'untranslated', len(missing), '| sentences:', sorted(keep, key=len)[:12])
