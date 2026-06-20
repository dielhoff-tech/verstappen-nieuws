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
  { "vlag":"🇦🇺","naam":"Grand Prix van Australië",        "circuit":"Albert Park",                    "en_naam":"Australian",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-03-06T11:30:00+11:00"),
      ("🔵","Vrije Training 2", "2026-03-06T15:00:00+11:00"),
      ("🔵","Vrije Training 3", "2026-03-07T11:30:00+11:00"),
      ("🟡","Kwalificatie",     "2026-03-07T15:00:00+11:00"),
      ("🔴","Race",             "2026-03-08T15:00:00+11:00"),
    ]},
  { "vlag":"🇨🇳","naam":"Grand Prix van China",            "circuit":"Shanghai International Circuit", "en_naam":"Chinese",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-03-13T11:30:00+08:00"),
      ("🔵","Vrije Training 2", "2026-03-13T15:00:00+08:00"),
      ("🔵","Vrije Training 3", "2026-03-14T11:30:00+08:00"),
      ("🟡","Kwalificatie",     "2026-03-14T15:00:00+08:00"),
      ("🔴","Race",             "2026-03-15T15:00:00+08:00"),
    ]},
  { "vlag":"🇯🇵","naam":"Grand Prix van Japan",            "circuit":"Suzuka Circuit",                 "en_naam":"Japanese",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-03-27T12:30:00+09:00"),
      ("🔵","Vrije Training 2", "2026-03-27T16:00:00+09:00"),
      ("🔵","Vrije Training 3", "2026-03-28T12:30:00+09:00"),
      ("🟡","Kwalificatie",     "2026-03-28T16:00:00+09:00"),
      ("🔴","Race",             "2026-03-29T14:00:00+09:00"),
    ]},
  { "vlag":"🇺🇸","naam":"Grand Prix van Miami",            "circuit":"Miami International Autodrome",  "en_naam":"Miami",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-05-01T18:30:00-04:00"),
      ("🔵","Vrije Training 2", "2026-05-01T22:00:00-04:00"),
      ("🔵","Vrije Training 3", "2026-05-02T15:30:00-04:00"),
      ("🟡","Kwalificatie",     "2026-05-02T19:00:00-04:00"),
      ("🔴","Race",             "2026-05-03T16:00:00-04:00"),
    ]},
  { "vlag":"🇨🇦","naam":"Grand Prix van Canada",           "circuit":"Circuit Gilles Villeneuve",      "en_naam":"Canadian",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-05-22T13:30:00-04:00"),
      ("🔵","Vrije Training 2", "2026-05-22T17:00:00-04:00"),
      ("🔵","Vrije Training 3", "2026-05-23T12:30:00-04:00"),
      ("🟡","Kwalificatie",     "2026-05-23T16:00:00-04:00"),
      ("🔴","Race",             "2026-05-24T14:00:00-04:00"),
    ]},
  { "vlag":"🇲🇨","naam":"Grand Prix van Monaco",           "circuit":"Circuit de Monaco",              "en_naam":"Monaco",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-06-05T13:30:00+02:00"),
      ("🔵","Vrije Training 2", "2026-06-05T17:00:00+02:00"),
      ("🔵","Vrije Training 3", "2026-06-06T12:30:00+02:00"),
      ("🟡","Kwalificatie",     "2026-06-06T16:00:00+02:00"),
      ("🔴","Race",             "2026-06-07T15:00:00+02:00"),
    ]},
  { "vlag":"🇪🇸","naam":"Grand Prix van Barcelona",        "circuit":"Circuit de Barcelona-Catalunya", "en_naam":"Spanish",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-06-12T13:30:00+02:00"),
      ("🔵","Vrije Training 2", "2026-06-12T17:00:00+02:00"),
      ("🔵","Vrije Training 3", "2026-06-13T12:30:00+02:00"),
      ("🟡","Kwalificatie",     "2026-06-13T16:00:00+02:00"),
      ("🔴","Race",             "2026-06-14T15:00:00+02:00"),
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
      ("🔵","Vrije Training 1", "2026-07-17T13:30:00+02:00"),
      ("🔵","Vrije Training 2", "2026-07-17T17:00:00+02:00"),
      ("🔵","Vrije Training 3", "2026-07-18T12:30:00+02:00"),
      ("🟡","Kwalificatie",     "2026-07-18T16:00:00+02:00"),
      ("🔴","Race",             "2026-07-19T15:00:00+02:00"),
    ]},
  { "vlag":"🇭🇺","naam":"Grand Prix van Hongarije",        "circuit":"Hungaroring",                    "en_naam":"Hungarian",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-07-24T13:30:00+02:00"),
      ("🔵","Vrije Training 2", "2026-07-24T17:00:00+02:00"),
      ("🔵","Vrije Training 3", "2026-07-25T12:30:00+02:00"),
      ("🟡","Kwalificatie",     "2026-07-25T16:00:00+02:00"),
      ("🔴","Race",             "2026-07-26T15:00:00+02:00"),
    ]},
  { "vlag":"🇳🇱","naam":"Grand Prix van Nederland",        "circuit":"Circuit Zandvoort",              "en_naam":"Dutch",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-08-21T12:30:00+02:00"),
      ("🔵","Vrije Training 2", "2026-08-21T16:00:00+02:00"),
      ("🔵","Vrije Training 3", "2026-08-22T11:30:00+02:00"),
      ("🟡","Kwalificatie",     "2026-08-22T15:00:00+02:00"),
      ("🔴","Race",             "2026-08-23T15:00:00+02:00"),
    ]},
  { "vlag":"🇮🇹","naam":"Grand Prix van Italië",           "circuit":"Autodromo Nazionale Monza",      "en_naam":"Italian",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-09-04T13:30:00+02:00"),
      ("🔵","Vrije Training 2", "2026-09-04T17:00:00+02:00"),
      ("🔵","Vrije Training 3", "2026-09-05T12:30:00+02:00"),
      ("🟡","Kwalificatie",     "2026-09-05T16:00:00+02:00"),
      ("🔴","Race",             "2026-09-06T15:00:00+02:00"),
    ]},
  { "vlag":"🇪🇸","naam":"Grand Prix van Madrid",           "circuit":"Circuito de Madrid",             "en_naam":"Madrid",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-09-11T13:30:00+02:00"),
      ("🔵","Vrije Training 2", "2026-09-11T17:00:00+02:00"),
      ("🔵","Vrije Training 3", "2026-09-12T12:30:00+02:00"),
      ("🟡","Kwalificatie",     "2026-09-12T16:00:00+02:00"),
      ("🔴","Race",             "2026-09-13T15:00:00+02:00"),
    ]},
  { "vlag":"🇦🇿","naam":"Grand Prix van Azerbeidzjan",     "circuit":"Baku City Circuit",              "en_naam":"Azerbaijan",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-09-25T11:30:00+04:00"),
      ("🔵","Vrije Training 2", "2026-09-25T15:00:00+04:00"),
      ("🔵","Vrije Training 3", "2026-09-26T11:30:00+04:00"),
      ("🟡","Kwalificatie",     "2026-09-26T15:00:00+04:00"),
      ("🔴","Race",             "2026-09-27T15:00:00+04:00"),  # Zondag 27 sep
    ]},
  { "vlag":"🇸🇬","naam":"Grand Prix van Singapore",        "circuit":"Marina Bay Street Circuit",      "en_naam":"Singapore",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-10-09T17:30:00+08:00"),
      ("🔵","Vrije Training 2", "2026-10-09T21:00:00+08:00"),
      ("🔵","Vrije Training 3", "2026-10-10T17:30:00+08:00"),
      ("🟡","Kwalificatie",     "2026-10-10T21:00:00+08:00"),
      ("🔴","Race",             "2026-10-11T20:00:00+08:00"),
    ]},
  { "vlag":"🇺🇸","naam":"Grand Prix van de VS",            "circuit":"Circuit of the Americas",        "en_naam":"US",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-10-23T18:30:00-05:00"),
      ("🔵","Vrije Training 2", "2026-10-23T22:00:00-05:00"),
      ("🔵","Vrije Training 3", "2026-10-24T15:30:00-05:00"),
      ("🟡","Kwalificatie",     "2026-10-24T19:00:00-05:00"),
      ("🔴","Race",             "2026-10-25T14:00:00-05:00"),
    ]},
  { "vlag":"🇲🇽","naam":"Grand Prix van Mexico-Stad",      "circuit":"Autodromo Hermanos Rodriguez",   "en_naam":"Mexican",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-10-30T13:30:00-06:00"),
      ("🔵","Vrije Training 2", "2026-10-30T17:00:00-06:00"),
      ("🔵","Vrije Training 3", "2026-10-31T12:30:00-06:00"),
      ("🟡","Kwalificatie",     "2026-10-31T16:00:00-06:00"),
      ("🔴","Race",             "2026-11-01T14:00:00-06:00"),
    ]},
  { "vlag":"🇧🇷","naam":"Grand Prix van Brazilië",         "circuit":"Autodromo José Carlos Pace",     "en_naam":"Brazilian",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-11-06T13:30:00-03:00"),
      ("🔵","Vrije Training 2", "2026-11-06T17:00:00-03:00"),
      ("🔵","Vrije Training 3", "2026-11-07T12:30:00-03:00"),
      ("🟡","Kwalificatie",     "2026-11-07T16:00:00-03:00"),
      ("🔴","Race",             "2026-11-08T14:00:00-03:00"),
    ]},
  { "vlag":"🇺🇸","naam":"Grand Prix van Las Vegas",        "circuit":"Las Vegas Street Circuit",       "en_naam":"Las Vegas",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-11-20T20:00:00-08:00"),
      ("🔵","Vrije Training 2", "2026-11-21T00:00:00-08:00"),
      ("🔵","Vrije Training 3", "2026-11-21T20:00:00-08:00"),
      ("🟡","Kwalificatie",     "2026-11-22T00:00:00-08:00"),
      ("🔴","Race",             "2026-11-22T22:00:00-08:00"),
    ]},
  { "vlag":"🇶🇦","naam":"Grand Prix van Qatar",            "circuit":"Lusail International Circuit",   "en_naam":"Qatar",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-11-27T16:30:00+03:00"),
      ("🔵","Vrije Training 2", "2026-11-27T20:00:00+03:00"),
      ("🔵","Vrije Training 3", "2026-11-28T16:30:00+03:00"),
      ("🟡","Kwalificatie",     "2026-11-28T20:00:00+03:00"),
      ("🔴","Race",             "2026-11-29T18:00:00+03:00"),
    ]},
  { "vlag":"🇦🇪","naam":"Grand Prix van Abu Dhabi",        "circuit":"Yas Marina Circuit",             "en_naam":"Abu Dhabi",
    "sessies":[
      ("🔵","Vrije Training 1", "2026-12-04T13:30:00+04:00"),
      ("🔵","Vrije Training 2", "2026-12-04T17:00:00+04:00"),
      ("🔵","Vrije Training 3", "2026-12-05T13:30:00+04:00"),
      ("🟡","Kwalificatie",     "2026-12-05T17:00:00+04:00"),
      ("🔴","Race",             "2026-12-06T17:00:00+04:00"),
    ]},
]

