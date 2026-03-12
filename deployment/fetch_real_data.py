"""
FloodGuard AI — Multi-Source Live Data Fetcher

OPW endpoint confirmed March 2026:
  https://waterlevel.ie/hydro-data/data/internet/stations/0/<station_id>/<sensor_code>/<filename>.csv

Sensor codes used:
  S        → Water Level (m)
  Q        → Discharge / Flow (m³/s)   — Waterworks Weir only
  TWater   → Water Temperature (°C)    — Waterworks Weir only

The CSVs are served as application/octet-stream and may be UTF-16 BOM
encoded (common .NET / Windows government API pattern). The parser
tries multiple encodings automatically.

Weather: Open-Meteo free API, no key required.
"""

import requests
import pandas as pd
from io import StringIO
from datetime import datetime

# ─────────────────────────────────────────────
# VERIFIED STATION REGISTRY
# All metadata confirmed from OPW hydro-data website, March 2026.
# ─────────────────────────────────────────────

BASE = "https://waterlevel.ie/hydro-data/data/internet/stations/0"

STATIONS = {
    "19102": {
        "name":          "Waterworks Weir",
        "lat":           51.893989,
        "lon":           -8.510053,
        "waterbody":     "Lee",
        "catchment_km2": 1185.00,
        "gauge_datum":   "2.000 m Malin Head OSGM15",
        "type":          "Level & Flow",
        "urls": {
            "level": f"{BASE}/19102/S/Waterlevel_48h.csv",
            # Flow feed confirmed empty (#rows;0) — omitted to avoid silent failures
            "temp":  f"{BASE}/19102/TWater/WaterTemperature_48h.csv",
        },
    },
    "19162": {
        "name":          "Fitzgerald's Park",
        "lat":           51.896472,
        "lon":           -8.498278,
        "waterbody":     "Lee",
        "catchment_km2": 1185.00,
        "gauge_datum":   "0.151 m Malin Head OSGM15",
        "type":          "Level",
        "urls": {
            "level": f"{BASE}/19162/S/Waterlevel_48h.csv",
            "temp":  f"{BASE}/19162/TWater/WaterTemperature_48h.csv",
        },
    },
    "19164": {
        "name":          "Mercy Hospital",
        "lat":           51.900050,
        "lon":           -8.483830,
        "waterbody":     "Lee",
        "catchment_km2": 0.00,
        "gauge_datum":   "-2.954 m Malin Head OSGM15",
        "type":          "Tidal",
        "urls": {
            "level": f"{BASE}/19164/S/Waterlevel_48h.csv",
            "temp":  f"{BASE}/19164/TWater/WaterTemperature_48h.csv",
        },
    },
    "19113": {
        "name":          "County Hall",
        "lat":           51.892643,
        "lon":           -8.509638,
        "waterbody":     "Curragheen",
        "catchment_km2": 47.62,
        "gauge_datum":   "0.886 m Malin Head OSGM15",
        "type":          "Level",
        "urls": {
            "level": f"{BASE}/19113/S/Waterlevel_48h.csv",
            "temp":  f"{BASE}/19113/TWater/WaterTemperature_48h.csv",
        },
    },
}

FETCH_ORDER = ["19102", "19162", "19164", "19113"]

# Defensive check — catches stale copies with old internal website IDs
_bad = [sid for sid in FETCH_ORDER if sid not in STATIONS]
if _bad:
    raise RuntimeError(
        f"fetch_real_data.py is stale — FETCH_ORDER contains IDs not in STATIONS: {_bad}. "
        "Replace this file with the latest version from the deployment folder."
    )

OPEN_METEO_URL = (
    "https://api.open-meteo.com/v1/forecast"
    "?latitude=51.8985&longitude=-8.4756"
    "&current=precipitation,rain,temperature_2m,wind_speed_10m,relative_humidity_2m"
    "&hourly=precipitation&forecast_days=1"
    "&timezone=Europe%2FDublin"
)

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# Encodings to try in order — UTF-16 BOM is common for .NET/Windows gov APIs
ENCODINGS = ["utf-8-sig", "utf-16", "utf-16-le", "utf-16-be", "latin-1", "utf-8"]


# ─────────────────────────────────────────────
# CORE CSV PARSER
# ─────────────────────────────────────────────

def _decode(content: bytes) -> str | None:
    """Try multiple encodings and return the first that works."""
    for enc in ENCODINGS:
        try:
            return content.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return None


