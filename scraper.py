#!/usr/bin/env python3
"""
Verstappen Nieuws Scraper
- Haalt nieuws van alle grote NL + EN racingsites
- Filtert op Max Verstappen, GT, Simracing, volgende F1-race
- Vertaalt Engelse koppen automatisch naar Nederlands
- Linkt altijd naar het originele artikel
"""

import requests, re, time
from datetime import datetime, timezone, timedelta
from deep_translator import GoogleTranslator

AMSTERDAM = timezone(timedelta(hours=2))
NOW = datetime.now(AMSTERDAM)
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; VerstappenBot/1.0)"}

# ─── ZOEKTERMEN (filter) ──────────────────────────────────────────────────
TERMEN_MAX = ["verstappen"]
TERMEN_RACE = []  # Wordt gevuld met naam volgende race

# ─── RACE KALENDER 2026 (met alle sessies) ───────────────────────────────
AMSTERDAM = timezone(timedelta(hours=2))  # CEST

def s(iso): return iso  # shorthand

RACES_2026 = [
  { "vlag":"🇲🇨","naam":"Grand Prix van Monaco",           "circuit":"Circuit de Monaco",              "en_naam":"Monaco",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-06-05T13:30:00+02:00"),
      ("🔵","Vrije Training 2", "2026-06-05T17:00:00+02:00"),
      ("🔵","Vrije Training 3", "2026-06-06T12:30:00+02:00"),
      ("🟡","Kwalificatie",     "2026-06-06T16:00:00+02:00"),
      ("🔴","Race",             "2026-06-07T15:00:00+02:00"),
    ]},
  { "vlag":"🇨🇦","naam":"Grand Prix van Canada",           "circuit":"Circuit Gilles Villeneuve",      "en_naam":"Canadian",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-06-12T13:30:00-04:00"),
      ("🔵","Vrije Training 2", "2026-06-12T17:00:00-04:00"),
      ("🔵","Vrije Training 3", "2026-06-13T12:30:00-04:00"),
      ("🟡","Kwalificatie",     "2026-06-13T16:00:00-04:00"),
      ("🔴","Race",             "2026-06-14T14:00:00-04:00"),
    ]},
  { "vlag":"🇪🇸","naam":"Grand Prix van Spanje",           "circuit":"Circuit de Barcelona-Catalunya", "en_naam":"Spanish",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-06-19T13:30:00+02:00"),
      ("🔵","Vrije Training 2", "2026-06-19T17:00:00+02:00"),
      ("🔵","Vrije Training 3", "2026-06-20T12:30:00+02:00"),
      ("🟡","Kwalificatie",     "2026-06-20T16:00:00+02:00"),
      ("🔴","Race",             "2026-06-21T15:00:00+02:00"),
    ]},
  { "vlag":"🇦🇹","naam":"Grand Prix van Oostenrijk",       "circuit":"Red Bull Ring",                  "en_naam":"Austrian",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-06-26T13:30:00+02:00"),
      ("🔵","Vrije Training 2", "2026-06-26T17:00:00+02:00"),
      ("🔵","Vrije Training 3", "2026-06-27T12:30:00+02:00"),
      ("🟡","Kwalificatie",     "2026-06-27T16:00:00+02:00"),
      ("🔴","Race",             "2026-06-28T15:00:00+02:00"),
    ]},
  { "vlag":"🇬🇧","naam":"Grand Prix van Groot-Brittannië", "circuit":"Silverstone Circuit",            "en_naam":"British",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-07-03T13:30:00+01:00"),
      ("🔵","Vrije Training 2", "2026-07-03T17:00:00+01:00"),
      ("🔵","Vrije Training 3", "2026-07-04T12:30:00+01:00"),
      ("🟡","Kwalificatie",     "2026-07-04T16:00:00+01:00"),
      ("🔴","Race",             "2026-07-05T15:00:00+01:00"),
    ]},
  { "vlag":"🇧🇪","naam":"Grand Prix van België",           "circuit":"Circuit de Spa-Francorchamps",   "en_naam":"Belgian",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-07-24T13:30:00+02:00"),
      ("🔵","Vrije Training 2", "2026-07-24T17:00:00+02:00"),
      ("🔵","Vrije Training 3", "2026-07-25T12:30:00+02:00"),
      ("🟡","Kwalificatie",     "2026-07-25T16:00:00+02:00"),
      ("🔴","Race",             "2026-07-26T15:00:00+02:00"),
    ]},
  { "vlag":"🇭🇺","naam":"Grand Prix van Hongarije",        "circuit":"Hungaroring",                    "en_naam":"Hungarian",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-07-31T13:30:00+02:00"),
      ("🔵","Vrije Training 2", "2026-07-31T17:00:00+02:00"),
      ("🔵","Vrije Training 3", "2026-08-01T12:30:00+02:00"),
      ("🟡","Kwalificatie",     "2026-08-01T16:00:00+02:00"),
      ("🔴","Race",             "2026-08-02T15:00:00+02:00"),
    ]},
  { "vlag":"🇳🇱","naam":"Grand Prix van Nederland",        "circuit":"Circuit Zandvoort",              "en_naam":"Dutch",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-08-28T12:30:00+02:00"),
      ("🔵","Vrije Training 2", "2026-08-28T16:00:00+02:00"),
      ("🔵","Vrije Training 3", "2026-08-29T11:30:00+02:00"),
      ("🟡","Kwalificatie",     "2026-08-29T15:00:00+02:00"),
      ("🔴","Race",             "2026-08-30T15:00:00+02:00"),
    ]},
  { "vlag":"🇮🇹","naam":"Grand Prix van Italië",           "circuit":"Autodromo Nazionale Monza",      "en_naam":"Italian",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-09-04T13:30:00+02:00"),
      ("🔵","Vrije Training 2", "2026-09-04T17:00:00+02:00"),
      ("🔵","Vrije Training 3", "2026-09-05T12:30:00+02:00"),
      ("🟡","Kwalificatie",     "2026-09-05T16:00:00+02:00"),
      ("🔴","Race",             "2026-09-06T15:00:00+02:00"),
    ]},
  { "vlag":"🇦🇿","naam":"Grand Prix van Azerbeidzjan",     "circuit":"Baku City Circuit",              "en_naam":"Azerbaijan",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-09-18T13:30:00+04:00"),
      ("🔵","Vrije Training 2", "2026-09-18T17:00:00+04:00"),
      ("🔵","Vrije Training 3", "2026-09-19T12:30:00+04:00"),
      ("🟡","Kwalificatie",     "2026-09-19T16:00:00+04:00"),
      ("🔴","Race",             "2026-09-20T15:00:00+04:00"),
    ]},
  { "vlag":"🇸🇬","naam":"Grand Prix van Singapore",        "circuit":"Marina Bay Street Circuit",      "en_naam":"Singapore",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-10-02T17:30:00+08:00"),
      ("🔵","Vrije Training 2", "2026-10-02T21:00:00+08:00"),
      ("🔵","Vrije Training 3", "2026-10-03T17:30:00+08:00"),
      ("🟡","Kwalificatie",     "2026-10-03T21:00:00+08:00"),
      ("🔴","Race",             "2026-10-04T20:00:00+08:00"),
    ]},
  { "vlag":"🇺🇸","naam":"Grand Prix van de VS",            "circuit":"Circuit of the Americas",        "en_naam":"US",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-10-16T13:30:00-05:00"),
      ("🔵","Vrije Training 2", "2026-10-16T17:00:00-05:00"),
      ("🔵","Vrije Training 3", "2026-10-17T12:30:00-05:00"),
      ("🟡","Kwalificatie",     "2026-10-17T16:00:00-05:00"),
      ("🔴","Race",             "2026-10-18T14:00:00-05:00"),
    ]},
  { "vlag":"🇲🇽","naam":"Grand Prix van Mexico",           "circuit":"Autodromo Hermanos Rodriguez",   "en_naam":"Mexico",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-10-23T13:30:00-06:00"),
      ("🔵","Vrije Training 2", "2026-10-23T17:00:00-06:00"),
      ("🔵","Vrije Training 3", "2026-10-24T12:30:00-06:00"),
      ("🟡","Kwalificatie",     "2026-10-24T16:00:00-06:00"),
      ("🔴","Race",             "2026-10-25T14:00:00-06:00"),
    ]},
  { "vlag":"🇧🇷","naam":"Grand Prix van Brazilië",         "circuit":"Autodromo José Carlos Pace",     "en_naam":"Brazilian",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-11-06T13:30:00-03:00"),
      ("🔵","Vrije Training 2", "2026-11-06T17:00:00-03:00"),
      ("🔵","Vrije Training 3", "2026-11-07T12:30:00-03:00"),
      ("🟡","Kwalificatie",     "2026-11-07T16:00:00-03:00"),
      ("🔴","Race",             "2026-11-08T14:00:00-03:00"),
    ]},
  { "vlag":"🇦🇪","naam":"Grand Prix van Abu Dhabi",        "circuit":"Yas Marina Circuit",             "en_naam":"Abu Dhabi",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-11-27T13:30:00+04:00"),
      ("🔵","Vrije Training 2", "2026-11-27T17:00:00+04:00"),
      ("🔵","Vrije Training 3", "2026-11-28T13:30:00+04:00"),
      ("🟡","Kwalificatie",     "2026-11-28T17:00:00+04:00"),
      ("🔴","Race",             "2026-11-29T17:00:00+04:00"),
    ]},
]