CIRCUIT_INFO = {
    "Australian": {"lengte":"5.278 km","ronden":58,"record":"1:20.235","record_door":"Charles Leclerc (2022)"},
    "Chinese":    {"lengte":"5.451 km","ronden":56,"record":"1:32.238","record_door":"Michael Schumacher (2004)"},
    "Japanese":   {"lengte":"5.807 km","ronden":53,"record":"1:30.983","record_door":"Kimi Räikkönen (2005)"},
    "Miami":      {"lengte":"5.412 km","ronden":57,"record":"1:29.708","record_door":"Max Verstappen (2023)"},
    "Canadian":   {"lengte":"4.361 km","ronden":70,"record":"1:13.078","record_door":"Valtteri Bottas (2019)"},
    "Monaco":     {"lengte":"3.337 km","ronden":78,"record":"1:12.909","record_door":"Lewis Hamilton (2021)"},
    "Spanish":    {"lengte":"4.657 km","ronden":66,"record":"1:16.330","record_door":"Max Verstappen (2023)"},
    "Austrian":   {"lengte":"4.318 km","ronden":71,"record":"1:05.619","record_door":"Carlos Sainz (2020)"},
    "British":    {"lengte":"5.891 km","ronden":52,"record":"1:27.097","record_door":"Max Verstappen (2020)"},
    "Belgian":    {"lengte":"7.004 km","ronden":44,"record":"1:46.286","record_door":"Valtteri Bottas (2018)"},
    "Hungarian":  {"lengte":"4.381 km","ronden":70,"record":"1:16.627","record_door":"Lewis Hamilton (2020)"},
    "Dutch":      {"lengte":"4.259 km","ronden":72,"record":"1:11.097","record_door":"Max Verstappen (2021)"},
    "Italian":    {"lengte":"5.793 km","ronden":53,"record":"1:21.046","record_door":"Rubens Barrichello (2004)"},
    "Madrid":     {"lengte":"5.476 km","ronden":55,"record":"–","record_door":"Nieuw circuit (2026)"},
    "Azerbaijan": {"lengte":"6.003 km","ronden":51,"record":"1:43.009","record_door":"Charles Leclerc (2019)"},
    "Singapore":  {"lengte":"4.940 km","ronden":62,"record":"1:35.867","record_door":"Kevin Magnussen (2018)"},
    "US":         {"lengte":"5.513 km","ronden":56,"record":"1:36.169","record_door":"Charles Leclerc (2019)"},
    "Mexican":    {"lengte":"4.304 km","ronden":71,"record":"1:17.774","record_door":"Valtteri Bottas (2021)"},
    "Brazilian":  {"lengte":"4.309 km","ronden":71,"record":"1:10.540","record_door":"Valtteri Bottas (2018)"},
    "Las Vegas":  {"lengte":"6.201 km","ronden":50,"record":"1:35.490","record_door":"Oscar Piastri (2024)"},
    "Qatar":      {"lengte":"5.380 km","ronden":57,"record":"1:24.319","record_door":"Max Verstappen (2023)"},
    "Abu Dhabi":  {"lengte":"5.281 km","ronden":58,"record":"1:26.103","record_door":"Max Verstappen (2021)"},
}

