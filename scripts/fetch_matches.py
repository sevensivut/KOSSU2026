#!/usr/bin/env python3
"""
fetch_matches.py  —  KOSSU 2026 data fetcher
Reads CSV predictions, fetches live results from Bzzoiro (paginated),
merges them, and writes data/matches.json.
"""

import csv
import json
import os
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
BZZOIRO_KEY  = os.environ.get("BZZOIRO_KEY", "").strip()
BASE_URL     = "https://sports.bzzoiro.com/api/v2/events/"
PARAMS       = "date_from=2026-06-11&date_to=2026-06-28&league_id=27&limit=100"
OUTPUT_FILE  = Path("data/matches.json")
PLAYERS      = ["Markus","Juuso","Pera","Lari","Erno","Elmo",
                "Petri","Tommi","Severi","Matti H","Pasi","Matti K"]

# ---------------------------------------------------------------------------
# Finnish → English team names (matches what the CSV encodes)
# ---------------------------------------------------------------------------
FI_TO_EN = {
    "Meksiko": "Mexico",
    "Etelä-Afrikka": "South Africa",
    "Etelä-Korea": "South Korea",
    "Tšekki": "Czech Republic",
    "Kanada": "Canada",
    "Bosnia ja Hertsegovina": "Bosnia and Herzegovina",
    "USA": "United States",
    "Paraguay": "Paraguay",
    "Qatar": "Qatar",
    "Sveitsi": "Switzerland",
    "Brasilia": "Brazil",
    "Marokko": "Morocco",
    "Haiti": "Haiti",
    "Skotlanti": "Scotland",
    "Australia": "Australia",
    "Turkki": "Turkey",
    "Saksa": "Germany",
    "Curaçao": "Curacao",
    "Hollanti": "Netherlands",
    "Japani": "Japan",
    "Norsunluurannikko": "Ivory Coast",
    "Ecuador": "Ecuador",
    "Ruotsi": "Sweden",
    "Tunisia": "Tunisia",
    "Espanja": "Spain",
    "Kap Verde": "Cape Verde",
    "Belgia": "Belgium",
    "Egypti": "Egypt",
    "Saudi-Arabia": "Saudi Arabia",
    "Uruguay": "Uruguay",
    "Iran": "Iran",
    "Uusi-Seelanti": "New Zealand",
    "Ranska": "France",
    "Senegal": "Senegal",
    "Irak": "Iraq",
    "Norja": "Norway",
    "Argentiina": "Argentina",
    "Algeria": "Algeria",
    "Itävalta": "Austria",
    "Jordania": "Jordan",
    "Portugali": "Portugal",
    "Kongon dem. tasavalta": "Congo DR",
    "Kongon dem. tv": "Congo DR",
    "Englanti": "England",
    "Kroatia": "Croatia",
    "Ghana": "Ghana",
    "Panama": "Panama",
    "Uzbekistan": "Uzbekistan",
    "Kolumbia": "Colombia",
}

# Bzzoiro English name → canonical English name used in this file
BZZOIRO_FIX = {
    "Bosnia & Herzegovina": "Bosnia and Herzegovina",
    "Cabo Verde":           "Cape Verde",
    "Côte d'Ivoire":        "Ivory Coast",
    "DR Congo":             "Congo DR",
    "Czechia":              "Czech Republic",
    "USA":                  "United States",
    "Türkiye":              "Turkey",
    "Curaçao":              "Curacao",
    "South Korea":          "South Korea",   # already correct, listed for clarity
}

STATUS_MAP = {
    "ft":         "FINISHED",
    "finished":   "FINISHED",
    "inprogress": "IN_PLAY",
    "live":       "IN_PLAY",
    "1h":         "IN_PLAY",
    "ht":         "IN_PLAY",
    "2h":         "IN_PLAY",
    "et":         "IN_PLAY",
    "notstarted": "SCHEDULED",
    "postponed":  "POSTPONED",
    "cancelled":  "CANCELLED",
}