def sessie_naar_amsterdam(iso):
    """Converteer sessietijd naar Amsterdam tijd string."""
    dt = datetime.fromisoformat(iso).astimezone(AMSTERDAM)
    dagen = ["ma","di","wo","do","vr","za","zo"]
    return f"{dagen[dt.weekday()]} {dt.day}/{dt.month} · {dt.strftime('%H:%M')}"

def volgende_race():
    now_utc = datetime.now(timezone.utc)
    for race in RACES_2026:
        race_iso = race["sessies"][-1][2]  # Race is altijd laatste sessie
        race_dt = datetime.fromisoformat(race_iso).astimezone(timezone.utc)
        if race_dt > now_utc:
            local_dt = datetime.fromisoformat(race_iso)
            dagen   = ["maandag","dinsdag","woensdag","donderdag","vrijdag","zaterdag","zondag"]
            maanden = ["januari","februari","maart","april","mei","juni","juli",
                       "augustus","september","oktober","november","december"]
            dag_str = f"{dagen[local_dt.weekday()]} {local_dt.day} {maanden[local_dt.month-1]} {local_dt.year}"
            # Amsterdam tijd voor de race
            race_ams = datetime.fromisoformat(race_iso).astimezone(AMSTERDAM)
            return {
                "vlag":       race["vlag"],
                "naam":       race["naam"],
                "circuit":    race["circuit"],
                "en_naam":    race["en_naam"],
                "datum_lang": f"{dag_str} · {race_ams.strftime('%H:%M')} Amsterdam tijd",
                "iso":        race_ams.isoformat(),
                "sessies":    race["sessies"],
            }
    return None

