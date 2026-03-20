"""Find nearby accommodations via OpenStreetMap Overpass API."""

import requests
import math

OVERPASS_URL = "https://overpass-api.de/api/interpreter"


def fetch_accommodations(lat: float, lon: float, radius_m: int = 15000, max_results: int = 12) -> list[dict]:
    """Query OSM Overpass for hotels, lodges, chalets, hostels near coordinates."""
    query = f"""
    [out:json][timeout:25];
    (
      node["tourism"="hotel"](around:{radius_m},{lat},{lon});
      node["tourism"="chalet"](around:{radius_m},{lat},{lon});
      node["tourism"="alpine_hut"](around:{radius_m},{lat},{lon});
      node["tourism"="hostel"](around:{radius_m},{lat},{lon});
      node["tourism"="guest_house"](around:{radius_m},{lat},{lon});
      node["tourism"="motel"](around:{radius_m},{lat},{lon});
      way["tourism"="hotel"](around:{radius_m},{lat},{lon});
      way["tourism"="chalet"](around:{radius_m},{lat},{lon});
      way["tourism"="alpine_hut"](around:{radius_m},{lat},{lon});
      way["tourism"="hostel"](around:{radius_m},{lat},{lon});
      way["tourism"="guest_house"](around:{radius_m},{lat},{lon});
      way["tourism"="motel"](around:{radius_m},{lat},{lon});
    );
    out center body;
    """
    resp = requests.post(OVERPASS_URL, data={"data": query}, timeout=30)
    resp.raise_for_status()
    data = resp.json()

    accommodations = []
    seen_names = set()

    for elem in data.get("elements", []):
        tags = elem.get("tags", {})
        name = tags.get("name")
        if not name or name in seen_names:
            continue
        seen_names.add(name)

        a_lat = elem.get("lat") or elem.get("center", {}).get("lat")
        a_lon = elem.get("lon") or elem.get("center", {}).get("lon")
        if not a_lat or not a_lon:
            continue

        dist = _haversine(lat, lon, a_lat, a_lon)
        tourism_type = tags.get("tourism", "hotel")

        accommodations.append({
            "name": name,
            "type": _friendly_type(tourism_type),
            "type_icon": _type_icon(tourism_type),
            "lat": a_lat,
            "lon": a_lon,
            "distance_mi": round(dist, 1),
            "proximity_tag": _proximity_tag(dist),
            "phone": tags.get("phone", ""),
            "website": tags.get("website", ""),
            "stars": tags.get("stars", ""),
            "addr": _build_address(tags),
        })

    accommodations.sort(key=lambda a: a["distance_mi"])
    return accommodations[:max_results]


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Distance between two points in miles."""
    R = 3958.8
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2
    )
    return R * 2 * math.asin(math.sqrt(a))


def _build_address(tags: dict) -> str:
    parts = []
    for key in ("addr:housenumber", "addr:street", "addr:city", "addr:state"):
        if tags.get(key):
            parts.append(tags[key])
    return ", ".join(parts) if parts else ""


def _proximity_tag(distance_mi: float) -> str:
    """Return a proximity label for lodging near the resort."""
    if distance_mi <= 0.5:
        return "onsite"
    if distance_mi <= 1.5:
        return "slopeside"
    return ""


def _friendly_type(tourism: str) -> str:
    return {
        "hotel": "Hotel",
        "chalet": "Chalet",
        "alpine_hut": "Alpine Hut",
        "hostel": "Hostel",
        "guest_house": "Guest House",
        "motel": "Motel",
    }.get(tourism, tourism.replace("_", " ").title())


def _type_icon(tourism: str) -> str:
    return {
        "hotel": "🏨",
        "chalet": "🏔️",
        "alpine_hut": "🛖",
        "hostel": "🛏️",
        "guest_house": "🏡",
        "motel": "🏩",
    }.get(tourism, "🏠")
