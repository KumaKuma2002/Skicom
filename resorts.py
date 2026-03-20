"""Ski resort database with fuzzy name matching."""

import json
import os
import re
from thefuzz import fuzz, process

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "us_resorts.json")

US_STATES = {
    "AL","AK","AZ","AR","CA","CO","CT","DE","FL","GA","HI","ID","IL","IN","IA",
    "KS","KY","LA","ME","MD","MA","MI","MN","MS","MO","MT","NE","NV","NH","NJ",
    "NM","NY","NC","ND","OH","OK","OR","PA","RI","SC","SD","TN","TX","UT","VT",
    "VA","WA","WV","WI","WY","BC","AB","ON","QC",
}

STATE_NAMES = {
    "alabama":"AL","alaska":"AK","arizona":"AZ","arkansas":"AR","california":"CA",
    "colorado":"CO","connecticut":"CT","delaware":"DE","florida":"FL","georgia":"GA",
    "hawaii":"HI","idaho":"ID","illinois":"IL","indiana":"IN","iowa":"IA","kansas":"KS",
    "kentucky":"KY","louisiana":"LA","maine":"ME","maryland":"MD","massachusetts":"MA",
    "michigan":"MI","minnesota":"MN","mississippi":"MS","missouri":"MO","montana":"MT",
    "nebraska":"NE","nevada":"NV","new hampshire":"NH","new jersey":"NJ","new mexico":"NM",
    "new york":"NY","north carolina":"NC","north dakota":"ND","ohio":"OH","oklahoma":"OK",
    "oregon":"OR","pennsylvania":"PA","rhode island":"RI","south carolina":"SC",
    "south dakota":"SD","tennessee":"TN","texas":"TX","utah":"UT","vermont":"VT",
    "virginia":"VA","washington":"WA","west virginia":"WV","wisconsin":"WI","wyoming":"WY",
}

_cache = None


def load_resorts() -> list[dict]:
    global _cache
    if _cache is None:
        with open(DATA_PATH, "r") as f:
            _cache = json.load(f)
    return _cache


def _parse_state_hint(query: str) -> tuple[str, str | None]:
    """Extract an optional state hint from the query.

    Handles: 'white pass, WA', 'white pass WA', 'crystal mountain washington'
    Returns (cleaned_query, state_abbr_or_none).
    """
    q = query.strip()

    # "resort, ST" or "resort ST" at the end
    m = re.search(r'[,\s]+([A-Za-z]{2})$', q)
    if m:
        candidate = m.group(1).upper()
        if candidate in US_STATES:
            return q[:m.start()].strip(), candidate

    # Full state name at the end: "crystal mountain washington"
    q_lower = q.lower()
    for name, abbr in sorted(STATE_NAMES.items(), key=lambda x: -len(x[0])):
        if q_lower.endswith(name):
            return q[:-(len(name))].strip().rstrip(",").strip(), abbr

    return q, None


def search_resort(query: str, limit: int = 5) -> list[dict]:
    """Return the top matching resorts for a given query string."""
    resorts = load_resorts()
    clean_query, state_hint = _parse_state_hint(query)

    # Build candidate pool — if state hint given, prefer that state
    candidates = {}
    for r in resorts:
        key = (r["full_name"], r["state"])
        if key not in candidates:
            candidates[key] = r

    # Build searchable name lists including aliases
    name_to_keys: dict[str, list[tuple[str, str]]] = {}
    for (full_name, state), r in candidates.items():
        for n in [r["name"], r["full_name"]] + r.get("aliases", []):
            name_to_keys.setdefault(n, []).append((full_name, state))

    all_names = list(name_to_keys.keys())

    results_map: dict[tuple[str, str], int] = {}

    for scorer in (fuzz.token_sort_ratio, fuzz.partial_ratio):
        matches = process.extract(clean_query, all_names, scorer=scorer, limit=limit * 3)
        for item in matches:
            matched_name, score = item[0], item[1]
            for key in name_to_keys[matched_name]:
                _, st = key
                adjusted = score
                if state_hint and st == state_hint:
                    adjusted += 30
                elif state_hint and st != state_hint:
                    adjusted -= 15
                if key not in results_map or adjusted > results_map[key]:
                    results_map[key] = adjusted

    ranked = sorted(results_map.items(), key=lambda x: x[1], reverse=True)

    seen = set()
    results = []
    for key, score in ranked:
        full_name, state = key
        if full_name not in seen:
            seen.add(full_name)
            results.append({**candidates[key], "match_score": min(score, 100)})
        if len(results) >= limit:
            break

    return results


def find_resort(query: str) -> dict | None:
    """Return the single best matching resort or None."""
    results = search_resort(query, limit=1)
    return results[0] if results else None
