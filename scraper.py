#!/usr/bin/env python3
"""
Verstappen Nieuws Scraper – via RSS feeds
"""

import requests
import xml.etree.ElementTree as ET
from datetime import datetime, timezone, timedelta
import re, time

AMSTERDAM = timezone(timedelta(hours=2))
NOW = datetime.now(AMSTERDAM)
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; VerstappenBot/1.0)"}

# ─── RACE KALENDER 2026 ────────────────────────────────────────────────────
RACES_2026 = [
    ("🇲🇨", "Grand Prix van Monaco",        "Circuit de Monaco",              "2026-06-07T15:00:00+02:00"),
    ("🇨🇦", "Grand Prix van Canada",        "Circuit Gilles Villeneuve",      "2026-06-14T14:00:00-04:00"),
    ("🇪🇸", "Grand Prix van Spanje",        "Circuit de Barcelona-Catalunya", "2026-06-21T15:00:00+02:00"),
    ("🇦🇹", "Grand Prix van Oostenrijk",    "Red Bull Ring",                  "2026-06-28T15:00:00+02:00"),
    ("🇬🇧", "Grand Prix van Groot-Brittannië","Silverstone Circuit",          "2026-07-05T15:00:00+01:00"),
    ("🇧🇪", "Grand Prix van België",        "Circuit de Spa-Francorchamps",   "2026-07-26T15:00:00+02:00"),
    ("🇭🇺", "Grand Prix van Hongarije",     "Hungaroring",                    "2026-08-02T15:00:00+02:00"),
    ("🇳🇱", "Grand Prix van Nederland",     "Circuit Zandvoort",              "2026-08-30T15:00:00+02:00"),
    ("🇮🇹", "Grand Prix van Italië",        "Autodromo Nazionale Monza",      "2026-09-06T15:00:00+02:00"),
    ("🇦🇿", "Grand Prix van Azerbeidzjan",  "Baku City Circuit",              "2026-09-20T15:00:00+04:00"),
    ("🇸🇬", "Grand Prix van Singapore",     "Marina Bay Street Circuit",      "2026-10-04T20:00:00+08:00"),
    ("🇺🇸", "Grand Prix van de VS",         "Circuit of the Americas",        "2026-10-18T14:00:00-05:00"),
    ("🇲🇽", "Grand Prix van Mexico",        "Autodromo Hermanos Rodriguez",   "2026-10-25T14:00:00-06:00"),
    ("🇧🇷", "Grand Prix van Brazilië",      "Autodromo José Carlos Pace",     "2026-11-08T14:00:00-03:00"),
    ("🇦🇪", "Grand Prix van Abu Dhabi",     "Yas Marina Circuit",             "2026-11-29T17:00:00+04:00"),
]

def volgende_race():
    now_utc = datetime.now(timezone.utc)
    for vlag, naam, circuit, iso in RACES_2026:
        race_dt = datetime.fromisoformat(iso).astimezone(timezone.utc)
        if race_dt > now_utc:
            local_dt = datetime.fromisoformat(iso)
            dagen = ["maandag","dinsdag","woensdag","donderdag","vrijdag","zaterdag","zondag"]
            maanden = ["januari","februari","maart","april","mei","juni","juli","augustus","september","oktober","november","december"]
            dag_str = f"{dagen[local_dt.weekday()]} {local_dt.day} {maanden[local_dt.month-1]} {local_dt.year}"
            offset = local_dt.utcoffset().total_seconds() / 3600
            tz_label = "CEST" if offset == 2 else "CET" if offset == 1 else f"UTC+{int(offset)}"
            return {
                "vlag": vlag, "naam": naam, "circuit": circuit,
                "datum_lang": f"{dag_str} · {local_dt.strftime('%H:%M')} lokale tijd ({tz_label})",
                "iso": iso,
            }
    return None

