"""Self-contained offline test suite for the Skicom project.

Runs two ways:

    # plain stdlib — no test runner required
    python tests/test_skicom.py

    # or, if pytest happens to be installed
    pytest tests/test_skicom.py

Every check is a plain ``assert`` inside a ``test_*`` function so pytest can
collect them, and the ``__main__`` block at the bottom discovers and runs the
same functions, printing PASS/FAIL per test and exiting non-zero on any
failure.

Only pure / offline logic is exercised — nothing here touches the network.
"""

import json
import os
import re
import sys

# Make the repo root importable so we can `import resorts`, `import weather`,
# etc. even though this file lives in the tests/ subdirectory.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import resorts
import weather
import renderer
import server
import accommodations


# ───────────────────────── helpers ─────────────────────────

# Keys that the project (and the task spec) treats as required on every record.
REQUIRED_RESORT_KEYS = (
    "name", "full_name", "state",
    "lat", "lon",
    "elevation_ft", "vertical_ft", "lifts",
    "region",
)


def _record_haystack(record):
    """Lower-cased concatenation of every string-ish value in a resort dict.

    Lets country/region assertions stay robust regardless of whether the
    catalog stores e.g. "Switzerland" under ``state``, ``country`` or
    ``region``.
    """
    parts = []
    for v in record.values():
        if isinstance(v, str):
            parts.append(v)
    return " ".join(parts).lower()


def _make_day(day_name="Monday", date="2026-01-05", high=30.0, low=15.0,
              snow=0.0, depth=0.0):
    """Build a single parsed-daily-forecast-shaped dict for chart tests.

    Mirrors the keys produced by weather.parse_daily_forecast / get_full_forecast
    that the renderer chart builders read.
    """
    return {
        "date": date,
        "date_short": "Jan 05",
        "day_name": day_name,
        "temp_high_f": high,
        "temp_low_f": low,
        "snowfall_in": snow,
        "snow_depth_in": depth,
    }


# ───────────────────────── 1. resort database ─────────────────────────

def test_load_resorts_shape():
    """load_resorts() returns >=500 dicts, each with the required keys, and
    every coordinate is in range."""
    data = resorts.load_resorts()
    assert isinstance(data, list), "load_resorts() must return a list"
    assert len(data) >= 500, "expected at least 500 resorts, got %d" % len(data)

    for r in data:
        assert isinstance(r, dict), "every record must be a dict"
        for key in REQUIRED_RESORT_KEYS:
            assert key in r, "record %r missing required key %r" % (
                r.get("full_name", "?"), key)
        lat, lon = r["lat"], r["lon"]
        assert -90 <= lat <= 90, "lat out of range for %r: %r" % (r["full_name"], lat)
        assert -180 <= lon <= 180, "lon out of range for %r: %r" % (r["full_name"], lon)


def test_no_duplicate_full_names():
    """full_name must be unique across the catalog."""
    data = resorts.load_resorts()
    names = [r["full_name"] for r in data]
    seen = set()
    dupes = set()
    for n in names:
        if n in seen:
            dupes.add(n)
        seen.add(n)
    assert not dupes, "duplicate full_name(s): %s" % sorted(dupes)


def test_load_resorts_cached():
    """load_resorts() memoizes and returns the same object on repeat calls."""
    assert resorts.load_resorts() is resorts.load_resorts()


def test_international_and_us_records():
    """find_resort resolves well-known international and US resorts."""
    vail = resorts.find_resort("Vail")
    assert vail is not None, "find_resort('Vail') returned None"
    assert "vail" in vail["full_name"].lower()

    zermatt = resorts.find_resort("Zermatt")
    assert zermatt is not None, "find_resort('Zermatt') returned None"
    assert "switzerland" in _record_haystack(zermatt), \
        "Zermatt should resolve to Switzerland, got %r" % zermatt

    niseko = resorts.find_resort("Niseko")
    assert niseko is not None, "find_resort('Niseko') returned None"
    assert "japan" in _record_haystack(niseko), \
        "Niseko should resolve to Japan, got %r" % niseko


def test_southern_hemisphere_present():
    """At least one resort sits below the equator (negative latitude)."""
    data = resorts.load_resorts()
    assert any(r["lat"] < 0 for r in data), \
        "expected at least one Southern-Hemisphere resort with lat < 0"


# ───────────────────────── 2. search + state hints ─────────────────────────

def test_search_resort_ranked():
    """search_resort returns a ranked list of dicts carrying match_score."""
    results = resorts.search_resort("Vail", limit=5)
    assert isinstance(results, list)
    assert 1 <= len(results) <= 5
    for r in results:
        assert isinstance(r, dict)
        assert "match_score" in r
        assert "full_name" in r
    # ranked == scores are non-increasing
    scores = [r["match_score"] for r in results]
    assert scores == sorted(scores, reverse=True), \
        "results should be ranked by descending match_score: %r" % scores