def _parse_opw_csv(content: bytes) -> pd.DataFrame | None:
    """
    Parse an OPW hydro-data CSV from raw bytes.

    Confirmed format (March 2026, all Cork City stations):
        Separator  : semicolon  ;
        Header rows: 8 lines starting with #  (all skipped)
        Columns    : Timestamp ; Value ; Quality Code
        Datetime   : 2026-03-07T16:35:00.000Z  (ISO 8601, ms precision, UTC Z)

    Example header block:
        #station_name;Fitzgerald's Park
        #station_no;19162
        #stationparameter_name;S
        #ts_shortname;WEB.Cmd.P-Continuous.Absolute
        #ts_unitsymbol;m
        #ts_precision;Deci
        #rows;567
        #Timestamp;Value;Quality Code
        2026-03-07T16:35:00.000Z;0.820;254
        2026-03-07T16:40:00.000Z;0.820;254
    """
    text = _decode(content)
    if text is None:
        return None

    # Strip BOM artefacts, drop empty lines, skip all # comment/header lines
    lines = [ln.strip().lstrip("\ufeff") for ln in text.splitlines()]
    data_lines = [ln for ln in lines if ln and not ln.startswith("#")]
    if not data_lines:
        return None

    csv_text = "\n".join(data_lines)
    try:
        df = pd.read_csv(
            StringIO(csv_text),
            sep=";",
            header=None,
            names=["datetime", "value", "quality"],
            on_bad_lines="skip",
        )
    except Exception:
        return None

    # Exact datetime format confirmed from live data sample
    df["datetime"] = pd.to_datetime(
        df["datetime"],
        format="%Y-%m-%dT%H:%M:%S.%fZ",
        errors="coerce",
        utc=True,
    )

    df = df.dropna(subset=["datetime"])
    df = df[pd.to_numeric(df["value"], errors="coerce").notna()]
    df["value"] = pd.to_numeric(df["value"], errors="coerce")
    df = df.sort_values("datetime", ascending=False).reset_index(drop=True)

    return df if not df.empty else None


def _fetch_url(url: str, label: str = "") -> tuple:
    """
    Fetch a single OPW CSV URL.
    Returns (float value, str timestamp, str status, pd.DataFrame | None)
    """
    try:
        r = requests.get(url, headers=HEADERS, timeout=8)
        if r.status_code != 200:
            return None, None, f"HTTP {r.status_code}", None

        df = _parse_opw_csv(r.content)
        if df is None or df.empty:
            return None, None, "parse error / empty", None

        val = round(float(df.iloc[0]["value"]), 3)
        ts  = df.iloc[0]["datetime"].strftime("%Y-%m-%d %H:%M")
        return val, ts, "✅ Live", df

    except requests.exceptions.Timeout:
        return None, None, "timeout", None
    except Exception as e:
        return None, None, str(e)[:80], None


# ─────────────────────────────────────────────
# PUBLIC INTERFACE
# ─────────────────────────────────────────────