def volgende_race():
    now_utc = datetime.now(timezone.utc)
    for race in RACES_2026:
        race_iso = race["sessies"][-1][2]
        race_dt  = datetime.fromisoformat(race_iso).astimezone(timezone.utc)
        if race_dt > now_utc:
            race_ams = datetime.fromisoformat(race_iso).astimezone(AMSTERDAM)
            maanden  = ["januari","februari","maart","april","mei","juni","juli",
                        "augustus","september","oktober","november","december"]
            dagen    = ["maandag","dinsdag","woensdag","donderdag","vrijdag","zaterdag","zondag"]
            dag_str  = f"{dagen[race_ams.weekday()]} {race_ams.day} {maanden[race_ams.month-1]} {race_ams.year}"
            return {
                "vlag":       race["vlag"],
                "naam":       race["naam"],
                "circuit":    race["circuit"],
                "en_naam":    race["en_naam"],
                "datum_lang": f"{dag_str} · {race_ams.strftime('%H:%M')} Amsterdam",
                "iso_race":   race_ams.isoformat(),
                "sessies":    race["sessies"],
                "info":       CIRCUIT_INFO.get(race["en_naam"], {}),
            }
    return None

def volgende_sessie(race):
    """Geeft de eerstvolgende sessie die nog niet voorbij is (of nu live is)."""
    if not race:
        return None
    now_utc = datetime.now(timezone.utc)
    for icoon, naam, iso in race["sessies"]:
        dt_utc = datetime.fromisoformat(iso).astimezone(timezone.utc)
        # Beschouw sessie als "live" als hij max 2u geleden begon
        if dt_utc > now_utc - timedelta(hours=2):
            dt_ams = dt_utc.astimezone(AMSTERDAM)
            is_live = dt_utc <= now_utc
            return {"naam": naam, "iso_ams": dt_ams.isoformat(), "is_live": is_live}
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