def test_parse_state_hint_full_name():
    """A trailing full state name is stripped and mapped to its abbreviation."""
    cleaned, state = resorts._parse_state_hint("crystal mountain washington")
    assert state == "WA", "expected WA, got %r" % state
    assert cleaned.lower() == "crystal mountain", "unexpected cleaned query %r" % cleaned


def test_parse_state_hint_abbrev():
    """A trailing ', ST' abbreviation is stripped and recognized."""
    cleaned, state = resorts._parse_state_hint("white pass, WA")
    assert state == "WA", "expected WA, got %r" % state
    assert cleaned.lower() == "white pass", "unexpected cleaned query %r" % cleaned


def test_parse_state_hint_none():
    """No state hint -> the query is returned unchanged with None."""
    cleaned, state = resorts._parse_state_hint("Vail")
    assert state is None
    assert cleaned == "Vail"


def test_search_respects_state_hint():
    """A state hint must not break search, and must bias ranking toward the
    hinted state.

    The code parses 'washington' -> WA and applies a +30 score boost to WA
    candidates (and a -15 penalty to others). We verify the hinted query still
    returns matches and that a WA candidate is ranked ahead of where it lands
    without the hint."""
    hinted = resorts.search_resort("crystal mountain washington", limit=8)
    assert hinted, "expected at least one match for a WA-hinted query"

    def first_wa_rank(results):
        for i, r in enumerate(results):
            if r.get("state") == "WA":
                return i
        return None

    rank_hinted = first_wa_rank(hinted)
    assert rank_hinted is not None, \
        "a Washington resort should appear among results for a WA-hinted query"

    plain = resorts.search_resort("crystal mountain", limit=8)
    rank_plain = first_wa_rank(plain)
    # The hint should pull a WA result no further down the list than the
    # un-hinted query would (and usually to the very top).
    if rank_plain is not None:
        assert rank_hinted <= rank_plain, (
            "state hint should not demote the WA match: %d (hinted) vs %d (plain)"
            % (rank_hinted, rank_plain)
        )


# ───────────────────────── 3. weather logic ─────────────────────────

def test_compute_snow_summary():
    """compute_snow_summary aggregates total / snow-day count / best day."""
    days = [
        _make_day(day_name="Monday", snow=0.0),
        _make_day(day_name="Tuesday", snow=3.0),
        _make_day(day_name="Wednesday", snow=7.5),
        _make_day(day_name="Thursday", snow=0.0),
        _make_day(day_name="Friday", snow=1.2),
    ]
    summary = weather.compute_snow_summary(days)
    # total = 3.0 + 7.5 + 1.2 = 11.7
    assert summary["total_snowfall_in"] == 11.7, summary["total_snowfall_in"]
    assert summary["snow_days_count"] == 3, summary["snow_days_count"]
    best = summary["best_powder_day"]
    assert best is not None
    assert best["day_name"] == "Wednesday", best["day_name"]
    assert best["snowfall_in"] == 7.5


def test_compute_snow_summary_empty():
    """An empty forecast produces zeros and no best day."""
    summary = weather.compute_snow_summary([])
    assert summary["total_snowfall_in"] == 0
    assert summary["snow_days_count"] == 0
    assert summary["best_powder_day"] is None


def test_extract_snow_depth_meters_to_inches():
    """Hourly snow_depth (meters) -> max positive value, converted to inches.

    With resort=None the elevation tolerance / base-vs-summit logic is skipped,
    so the value lands in base_depth_in. round(1.2 * 39.37) == 47.
    """
    raw = {"hourly": {"snow_depth": [0.5, 1.2, None, 0.8, 0.0]}}
    out = weather.extract_snow_depth(raw, resort=None)
    expected = round(1.2 * 39.37)  # == 47
    assert out["base_depth_in"] == expected, out
    assert out["summit_depth_in"] is None, out
    assert out["depth_source_ft"] == 0, out  # no elevation supplied -> 0


def test_extract_snow_depth_no_positive():
    """No positive depth reading -> base_depth_in (and summit) is None."""
    raw = {"hourly": {"snow_depth": [0.0, 0.0, None, 0.0]}}
    out = weather.extract_snow_depth(raw, resort=None)
    assert out["base_depth_in"] is None, out
    assert out["summit_depth_in"] is None, out


def test_extract_snow_depth_missing_hourly():
    """A raw dict with no hourly data degrades gracefully to None depths."""
    out = weather.extract_snow_depth({}, resort=None)
    assert out["base_depth_in"] is None
    assert out["summit_depth_in"] is None