# ─── RSS BRONNEN (NL eerst, dan EN) ──────────────────────────────────────
RSS_BRONNEN = [
    # Nederlandse bronnen
    ("https://www.formule1.nl/feed/",                                        "Formule1.nl",    "f1",  "nl"),
    ("https://www.racingnews365.com/feed",                                   "RacingNews365",  "f1",  "nl"),
    ("https://nos.nl/sport/formule1/rss.xml",                                "NOS Sport",      "f1",  "nl"),
    # Engelstalige bronnen
    ("https://www.motorsport.com/rss/f1/news/",                              "Motorsport.com", "f1",  "en"),
    ("https://www.autosport.com/rss/f1/news/",                               "Autosport",      "f1",  "en"),
    ("https://www.racefans.net/feed/",                                       "RaceFans",       "f1",  "en"),
    ("https://www.thecheckeredflag.co.uk/feed/",                             "CheckeredFlag",  "f1",  "en"),
    ("https://planetf1.com/feed/",                                           "PlanetF1",       "f1",  "en"),
    ("https://www.formula1.com/content/fom-website/en/latest/all.rss.html", "Formula1.com",   "f1",  "en"),
]

# ─── PARSER ───────────────────────────────────────────────────────────────
def parse_rss_regex(raw, bron, categorie, taal, race_termen):
    items = []
    blokken = re.findall(r'<item[^>]*>(.*?)</item>', raw, re.DOTALL)
    for blok in blokken:
        title_m = re.search(r'<title[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</title>', blok, re.DOTALL)
        link_m  = re.search(r'<link[^>]*>\s*(?:<!\[CDATA\[)?(https?://[^\s<"]+?)(?:\]\]>)?\s*</link>', blok, re.DOTALL)
        desc_m  = re.search(r'<description[^>]*>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</description>', blok, re.DOTALL)

        if not title_m or not link_m:
            continue

        title_raw = re.sub(r'<[^>]+>', '', title_m.group(1)).strip()
        link_url  = link_m.group(1).strip()
        desc_raw  = re.sub(r'<[^>]+>', '', desc_m.group(1) if desc_m else '').strip()
        combined  = (title_raw + " " + desc_raw).lower()

        # Filter: alleen Verstappen, GT, simracing of volgende race
        relevant = (
            any(t in combined for t in TERMEN_MAX) or
            any(t.lower() in combined for t in race_termen) or
            "gt3" in combined or "gt racing" in combined or "nürburgring" in combined or
            "simracing" in combined or "sim racing" in combined or "esports" in combined
        )
        if not relevant:
            continue

        # Bepaal categorie op basis van inhoud
        if "gt3" in combined or "gt racing" in combined or "nürburgring" in combined or "endurance" in combined:
            categorie = "gt"
        elif "simracing" in combined or "sim racing" in combined or "esports" in combined or "iracing" in combined:
            categorie = "sim"
        else:
            categorie = "f1"

        items.append({
            "titel_orig": title_raw,
            "url": link_url,
            "bron": bron,
            "categorie": categorie,
            "taal": taal,
            "samenvatting_orig": desc_raw[:200],
        })
        if len(items) >= 8:
            break
    return items