def sessie_tijdlijn(race):
    if not race:
        return ""
    now_utc = datetime.now(timezone.utc)
    dagen_k = ["ma","di","wo","do","vr","za","zo"]
    rows = ""
    for icoon, naam, iso in race["sessies"]:
        dt_utc = datetime.fromisoformat(iso).astimezone(timezone.utc)
        dt_ams = datetime.fromisoformat(iso).astimezone(AMSTERDAM)
        voorbij  = dt_utc < now_utc - timedelta(hours=2)
        is_live  = (now_utc - timedelta(hours=2)) <= dt_utc <= now_utc
        is_race  = naam == "Race"
        dag_lbl  = f"{dagen_k[dt_ams.weekday()]} {dt_ams.day}/{dt_ams.month}"
        tijd_lbl = dt_ams.strftime("%H:%M")

        if voorbij:
            cls, badge = "s-done", '<span class="s-check">✓</span>'
        elif is_live:
            cls, badge = "s-live", '<span class="s-live-badge">LIVE</span>'
        elif is_race:
            cls, badge = "s-race", '<span class="s-dot-race">🏁</span>'
        else:
            cls, badge = "s-next", '<span class="s-dot-next">◉</span>'

        rows += f'<div class="s-row {cls}">{badge}<span class="s-naam">{naam}</span><span class="s-tijd">{dag_lbl} · {tijd_lbl}</span></div>\n'
    return rows

