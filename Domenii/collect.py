import json, os, ssl, urllib.request, urllib.error, re, socket
from datetime import date
TOK=os.environ["HOSTINGER_TOKEN"]; BASE="https://developers.hostinger.com"
OUT="Domenii"; TODAY=date.today().isoformat()
PARKING_IPS={"84.32.84.32"}

import time
def api(p):
    for i in range(5):
        r=urllib.request.Request(BASE+p,headers={"Authorization":"Bearer "+TOK,"Accept":"application/json","User-Agent":"curl/8.7.1"})
        try:
            with urllib.request.urlopen(r,timeout=30) as f: time.sleep(0.4); return json.load(f)
        except urllib.error.HTTPError as e:
            if e.code in (429,502,503): time.sleep(2*(i+1)); continue
            return {"_error":e.code}
    raise SystemExit(f"API failed repeatedly: {p}")

def probe(domain):
    ctx=ssl.create_default_context(); ctx.check_hostname=False; ctx.verify_mode=ssl.CERT_NONE
    for scheme in ("https","http"):
        try:
            req=urllib.request.Request(f"{scheme}://{domain}/",headers={"User-Agent":"Mozilla/5.0"})
            with urllib.request.urlopen(req,timeout=12,context=ctx) as f:
                body=f.read(200000).decode("utf-8","ignore")
                m=re.search(r"<title[^>]*>(.*?)</title>",body,re.I|re.S)
                return {"ok":True,"status":f.status,"final_url":f.geturl(),"title":(m.group(1).strip()[:120] if m else ""),"parking":("dns-parking" in body.lower() or "domain is parked" in body.lower() or "hostinger" in (m.group(1).lower() if m else "") and "parked" in body.lower())}
        except urllib.error.HTTPError as e:
            return {"ok":False,"status":e.code,"final_url":e.geturl(),"title":"","parking":False}
        except Exception as e:
            last=str(e)[:100]
    return {"ok":False,"status":None,"final_url":None,"title":"","parking":False,"error":last}

portfolio=api("/api/domains/v1/portfolio")
subs=api("/api/billing/v1/subscriptions")
seen=set(); rows=[]
for d in portfolio:
    dom=d["domain"]
    if dom in seen: continue
    seen.add(dom)
    det=api(f"/api/domains/v1/portfolio/{dom}")
    zone=api(f"/api/dns/v1/zones/{dom}")
    if isinstance(zone,dict): zone=[]
    a=[r["content"] for z in zone if z["type"]=="A" and z["name"]=="@" for r in z["records"]]
    cname=[r["content"] for z in zone if z["type"]=="CNAME" and z["name"]=="@" for r in z["records"]]
    mx=[r["content"] for z in zone if z["type"]=="MX" for r in z["records"]]
    dkim=[z["name"] for z in zone if "_domainkey" in z["name"]]
    try: resolved=sorted({i[4][0] for i in socket.getaddrinfo(dom,None,socket.AF_INET)})
    except Exception: resolved=[]
    pr=probe(dom)
    parked=bool(set(a)&PARKING_IPS) or bool(set(resolved)&PARKING_IPS) or pr.get("parking")
    deployed=bool(pr["ok"] and 200<=pr["status"]<400 and not parked)
    rows.append(dict(domain=dom,ids=[x["id"] for x in portfolio if x["domain"]==dom],status=d["status"],expires=d.get("expires_at"),
        detail=det,zone=zone,a=a,cname=cname,mx=mx,dkim=dkim,resolved=resolved,probe=pr,parked=parked,deployed=deployed,
        email=any("hostinger" in m for m in mx)))
    print(f"{dom:20} deployed={deployed!s:5} status={pr['status']} A={a} resolved={resolved} parked={parked} email={rows[-1]['email']} title={pr['title'][:50]!r}")