# ─── VERTALING ────────────────────────────────────────────────────────────
def vertaal_batch(items):
    """Vertaal titel + samenvatting van Engelse items naar Nederlands."""
    translator = GoogleTranslator(source='en', target='nl')
    for item in items:
        if item["taal"] == "en":
            try:
                item["titel"] = translator.translate(item["titel_orig"])
                time.sleep(0.15)
                if item["samenvatting_orig"]:
                    item["samenvatting"] = translator.translate(item["samenvatting_orig"][:500])
                    time.sleep(0.15)
                else:
                    item["samenvatting"] = ""
            except Exception as e:
                print(f"  Vertaalfout: {e}")
                item["titel"] = item["titel_orig"]
                item["samenvatting"] = item["samenvatting_orig"]
        else:
            item["titel"] = item["titel_orig"]
            item["samenvatting"] = item["samenvatting_orig"][:140] + "…" if item["samenvatting_orig"] else ""
    return items

# ─── ALLES OPHALEN ────────────────────────────────────────────────────────
def haal_nieuws(race):
    race_termen = [race["naam"], race["en_naam"], race["circuit"]] if race else []

    alle = []
    for url, bron, cat, taal in RSS_BRONNEN:
        print(f"  {bron}…")
        try:
            r = requests.get(url, headers=HEADERS, timeout=10)
            if r.status_code == 200:
                resultaten = parse_rss_regex(r.text, bron, cat, taal, race_termen)
                print(f"    → {len(resultaten)} items")
                alle.extend(resultaten)
        except Exception as e:
            print(f"    Fout: {e}")
        time.sleep(0.2)

    # Dedupliceren
    gezien, uniek = set(), []
    for item in alle:
        sleutel = re.sub(r'\W+', '', item["titel_orig"].lower())[:50]
        if sleutel not in gezien:
            gezien.add(sleutel)
            uniek.append(item)

    uniek = uniek[:20]  # Max 20 voor vertaling

    print(f"\n  Vertalen ({sum(1 for i in uniek if i['taal']=='en')} Engelse items)…")
    uniek = vertaal_batch(uniek)

    return uniek

