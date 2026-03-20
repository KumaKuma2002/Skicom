"""Render ski resort report into a cozy Nordic-styled HTML file."""

import os
from datetime import datetime
from jinja2 import Template

TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Skicom — {{ resort.full_name }}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display&family=Inter:wght@300;400;500;600&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
<style>
  :root {
    --bg-deep: #1a1d23;
    --bg-card: #232730;
    --bg-card-hover: #2a2f3a;
    --bg-warm: #2c2418;
    --border: #3a3f4b;
    --border-warm: #4a3d2a;
    --text-primary: #e8e4df;
    --text-secondary: #9b978f;
    --text-muted: #6b6860;
    --accent-blue: #7eb8d8;
    --accent-amber: #d4a574;
    --accent-green: #8fbc8f;
    --accent-snow: #c8dbe6;
    --accent-red: #d88a7e;
    --glow-amber: rgba(212, 165, 116, 0.08);
    --glow-blue: rgba(126, 184, 216, 0.08);
    --radius: 16px;
    --radius-sm: 10px;
    --shadow: 0 4px 24px rgba(0,0,0,0.3);
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Inter', -apple-system, sans-serif;
    background: var(--bg-deep);
    color: var(--text-primary);
    line-height: 1.6;
    min-height: 100vh;
  }

  .snow-overlay {
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    pointer-events: none;
    z-index: 1000;
    overflow: hidden;
  }

  .snowflake {
    position: absolute;
    top: -10px;
    color: rgba(255,255,255,0.15);
    font-size: 14px;
    animation: snowfall linear infinite;
    user-select: none;
  }

  @keyframes snowfall {
    0% { transform: translateY(-10px) rotate(0deg); opacity: 1; }
    100% { transform: translateY(100vh) rotate(360deg); opacity: 0.2; }
  }

  .container { max-width: 1100px; margin: 0 auto; padding: 32px 24px 64px; }

  /* ─── Header ─── */
  .hero {
    text-align: center;
    padding: 56px 24px 40px;
    position: relative;
  }

  .hero::before {
    content: '';
    position: absolute;
    top: 0; left: 50%;
    transform: translateX(-50%);
    width: 120px; height: 3px;
    background: linear-gradient(90deg, transparent, var(--accent-amber), transparent);
    border-radius: 2px;
  }

  .brand {
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    letter-spacing: 4px;
    text-transform: uppercase;
    color: var(--accent-amber);
    margin-bottom: 16px;
  }

  .resort-name {
    font-family: 'DM Serif Display', serif;
    font-size: clamp(2.2rem, 5vw, 3.6rem);
    color: var(--text-primary);
    margin-bottom: 8px;
    letter-spacing: -0.5px;
  }

  .resort-meta {
    font-size: 15px;
    color: var(--text-secondary);
    display: flex;
    justify-content: center;
    gap: 20px;
    flex-wrap: wrap;
  }

  .resort-meta span { display: flex; align-items: center; gap: 6px; }

  .stat-bar {
    display: flex;
    justify-content: center;
    gap: 40px;
    margin-top: 28px;
    flex-wrap: wrap;
  }

  .stat-item {
    text-align: center;
  }

  .stat-value {
    font-family: 'DM Serif Display', serif;
    font-size: 28px;
    color: var(--accent-blue);
  }

  .stat-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--text-muted);
    margin-top: 2px;
  }

  /* ─── Section ─── */
  .section {
    margin-top: 48px;
  }

  .section-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 20px;
    padding-bottom: 12px;
    border-bottom: 1px solid var(--border);
  }

  .section-icon {
    font-size: 22px;
    width: 42px;
    height: 42px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--glow-amber);
    border: 1px solid var(--border-warm);
    border-radius: var(--radius-sm);
  }

  .section-title {
    font-family: 'DM Serif Display', serif;
    font-size: 22px;
    color: var(--text-primary);
  }

  .section-subtitle {
    font-size: 13px;
    color: var(--text-muted);
  }

  /* ─── Ski Map ─── */
  .map-frame {
    border-radius: var(--radius);
    overflow: hidden;
    border: 1px solid var(--border);
    box-shadow: var(--shadow);
    background: var(--bg-card);
  }

  .map-frame iframe {
    width: 100%;
    height: 480px;
    border: none;
    display: block;
  }

  .map-link {
    padding: 12px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: var(--bg-card);
    border-top: 1px solid var(--border);
    font-size: 13px;
  }

  .map-link a {
    color: var(--accent-blue);
    text-decoration: none;
    transition: color 0.2s;
  }

  .map-link a:hover { color: var(--accent-amber); }

  /* ─── Forecast Cards ─── */
  .forecast-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(135px, 1fr));
    gap: 12px;
  }

  .forecast-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 16px 14px;
    text-align: center;
    transition: all 0.25s ease;
  }

  .forecast-card:hover {
    background: var(--bg-card-hover);
    transform: translateY(-2px);
    box-shadow: var(--shadow);
  }

  .forecast-card.snow-day {
    border-color: var(--border-warm);
    background: var(--bg-warm);
  }

  .forecast-day {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--text-muted);
    margin-bottom: 4px;
  }

  .forecast-date {
    font-size: 11px;
    color: var(--text-muted);
    margin-bottom: 10px;
  }

  .forecast-icon { font-size: 32px; margin-bottom: 8px; }

  .forecast-temp {
    font-family: 'JetBrains Mono', monospace;
    font-size: 14px;
    color: var(--text-primary);
    margin-bottom: 4px;
  }

  .forecast-snow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 13px;
    color: var(--accent-snow);
    font-weight: 500;
  }

  .forecast-wind {
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 4px;
  }

  .forecast-desc {
    font-size: 11px;
    color: var(--text-secondary);
    margin-top: 4px;
  }

  /* ─── Snow Summary Banner ─── */
  .snow-banner {
    background: linear-gradient(135deg, var(--bg-warm) 0%, #1f2a1f 100%);
    border: 1px solid var(--border-warm);
    border-radius: var(--radius);
    padding: 24px 28px;
    display: flex;
    justify-content: space-around;
    align-items: center;
    gap: 20px;
    flex-wrap: wrap;
    margin-top: 16px;
  }

  .snow-stat { text-align: center; }

  .snow-stat-value {
    font-family: 'DM Serif Display', serif;
    font-size: 32px;
    color: var(--accent-amber);
  }

  .snow-stat-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--text-secondary);
  }

  /* ─── Accommodation ─── */
  .accom-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 14px;
  }

  .accom-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 18px 20px;
    display: flex;
    gap: 14px;
    align-items: flex-start;
    transition: all 0.25s ease;
  }

  .accom-card:hover {
    background: var(--bg-card-hover);
    transform: translateY(-1px);
    box-shadow: var(--shadow);
  }

  .accom-icon {
    font-size: 24px;
    width: 44px;
    height: 44px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--glow-blue);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    flex-shrink: 0;
  }

  .accom-info { flex: 1; min-width: 0; }

  .accom-name {
    font-weight: 600;
    font-size: 14px;
    color: var(--text-primary);
    margin-bottom: 3px;
  }

  .accom-type {
    font-size: 12px;
    color: var(--accent-amber);
    margin-bottom: 6px;
  }

  .accom-details {
    font-size: 12px;
    color: var(--text-secondary);
    display: flex;
    flex-direction: column;
    gap: 2px;
  }

  .accom-details a.accom-link-text {
    color: var(--accent-blue);
    text-decoration: none;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .accom-details a.accom-link-text:hover { text-decoration: underline; }

  .accom-distance {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    color: var(--text-muted);
  }

  .accom-tag {
    display: inline-block;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 600;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    border-radius: 4px;
    vertical-align: middle;
    margin-left: 6px;
  }

  .accom-tag.onsite {
    color: #1a1d23;
    background: var(--accent-amber);
  }

  .accom-tag.slopeside {
    color: var(--accent-blue);
    background: var(--glow-blue);
    border: 1px solid rgba(126, 184, 216, 0.25);
  }

  .accom-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    margin-top: 8px;
    padding: 7px 14px;
    font-size: 12px;
    font-weight: 500;
    font-family: 'Inter', sans-serif;
    color: var(--accent-amber);
    background: var(--glow-amber);
    border: 1px solid var(--border-warm);
    border-radius: 8px;
    text-decoration: none;
    cursor: pointer;
    transition: all 0.25s ease;
    white-space: nowrap;
  }

  .accom-btn:hover {
    background: rgba(212, 165, 116, 0.18);
    border-color: var(--accent-amber);
    color: var(--text-primary);
    transform: translateY(-1px);
    box-shadow: 0 2px 12px rgba(212, 165, 116, 0.15);
  }

  .accom-btn:active { transform: translateY(0); }

  .accom-btn svg {
    width: 13px;
    height: 13px;
    fill: none;
    stroke: currentColor;
    stroke-width: 2;
    stroke-linecap: round;
    stroke-linejoin: round;
  }

  /* ─── Accommodation Map ─── */
  .accom-map {
    border-radius: var(--radius);
    overflow: hidden;
    border: 1px solid var(--border);
    margin-bottom: 16px;
    box-shadow: var(--shadow);
  }

  .accom-map iframe {
    width: 100%;
    height: 360px;
    border: none;
    display: block;
  }

  /* ─── LLM Summary ─── */
  .summary-card {
    background: linear-gradient(135deg, var(--bg-warm) 0%, var(--bg-card) 100%);
    border: 1px solid var(--border-warm);
    border-radius: var(--radius);
    padding: 32px;
  }

  .summary-card p {
    color: var(--text-secondary);
    font-size: 15px;
    line-height: 1.8;
    margin-bottom: 12px;
  }

  .summary-card p:last-child { margin-bottom: 0; }

  .summary-card strong { color: var(--accent-amber); }

  /* ─── Model Badge ─── */
  .model-badge {
    margin-left: auto;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    font-size: 12px;
    font-family: 'JetBrains Mono', monospace;
    color: var(--text-secondary);
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: 20px;
    white-space: nowrap;
    flex-shrink: 0;
  }

  .model-badge-icon {
    font-size: 14px;
    line-height: 1;
  }

  .model-badge-name {
    color: var(--accent-blue);
    font-weight: 500;
  }

  /* ─── Footer ─── */
  .footer {
    margin-top: 64px;
    text-align: center;
    padding: 24px;
    border-top: 1px solid var(--border);
  }

  .footer-brand {
    font-family: 'JetBrains Mono', monospace;
    font-size: 12px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--text-muted);
  }

  .footer-sub {
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 4px;
  }

  /* ─── No-data state ─── */
  .empty-state {
    text-align: center;
    padding: 40px 20px;
    color: var(--text-muted);
    font-size: 14px;
    background: var(--bg-card);
    border: 1px dashed var(--border);
    border-radius: var(--radius-sm);
  }

  @media (max-width: 640px) {
    .container { padding: 16px 12px 48px; }
    .forecast-grid { grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); }
    .accom-grid { grid-template-columns: 1fr; }
    .stat-bar { gap: 24px; }
    .snow-banner { flex-direction: column; gap: 16px; }
  }