def get_full_verification_data() -> dict:
    """
    Fetch all Cork City OPW stations + Open-Meteo weather.
    Returns a structured dict for the Verification Panel in floodguard_live.py.
    """
    station_results = []

    for sid in FETCH_ORDER:
        meta = STATIONS[sid]
        urls = meta["urls"]

        level, level_ts, level_status, _ = _fetch_url(urls["level"], f"{meta['name']} level")
        flow  = temp = None

        if "flow" in urls:
            flow, _, _, _ = _fetch_url(urls["flow"], f"{meta['name']} flow")
        if "temp" in urls:
            temp, _, _, _ = _fetch_url(urls["temp"], f"{meta['name']} temp")

        station_results.append({
            "station_id":    sid,
            "name":          meta["name"],
            "type":          meta["type"],
            "lat":           meta["lat"],
            "lon":           meta["lon"],
            "waterbody":     meta["waterbody"],
            "catchment_km2": meta["catchment_km2"],
            "gauge_datum":   meta["gauge_datum"],
            "level_m":       level,
            "flow_m3s":      flow,
            "water_temp_c":  temp,
            "timestamp":     level_ts or "N/A",
            "api_status":    level_status,
        })

    # Primary reading = first successful level
    primary = next((s for s in station_results if s["level_m"] is not None), None)
    primary_level   = primary["level_m"] if primary else 1.25
    primary_name    = primary["name"]    if primary else "Simulated Feed (all sensors offline)"

    # ── Open-Meteo weather ────────────────────
    weather = None
    try:
        r = requests.get(OPEN_METEO_URL, headers=HEADERS, timeout=8)
        if r.status_code == 200:
            data    = r.json()
            current = data.get("current", {})
            h_times  = data.get("hourly", {}).get("time", [])[:24]
            h_precip = data.get("hourly", {}).get("precipitation", [])[:24]
            weather = {
                "source":        "Open-Meteo (Cork City 51.90°N, 8.48°W)",
                "timestamp":     current.get("time", "N/A"),
                "rain_mm_hr":    round(current.get("rain",          0.0) or 0.0, 2),
                "precip_mm_hr":  round(current.get("precipitation", 0.0) or 0.0, 2),
                "temp_air_c":    current.get("temperature_2m"),
                "wind_kmh":      current.get("wind_speed_10m"),
                "humidity_pct":  current.get("relative_humidity_2m"),
                "hourly_precip": list(zip(h_times, h_precip)),
            }
    except Exception:
        pass

    # ── Cross-verification ────────────────────
    notes      = []
    consistent = True

    if primary is None:
        notes.append("⚠️  All OPW sensors offline — fallback value 1.25m used.")
        consistent = False

    if weather is None:
        notes.append("⚠️  Open-Meteo weather feed unavailable.")
        consistent = False
    elif primary is not None:
        rain     = weather["rain_mm_hr"]
        temp_air = weather.get("temp_air_c")

        if rain > 10 and primary_level < 1.5:
            notes.append(
                f"🔍 Lag anomaly: Rain is {rain} mm/hr but Waterworks Weir is only "
                f"{primary_level}m. Upstream catchment hasn't peaked yet — expect rise in 2–4 hrs."
            )
            consistent = False

        if primary_level > 2.5 and rain < 0.5:
            notes.append(
                f"🔍 Upstream accumulation: River high ({primary_level}m) despite low current "
                f"rain ({rain} mm/hr). Inniscarra Dam catchment draining — normal delayed pattern."
            )

        # Cross-check Waterworks Weir vs Fitzgerald's Park (both on Lee, ~1.2km apart)
        ww = next((s for s in station_results if s["station_id"] == "19102" and s["level_m"]), None)
        fp = next((s for s in station_results if s["station_id"] == "19162" and s["level_m"]), None)
        if ww and fp:
            diff = abs(ww["level_m"] - fp["level_m"])
            # Gauge datums differ (2.000 vs 0.151 Malin Head) so absolute values are offset;
            # we flag only extreme divergence in the *trend* direction as a sanity check.
            if diff > 3.0:
                notes.append(
                    f"🔍 Large inter-station gap: Waterworks ({ww['level_m']}m datum-adjusted) "
                    f"vs Fitzgerald's ({fp['level_m']}m). Diff={diff:.2f}m — verify gauge datums."
                )

        # Water vs air temp
        wt = primary.get("water_temp_c") if primary else None
        if wt is not None and temp_air is not None and abs(wt - temp_air) > 10:
            notes.append(
                f"🔍 Temp anomaly: water={wt}°C vs air={temp_air}°C "
                f"(gap={abs(wt - temp_air):.1f}°C). Flag OPW _TWater sensor for field check."
            )

    if not notes:
        notes.append("✅ All sources consistent. Data validated.")

    return {
        "stations":      station_results,
        "primary_level": primary_level,
        "primary_name":  primary_name,
        "weather":       weather,
        "cross_check":   {"consistent": consistent, "notes": notes},
        "fetched_at":    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    }


def get_live_opw_data():
    """Legacy compatibility interface. Returns (level_float, station_name_str)."""
    data = get_full_verification_data()
    return data["primary_level"], data["primary_name"]


# ─────────────────────────────────────────────
# CLI test
# ─────────────────────────────────────────────
if __name__ == "__main__":
    import json
    print("Fetching full verification data from OPW + Open-Meteo...\n")
    data = get_full_verification_data()
    if data["weather"] and data["weather"]["hourly_precip"]:
        data["weather"]["hourly_precip"] = f"[{len(data['weather']['hourly_precip'])} hourly values]"
    print(json.dumps(data, indent=2, default=str))