# ---------------------------------------------------------------------------
# CSV parsing
# ---------------------------------------------------------------------------
def find_csv():
    for p in [Path("."), Path("data"), Path("scripts")]:
        for f in (p.glob("*.csv") if p.exists() else []):
            if "kossu" in f.name.lower() or "2026" in f.name:
                print(f"✅ CSV: {f}")
                return f
    print("❌ CSV not found", file=sys.stderr)
    return None

def parse_csv(csv_file):
    with open(csv_file, encoding="utf-8-sig") as f:
        rows = list(csv.reader(f))

    # Locate header row
    header_row = next((i for i, r in enumerate(rows) if "Pvm ja klo" in str(r)), None)
    if header_row is None:
        raise ValueError("CSV header not found")

    header = rows[header_row]

    # Locate weight columns
    def find_col(keyword):
        return next((i for i, c in enumerate(header) if keyword in str(c).lower()), None)

    w1 = find_col("painoarvo 1")
    w2 = find_col("painoarvo 2")
    wx = find_col("painoarvo x")
    print(f"📊 Weight cols: 1={w1}  2={w2}  X={wx}")

    matches = []
    for row in rows[header_row + 1:]:
        if len(row) < 5:
            continue
        date_cell = row[0].strip()
        if "." not in date_cell or "2026" not in date_cell:
            continue

        try:
            d_part, t_part = date_cell.split(" ", 1)
            day, mon, yr = d_part.split(".")
            date_iso = f"{yr}-{int(mon):02d}-{int(day):02d}T{t_part}:00Z"
        except Exception:
            continue

        home = row[1].strip() if len(row) > 1 else ""
        away = row[3].strip() if len(row) > 3 else ""
        if not home or not away:
            continue

        csv_result_raw = row[4].strip().upper() if len(row) > 4 else ""
        csv_result = csv_result_raw if csv_result_raw in ("1", "2", "X") else None

        def get_weight(idx):
            if idx is not None and idx < len(row):
                try:
                    return float(row[idx].strip())
                except ValueError:
                    pass
            return 0.0

        preds = {}
        for i, player in enumerate(PLAYERS):
            col = 6 + i
            if col < len(row):
                v = row[col].strip().upper()
                if v in ("1", "2", "X"):
                    preds[player] = v

        matches.append({
            "id":          len(matches) + 1,
            "date":        date_iso,
            "homeTeam":    home,
            "awayTeam":    away,
            "homeTeamEn":  FI_TO_EN.get(home, home),
            "awayTeamEn":  FI_TO_EN.get(away, away),
            "csv_result":  csv_result,
            "weight_1":    get_weight(w1),
            "weight_2":    get_weight(w2),
            "weight_x":    get_weight(wx),
            "predictions": preds,
            "score":       {"home": None, "away": None},
            "status":      "SCHEDULED",
            "result":      None,
        })

    print(f"✅ Parsed {len(matches)} matches from CSV")
    return matches

# ---------------------------------------------------------------------------
# Bzzoiro fetch (paginated)
# ---------------------------------------------------------------------------
def bzzoiro_name(raw):
    """Normalise a Bzzoiro team name to our canonical English name."""
    return BZZOIRO_FIX.get(raw, raw)

def fetch_bzzoiro():
    if not BZZOIRO_KEY:
        print("⚠️  BZZOIRO_KEY not set — skipping live fetch", file=sys.stderr)
        return []

    url = f"{BASE_URL}?{PARAMS}"
    all_results, page = [], 1

    while url:
        print(f"  Page {page}: {url}")
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Token {BZZOIRO_KEY}", "Accept": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                data = json.loads(r.read().decode())
        except urllib.error.HTTPError as e:
            raise RuntimeError(f"HTTP {e.code}: {e.read().decode()[:200]}")

        results = data.get("results", [])
        all_results.extend(results)
        print(f"    → {len(results)} items (total {len(all_results)}/{data.get('count','?')})")
        url = data.get("next")
        page += 1
        if url:
            time.sleep(0.3)

    return all_results