</style>
</head>
<body>

<!-- Falling snow -->
<div class="snow-overlay" id="snowOverlay"></div>

<div class="container">

  <!-- ─── Hero ─── -->
  <header class="hero">
    <div class="brand">⛷ Skicom</div>
    <h1 class="resort-name">{{ resort.full_name }}</h1>
    <div class="resort-meta">
      <span>📍 {{ resort.state }}</span>
      <span>🏔️ {{ resort.region }}</span>
      <span>📐 {{ resort.lat }}°N, {{ resort.lon | abs }}°W</span>
    </div>
    <div class="stat-bar">
      {% if resort.elevation_ft %}
      <div class="stat-item">
        <div class="stat-value">{{ "{:,}".format(resort.elevation_ft) }}'</div>
        <div class="stat-label">Summit Elevation</div>
      </div>
      {% endif %}
      {% if resort.vertical_ft %}
      <div class="stat-item">
        <div class="stat-value">{{ "{:,}".format(resort.vertical_ft) }}'</div>
        <div class="stat-label">Vertical Drop</div>
      </div>
      {% endif %}
      {% if resort.trails %}
      <div class="stat-item">
        <div class="stat-value">{{ resort.trails }}</div>
        <div class="stat-label">Trails</div>
      </div>
      {% endif %}
      {% if resort.acres %}
      <div class="stat-item">
        <div class="stat-value">{{ "{:,}".format(resort.acres) }}</div>
        <div class="stat-label">Skiable Acres</div>
      </div>
      {% endif %}
      {% if resort.lifts %}
      <div class="stat-item">
        <div class="stat-value">{{ resort.lifts }}</div>
        <div class="stat-label">Lifts</div>
      </div>
      {% endif %}
    </div>
  </header>

  <!-- ─── Ski Map ─── -->
  <section class="section">
    <div class="section-header">
      <div class="section-icon">🗺️</div>
      <div>
        <div class="section-title">Trail Map</div>
        <div class="section-subtitle">via OpenSkiMap.org</div>
      </div>
    </div>
    <div class="map-frame">
      <iframe
        src="https://openskimap.org/#{{ zoom }}/{{ resort.lat }}/{{ resort.lon }}"
        loading="lazy"
        title="Ski trail map"
      ></iframe>
      <div class="map-link">
        <span style="color: var(--text-muted)">Explore runs, lifts & more</span>
        <a href="https://openskimap.org/#{{ zoom }}/{{ resort.lat }}/{{ resort.lon }}" target="_blank" rel="noopener">
          Open full map ↗
        </a>
      </div>
    </div>
  </section>

  <!-- ─── Weather Forecast ─── -->
  <section class="section">
    <div class="section-header">
      <div class="section-icon">🌨️</div>
      <div>
        <div class="section-title">7-Day Forecast</div>
        <div class="section-subtitle">{{ forecast.timezone }}</div>
      </div>
    </div>

    <div class="forecast-grid">
      {% for day in forecast.daily %}
      <div class="forecast-card {{ 'snow-day' if day.snowfall_in and day.snowfall_in > 0 }}">
        <div class="forecast-day">{{ day.day_name[:3] }}</div>
        <div class="forecast-date">{{ day.date[5:] }}</div>
        <div class="forecast-icon">{{ day.weather_icon }}</div>
        <div class="forecast-temp">{{ day.temp_high_f | round | int }}° / {{ day.temp_low_f | round | int }}°</div>
        {% if day.snowfall_in and day.snowfall_in > 0 %}
        <div class="forecast-snow">❄ {{ day.snowfall_in }}"</div>
        {% endif %}
        <div class="forecast-wind">💨 {{ day.wind_max_mph | round | int }} mph</div>
        <div class="forecast-desc">{{ day.weather_desc }}</div>
      </div>
      {% endfor %}
    </div>

    <div class="snow-banner">
      <div class="snow-stat">
        <div class="snow-stat-value">{{ forecast.snow_summary.total_snowfall_in }}"</div>
        <div class="snow-stat-label">Total Snowfall</div>
      </div>
      <div class="snow-stat">
        <div class="snow-stat-value">{{ forecast.snow_summary.snow_days_count }}</div>
        <div class="snow-stat-label">Snow Days</div>
      </div>
      <div class="snow-stat">
        {% if forecast.snow_summary.best_powder_day and forecast.snow_summary.best_powder_day.snowfall_in and forecast.snow_summary.best_powder_day.snowfall_in > 0 %}
        <div class="snow-stat-value">{{ forecast.snow_summary.best_powder_day.date_short }}</div>
        {% else %}
        <div class="snow-stat-value" style="color: var(--text-muted);">—</div>
        {% endif %}
        <div class="snow-stat-label">Best Powder Day</div>
      </div>
    </div>
  </section>

  <!-- ─── Accommodations ─── -->
  <section class="section">
    <div class="section-header">
      <div class="section-icon">🏨</div>
      <div>
        <div class="section-title">Nearby Stays</div>
        <div class="section-subtitle">Within {{ search_radius_mi }} miles via OpenStreetMap</div>
      </div>
    </div>

    {% if accommodations %}
    <div class="accom-map">
      <iframe
        src="https://www.openstreetmap.org/export/embed.html?bbox={{ bbox }}&layer=mapnik&marker={{ resort.lat }},{{ resort.lon }}"
        loading="lazy"
        title="Accommodation map"
      ></iframe>
    </div>

    <div class="accom-grid">
      {% for a in accommodations %}
      <div class="accom-card">
        <div class="accom-icon">{{ a.type_icon }}</div>
        <div class="accom-info">
          <div class="accom-name">{{ a.name }}{% if a.proximity_tag %}<span class="accom-tag {{ a.proximity_tag }}">{% if a.proximity_tag == 'onsite' %}Onsite Lodging{% else %}Slopeside{% endif %}</span>{% endif %}</div>
          <div class="accom-type">{{ a.type }}{% if a.stars %} · {{ a.stars }}★{% endif %}</div>
          <div class="accom-details">
            <span class="accom-distance">↕ {{ a.distance_mi }} mi from resort</span>
            {% if a.addr %}<span>{{ a.addr }}</span>{% endif %}
            {% if a.phone %}<span>📞 {{ a.phone }}</span>{% endif %}
            {% if a.website %}
            <a class="accom-btn" href="{{ a.website }}" target="_blank" rel="noopener">
              <svg viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
              Visit Website
            </a>
            {% endif %}
          </div>
        </div>
      </div>
      {% endfor %}
    </div>
    {% else %}
    <div class="empty-state">
      No accommodations found nearby in OpenStreetMap data.<br>
      Try searching booking sites for lodging near {{ resort.full_name }}.
    </div>
    {% endif %}
  </section>

  <!-- ─── LLM Summary ─── -->
  {% if summary %}
  <section class="section">
    <div class="section-header">
      <div class="section-icon">✨</div>
      <div>
        <div class="section-title">Trip Advisor</div>
        <div class="section-subtitle">AI-generated ski trip summary</div>
      </div>
      {% if llm_model %}
      <div class="model-badge">
        <span class="model-badge-icon">{{ llm_provider_icon }}</span>
        <span class="model-badge-name">{{ llm_model }}</span>
      </div>
      {% endif %}
    </div>
    <div class="summary-card">
      {% for paragraph in summary.split('\n\n') %}
        {% if paragraph.strip() %}
        <p>{{ paragraph | replace('\n', '<br>') }}</p>
        {% endif %}
      {% endfor %}
    </div>
  </section>
  {% endif %}

  <!-- ─── Footer ─── -->
  <footer class="footer">
    <div class="footer-brand">⛷ Skicom</div>
    <div class="footer-sub">
      Generated {{ generated_at }} · Weather via Open-Meteo · Maps via OpenSkiMap & OpenStreetMap
    </div>
  </footer>

