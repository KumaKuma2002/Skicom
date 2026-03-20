#!/usr/bin/env python3
"""
Skicom — Cozy ski resort companion.

Look up any ski resort by name and get trail maps, snow forecasts,
nearby accommodations, and an optional AI-powered trip summary,
all wrapped in a warm Nordic-styled HTML report.

Usage:
    python skicom.py                      # interactive prompt
    python skicom.py "Vail"               # direct search
    python skicom.py --config my.yaml     # custom config
"""

import argparse
import os
import sys
import webbrowser

import yaml

from resorts import search_resort, find_resort
from weather import get_full_forecast
from accommodations import fetch_accommodations
from llm import generate_summary
from renderer import render_report

BANNER = r"""
   _____ __   _
  / ___// /__(_)________  ____ ___
  \__ \/ //_/ / ___/ __ \/ __ `__ \
 ___/ / ,< / / /__/ /_/ / / / / / /
/____/_/|_/_/\___/\____/_/ /_/ /_/

       ⛷  Your ski companion  🏔️
"""


def load_config(path: str = "config.yaml") -> dict:
    if os.path.exists(path):
        with open(path, "r") as f:
            return yaml.safe_load(f) or {}
    example = os.path.join(os.path.dirname(path) or ".", "config.example.yaml")
    if os.path.exists(example) and path == "config.yaml":
        print("  ℹ No config.yaml found. Run: cp config.example.yaml config.yaml")
        print("    (LLM summary will be skipped)\n")
    return {}


def interactive_search() -> dict | None:
    """Prompt user to search and select a resort."""
    query = input("\n  🔍 Enter ski resort name: ").strip()
    if not query:
        return None

    results = search_resort(query, limit=5)
    if not results:
        print("  No resorts found. Try a different name.")
        return None

    if results[0]["match_score"] >= 95:
        resort = results[0]
        print(f"\n  ✓ Found: {resort['full_name']}, {resort['state']}")
        return resort

    print("\n  Did you mean:\n")
    for i, r in enumerate(results, 1):
        print(f"    [{i}] {r['full_name']}, {r['state']}  (match: {r['match_score']}%)")
    print(f"    [0] Search again\n")

    while True:
        choice = input("  Pick a number: ").strip()
        if choice == "0":
            return interactive_search()
        try:
            idx = int(choice) - 1
            if 0 <= idx < len(results):
                return results[idx]
        except ValueError:
            pass
        print("  Invalid choice, try again.")


def run(query: str | None = None, config_path: str = "config.yaml"):
    print(BANNER)
    config = load_config(config_path)

    if query:
        resort = find_resort(query)
        if resort:
            print(f"  ✓ Best match: {resort['full_name']}, {resort['state']}")
        else:
            print(f"  ✗ No match for '{query}'")
            return
    else:
        resort = interactive_search()
        if not resort:
            return

    weather_days = config.get("weather", {}).get("forecast_days", 7)
    search_radius = config.get("accommodations", {}).get("search_radius_m", 15000)
    max_accom = config.get("accommodations", {}).get("max_results", 12)

    print(f"\n  ⏳ Fetching 7-day forecast for {resort['full_name']}...")
    try:
        forecast = get_full_forecast(resort["lat"], resort["lon"], days=weather_days)
        snow = forecast["snow_summary"]
        print(f"  ✓ Forecast loaded — {snow['total_snowfall_in']}\" snow expected, {snow['snow_days_count']} snow days")
    except Exception as e:
        print(f"  ⚠ Weather fetch failed: {e}")
        forecast = {"daily": [], "snow_summary": {"total_snowfall_in": 0, "snow_days_count": 0, "best_powder_day": None}, "timezone": "", "elevation_m": None}

    print(f"  ⏳ Searching for lodging within {search_radius / 1609.34:.0f} miles...")
    try:
        accommodations = fetch_accommodations(resort["lat"], resort["lon"], radius_m=search_radius, max_results=max_accom)
        print(f"  ✓ Found {len(accommodations)} nearby accommodation{'s' if len(accommodations) != 1 else ''}")
    except Exception as e:
        print(f"  ⚠ Accommodation search failed: {e}")
        accommodations = []

    summary = None
    if config.get("llm", {}).get("enabled", False):
        print("  ⏳ Generating AI trip summary...")
        summary = generate_summary(resort, forecast, accommodations, config)
        if summary:
            print("  ✓ AI summary generated")
        else:
            print("  ⚠ AI summary unavailable")

    print("  ⏳ Rendering report...")
    html_path, txt_path = render_report(resort, forecast, accommodations, summary, config)
    abs_html = os.path.abspath(html_path)
    abs_txt = os.path.abspath(txt_path)
    print(f"\n  ✅ HTML report: {abs_html}")
    print(f"  ✅ Text report: {abs_txt}")

    if config.get("output", {}).get("auto_open", True):
        print("  🌐 Opening in browser...")
        webbrowser.open(f"file://{abs_html}")

    print()


def main():
    parser = argparse.ArgumentParser(
        description="Skicom — Cozy ski resort companion",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("resort", nargs="?", help="Ski resort name to search for")
    parser.add_argument("--config", "-c", default="config.yaml", help="Path to config YAML (default: config.yaml)")
    parser.add_argument("--no-open", action="store_true", help="Don't auto-open the report in browser")
    args = parser.parse_args()

    if args.no_open:
        config = load_config(args.config)
        config.setdefault("output", {})["auto_open"] = False
        tmp_cfg = "__skicom_tmp_cfg.yaml"
        with open(tmp_cfg, "w") as f:
            yaml.dump(config, f)
        try:
            run(query=args.resort, config_path=tmp_cfg)
        finally:
            if os.path.exists(tmp_cfg):
                os.remove(tmp_cfg)
    else:
        run(query=args.resort, config_path=args.config)


if __name__ == "__main__":
    main()