# ─── RSS FEEDS (Nederlandse bronnen eerst) ────────────────────────────────
RSS_BRONNEN = [
    ("https://www.formule1.nl/feed/",           "Formule1.nl",   "f1", True),
    ("https://www.racingnews365.com/feed",       "RacingNews365", "f1", True),
    ("https://nos.nl/sport/formule1/rss.xml",    "NOS Sport",     "f1", True),
    ("https://www.motorsport.com/rss/f1/news/",  "Motorsport.com","f1", False),
    ("https://www.autosport.com/rss/f1/news/",   "Autosport",     "f1", False),
]

def parse_rss_regex(raw, bron, categorie, max_items=4):
    """Robuuste parser die ook malformed XML aankan via regex."""
    items = []
    # Extraheer <item>…</item> blokken
    blokken = re.findall(r'<item[^>]*>(.*?)</item>', raw, re.DOTALL)
    for blok in blokken:
        title = re.search(r'<title[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', blok, re.DOTALL)
        link  = re.search(r'<link[^>]*>(?:<!\[CDATA\[)?(https?://[^\s<"]+?)(?:\]\]>)?</link>', blok, re.DOTALL)
        desc  = re.search(r'<description[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>', blok, re.DOTALL)

        if not title or not link:
            continue
        title_txt = re.sub(r'<[^>]+>', '', title.group(1)).strip()
        link_txt  = link.group(1).strip()
        desc_txt  = re.sub(r'<[^>]+>', '', desc.group(1) if desc else '')[:140].strip()

        if "verstappen" not in title_txt.lower():
            continue

        if desc_txt and not desc_txt.endswith("…"):
            desc_txt += "…"

        items.append({
            "titel": title_txt, "url": link_txt,
            "bron": bron, "categorie": categorie,
            "samenvatting": desc_txt,
        })
        if len(items) >= max_items:
            break
    return items

def parse_rss(url, bron, categorie, is_dutch):
    items = []
    try:
        r = requests.get(url, headers=HEADERS, timeout=10)
        if r.status_code != 200:
            return items
        raw = r.text
        items = parse_rss_regex(raw, bron, categorie)
    except Exception as e:
        print(f"  {bron} fout: {e}")
    return items

def haal_nieuws():
    alle = []
    dutch_count = 0

    for url, bron, cat, is_dutch in RSS_BRONNEN:
        # Sla Engelstalige bronnen over als we al genoeg Nederlands hebben
        if not is_dutch and dutch_count >= 5:
            continue
        print(f"  Ophalen: {bron}…")
        resultaten = parse_rss(url, bron, cat, is_dutch)
        if is_dutch:
            dutch_count += len(resultaten)
        print(f"    → {len(resultaten)} Verstappen-items")
        alle.extend(resultaten)
        time.sleep(0.3)

    # Dedupliceren op titel
    gezien, uniek = set(), []
    for item in alle:
        sleutel = re.sub(r'\W+', '', item["titel"].lower())[:50]
        if sleutel not in gezien:
            gezien.add(sleutel)
            uniek.append(item)

    return uniek[:9]

# ─── HTML ─────────────────────────────────────────────────────────────────
def cat_label(cat):
    return {"f1":"F1","gt":"GT","sim":"SIM","alg":"ALGEMEEN"}.get(cat,"F1")

def nieuws_cards(items):
    if not items:
        return '<div class="no-news">Geen nieuws gevonden — probeer het later opnieuw.</div>'
    html = ""
    for item in items:
        cat = item.get("categorie","f1")
        samenvatting = item.get("samenvatting","")
        summary_html = f'<div class="card-summary">{samenvatting}</div>' if samenvatting else ""
        html += f'''<a class="news-card cat-{cat}-card" href="{item['url']}" target="_blank" rel="noopener" data-cat="{cat}">
  <div>
    <div class="card-meta">
      <span class="cat-tag cat-{cat}">{cat_label(cat)}</span>
      <span class="card-source">{item['bron']}</span>
    </div>
    <div class="card-title">{item['titel']}</div>
    {summary_html}
  </div>
  <div class="card-arrow">↗</div>
</a>\n'''
    return html