def md(r):
    det=r["detail"]; ns=det.get("name_servers") or {}
    lines=[f"# {r['domain']}","",f"_Sursă: Hostinger API, {TODAY}_","",
      "## Stare",f"- **Clasificare:** {'Deployed' if r['deployed'] else 'Undeployed'}",
      f"- **Status Hostinger:** {r['status']}",f"- **ID(-uri) portofoliu:** {', '.join(map(str,r['ids']))}",
      f"- **Înregistrat:** {det.get('registered_at') or '-'}",f"- **Expiră:** {r['expires'] or '-'}",
      f"- **Blocat transfer:** {det.get('is_locked')}",f"- **Privacy protection:** {det.get('is_privacy_protected')} (permis: {det.get('is_privacy_protection_allowed')})",
      f"- **Nameservere:** {', '.join(v for v in ns.values() if v) or '-'}","",
      "## Verificare live",f"- **A (@):** {', '.join(r['a']) or '-'}",f"- **Rezolvă la:** {', '.join(r['resolved']) or 'nu rezolvă'}",
      f"- **HTTP:** {r['probe']['status'] or 'fără răspuns'}"+(f" → `{r['probe']['final_url']}`" if r['probe'].get('final_url') else "")+(f" — eroare: {r['probe']['error']}" if r['probe'].get('error') else ""),
      f"- **Titlu pagină:** {r['probe']['title'] or '-'}",f"- **Parcat (Hostinger parking):** {r['parked']}","",
      "## Email",f"- **MX:** {', '.join(r['mx']) or '-'}",f"- **DKIM:** {', '.join(r['dkim']) or '-'}",
      f"- **Email Hostinger configurat:** {r['email']}","","## Zonă DNS completă","","| Nume | Tip | TTL | Conținut |","|---|---|---|---|"]
    for z in sorted(r["zone"],key=lambda z:(z["type"],z["name"])):
        for rec in z["records"]:
            lines.append(f"| `{z['name']}` | {z['type']} | {z['ttl']} | `{rec['content']}` |")
    return "\n".join(lines)+"\n"

for r in rows:
    sub="Deployed" if r["deployed"] else "Undeployed"
    open(f"{OUT}/{sub}/{r['domain']}.md","w").write(md(r))

# emails/
em=[s for s in subs if "Email" in s["name"]]
lines=["# Abonamente email (Hostinger)","",f"_Sursă: Hostinger API, {TODAY}. API-ul de facturare nu leagă abonamentul de domeniu; legătura domeniu↔email de mai jos e dedusă din MX/DKIM._","",
  "## Abonamente","","| ID | Plan | Status | Auto-renew | Preț reînnoire | Următoarea facturare | Expiră |","|---|---|---|---|---|---|---|"]
for s in sorted(em,key=lambda s:s["next_billing_at"] or s["expires_at"] or ""):
    lines.append(f"| `{s['id']}` | {s['name']} | {s['status']} | {s['is_auto_renewed']} | {s['renewal_price']/100:.2f} {s['currency_code']}/{s['billing_period_unit']} | {s['next_billing_at'] or '-'} | {s['expires_at'] or '-'} |")
lines+=["","## Domenii cu email Hostinger (MX mx1/mx2.hostinger.com)",""]
for r in rows:
    if r["email"]: lines.append(f"- **{r['domain']}** — DKIM: {', '.join(r['dkim']) or 'lipsă'}; fișier: `../{'Deployed' if r['deployed'] else 'Undeployed'}/{r['domain']}.md`")
lines+=["","## Domenii fără email Hostinger",""]
for r in rows:
    if not r["email"]: lines.append(f"- {r['domain']} — MX: {', '.join(r['mx']) or 'niciun MX'}")
open(f"{OUT}/emails/README.md","w").write("\n".join(lines)+"\n")
for r in rows:
    if r["email"]:
        open(f"{OUT}/emails/{r['domain']}.md","w").write("\n".join([f"# Email — {r['domain']}","",f"_Sursă: DNS Hostinger, {TODAY}_","",
          f"- **MX:** {', '.join(r['mx'])}",f"- **DKIM:** {', '.join(r['dkim']) or '-'}",
          "- **SPF:** "+(", ".join(rec['content'] for z in r['zone'] if z['type']=='TXT' and z['name']=='@' for rec in z['records'] if 'spf' in rec['content'].lower()) or '-'),
          "- **DMARC:** "+(", ".join(rec['content'] for z in r['zone'] if z['type']=='TXT' and z['name']=='_dmarc' for rec in z['records']) or '-'),
          f"- **Domeniu:** `../{'Deployed' if r['deployed'] else 'Undeployed'}/{r['domain']}.md`",""]))

# index
idx=["# Domenii Hostinger","",f"_Generat {TODAY} din API-ul Hostinger. Regenerare: `HOSTINGER_TOKEN` în `.env` + scriptul de colectare._","",
 "| Domeniu | Clasificare | Status | Expiră | A (@) | HTTP | Email |","|---|---|---|---|---|---|---|"]
for r in sorted(rows,key=lambda r:(not r["deployed"],r["domain"])):
    idx.append(f"| [{r['domain']}]({'Deployed' if r['deployed'] else 'Undeployed'}/{r['domain']}.md) | {'Deployed' if r['deployed'] else 'Undeployed'} | {r['status']} | {(r['expires'] or '-')[:10]} | {', '.join(r['a']) or '-'} | {r['probe']['status'] or '-'} | {'da' if r['email'] else '-'} |")
open(f"{OUT}/README.md","w").write("\n".join(idx)+"\n")
print(f"\n{sum(r['deployed'] for r in rows)} deployed, {sum(not r['deployed'] for r in rows)} undeployed, {sum(r['email'] for r in rows)} cu email")