# ---------------------------------------------------------------------------
# Merge
# ---------------------------------------------------------------------------
def merge(csv_matches, bzzoiro_games):
    # Build lookup: canonical_english_home + "_" + canonical_english_away → game
    api_map = {}
    for g in bzzoiro_games:
        h = bzzoiro_name(g.get("home_team", ""))
        a = bzzoiro_name(g.get("away_team", ""))
        if not h or not a:
            continue
        api_map[f"{h}|{a}"] = g
        api_map[f"{a}|{h}"] = g   # reversed too

    matched, fallback = 0, 0

    for m in csv_matches:
        h_en = m["homeTeamEn"]
        a_en = m["awayTeamEn"]
        g = api_map.get(f"{h_en}|{a_en}")

        if g:
            matched += 1
            hs = g.get("home_score")
            as_ = g.get("away_score")
            raw_status = (g.get("status") or "").lower()
            status = STATUS_MAP.get(raw_status, "SCHEDULED")

            m["score"]  = {"home": int(hs) if hs is not None else None,
                           "away": int(as_) if as_ is not None else None}
            m["status"] = status

            if status == "FINISHED" and hs is not None and as_ is not None:
                hs, as_ = int(hs), int(as_)
                m["result"] = "1" if hs > as_ else ("2" if as_ > hs else "X")
            else:
                m["result"] = None
        else:
            # Fall back to CSV result if available
            fallback += 1
            if m["csv_result"]:
                m["result"] = m["csv_result"]
                m["status"] = "FINISHED"
                # Approximate score so the UI can show something
                if not any(m["score"].values()):
                    r = m["csv_result"]
                    m["score"] = {"home": (1 if r == "1" else 0),
                                  "away": (1 if r == "2" else 0)}

    print(f"🔗 Matched: {matched} from API, {fallback} from CSV fallback")
    return csv_matches

# ---------------------------------------------------------------------------
# Score calculation
# ---------------------------------------------------------------------------
def calc_scores(matches):
    scores = {p: 0.0 for p in PLAYERS}
    for m in matches:
        if m["status"] == "FINISHED" and m["result"]:
            r = m["result"]
            w = m.get(f"weight_{r.lower()}", 0.0)
            for p, pred in m.get("predictions", {}).items():
                if pred == r:
                    scores[p] = round(scores.get(p, 0.0) + w, 2)
    return scores

# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    print("🥃 KOSSU 2026 — fetch_matches.py")
    print("=" * 50)

    csv_file = find_csv()
    if not csv_file:
        sys.exit(1)

    csv_matches = parse_csv(csv_file)
    if not csv_matches:
        print("❌ No matches parsed from CSV", file=sys.stderr)
        sys.exit(1)

    try:
        bzzoiro_games = fetch_bzzoiro()
    except Exception as e:
        print(f"⚠️  Bzzoiro fetch failed: {e} — using CSV only", file=sys.stderr)
        bzzoiro_games = []

    merged   = merge(csv_matches, bzzoiro_games)
    scores   = calc_scores(merged)
    finished = sum(1 for m in merged if m["status"] == "FINISHED")
    live     = sum(1 for m in merged if m["status"] == "IN_PLAY")

    output = {
        "updatedAt":   datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "source":      "Bzzoiro Sports Data" if bzzoiro_games else "CSV only",
        "matchCount":  len(merged),
        "liveCount":   live,
        "players":     PLAYERS,
        "scores":      scores,
        "matches":     merged,
    }

    OUTPUT_FILE.parent.mkdir(exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, separators=(",", ":"))

    print(f"\n✅  data/matches.json — {finished} finished, {live} live, {len(merged)} total")
    print("\n📊 Scores:")
    for p, s in sorted(scores.items(), key=lambda x: -x[1]):
        print(f"  {p:12} {s:.1f}")

if __name__ == "__main__":
    main()
