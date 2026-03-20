"""Weather and snow forecast via Open-Meteo (free, no API key)."""

import time
import requests
from datetime import datetime, timedelta

OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"
MAX_RETRIES = 3
RETRY_DELAY = 2


def fetch_forecast(lat: float, lon: float, days: int = 7) -> dict:
    """Fetch hourly and daily forecast for a ski resort location."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": ",".join([
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_sum",
            "snowfall_sum",
            "precipitation_probability_max",
            "wind_speed_10m_max",
            "wind_gusts_10m_max",
            "weather_code",
        ]),
        "hourly": ",".join([
            "temperature_2m",
            "snowfall",
            "snow_depth",
            "precipitation",
            "wind_speed_10m",
            "weather_code",
        ]),
        "temperature_unit": "fahrenheit",
        "wind_speed_unit": "mph",
        "precipitation_unit": "inch",
        "forecast_days": days,
        "timezone": "auto",
    }
    last_err = None
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.get(OPEN_METEO_URL, params=params, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except (requests.RequestException, ValueError) as e:
            last_err = e
            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY * (attempt + 1))
    raise last_err


def parse_daily_forecast(raw: dict) -> list[dict]:
    """Parse raw Open-Meteo response into a clean daily forecast list."""
    daily = raw.get("daily", {})
    dates = daily.get("time", [])
    results = []
    for i, date_str in enumerate(dates):
        wmo = daily["weather_code"][i]
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        results.append({
            "date": date_str,
            "date_short": dt.strftime("%b %d"),
            "day_name": dt.strftime("%A"),
            "temp_high_f": daily["temperature_2m_max"][i],
            "temp_low_f": daily["temperature_2m_min"][i],
            "precip_in": daily["precipitation_sum"][i],
            "snowfall_in": daily["snowfall_sum"][i],
            "precip_prob_pct": daily["precipitation_probability_max"][i],
            "wind_max_mph": daily["wind_speed_10m_max"][i],
            "wind_gust_mph": daily["wind_gusts_10m_max"][i],
            "weather_code": wmo,
            "weather_desc": _wmo_description(wmo),
            "weather_icon": _wmo_icon(wmo),
        })
    return results


def compute_snow_summary(daily_forecast: list[dict]) -> dict:
    """Aggregate snow totals and pick the best powder day."""
    total_snow = sum(d["snowfall_in"] or 0 for d in daily_forecast)
    snow_days = [d for d in daily_forecast if (d["snowfall_in"] or 0) > 0]
    best_day = max(daily_forecast, key=lambda d: d["snowfall_in"] or 0) if daily_forecast else None
    return {
        "total_snowfall_in": round(total_snow, 1),
        "snow_days_count": len(snow_days),
        "best_powder_day": best_day,
    }


def get_full_forecast(lat: float, lon: float, days: int = 7) -> dict:
    """One-call convenience: fetch + parse + summarize."""
    raw = fetch_forecast(lat, lon, days)
    daily = parse_daily_forecast(raw)
    snow = compute_snow_summary(daily)
    return {
        "daily": daily,
        "snow_summary": snow,
        "timezone": raw.get("timezone", ""),
        "elevation_m": raw.get("elevation", None),
    }


def _wmo_description(code: int | None) -> str:
    """WMO weather interpretation code to human description."""
    if code is None:
        return "Unknown"
    table = {
        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
        45: "Fog", 48: "Rime fog",
        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
        56: "Freezing drizzle (light)", 57: "Freezing drizzle (dense)",
        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
        66: "Freezing rain (light)", 67: "Freezing rain (heavy)",
        71: "Slight snowfall", 73: "Moderate snowfall", 75: "Heavy snowfall",
        77: "Snow grains",
        80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
        85: "Slight snow showers", 86: "Heavy snow showers",
        95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail",
    }
    return table.get(code, f"Code {code}")


def _wmo_icon(code: int | None) -> str:
    """WMO code to a weather emoji for the HTML UI."""
    if code is None:
        return "❓"
    if code == 0:
        return "☀️"
    if code in (1, 2):
        return "⛅"
    if code == 3:
        return "☁️"
    if code in (45, 48):
        return "🌫️"
    if code in (51, 53, 55, 56, 57):
        return "🌧️"
    if code in (61, 63, 65, 66, 67):
        return "🌧️"
    if code in (71, 73, 75, 77, 85, 86):
        return "🌨️"
    if code in (80, 81, 82):
        return "🌦️"
    if code in (95, 96, 99):
        return "⛈️"
    return "🌤️"