def test_parse_daily_forecast():
    """parse_daily_forecast turns a raw Open-Meteo 'daily' block into clean rows."""
    raw = {
        "daily": {
            "time": ["2026-01-05", "2026-01-06"],
            "temperature_2m_max": [30.0, 28.0],
            "temperature_2m_min": [12.0, 10.0],
            "precipitation_sum": [0.1, 0.0],
            "snowfall_sum": [2.0, 0.0],
            "precipitation_probability_max": [80, 10],
            "wind_speed_10m_max": [15.0, 9.0],
            "wind_gusts_10m_max": [25.0, 14.0],
            "weather_code": [73, 0],
        }
    }
    rows = weather.parse_daily_forecast(raw)
    assert len(rows) == 2
    first = rows[0]
    assert first["date"] == "2026-01-05"
    assert first["temp_high_f"] == 30.0
    assert first["temp_low_f"] == 12.0
    assert first["snowfall_in"] == 2.0
    assert first["weather_code"] == 73
    # day_name should be a weekday string; date_short non-empty
    assert isinstance(first["day_name"], str) and first["day_name"]
    assert isinstance(first["date_short"], str) and first["date_short"]


# ───────────────────────── 4. SVG chart builders ─────────────────────────

def _multi_days():
    return [
        _make_day(day_name="Monday", high=30, low=15, snow=2.0, depth=10.0),
        _make_day(day_name="Tuesday", high=28, low=12, snow=0.0, depth=12.0),
        _make_day(day_name="Wednesday", high=33, low=18, snow=5.0, depth=18.0),
    ]


def test_temp_chart_normal():
    svg = renderer._build_temp_chart_svg(_multi_days())
    assert svg.startswith("<svg"), "temp chart should start with <svg"


def test_temp_chart_empty():
    assert renderer._build_temp_chart_svg([]) == ""


def test_temp_chart_single_day():
    """A single day is not enough to draw a trend -> empty string."""
    assert renderer._build_temp_chart_svg([_make_day()]) == ""


def test_snow_chart_normal():
    svg = renderer._build_snow_chart_svg(_multi_days())
    assert svg.startswith("<svg"), "snow chart should start with <svg"


def test_snow_chart_empty():
    assert renderer._build_snow_chart_svg([]) == ""


def test_depth_chart_normal():
    svg = renderer._build_depth_chart_svg(_multi_days())
    assert svg.startswith("<svg"), "depth chart should start with <svg"


def test_depth_chart_empty():
    assert renderer._build_depth_chart_svg([]) == ""


def test_depth_chart_all_zero():
    """All-zero snow depth -> nothing to plot -> empty string."""
    zero_days = [
        _make_day(day_name="Monday", depth=0.0),
        _make_day(day_name="Tuesday", depth=0.0),
        _make_day(day_name="Wednesday", depth=0.0),
    ]
    assert renderer._build_depth_chart_svg(zero_days) == ""


# ───────────────────────── 5. server home page ─────────────────────────

def test_home_page_tokens_replaced():
    """_home_page() returns bytes with both injection tokens replaced."""
    page = server._home_page()
    assert isinstance(page, bytes), "_home_page() should return bytes"
    html = page.decode("utf-8")
    assert "__RESORTS_JSON__" not in html, "RESORTS placeholder not replaced"
    assert "__FEATURED_JSON__" not in html, "FEATURED placeholder not replaced"
    assert "var RESORTS = [" in html and "var FEATURED = [" in html


def test_home_page_json_parses_and_matches_count():
    """The injected RESORTS array parses and matches the catalog size; the
    FEATURED array is a non-empty subset."""
    html = server._home_page().decode("utf-8")
    mr = re.search(r"var RESORTS = (\[.*?\]);", html, re.DOTALL)
    mf = re.search(r"var FEATURED = (\[.*?\]);", html, re.DOTALL)
    assert mr and mf, "could not locate RESORTS / FEATURED array assignments"
    resorts_arr = json.loads(mr.group(1))
    featured_arr = json.loads(mf.group(1))
    assert len(resorts_arr) == len(resorts.load_resorts())
    assert 0 < len(featured_arr) <= len(resorts_arr), "featured should be a non-empty subset"


def test_featured_is_curated_subset():
    """server._featured() returns curated marquee resorts that exist in the DB."""
    feat = server._featured()
    assert 8 <= len(feat) <= len(server._FEATURED_QUERIES)
    names = {r["full_name"] for r in resorts.load_resorts()}
    assert all(f["full_name"] in names for f in feat)


# ───────────────────────── 6. accommodations mirrors ─────────────────────────

def test_overpass_mirrors():
    """At least two Overpass mirrors are configured for failover."""
    assert isinstance(accommodations.OVERPASS_URLS, (list, tuple))
    assert len(accommodations.OVERPASS_URLS) >= 2, \
        "expected >=2 Overpass mirrors, got %d" % len(accommodations.OVERPASS_URLS)