def genereer_html(nieuws, race):
    dagen = ["maandag","dinsdag","woensdag","donderdag","vrijdag","zaterdag","zondag"]
    maanden = ["januari","februari","maart","april","mei","juni","juli","augustus","september","oktober","november","december"]
    datum_nl = f"{dagen[NOW.weekday()]} {NOW.day} {maanden[NOW.month-1]} {NOW.year}"

    race_vlag    = race["vlag"]      if race else "🏁"
    race_naam    = race["naam"]      if race else "Seizoen afgelopen"
    race_circuit = race["circuit"]   if race else ""
    race_datum   = race["datum_lang"]if race else ""
    race_iso     = race["iso"]       if race else ""
    cards        = nieuws_cards(nieuws)

    return f'''<!DOCTYPE html><script type="application/json" id="cowork-artifact-meta">
{{
  "name": "Verstappen Nieuws",
  "schemaVersion": 1,
  "description": "Dagelijks Nederlandstalig nieuwsoverzicht over Max Verstappen (F1 & GT), automatisch bijgewerkt via AI.",
  "mcpTools": [],
  "mcpServerNames": []
}}
</script>
<html lang="nl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Max Verstappen Nieuws</title>
<style>
  :root{{color-scheme:dark}}*{{box-sizing:border-box;margin:0;padding:0}}
  body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;background:#07091a;color:#f0f0f0;min-height:100vh;overflow-x:hidden}}
  .header{{position:relative;width:100%;background:#07091a}}
  .header-photos{{width:100%;height:260px;overflow:hidden}}
  .header-photos img{{width:100%;height:100%;object-fit:cover;object-position:center;display:block}}
  .header-track{{height:3px;background:linear-gradient(90deg,transparent 0%,#e8002d 15%,#ffd700 50%,#e8002d 85%,transparent 100%);box-shadow:0 0 14px rgba(232,0,45,.5)}}
  .header-title-bar{{padding:18px 28px 16px;display:flex;align-items:baseline;gap:14px;background:#07091a;flex-wrap:wrap}}
  .header-eyebrow{{font-size:9px;font-weight:800;letter-spacing:3.5px;text-transform:uppercase;color:#e8002d;flex-shrink:0}}
  .header-title{{font-size:28px;font-weight:900;color:#fff;line-height:1;letter-spacing:-.5px}}
  .header-title em{{font-style:normal;color:#ffd700}}
  .header-sub{{margin-left:auto;font-size:11px;color:rgba(255,255,255,.3);display:flex;align-items:center;gap:8px;flex-shrink:0}}
  .live-dot{{width:7px;height:7px;border-radius:50%;background:#22c55e;box-shadow:0 0 8px #22c55e;animation:blink 2s infinite;flex-shrink:0}}
  @keyframes blink{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}
  .next-race-bar{{background:linear-gradient(90deg,#0c1636,#121e44 40%,#160a0a);border-bottom:1px solid rgba(255,255,255,.06);padding:10px 28px;display:flex;align-items:center;gap:14px;overflow-x:auto;scrollbar-width:none}}
  .next-race-bar::-webkit-scrollbar{{display:none}}
  .nr-label{{font-size:9px;font-weight:800;letter-spacing:2.5px;text-transform:uppercase;color:#e8002d;white-space:nowrap;flex-shrink:0}}
  .nr-divider{{width:1px;height:24px;background:rgba(255,255,255,.1);flex-shrink:0}}
  .nr-flag{{font-size:20px;flex-shrink:0}}
  .nr-info{{flex-shrink:0}}
  .nr-race{{font-size:14px;font-weight:800;color:#fff;white-space:nowrap}}
  .nr-date{{font-size:11px;color:rgba(255,255,255,.35);margin-top:1px}}
  .nr-countdown{{margin-left:auto;display:flex;gap:8px;flex-shrink:0}}
  .nr-unit{{text-align:center;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);border-radius:6px;padding:4px 10px}}
  .nr-num{{font-size:18px;font-weight:900;color:#ffd700;line-height:1;font-variant-numeric:tabular-nums}}
  .nr-lbl{{font-size:8px;color:rgba(255,255,255,.28);letter-spacing:1px;text-transform:uppercase}}
  .filter-bar{{display:flex;gap:8px;padding:14px 28px;background:rgba(255,255,255,.015);border-bottom:1px solid rgba(255,255,255,.05);overflow-x:auto;scrollbar-width:none}}
  .filter-bar::-webkit-scrollbar{{display:none}}
  .filter-btn{{flex-shrink:0;padding:5px 16px;border-radius:20px;border:1px solid rgba(255,255,255,.1);background:transparent;color:rgba(255,255,255,.38);font-size:11px;font-weight:700;letter-spacing:.5px;cursor:pointer;transition:all .15s;text-transform:uppercase}}
  .filter-btn:hover{{border-color:rgba(232,0,45,.4);color:rgba(255,255,255,.75)}}
  .filter-btn.active{{background:#e8002d;border-color:#e8002d;color:#fff;box-shadow:0 0 14px rgba(232,0,45,.3)}}
  .news-section{{padding:22px 28px 40px;max-width:920px;margin:0 auto}}
  .section-label{{font-size:10px;font-weight:700;letter-spacing:2.5px;text-transform:uppercase;color:rgba(255,255,255,.18);margin-bottom:14px}}
  .news-list{{display:flex;flex-direction:column;gap:10px}}
  .news-card{{background:rgba(255,255,255,.032);border:1px solid rgba(255,255,255,.055);border-left:3px solid transparent;border-radius:10px;padding:16px 18px;display:grid;grid-template-columns:1fr auto;gap:12px;align-items:center;transition:all .15s;text-decoration:none;color:inherit}}
  .news-card:hover{{background:rgba(255,255,255,.058);transform:translateX(4px)}}
  .news-card.cat-f1-card{{border-left-color:#e8002d}}.news-card.cat-f1-card:hover{{box-shadow:-2px 0 18px rgba(232,0,45,.18)}}
  .news-card.cat-gt-card{{border-left-color:#3b82f6}}.news-card.cat-gt-card:hover{{box-shadow:-2px 0 18px rgba(59,130,246,.18)}}
  .news-card.cat-sim-card{{border-left-color:#a855f7}}.news-card.cat-sim-card:hover{{box-shadow:-2px 0 18px rgba(168,85,247,.18)}}
  .news-card.cat-alg-card{{border-left-color:rgba(255,255,255,.18)}}
  .card-meta{{display:flex;align-items:center;gap:7px;margin-bottom:6px;flex-wrap:wrap}}
  .cat-tag{{font-size:9px;font-weight:800;padding:2px 8px;border-radius:20px;text-transform:uppercase;letter-spacing:1px}}
  .cat-f1{{background:rgba(232,0,45,.16);color:#ff7088;border:1px solid rgba(232,0,45,.22)}}
  .cat-gt{{background:rgba(59,130,246,.16);color:#7dd3fc;border:1px solid rgba(59,130,246,.22)}}
  .cat-sim{{background:rgba(168,85,247,.16);color:#d8b4fe;border:1px solid rgba(168,85,247,.22)}}
  .cat-alg{{background:rgba(255,255,255,.06);color:#999;border:1px solid rgba(255,255,255,.1)}}
  .card-source{{font-size:11px;color:rgba(255,255,255,.26)}}
  .card-title{{font-size:14px;font-weight:700;color:rgba(255,255,255,.88);line-height:1.35;margin-bottom:5px}}
  .card-summary{{font-size:12px;color:rgba(255,255,255,.36);line-height:1.6}}
  .card-arrow{{color:rgba(255,255,255,.18);font-size:18px;transition:color .15s;flex-shrink:0;padding-left:4px}}
  .news-card:hover .card-arrow{{color:#e8002d}}
  .no-news{{text-align:center;padding:48px;color:rgba(255,255,255,.14);font-size:13px}}
  .footer{{text-align:center;padding:0 0 32px;font-size:10px;color:rgba(255,255,255,.09);letter-spacing:.5px}}
  @media(max-width:600px){{
    .header-photos{{height:160px}}
    .header-title-bar{{padding:12px 16px}}
    .header-title{{font-size:20px}}
    .header-sub{{margin-left:0}}
    .next-race-bar,.filter-bar{{padding:10px 16px}}
    .news-section{{padding:18px 16px 32px}}
    .card-summary{{display:none}}
  }}
</style>
</head>
<body>

<div class="header">
  <div class="header-photos"><img src="header.jpg" alt="Max Verstappen"></div>
  <div class="header-track"></div>
  <div class="header-title-bar">
    <div class="header-eyebrow">Verstappen Racing Universe</div>
    <h1 class="header-title">Max <em>Verstappen</em> Nieuws</h1>
    <div class="header-sub">
      <div class="live-dot"></div>
      <span>Bijgewerkt op {datum_nl} · Dagelijks om 18:00</span>
    </div>
  </div>
</div>

<div class="next-race-bar">
  <div class="nr-label">Volgende Race</div>
  <div class="nr-divider"></div>
  <div class="nr-flag">{race_vlag}</div>
  <div class="nr-info">
    <div class="nr-race">{race_naam}</div>
    <div class="nr-date">{race_circuit} · {race_datum}</div>
  </div>
  <div class="nr-countdown" id="countdown"></div>
</div>

<div class="filter-bar">
  <button class="filter-btn active" onclick="filter('alles',this)">🏁 Alles</button>
  <button class="filter-btn" onclick="filter('f1',this)">🔴 Formule 1</button>
  <button class="filter-btn" onclick="filter('gt',this)">🔵 GT Racing</button>
  <button class="filter-btn" onclick="filter('sim',this)">🟣 Simracing</button>
  <button class="filter-btn" onclick="filter('alg',this)">⬛ Algemeen</button>
</div>

<div class="news-section">
  <div class="section-label">Actueel nieuws</div>
  <div class="news-list">{cards}</div>
</div>

<div class="footer">MAX VERSTAPPEN NIEUWS · AUTOMATISCH BIJGEWERKT · DAGELIJKS 18:00</div>

<script>
(function(){{
  const d=new Date('{race_iso}');
  function tick(){{
    const diff=d-new Date();
    if(diff<=0){{document.getElementById('countdown').innerHTML='<span style="color:#22c55e;font-weight:800">🏁 RACE DAY!</span>';return}}
    const dd=Math.floor(diff/86400000),h=Math.floor(diff%86400000/3600000),m=Math.floor(diff%3600000/60000),s=Math.floor(diff%60000/1000);
    document.getElementById('countdown').innerHTML=
      `<div class="nr-unit"><div class="nr-num">${{dd}}</div><div class="nr-lbl">Dagen</div></div>`+
      `<div class="nr-unit"><div class="nr-num">${{String(h).padStart(2,'0')}}</div><div class="nr-lbl">Uur</div></div>`+
      `<div class="nr-unit"><div class="nr-num">${{String(m).padStart(2,'0')}}</div><div class="nr-lbl">Min</div></div>`+
      `<div class="nr-unit"><div class="nr-num">${{String(s).padStart(2,'0')}}</div><div class="nr-lbl">Sec</div></div>`;
  }}
  tick();setInterval(tick,1000);
}})();
function filter(cat,btn){{
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.news-card').forEach(c=>{{c.style.display=(cat==='alles'||c.dataset.cat===cat)?'':'none'}});
}}
</script>
</body>
</html>'''

if __name__ == "__main__":
    print("Nieuws ophalen via RSS...")
    nieuws = haal_nieuws()
    print(f"\nTotaal: {len(nieuws)} unieke artikelen")
    race = volgende_race()
    print(f"Volgende race: {race['naam'] if race else 'geen'}")
    html = genereer_html(nieuws, race)
    with open("index.html","w",encoding="utf-8") as f:
        f.write(html)
    print("index.html geschreven ✓")