</div>

<script>
(function() {
  const overlay = document.getElementById('snowOverlay');
  const flakes = ['❄', '❅', '❆', '✦', '·'];
  for (let i = 0; i < 35; i++) {
    const s = document.createElement('span');
    s.className = 'snowflake';
    s.textContent = flakes[Math.floor(Math.random() * flakes.length)];
    s.style.left = Math.random() * 100 + '%';
    s.style.fontSize = (8 + Math.random() * 12) + 'px';
    s.style.animationDuration = (8 + Math.random() * 12) + 's';
    s.style.animationDelay = Math.random() * 10 + 's';
    s.style.opacity = 0.1 + Math.random() * 0.2;
    overlay.appendChild(s);
  }
})();
</script>

</body>
</html>"""


def _provider_icon(api_base: str) -> str:
    """Map known API base URLs to a provider icon."""
    base = api_base.lower()
    if "openai" in base:
        return "🟢"
    if "anthropic" in base or "claude" in base:
        return "🟠"
    if "localhost" in base or "127.0.0.1" in base:
        return "🖥️"
    if "google" in base or "gemini" in base:
        return "🔵"
    if "mistral" in base:
        return "🟣"
    if "groq" in base:
        return "⚡"
    if "together" in base:
        return "🤝"
    return "🤖"


def render_report(
    resort: dict,
    forecast: dict,
    accommodations: list[dict],
    summary: str | None,
    config: dict,
) -> tuple[str, str]:
    """Render and save both HTML and TXT reports. Returns (html_path, txt_path)."""
    out_dir = config.get("output", {}).get("directory", "./reports")
    os.makedirs(out_dir, exist_ok=True)

    safe_name = resort["full_name"].replace(" ", "_").replace("/", "-")
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    html_path = os.path.join(out_dir, f"skicom_{safe_name}_{timestamp}.html")
    txt_path = os.path.join(out_dir, f"skicom_{safe_name}_{timestamp}.txt")

    search_radius_m = config.get("accommodations", {}).get("search_radius_m", 15000)
    search_radius_mi = round(search_radius_m / 1609.34, 1)

    delta = search_radius_m / 111320.0 * 1.2
    bbox = (
        f"{resort['lon'] - delta},{resort['lat'] - delta},"
        f"{resort['lon'] + delta},{resort['lat'] + delta}"
    )

    zoom = 13
    generated_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    llm_cfg = config.get("llm", {})
    llm_model = llm_cfg.get("model", "") if llm_cfg.get("enabled") and summary else ""
    llm_provider_icon = _provider_icon(llm_cfg.get("api_base", "")) if llm_model else ""

    template = Template(TEMPLATE)
    html = template.render(
        resort=resort,
        forecast=forecast,
        accommodations=accommodations,
        summary=summary,
        generated_at=generated_at,
        search_radius_mi=search_radius_mi,
        bbox=bbox,
        zoom=zoom,
        llm_model=llm_model,
        llm_provider_icon=llm_provider_icon,
    )

    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    txt = _render_txt(resort, forecast, accommodations, summary, search_radius_mi, generated_at, config)
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(txt)

    return html_path, txt_path


def _render_txt(
    resort: dict,
    forecast: dict,
    accommodations: list[dict],
    summary: str | None,
    search_radius_mi: float,
    generated_at: str,
    config: dict | None = None,
) -> str:
    """Build a plain-text version of the report."""
    W = 62
    hr = "─" * W
    dhr = "═" * W

    stats = [
        f"  Location:    {resort['state']} · {resort.get('region', '')}",
        f"  Coordinates: {resort['lat']}°N, {abs(resort['lon'])}°W",
        f"  Elevation:   {resort.get('elevation_ft', 0):,} ft",
    ]
    if resort.get('vertical_ft'):
        stats.append(f"  Vert. drop:  {resort['vertical_ft']:,} ft")
    if resort.get('trails'):
        stats.append(f"  Trails:      {resort['trails']}")
    if resort.get('acres'):
        stats.append(f"  Skiable:     {resort['acres']:,} acres")
    if resort.get('lifts'):
        stats.append(f"  Lifts:       {resort['lifts']}")

    lines = [
        dhr,
        f"  SKICOM — {resort['full_name']}".center(W),
        dhr,
        "",
        *stats,
        "",
        hr,
        "  TRAIL MAP",
        hr,
        f"  https://openskimap.org/#13/{resort['lat']}/{resort['lon']}",
        "",
        hr,
        "  7-DAY FORECAST",
        hr,
    ]

    for d in forecast.get("daily", []):
        snow_str = f"  Snow: {d['snowfall_in']}\"" if d.get("snowfall_in") and d["snowfall_in"] > 0 else ""
        lines.append(
            f"  {d['day_name'][:3]} {d.get('date_short', d['date'][5:])}  "
            f"{d['weather_desc']:<22s}  "
            f"{d['temp_high_f']:>3.0f}°/{d['temp_low_f']:>3.0f}°F  "
            f"Wind {d['wind_max_mph']:.0f}mph"
            f"{snow_str}"
        )

    snow = forecast.get("snow_summary", {})
    best = snow.get("best_powder_day")
    best_str = "—"
    if best and (best.get("snowfall_in") or 0) > 0:
        best_str = f"{best.get('date_short', best['date'])} ({best['snowfall_in']}\")"
    lines += [
        "",
        f"  Total snowfall: {snow.get('total_snowfall_in', 0)}\"  |  "
        f"Snow days: {snow.get('snow_days_count', 0)}  |  "
        f"Best powder day: {best_str}",
    ]

    lines += ["", hr, f"  NEARBY STAYS (within {search_radius_mi} mi)", hr]
    if accommodations:
        for a in accommodations:
            web = f"  {a['website']}" if a.get("website") else ""
            tag = ""
            if a.get("proximity_tag") == "onsite":
                tag = "  [ONSITE LODGING]"
            elif a.get("proximity_tag") == "slopeside":
                tag = "  [SLOPESIDE]"
            lines.append(f"  {a['type_icon']} {a['name']}{tag}")
            lines.append(f"    {a['type']} · {a['distance_mi']} mi away")
            if a.get("addr"):
                lines.append(f"    {a['addr']}")
            if a.get("phone"):
                lines.append(f"    Tel: {a['phone']}")
            if web:
                lines.append(f"   {web}")
            lines.append("")
    else:
        lines.append("  No accommodations found in OpenStreetMap data.")
        lines.append("")

    if summary:
        llm_cfg = (config or {}).get("llm", {})
        model_name = llm_cfg.get("model", "")
        model_line = f"  (via {model_name})" if model_name else ""
        lines += [hr, f"  AI TRIP SUMMARY{model_line}", hr, ""]
        for para in summary.split("\n"):
            if para.strip():
                while len(para) > W - 4:
                    cut = para[:W - 4].rfind(" ")
                    if cut == -1:
                        cut = W - 4
                    lines.append(f"  {para[:cut]}")
                    para = para[cut:].lstrip()
                lines.append(f"  {para}")
            else:
                lines.append("")

    lines += [
        "",
        dhr,
        f"  Generated {generated_at}".center(W),
        "  Weather: Open-Meteo · Maps: OpenSkiMap & OSM".center(W),
        dhr,
        "",
    ]

    return "\n".join(lines)