# ─── HTML GENEREREN ───────────────────────────────────────────────────────
def cat_label(cat):
    return {"f1": "F1", "gt": "GT", "sim": "SIM", "alg": "ALGEMEEN"}.get(cat, "F1")

def nieuws_cards(items):
    if not items:
        return '<div class="no-news">Geen nieuws gevonden — probeer het later opnieuw.</div>'
    html = ""
    for item in items:
        cat = item.get("categorie", "f1")
        samenvatting = item.get("samenvatting", "")
        if samenvatting and len(samenvatting) > 140:
            samenvatting = samenvatting[:137] + "…"
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

def sessie_rows(race):
    """Genereer HTML rijen voor alle sessies van het weekend."""
    if not race or "sessies" not in race:
        return ""
    now_utc = datetime.now(timezone.utc)
    rows = ""
    for icoon, naam, iso in race["sessies"]:
        dt_utc = datetime.fromisoformat(iso).astimezone(timezone.utc)
        dt_ams = datetime.fromisoformat(iso).astimezone(AMSTERDAM)
        voorbij = dt_utc < now_utc
        is_race = naam == "Race"
        dagen_kort = ["ma","di","wo","do","vr","za","zo"]
        dag_lbl = f"{dagen_kort[dt_ams.weekday()]} {dt_ams.day}/{dt_ams.month}"
        tijd_lbl = dt_ams.strftime("%H:%M")
        status_cls = "sessie-done" if voorbij else ("sessie-race" if is_race else "sessie-upcoming")
        status_dot = "✓" if voorbij else ("🏁" if is_race else "◉")
        rows += f'''<div class="sessie-row {status_cls}">
  <span class="sessie-dot">{status_dot}</span>
  <span class="sessie-naam">{naam}</span>
  <span class="sessie-tijd">{dag_lbl} · {tijd_lbl}</span>
</div>\n'''
    return rows