# ───────────────────────── 7. home-page coordinates + map ─────────────────────────

def test_card_fields_include_latlon():
    """_CARD_FIELDS must carry the coordinates (the map needs them) plus the
    display essentials the cards render."""
    fields = server._CARD_FIELDS
    for key in ("lat", "lon", "full_name", "region"):
        assert key in fields, "_CARD_FIELDS missing %r: %r" % (key, fields)


def test_home_payload_has_coordinates():
    """The injected RESORTS array carries valid numeric coordinates for every
    resort, and matches the catalog size — the map plots one marker each."""
    html = server._home_page().decode("utf-8")
    mr = re.search(r"var RESORTS = (\[.*?\]);", html, re.DOTALL)
    assert mr, "could not locate the RESORTS array assignment"
    arr = json.loads(mr.group(1))
    assert len(arr) == len(resorts.load_resorts()), \
        "RESORTS payload size %d != catalog size" % len(arr)
    for r in arr:
        assert "lat" in r and "lon" in r, "payload record missing lat/lon: %r" % r
        lat, lon = r["lat"], r["lon"]
        assert isinstance(lat, (int, float)) and not isinstance(lat, bool), \
            "lat must be numeric for %r: %r" % (r.get("full_name", "?"), lat)
        assert isinstance(lon, (int, float)) and not isinstance(lon, bool), \
            "lon must be numeric for %r: %r" % (r.get("full_name", "?"), lon)
        assert -90 <= lat <= 90, "lat out of range for %r: %r" % (r.get("full_name", "?"), lat)
        assert -180 <= lon <= 180, "lon out of range for %r: %r" % (r.get("full_name", "?"), lon)


def test_home_includes_leaflet():
    """The home page loads Leaflet for the map view."""
    html = server._home_page().decode("utf-8")
    assert "leaflet" in html.lower(), "home page should reference Leaflet for the map"


def test_featured_subset():
    """_featured() is a non-empty subset of the catalog, no larger than the
    curated query list."""
    feat = server._featured()
    assert isinstance(feat, list) and feat, "_featured() should be a non-empty list"
    assert len(feat) <= len(server._FEATURED_QUERIES), \
        "featured list longer than the curated query list"
    names = {r["full_name"] for r in resorts.load_resorts()}
    for f in feat:
        assert f["full_name"] in names, \
            "featured resort %r not in the catalog" % f.get("full_name", "?")


def test_summary_to_html():
    """_summary_to_html renders bold + paragraph blocks, and _escape neutralizes
    angle brackets / ampersands."""
    html = server._summary_to_html("**Hi**\n\npara two")
    assert "<strong>Hi</strong>" in html, "bold markdown should become <strong>: %r" % html
    assert html.count("<p>") == 2, "expected two <p> blocks, got %r" % html

    escaped = server._escape("<a> & 'x'")
    assert "<a>" not in escaped, "raw <a> should be escaped: %r" % escaped
    assert "&lt;" in escaped and "&gt;" in escaped and "&amp;" in escaped, \
        "expected <, >, & to be escaped: %r" % escaped


def test_empty_forecast_shape():
    """EMPTY_FORECAST is the offline fallback shape the pipeline relies on."""
    ef = server.EMPTY_FORECAST
    assert isinstance(ef.get("daily"), list), "EMPTY_FORECAST['daily'] must be a list"
    summary = ef.get("snow_summary")
    assert isinstance(summary, dict), "EMPTY_FORECAST['snow_summary'] must be a dict"
    assert "total_snowfall_in" in summary, "snow_summary missing total_snowfall_in"
    assert "snow_days_count" in summary, "snow_summary missing snow_days_count"


# ───────────────────────── plain-python runner ─────────────────────────

def _run_all():
    """Discover and run every test_* function in this module.

    Prints PASS/FAIL per test and returns the number of failures so the
    process can exit non-zero when something breaks. Used only when this file
    is executed directly (pytest collects the test_* functions itself).
    """
    mod = sys.modules[__name__]
    tests = sorted(
        (name, obj)
        for name, obj in vars(mod).items()
        if name.startswith("test_") and callable(obj)
    )
    failures = 0
    print("Running %d Skicom tests\n" % len(tests))
    for name, fn in tests:
        try:
            fn()
        except Exception as e:  # noqa: BLE001 - report any failure verbatim
            failures += 1
            print("FAIL  %s\n        %s: %s" % (name, type(e).__name__, e))
        else:
            print("PASS  %s" % name)
    print("\n%d passed, %d failed" % (len(tests) - failures, failures))
    return failures


if __name__ == "__main__":
    sys.exit(1 if _run_all() else 0)