def genereer_html(nieuws, race):
    maanden  = ["januari","februari","maart","april","mei","juni","juli",
                "augustus","september","oktober","november","december"]
    dagen    = ["maandag","dinsdag","woensdag","donderdag","vrijdag","zaterdag","zondag"]
    now_ams  = datetime.now(AMSTERDAM)
    datum_nl = f"{dagen[now_ams.weekday()]} {now_ams.day} {maanden[now_ams.month-1]} {now_ams.year}"

    vsessie  = volgende_sessie(race)
    cards    = nieuws_cards(nieuws)
    tijdlijn = sessie_tijdlijn(race)

    race_vlag    = race["vlag"]        if race else "🏁"
    race_naam    = race["naam"]        if race else "Seizoen afgelopen"
    race_circuit = race["circuit"]     if race else ""
    race_datum   = race["datum_lang"]  if race else ""
    iso_race     = race["iso_race"]    if race else ""
    info         = race.get("info", {}) if race else {}
    lengte       = info.get("lengte","–")
    ronden       = info.get("ronden","–")
    record       = info.get("record","–")
    record_door  = info.get("record_door","–")

    # Volgende sessie countdown target (Amsterdam ISO)
    vsessie_naam = vsessie["naam"]    if vsessie else "Race"
    vsessie_iso  = vsessie["iso_ams"] if vsessie else iso_race
    vsessie_live = vsessie["is_live"] if vsessie else False
    countdown_label = "LIVE nu" if vsessie_live else f"Tot {vsessie_naam}"

    return f'''<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<title>Max Verstappen Nieuws</title>
<style>
:root{{color-scheme:dark}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;background:#07091a;color:#f0f0f0;min-height:100vh;overflow-x:hidden}}

/* ── HEADER ── */
.header{{position:relative;width:100%}}
.header-img{{width:100%;height:260px;overflow:hidden}}
.header-img img{{width:100%;height:100%;object-fit:cover;object-position:center top;display:block}}
.track-line{{height:3px;background:linear-gradient(90deg,transparent,#e8002d 20%,#ffd700 50%,#e8002d 80%,transparent);box-shadow:0 0 16px rgba(232,0,45,.6)}}
.title-bar{{padding:14px 28px 12px;display:flex;align-items:center;gap:14px;flex-wrap:wrap}}
.eyebrow{{font-size:9px;font-weight:800;letter-spacing:3.5px;text-transform:uppercase;color:#e8002d}}
.site-title{{font-size:26px;font-weight:900;color:#fff;letter-spacing:-.5px;line-height:1}}
.site-title em{{font-style:normal;color:#ffd700}}
.update-badge{{margin-left:auto;display:flex;align-items:center;gap:6px;font-size:10px;color:rgba(255,255,255,.28)}}
.live-dot{{width:6px;height:6px;border-radius:50%;background:#22c55e;box-shadow:0 0 8px #22c55e;animation:pulse 2s infinite;flex-shrink:0}}
@keyframes pulse{{0%,100%{{opacity:1}}50%{{opacity:.2}}}}

/* ── RACE BLOK ── */
.race-blok{{background:linear-gradient(160deg,#0d1840 0%,#111830 45%,#130818 100%);border-bottom:1px solid rgba(255,255,255,.07);padding:18px 28px 22px}}
.race-header{{display:flex;align-items:flex-start;gap:16px;flex-wrap:wrap;margin-bottom:18px}}
.race-flag{{font-size:32px;line-height:1;flex-shrink:0;margin-top:2px}}
.race-meta{{flex:1;min-width:180px}}
.race-label{{font-size:9px;font-weight:800;letter-spacing:2.5px;text-transform:uppercase;color:#e8002d;margin-bottom:4px}}
.race-naam{{font-size:18px;font-weight:900;color:#fff;line-height:1.1;margin-bottom:3px}}
.race-circuit{{font-size:11px;color:rgba(255,255,255,.35)}}
.race-datum{{font-size:11px;color:rgba(255,255,255,.5);margin-top:2px}}
.countdown-blok{{flex-shrink:0}}
.countdown-label{{font-size:9px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:rgba(255,255,255,.35);margin-bottom:6px;text-align:right}}
.countdown-label.live{{color:#22c55e}}
.countdown{{display:flex;gap:6px}}
.cd-unit{{text-align:center;background:rgba(0,0,0,.3);border:1px solid rgba(255,215,0,.15);border-radius:8px;padding:6px 10px;min-width:52px}}
.cd-num{{font-size:24px;font-weight:900;color:#ffd700;line-height:1;font-variant-numeric:tabular-nums}}
.cd-lbl{{font-size:8px;color:rgba(255,255,255,.3);letter-spacing:1.5px;text-transform:uppercase;margin-top:2px}}

/* ── CIRCUIT INFO ── */
.circuit-info{{display:flex;gap:6px;flex-wrap:wrap;margin-bottom:18px}}
.ci-item{{background:rgba(255,255,255,.04);border:1px solid rgba(255,255,255,.06);border-radius:8px;padding:8px 14px;flex:1;min-width:110px}}
.ci-val{{font-size:13px;font-weight:800;color:#fff;line-height:1}}
.ci-key{{font-size:9px;color:rgba(255,255,255,.3);letter-spacing:1px;text-transform:uppercase;margin-top:3px}}

/* ── SESSIE TIJDLIJN ── */
.tijdlijn-label{{font-size:9px;font-weight:800;letter-spacing:2px;text-transform:uppercase;color:rgba(255,255,255,.25);margin-bottom:8px}}
.tijdlijn{{display:flex;gap:5px;flex-wrap:wrap}}
.s-row{{display:flex;align-items:center;gap:7px;padding:7px 12px;border-radius:8px;border:1px solid rgba(255,255,255,.06);background:rgba(255,255,255,.03);flex:1;min-width:130px;transition:all .15s}}
.s-done{{opacity:.28}}
.s-live{{border-color:rgba(34,197,94,.4)!important;background:rgba(34,197,94,.08)!important;animation:liveglow 2s ease-in-out infinite}}
@keyframes liveglow{{0%,100%{{box-shadow:0 0 0 rgba(34,197,94,0)}}50%{{box-shadow:0 0 12px rgba(34,197,94,.25)}}}}
.s-race{{border-color:rgba(232,0,45,.3);background:rgba(232,0,45,.06)}}
.s-next{{border-color:rgba(255,215,0,.15)}}
.s-check{{color:#4ade80;font-size:11px;flex-shrink:0}}
.s-live-badge{{font-size:8px;font-weight:900;letter-spacing:1.5px;color:#22c55e;background:rgba(34,197,94,.15);border:1px solid rgba(34,197,94,.3);border-radius:4px;padding:2px 5px;flex-shrink:0}}
.s-dot-race{{font-size:11px;flex-shrink:0}}
.s-dot-next{{color:#ffd700;font-size:10px;flex-shrink:0}}
.s-naam{{font-size:11px;font-weight:700;color:rgba(255,255,255,.75);flex:1}}
.s-live .s-naam{{color:#4ade80;font-weight:800}}
.s-race .s-naam{{color:#fff;font-weight:800}}
.s-tijd{{font-size:10px;color:rgba(255,255,255,.3);white-space:nowrap}}
.s-next .s-tijd{{color:rgba(255,215,0,.5)}}

/* ── FILTER ── */
.filter-bar{{display:flex;gap:8px;padding:12px 28px;background:rgba(0,0,0,.2);border-bottom:1px solid rgba(255,255,255,.05);overflow-x:auto;scrollbar-width:none}}
.filter-bar::-webkit-scrollbar{{display:none}}
.filter-btn{{flex-shrink:0;padding:6px 16px;border-radius:20px;border:1px solid rgba(255,255,255,.1);background:transparent;color:rgba(255,255,255,.38);font-size:11px;font-weight:700;letter-spacing:.5px;cursor:pointer;transition:all .15s;text-transform:uppercase}}
.filter-btn:hover{{border-color:rgba(232,0,45,.5);color:rgba(255,255,255,.8)}}
.filter-btn.active{{background:#e8002d;border-color:#e8002d;color:#fff;box-shadow:0 0 16px rgba(232,0,45,.35)}}

/* ── NIEUWS ── */
.news-section{{padding:20px 28px 48px;max-width:960px;margin:0 auto}}
.section-label{{font-size:9px;font-weight:800;letter-spacing:2.5px;text-transform:uppercase;color:rgba(255,255,255,.18);margin-bottom:12px}}
.news-list{{display:flex;flex-direction:column;gap:8px}}
.news-card{{background:rgba(255,255,255,.03);border:1px solid rgba(255,255,255,.055);border-left:3px solid transparent;border-radius:10px;padding:14px 16px;display:grid;grid-template-columns:1fr auto;gap:12px;align-items:center;transition:all .15s;text-decoration:none;color:inherit}}
.news-card:hover{{background:rgba(255,255,255,.055);transform:translateX(3px)}}
.cat-f1-card{{border-left-color:#e8002d}}.cat-f1-card:hover{{box-shadow:-2px 0 16px rgba(232,0,45,.2)}}
.cat-gt-card{{border-left-color:#3b82f6}}.cat-gt-card:hover{{box-shadow:-2px 0 16px rgba(59,130,246,.2)}}
.cat-sim-card{{border-left-color:#a855f7}}.cat-sim-card:hover{{box-shadow:-2px 0 16px rgba(168,85,247,.2)}}
.card-meta{{display:flex;align-items:center;gap:6px;margin-bottom:5px;flex-wrap:wrap}}
.cat-tag{{font-size:9px;font-weight:800;padding:2px 7px;border-radius:20px;text-transform:uppercase;letter-spacing:1px}}
.cat-f1{{background:rgba(232,0,45,.15);color:#ff6b84;border:1px solid rgba(232,0,45,.2)}}
.cat-gt{{background:rgba(59,130,246,.15);color:#7dd3fc;border:1px solid rgba(59,130,246,.2)}}
.cat-sim{{background:rgba(168,85,247,.15);color:#d8b4fe;border:1px solid rgba(168,85,247,.2)}}
.cat-alg{{background:rgba(255,255,255,.05);color:#888;border:1px solid rgba(255,255,255,.1)}}
.card-source{{font-size:10px;color:rgba(255,255,255,.22)}}
.card-title{{font-size:14px;font-weight:700;color:rgba(255,255,255,.88);line-height:1.35;margin-bottom:4px}}
.card-summary{{font-size:12px;color:rgba(255,255,255,.34);line-height:1.55}}
.card-arrow{{color:rgba(255,255,255,.16);font-size:17px;transition:color .15s;flex-shrink:0}}
.news-card:hover .card-arrow{{color:#e8002d}}
.no-news{{text-align:center;padding:48px;color:rgba(255,255,255,.12);font-size:13px}}
.footer{{text-align:center;padding:0 0 32px;font-size:10px;color:rgba(255,255,255,.08);letter-spacing:.5px}}

/* ── RESPONSIVE ── */
@media(max-width:680px){{
  .header-img{{height:140px}}
  .title-bar{{padding:10px 14px;gap:10px}}
  .site-title{{font-size:19px}}
  .update-badge{{margin-left:0;width:100%}}
  .race-blok{{padding:14px 14px 18px}}
  .race-naam{{font-size:15px}}
  .race-flag{{font-size:26px}}
  .countdown-label{{text-align:left}}
  .countdown-blok{{width:100%}}
  .countdown{{justify-content:flex-start}}
  .cd-num{{font-size:20px}}
  .cd-unit{{min-width:44px;padding:5px 8px}}
  .circuit-info{{gap:5px}}
  .ci-item{{min-width:90px;padding:6px 10px}}
  .tijdlijn{{gap:4px}}
  .s-row{{min-width:110px;padding:6px 10px}}
  .filter-bar{{padding:8px 14px}}
  .news-section{{padding:14px 12px 32px}}
  .news-card{{padding:11px 13px}}
  .card-title{{font-size:13px}}
  .card-summary,.card-arrow{{display:none}}
}}
@media(max-width:380px){{
  .site-title{{font-size:16px}}
  .cd-num{{font-size:17px}}
  .card-summary{{display:none}}
}}
</style>
</head>
<body>

<div class="header">
  <div class="header-img"><img src="header.jpg" alt="Max Verstappen Racing"></div>
  <div class="track-line"></div>
  <div class="title-bar">
    <span class="eyebrow">Verstappen Racing Universe</span>
    <h1 class="site-title">Max <em>Verstappen</em> Nieuws</h1>
    <div class="update-badge">
      <div class="live-dot"></div>
      <span>Bijgewerkt {datum_nl} · 08:00 &amp; 18:00</span>
    </div>
  </div>
</div>

<div class="race-blok">
  <div class="race-header">
    <div class="race-flag">{race_vlag}</div>
    <div class="race-meta">
      <div class="race-label">Volgende Race</div>
      <div class="race-naam">{race_naam}</div>
      <div class="race-circuit">{race_circuit}</div>
      <div class="race-datum">🕐 Race: {race_datum}</div>
    </div>
    <div class="countdown-blok">
      <div class="countdown-label {'live' if vsessie_live else ''}" id="cd-label">{countdown_label}</div>
      <div class="countdown" id="countdown"></div>
    </div>
  </div>

  <div class="circuit-info">
    <div class="ci-item"><div class="ci-val">{lengte}</div><div class="ci-key">Rondelengte</div></div>
    <div class="ci-item"><div class="ci-val">{ronden}</div><div class="ci-key">Ronden</div></div>
    <div class="ci-item"><div class="ci-val">{record}</div><div class="ci-key">Ronderecord</div></div>
    <div class="ci-item"><div class="ci-val" style="font-size:10px;padding-top:2px">{record_door}</div><div class="ci-key">Door</div></div>
  </div>

  <div class="tijdlijn-label">Weekendschema — Amsterdam tijd</div>
  <div class="tijdlijn">{tijdlijn}</div>
</div>

<div class="filter-bar">
  <button class="filter-btn active" onclick="filter('alles',this)">🏁 Alles</button>
  <button class="filter-btn" onclick="filter('f1',this)">🔴 F1</button>
  <button class="filter-btn" onclick="filter('gt',this)">🔵 GT Racing</button>
  <button class="filter-btn" onclick="filter('sim',this)">🟣 Simracing</button>
  <button class="filter-btn" onclick="filter('alg',this)">⬛ Algemeen</button>
</div>

<div class="news-section">
  <div class="section-label">Actueel nieuws</div>
  <div class="news-list">{cards}</div>
</div>

<div class="footer">MAX VERSTAPPEN NIEUWS · DAGELIJKS 08:00 &amp; 18:00 AMSTERDAM TIJD</div>

<script>
(function(){{
  const target = new Date('{vsessie_iso}');
  const isLive = {'true' if vsessie_live else 'false'};
  const lbl = document.getElementById('cd-label');

  function tick(){{
    const diff = target - new Date();
    const el = document.getElementById('countdown');
    if(isLive || diff <= 0){{
      el.innerHTML = '<div class="cd-unit" style="border-color:rgba(34,197,94,.4)"><div class="cd-num" style="color:#22c55e;font-size:16px">LIVE</div><div class="cd-lbl">Nu bezig</div></div>';
      if(lbl) lbl.textContent = 'Nu live';
      return;
    }}
    const dd=Math.floor(diff/86400000),
          h=Math.floor(diff%86400000/3600000),
          m=Math.floor(diff%3600000/60000),
          s=Math.floor(diff%60000/1000);
    const u=(n,l)=>`<div class="cd-unit"><div class="cd-num">${{String(n).padStart(2,'0')}}</div><div class="cd-lbl">${{l}}</div></div>`;
    el.innerHTML = (dd>0?u(dd,'Dagen'):'') + u(h,'Uur') + u(m,'Min') + u(s,'Sec');
  }}
  tick(); setInterval(tick,1000);
}})();

function filter(cat,btn){{
  document.querySelectorAll('.filter-btn').forEach(b=>b.classList.remove('active'));
  btn.classList.add('active');
  document.querySelectorAll('.news-card').forEach(c=>{{
    c.style.display = (cat==='alles'||c.dataset.cat===cat) ? '' : 'none';
  }});
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
