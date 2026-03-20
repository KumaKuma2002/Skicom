"""LLM summary generation via any OpenAI-compatible API."""

import requests


def generate_summary(
    resort: dict,
    forecast: dict,
    accommodations: list[dict],
    config: dict,
) -> str | None:
    """Generate a ski trip summary using a configured LLM endpoint.

    Returns the generated text, or None if LLM is disabled / fails.
    """
    llm_cfg = config.get("llm", {})
    if not llm_cfg.get("enabled", False):
        return None

    api_base = llm_cfg.get("api_base", "https://api.openai.com/v1").rstrip("/")
    api_key = llm_cfg.get("api_key", "")
    model = llm_cfg.get("model", "gpt-4o")
    max_tokens = llm_cfg.get("max_tokens", 4096)
    system_prompt = llm_cfg.get("system_prompt", "You are a helpful ski trip advisor.")

    snow = forecast.get("snow_summary", {})
    daily_brief = []
    for d in forecast.get("daily", [])[:7]:
        daily_brief.append(
            f"{d['day_name']} {d['date']}: {d['weather_desc']}, "
            f"High {d['temp_high_f']}°F / Low {d['temp_low_f']}°F, "
            f"Snow: {d['snowfall_in']}in, Wind: {d['wind_max_mph']}mph"
        )

    accom_brief = []
    for a in accommodations[:8]:
        accom_brief.append(f"- {a['name']} ({a['type']}, {a['distance_mi']} mi away)")

    user_content = f"""{resort['full_name']}, {resort['state']} — {resort.get('region', '')}
{resort['elevation_ft']}ft · {resort.get('trails', '?')} trails · {resort.get('acres', '?')} acres

7-day snow: {snow.get('total_snowfall_in', 0)}in total, {snow.get('snow_days_count', 0)} snow days

Forecast:
{chr(10).join(daily_brief)}

Nearby stays:
{chr(10).join(accom_brief) if accom_brief else 'None found.'}
"""

    headers = {"Content-Type": "application/json"}
    if api_key and api_key != "sk-your-key-here":
        headers["Authorization"] = f"Bearer {api_key}"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_content},
    ]

    # Try max_completion_tokens first (GPT-5+), fall back to max_tokens (GPT-4 and earlier)
    for token_key in ("max_completion_tokens", "max_tokens"):
        payload = {"model": model, token_key: max_tokens, "messages": messages}
        try:
            resp = requests.post(
                f"{api_base}/chat/completions",
                headers=headers,
                json=payload,
                timeout=90,
            )
            if resp.status_code == 400 and "unsupported_parameter" in resp.text:
                continue
            resp.raise_for_status()
            data = resp.json()
            content = data["choices"][0]["message"]["content"]
            if content and content.strip():
                return content.strip()
            print("  ⚠ LLM returned empty response (try increasing max_tokens)")
            return None
        except requests.exceptions.HTTPError:
            if token_key == "max_tokens":
                print(f"  ⚠ LLM request failed: {resp.status_code} {resp.text[:200]}")
                return None
            continue
        except Exception as e:
            print(f"  ⚠ LLM request failed: {e}")
            return None

    return None