def genereer_html(nieuws, race):
    dagen   = ["maandag","dinsdag","woensdag","donderdag","vrijdag","zaterdag","zondag"]
    maanden = ["januari","februari","maart","april","mei","juni","juli",
               "augustus","september","oktober","november","december"]
    now_ams  = datetime.now(AMSTERDAM)
    datum_nl = f"{dagen[now_ams.weekday()]} {now_ams.day} {maanden[now_ams.month-1]} {now_ams.year}"

    race_vlag    = race["vlag"]       if race else "🏁"
    race_naam    = race["naam"]       if race else "Seizoen afgelopen"
    race_circuit = race["circuit"]    if race else ""
    race_datum   = race["datum_lang"] if race else ""
    race_iso     = race["iso"]        if race else ""
    cards        = nieuws_cards(nieuws)
    sessies_html = sessie_rows(race)

    return f'''<!DOCTYPE html><script type="application/json" id="cowork-artifact-meta">
{{
  "name": "Verstappen Nieuws",
  "schemaVersion": 1,
  "description": "Dagelijks Nederlandstalig nieuwsoverzicht over Max Verstappen (F1, GT, Simracing), automatisch bijgewerkt.",
  "mcpTools": [],
  "mcpServerNames": []
}}
</script>
<html lang="nl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0, viewport-fit=cover">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
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
  .race-blok{{background:linear-gradient(135deg,#0c1636 0%,#121e44 50%,#0f0a1a 100%);border-bottom:1px solid rgba(255,255,255,.08);padding:16px 28px 20px}}
  .race-top{{display:flex;align-items:center;gap:14px;flex-wrap:wrap;margin-bottom:14px}}
  .nr-label{{font-size:9px;font-weight:800;letter-spacing:2.5px;text-transform:uppercase;color:#e8002d;white-space:nowrap;flex-shrink:0}}
  .nr-divider{{width:1px;height:24px;background:rgba(255,255,255,.1);flex-shrink:0}}
  .nr-flag{{font-size:24px;flex-shrink:0}}
  .nr-info{{flex-shrink:0}}
  .nr-race{{font-size:16px;font-weight:800;color:#fff;white-space:nowrap}}
  .nr-date{{font-size:11px;color:rgba(255,255,255,.35);margin-top:2px}}
  .nr-countdown{{margin-left:auto;display:flex;gap:8px;flex-shrink:0}}
  .nr-unit{{text-align:center;background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.08);border-radius:6px;padding:5px 12px}}
  .nr-num{{font-size:22px;font-weight:900;color:#ffd700;line-height:1;font-variant-numeric:tabular-nums}}
  .nr-lbl{{font-size:8px;color:rgba(255,255,255,.28);letter-spacing:1px;text-transform:uppercase;margin-top:2px}}
  .sessies{{display:flex;gap:6px;flex-wrap:wrap}}
  .sessie-row{{display:flex;align-items:center;gap:8px;padding:6px 12px;border-radius:8px;border:1px solid rgba(255,255,255,.06);background:rgba(255,255,255,.03);flex:1;min-width:140px}}
  .sessie-done{{opacity:.35}}
  .sessie-upcoming .sessie-dot{{color:#4ade80}}
  .sessie-race{{border-color:rgba(232,0,45,.3);background:rgba(232,0,45,.07)}}
  .sessie-race .sessie-naam{{color:#fff;font-weight:800}}
  .sessie-race .sessie-dot{{color:#e8002d;font-size:14px}}
  .sessie-dot{{font-size:11px;flex-shrink:0}}
  .sessie-naam{{font-size:11px;font-weight:700;color:rgba(255,255,255,.7);flex:1}}
  .sessie-tijd{{font-size:10px;color:rgba(255,255,255,.3);white-space:nowrap}}
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
  @media(max-width:700px){{
    .header-photos{{height:140px}}
    .header-title-bar{{padding:10px 14px;gap:8px}}
    .header-title{{font-size:18px}}
    .header-eyebrow{{font-size:8px;letter-spacing:2px}}
    .header-sub{{margin-left:0;width:100%}}
    .race-blok{{padding:12px 14px 16px}}
    .race-top{{gap:8px}}
    .nr-countdown{{margin-left:0;width:100%;justify-content:flex-start}}
    .sessie-row{{min-width:120px}}
    .sessie-naam{{font-size:10px}}
    .filter-bar{{padding:8px 14px;gap:6px}}
    .filter-btn{{padding:5px 12px;font-size:10px}}
    .news-section{{padding:14px 12px 28px}}
    .news-card{{padding:12px 14px}}
    .card-title{{font-size:13px}}
    .card-summary{{font-size:11px;color:rgba(255,255,255,.3)}}
    .card-arrow{{display:none}}
  }}
  @media(max-width:400px){{
    .header-title{{font-size:16px}}
    .nr-num{{font-size:14px}}
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
      <span>Bijgewerkt op {datum_nl} · Dagelijks om 08:00 &amp; 18:00</span>
    </div>
  </div>
</div>

<div class="race-blok">
  <div class="race-top">
    <div class="nr-label">Volgende Race</div>
    <div class="nr-divider"></div>
    <div class="nr-flag">{race_vlag}</div>
    <div class="nr-info">
      <div class="nr-race">{race_naam}</div>
      <div class="nr-date">{race_circuit} · {race_datum}</div>
    </div>
    <div class="nr-countdown" id="countdown"></div>
  </div>
  <div class="sessies">{sessies_html}</div>
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

<div class="footer">MAX VERSTAPPEN NIEUWS · AUTOMATISCH BIJGEWERKT · DAGELIJKS 08:00 &amp; 18:00</div>

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

# ─── MAIN ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Volgende race bepalen…")
    race = volgende_race()
    print(f"→ {race['naam'] if race else 'geen'}")

    print("\nNieuws ophalen…")
    nieuws = haal_nieuws(race)
    print(f"\nTotaal: {len(nieuws)} unieke artikelen")

    html = genereer_html(nieuws, race)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html)
    print("index.html geschreven ✓")
