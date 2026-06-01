"""Render ski resort report into a clean Anthropic-style HTML file."""

import json
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
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Hanken+Grotesk:wght@400;500;600;700;800&display=swap" rel="stylesheet">
<link href="https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap" rel="stylesheet">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  :root {
    --bg-page: #FAF6EF;
    --bg-card: #FFFFFF;
    --bg-card-hover: #F7EFE3;
    --bg-warm: #F7EFE3;
    --border: #ECE3D6;
    --border-light: #F2EADF;
    --text-primary: #2B2622;
    --text-secondary: #8A7F72;
    --text-muted: #8A7F72;
    --accent: #D97757;
    --accent-deep: #C4623F;
    --accent-hover: #C4623F;
    --accent-light: #F7E6DD;
    --accent-subtle: rgba(217,119,87,0.08);
    --on-accent: #FFFFFF;
    --sand: #E8C9A0;
    --pine: #6B7F5E;
    --snow-blue: #BCD3DE;
    --radius: 14px;
    --radius-sm: 9px;
    --shadow: 0 1px 3px rgba(43,38,34,0.05), 0 6px 20px rgba(43,38,34,0.06);
    --shadow-md: 0 2px 6px rgba(43,38,34,0.08), 0 12px 32px rgba(43,38,34,0.10);
    --chart-grid: #ECE3D6;
    --chart-label: #8A7F72;
    --chart-day: #8A7F72;
    --chart-high: #2B2622;
    --chart-low: #8A7F72;
    --chart-fill: rgba(217,119,87,0.10);
    --chart-accent: #D97757;
    --chart-bar-empty: #ECE3D6;
  }

  [data-theme="dark"] {
    --bg-page: #1C1916;
    --bg-card: #262220;
    --bg-card-hover: #302B27;
    --bg-warm: #302B27;
    --border: #3A332D;
    --border-light: #322C27;
    --text-primary: #ECE4DA;
    --text-secondary: #9C9085;
    --text-muted: #9C9085;
    --accent: #E08A6B;
    --accent-deep: #D97757;
    --accent-hover: #D97757;
    --accent-light: #3A2C24;
    --accent-subtle: rgba(224,138,107,0.18);
    --on-accent: #FFFFFF;
    --shadow: 0 1px 3px rgba(0,0,0,0.30), 0 6px 20px rgba(0,0,0,0.35);
    --shadow-md: 0 2px 6px rgba(0,0,0,0.40), 0 12px 32px rgba(0,0,0,0.45);
    --chart-grid: #3A332D;
    --chart-label: #9C9085;
    --chart-day: #9C9085;
    --chart-high: #ECE4DA;
    --chart-low: #9C9085;
    --chart-fill: rgba(224,138,107,0.18);
    --chart-accent: #E08A6B;
    --chart-bar-empty: #3A332D;
  }

  * { margin: 0; padding: 0; box-sizing: border-box; }

  body {
    font-family: 'Hanken Grotesk', -apple-system, BlinkMacSystemFont, 'Inter', 'Segoe UI', sans-serif;
    background: var(--bg-page);
    color: var(--text-primary);
    line-height: 1.6;
    min-height: 100vh;
    -webkit-font-smoothing: antialiased;
    transition: background 0.3s, color 0.3s;
  }

  a { color: var(--accent); text-decoration: none; }
  a:hover { text-decoration: underline; }

  .container { max-width: 960px; margin: 0 auto; padding: 48px 24px 80px; }

  /* ─── Hero ─── */
  .hero {
    text-align: center;
    padding: 48px 24px 40px;
  }

  .hero::after {
    content: '';
    display: block;
    width: 48px;
    height: 3px;
    background: var(--accent);
    margin: 40px auto 0;
    border-radius: 2px;
  }

  .brand {
    font-size: 12px;
    letter-spacing: 3px;
    text-transform: uppercase;
    color: var(--accent);
    margin-bottom: 20px;
    font-weight: 700;
    display: inline-flex;
    align-items: center;
    gap: 7px;
  }
  .brand .icon { width: 15px; height: 15px; }

  .resort-name {
    font-size: clamp(2.6rem, 5.5vw, 4rem);
    color: var(--text-primary);
    margin-bottom: 12px;
    letter-spacing: -1.5px;
    line-height: 1.05;
    font-weight: 800;
  }

  .resort-meta {
    font-size: 14px;
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
    gap: 48px;
    margin-top: 36px;
    flex-wrap: wrap;
  }

  .stat-item { text-align: center; }

  .stat-value {
    font-size: 30px;
    font-weight: 800;
    letter-spacing: -1px;
    color: var(--accent);
  }

  .stat-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 2px;
    color: var(--text-muted);
    margin-top: 4px;
  }

  /* ─── Section ─── */
  .section { margin-top: 48px; }

  .section-header {
    display: flex;
    align-items: center;
    gap: 14px;
    margin-bottom: 24px;
  }

  .section-icon {
    font-size: 20px;
    width: 40px;
    height: 40px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--accent-light);
    color: var(--accent);
    border-radius: var(--radius);
    flex-shrink: 0;
  }

  .section-icon svg {
    width: 20px;
    height: 20px;
    fill: none;
    stroke: currentColor;
    stroke-width: 1.5;
    stroke-linecap: round;
    stroke-linejoin: round;
  }

  /* Inline line-icons (Apple SF-Symbols style) */
  .icon {
    width: 1em;
    height: 1em;
    display: inline-block;
    vertical-align: -0.125em;
    fill: none;
    stroke: currentColor;
    stroke-width: 1.5;
    stroke-linecap: round;
    stroke-linejoin: round;
    flex-shrink: 0;
  }

  .section-title {
    font-size: 24px;
    font-weight: 800;
    letter-spacing: -0.6px;
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
    box-shadow: var(--shadow-md);
    background: var(--bg-card);
  }

  .map-frame iframe {
    width: 100%;
    height: 480px;
    border: none;
    display: block;
  }

  .map-link {
    padding: 14px 20px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    background: var(--bg-card);
    border-top: 1px solid var(--border-light);
    font-size: 13px;
  }

  .map-link a {
    color: var(--accent);
    text-decoration: none;
    font-weight: 600;
    transition: color 0.2s;
  }

  .map-link a:hover { color: var(--accent-deep); text-decoration: underline; }

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
    padding: 18px 14px;
    text-align: center;
    transition: all 0.2s ease;
    box-shadow: var(--shadow);
  }

  .forecast-card:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
  }

  .forecast-card.snow-day {
    background: var(--accent-light);
    border-color: var(--accent);
    border-left: 3px solid var(--accent);
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
    font-size: 14px;
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: 4px;
    font-variant-numeric: tabular-nums;
  }

  .forecast-snow {
    font-size: 13px;
    color: var(--accent);
    font-weight: 700;
    font-variant-numeric: tabular-nums;
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

  /* ─── Snow Summary ─── */
  .snow-banner {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 28px;
    display: flex;
    justify-content: space-around;
    align-items: center;
    gap: 20px;
    flex-wrap: wrap;
    margin-top: 20px;
    box-shadow: var(--shadow);
  }

  .snow-stat { text-align: center; }

  .snow-stat-value {
    font-size: 34px;
    font-weight: 800;
    letter-spacing: -1px;
    color: var(--accent);
  }

  .snow-stat-label {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--text-secondary);
    margin-top: 4px;
  }

  .depth-row {
    display: flex;
    justify-content: center;
    gap: 48px;
    margin-top: 12px;
    padding: 16px 28px;
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    box-shadow: var(--shadow);
    flex-wrap: wrap;
  }

  .depth-item { text-align: center; }

  .depth-value {
    font-size: 26px;
    font-weight: 800;
    letter-spacing: -0.5px;
    color: var(--text-primary);
  }

  .depth-label {
    font-size: 10px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--text-muted);
    margin-top: 2px;
  }

  /* ─── Accommodation ─── */
  .accom-grid {
    display: grid;
    grid-template-columns: 1fr;
    gap: 0;
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    overflow: hidden;
    box-shadow: var(--shadow);
  }

  .accom-card {
    background: var(--bg-card);
    padding: 16px 20px;
    display: flex;
    gap: 14px;
    align-items: flex-start;
    border-bottom: 1px solid var(--border-light);
    transition: background 0.15s ease;
  }

  .accom-card:last-child { border-bottom: none; }

  .accom-card:hover { background: var(--bg-card-hover); }

  .accom-num {
    font-size: 11px;
    font-weight: 700;
    width: 26px;
    height: 26px;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--accent-light);
    color: var(--accent);
    border-radius: var(--radius);
    flex-shrink: 0;
    margin-top: 1px;
    font-variant-numeric: tabular-nums;
  }

  .accom-info { flex: 1; min-width: 0; }

  .accom-name {
    font-weight: 600;
    font-size: 14px;
    color: var(--text-primary);
    margin-bottom: 2px;
  }

  .accom-type {
    font-size: 12px;
    color: var(--text-muted);
    margin-bottom: 4px;
  }

  .accom-details {
    font-size: 12px;
    color: var(--text-secondary);
    display: flex;
    flex-wrap: wrap;
    gap: 4px 16px;
  }

  .accom-details a.accom-link-text {
    color: var(--accent);
    text-decoration: none;
    text-underline-offset: 2px;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .accom-details a.accom-link-text:hover { text-decoration: underline; }

  .accom-distance {
    font-size: 12px;
    color: var(--text-muted);
    font-variant-numeric: tabular-nums;
  }

  .accom-tag {
    display: inline-block;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 0.8px;
    text-transform: uppercase;
    border-radius: var(--radius);
    vertical-align: middle;
    margin-left: 6px;
  }

  .accom-tag.onsite {
    color: var(--on-accent);
    background: var(--accent);
  }

  .accom-tag.slopeside {
    color: var(--accent);
    background: var(--accent-light);
  }

  .accom-btn {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    font-weight: 600;
    font-family: inherit;
    color: var(--accent);
    text-decoration: none;
    background: none;
    border: none;
    cursor: pointer;
    transition: color 0.15s ease;
    white-space: nowrap;
  }

  .accom-btn:hover { color: var(--accent-deep); text-decoration: underline; }

  .accom-btn svg {
    width: 11px;
    height: 11px;
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
    box-shadow: var(--shadow-md);
    height: 400px;
  }

  .leaflet-popup-content-wrapper {
    background: var(--bg-card) !important;
    color: var(--text-primary) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius-sm) !important;
    box-shadow: var(--shadow-md) !important;
  }
  .leaflet-popup-tip { background: var(--bg-card) !important; }
  .leaflet-popup-content { font-family: inherit; font-size: 13px; line-height: 1.5; }
  .leaflet-popup-content .popup-name { font-weight: 600; color: var(--accent); margin-bottom: 4px; }
  .leaflet-popup-content .popup-type { font-size: 11px; color: var(--text-secondary); margin-bottom: 6px; }
  .leaflet-popup-content .popup-detail { font-size: 12px; color: var(--text-secondary); }
  .leaflet-popup-content a { color: var(--accent); }
  .leaflet-popup-close-button { color: var(--text-muted) !important; }

  /* ─── LLM Summary ─── */
  .summary-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 32px;
    box-shadow: var(--shadow);
  }

  .summary-card p {
    color: var(--text-secondary);
    font-size: 15px;
    line-height: 1.8;
    margin-bottom: 12px;
  }

  .summary-card p:last-child { margin-bottom: 0; }

  .summary-card strong { color: var(--accent); }

  /* ─── AI Suggest Button ─── */
  .btn {
    display: inline-flex;
    align-items: center;
    gap: 8px;
    font-family: inherit;
    font-size: 14px;
    font-weight: 700;
    letter-spacing: 0.2px;
    padding: 12px 22px;
    border-radius: 10px;
    border: 1px solid var(--accent);
    background: var(--accent);
    color: var(--on-accent);
    cursor: pointer;
    box-shadow: var(--shadow);
    transition: background 0.15s ease, border-color 0.15s ease, box-shadow 0.15s ease;
  }

  .btn:hover { background: var(--accent-deep); border-color: var(--accent-deep); box-shadow: var(--shadow-md); }
  .btn:disabled { opacity: 0.65; cursor: default; }

  .btn-ghost {
    background: var(--bg-card);
    color: var(--accent);
    border: 1px solid var(--accent);
    box-shadow: none;
  }
  .btn-ghost:hover { background: var(--accent-light); border-color: var(--accent-deep); box-shadow: none; }

  .ai-error {
    margin-top: 14px;
    font-size: 13px;
    color: #B0432A;
  }
  [data-theme="dark"] .ai-error { color: #E89A82; }

  /* ─── Model Badge ─── */
  .model-badge {
    margin-left: auto;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 5px 12px;
    font-size: 12px;
    color: var(--text-secondary);
    background: var(--accent-light);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    white-space: nowrap;
    flex-shrink: 0;
  }

  .model-badge-icon {
    font-size: 14px;
    line-height: 1;
  }

  .model-badge-name {
    color: var(--accent);
    font-weight: 700;
  }

  /* ─── Footer ─── */
  .footer {
    margin-top: 80px;
    text-align: center;
    padding: 24px;
    border-top: 1px solid var(--border);
  }

  .footer-brand {
    font-size: 12px;
    letter-spacing: 3px;
    font-weight: 700;
    text-transform: uppercase;
    color: var(--accent);
    display: inline-flex;
    align-items: center;
    gap: 7px;
  }
  .footer-brand .icon { width: 15px; height: 15px; }

  .footer-sub {
    font-size: 11px;
    color: var(--text-muted);
    margin-top: 6px;
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

  /* ─── Charts ─── */
  .charts-row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
    gap: 12px;
    margin-top: 20px;
  }

  .chart-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 16px 18px 12px;
    box-shadow: var(--shadow);
  }

  .chart-title {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    color: var(--text-muted);
    margin-bottom: 6px;
  }

  .chart-legend {
    display: flex;
    gap: 16px;
    margin-top: 4px;
    font-size: 10px;
    color: var(--text-muted);
  }

  .chart-legend span { display: flex; align-items: center; gap: 4px; }
  .chart-legend .leg-line { width: 14px; height: 0; border-top: 2px solid var(--text-primary); }
  .chart-legend .leg-dash { width: 14px; height: 0; border-top: 2px dashed var(--text-muted); }

  /* ─── Theme Toggle ─── */
  .theme-toggle {
    position: fixed;
    top: 20px;
    right: 20px;
    width: 40px;
    height: 40px;
    border-radius: var(--radius);
    border: 1px solid var(--border);
    background: var(--bg-card);
    color: var(--text-secondary);
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: var(--shadow);
    transition: border-color 0.2s, color 0.2s, background 0.3s;
    z-index: 100;
  }
  .theme-toggle:hover {
    border-color: var(--accent);
    color: var(--accent);
  }
  .theme-toggle svg { width: 18px; height: 18px; fill: none; stroke: currentColor; stroke-width: 1.5; stroke-linecap: round; stroke-linejoin: round; }
  .icon-sun { display: none; }
  [data-theme="dark"] .icon-sun { display: block; }
  [data-theme="dark"] .icon-moon { display: none; }

  /* ─── Back to home — pixel-art button (white + pink-red), served mode only ─── */
  .back-nav {
    position: fixed;
    top: 22px;
    left: 24px;
    z-index: 100;
  }
  .back-link {
    --px-accent: #D97757;  /* cozy clay */
    display: inline-block;
    font-family: 'Press Start 2P', ui-monospace, "Courier New", monospace;
    font-size: 9px;
    line-height: 1;
    letter-spacing: 0.5px;
    text-transform: uppercase;
    color: var(--px-accent);
    background: #FFFFFF;
    border: 3px solid var(--px-accent);
    border-radius: 0;
    padding: 9px 12px 8px;
    text-decoration: none;
    box-shadow: 4px 4px 0 var(--px-accent);
    image-rendering: pixelated;
    -webkit-font-smoothing: none;
    transition: transform 0.06s steps(2), box-shadow 0.06s steps(2);
  }
  .back-link:hover {
    transform: translate(2px, 2px);
    box-shadow: 2px 2px 0 var(--px-accent);
    color: var(--px-accent);
    text-decoration: none;
  }
  .back-link:active {
    transform: translate(4px, 4px);
    box-shadow: 0 0 0 var(--px-accent);
  }
  @media (max-width: 640px) {
    .back-nav { top: 14px; left: 14px; }
  }

  @media (max-width: 640px) {
    .container { padding: 24px 16px 48px; }
    .hero { padding: 32px 16px 28px; }
    .forecast-grid { grid-template-columns: repeat(auto-fill, minmax(110px, 1fr)); }
    .accom-grid { grid-template-columns: 1fr; }
    .stat-bar { gap: 24px; }
    .snow-banner { flex-direction: column; gap: 16px; }
    .charts-row { grid-template-columns: 1fr; }
  }
</style>
</head>
<body>

{% if ai_button %}
<nav class="back-nav">
  <a class="back-link" href="/" aria-label="Back to Skicom home">&lt; HOME</a>
</nav>
{% endif %}

<button class="theme-toggle" id="themeToggle" aria-label="Toggle dark mode">
  <svg class="icon-moon" viewBox="0 0 24 24"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"/></svg>
  <svg class="icon-sun" viewBox="0 0 24 24"><circle cx="12" cy="12" r="5"/><line x1="12" y1="1" x2="12" y2="3"/><line x1="12" y1="21" x2="12" y2="23"/><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"/><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"/><line x1="1" y1="12" x2="3" y2="12"/><line x1="21" y1="12" x2="23" y2="12"/><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"/><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"/></svg>
</button>

<div class="container">

  <!-- ─── Hero ─── -->
  <header class="hero">
    <div class="brand">
      <svg class="icon" viewBox="0 0 24 24"><path d="M3 20h18"/><path d="M3 20l6-12 4 7 3-5 5 10"/></svg>
      Skicom
    </div>
    <h1 class="resort-name">{{ resort.full_name }}</h1>
    <div class="resort-meta">
      <span><svg class="icon" viewBox="0 0 24 24"><path d="M12 21s-7-6.4-7-11a7 7 0 0 1 14 0c0 4.6-7 11-7 11z"/><circle cx="12" cy="10" r="2.5"/></svg> {{ resort.state }}</span>
      <span><svg class="icon" viewBox="0 0 24 24"><path d="M3 20l6-12 4 7 3-5 5 10z"/></svg> {{ resort.region }}</span>
      <span><svg class="icon" viewBox="0 0 24 24"><circle cx="12" cy="12" r="9"/><path d="M3 12h18"/><path d="M12 3a14 14 0 0 1 0 18 14 14 0 0 1 0-18z"/></svg> {{ resort.lat | abs }}°{{ 'N' if resort.lat >= 0 else 'S' }}, {{ resort.lon | abs }}°{{ 'E' if resort.lon >= 0 else 'W' }}</span>
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
      <div class="section-icon"><svg viewBox="0 0 24 24"><path d="M9 4 3 6v14l6-2 6 2 6-2V4l-6 2-6-2z"/><path d="M9 4v14"/><path d="M15 6v14"/></svg></div>
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
      <div class="section-icon"><svg viewBox="0 0 24 24"><path d="M7 16a4 4 0 0 1 .5-7.97 5.5 5.5 0 0 1 10.5 1.47A3.5 3.5 0 0 1 17.5 16H7z"/><path d="M8 19v2"/><path d="M12 19v2"/><path d="M16 19v2"/></svg></div>
      <div>
        <div class="section-title">6-Day Forecast</div>
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
        <div class="forecast-wind"><svg class="icon" viewBox="0 0 24 24"><path d="M3 9h11a2.5 2.5 0 1 0-2.5-2.5"/><path d="M3 14h15a2.5 2.5 0 1 1-2.5 2.5"/></svg> {{ day.wind_max_mph | round | int }} mph</div>
        <div class="forecast-desc">{{ day.weather_desc }}</div>
      </div>
      {% endfor %}
    </div>

    {% if temp_chart_svg or snow_chart_svg or depth_chart_svg %}
    <div class="charts-row">
      {% if temp_chart_svg %}
      <div class="chart-card">
        <div class="chart-title">Temperature Trend (°F)</div>
        {{ temp_chart_svg }}
        <div class="chart-legend">
          <span><span class="leg-line"></span> High</span>
          <span><span class="leg-dash"></span> Low</span>
        </div>
      </div>
      {% endif %}
      {% if snow_chart_svg %}
      <div class="chart-card">
        <div class="chart-title">Snowfall Forecast</div>
        {{ snow_chart_svg }}
      </div>
      {% endif %}
      {% if depth_chart_svg %}
      <div class="chart-card">
        <div class="chart-title">Snow Depth</div>
        {{ depth_chart_svg }}
      </div>
      {% endif %}
    </div>
    {% endif %}

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

    <div class="depth-row">
      <div class="depth-item">
        <div class="depth-value">{% if forecast.snow_summary.base_depth_in is not none %}{{ forecast.snow_summary.base_depth_in }}"{% else %}--{% endif %}</div>
        <div class="depth-label">Base Depth</div>
      </div>
      <div class="depth-item">
        <div class="depth-value">{% if forecast.snow_summary.summit_depth_in is not none %}{{ forecast.snow_summary.summit_depth_in }}"{% else %}--{% endif %}</div>
        <div class="depth-label">Summit Depth</div>
      </div>
    </div>
  </section>

  <!-- ─── Accommodations ─── -->
  <section class="section">
    <div class="section-header">
      <div class="section-icon"><svg viewBox="0 0 24 24"><path d="M3 18v-9"/><path d="M3 14h18v4"/><path d="M21 18v-3a3 3 0 0 0-3-3H9v3"/><path d="M6 11.5a1.5 1.5 0 1 0 0-.01"/></svg></div>
      <div>
        <div class="section-title">Nearby Stays</div>
        <div class="section-subtitle">Within {{ search_radius_mi }} miles via OpenStreetMap</div>
      </div>
    </div>

    {% if accommodations %}
    <div class="accom-map" id="accomMap"></div>

    <div class="accom-grid">
      {% for a in accommodations %}
      <div class="accom-card">
        <div class="accom-num">{{ loop.index }}</div>
        <div class="accom-info">
          <div class="accom-name">{{ a.name }}{% if a.proximity_tag %}<span class="accom-tag {{ a.proximity_tag }}">{% if a.proximity_tag == 'onsite' %}Onsite{% else %}Slopeside{% endif %}</span>{% endif %}</div>
          <div class="accom-type">{{ a.type_icon }} {{ a.type }}{% if a.stars %} · {{ a.stars }}★{% endif %} · {{ a.distance_mi }} mi</div>
          <div class="accom-details">
            {% if a.addr %}<span>{{ a.addr }}</span>{% endif %}
            {% if a.phone %}<span>{{ a.phone }}</span>{% endif %}
            {% if a.website %}
            <a class="accom-btn" href="{{ a.website }}" target="_blank" rel="noopener">
              <svg viewBox="0 0 24 24"><path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/></svg>
              Website
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

  <!-- ─── AI Trip Brief / LLM Summary ─── -->
  {% if ai_button %}
  <section class="section">
    <div class="section-header">
      <div class="section-icon"><svg viewBox="0 0 24 24"><path d="M12 3l1.8 4.7L18.5 9l-4.7 1.3L12 15l-1.8-4.7L5.5 9l4.7-1.3L12 3z"/><path d="M18 14l.8 2.2L21 17l-2.2.8L18 20l-.8-2.2L15 17l2.2-.8L18 14z"/></svg></div>
      <div>
        <div class="section-title">AI Trip Brief</div>
        <div class="section-subtitle">Generate an AI-written ski trip summary on demand</div>
      </div>
    </div>
    <button class="btn" id="aiSuggestBtn" data-resort="{{ resort.full_name | e }}"><svg class="icon" viewBox="0 0 24 24"><path d="M12 3l1.8 4.7L18.5 9l-4.7 1.3L12 15l-1.8-4.7L5.5 9l4.7-1.3L12 3z"/><path d="M18 14l.8 2.2L21 17l-2.2.8L18 20l-.8-2.2L15 17l2.2-.8L18 14z"/></svg> AI Suggest</button>
    <div id="aiSuggestOut"></div>
  </section>
  {% elif summary %}
  <section class="section">
    <div class="section-header">
      <div class="section-icon"><svg viewBox="0 0 24 24"><path d="M12 3l1.8 4.7L18.5 9l-4.7 1.3L12 15l-1.8-4.7L5.5 9l4.7-1.3L12 3z"/><path d="M18 14l.8 2.2L21 17l-2.2.8L18 20l-.8-2.2L15 17l2.2-.8L18 14z"/></svg></div>
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
    <div class="footer-brand">
      <svg class="icon" viewBox="0 0 24 24"><path d="M3 20h18"/><path d="M3 20l6-12 4 7 3-5 5 10"/></svg>
      Skicom
    </div>
    <div class="footer-sub">
      Generated {{ generated_at }} · Weather via Open-Meteo · Maps via OpenSkiMap & OpenStreetMap
    </div>
  </footer>

</div>

<script>
(function() {
  var html = document.documentElement;
  var toggle = document.getElementById('themeToggle');
  var stored = localStorage.getItem('skicom-theme');
  if (stored) {
    html.setAttribute('data-theme', stored);
  } else if (window.matchMedia('(prefers-color-scheme: dark)').matches) {
    html.setAttribute('data-theme', 'dark');
  }
  function isDark() { return html.getAttribute('data-theme') === 'dark'; }
  var tileAttr = '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>';
  function tileUrl() {
    return isDark()
      ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
      : 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png';
  }
  toggle.addEventListener('click', function() {
    var next = isDark() ? 'light' : 'dark';
    html.setAttribute('data-theme', next);
    localStorage.setItem('skicom-theme', next);
    if (window._skicomMap && window._skicomTile) {
      window._skicomMap.removeLayer(window._skicomTile);
      window._skicomTile = L.tileLayer(tileUrl(), { attribution: tileAttr, maxZoom: 18 }).addTo(window._skicomMap);
    }
  });
})();

{% if accommodations %}
(function() {
  var mapEl = document.getElementById('accomMap');
  if (!mapEl) return;
  var isDark = document.documentElement.getAttribute('data-theme') === 'dark';
  var tileAttr = '&copy; <a href="https://www.openstreetmap.org/copyright">OSM</a> &copy; <a href="https://carto.com/">CARTO</a>';
  var map = L.map('accomMap', { scrollWheelZoom: false });
  window._skicomMap = map;
  window._skicomTile = L.tileLayer(
    isDark
      ? 'https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png'
      : 'https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png',
    { attribution: tileAttr, maxZoom: 18 }
  ).addTo(map);

  var resortIcon = L.divIcon({
    className: '',
    html: '<div style="width:38px;height:38px;background:#FFFFFF;border:3px solid #D97757;border-radius:0;display:flex;align-items:center;justify-content:center;box-shadow:3px 3px 0 #C4623F;font-size:19px;line-height:1;image-rendering:pixelated">⛷️</div>',
    iconSize: [40, 40], iconAnchor: [20, 20]
  });
  L.marker([{{ resort.lat }}, {{ resort.lon }}], { icon: resortIcon, zIndexOffset: 1000 })
    .addTo(map).bindPopup('<div class="popup-name">{{ resort.full_name }}</div><div class="popup-type">⛷️ Ski Resort</div>');

  var bounds = L.latLngBounds([[{{ resort.lat }}, {{ resort.lon }}]]);

  function makeAccomIcon(num) {
    return L.divIcon({
      className: '',
      html: '<div style="position:relative;width:30px;height:40px">'
        + '<svg width="30" height="40" viewBox="0 0 30 40">'
        + '<path d="M15 38 C15 38 2 24 2 14 A13 13 0 1 1 28 14 C28 24 15 38 15 38Z" fill="#D97757" stroke="#C4623F" stroke-width="1.5"/>'
        + '<text x="15" y="18" text-anchor="middle" fill="#FFFFFF" font-family="-apple-system,Helvetica,Arial,sans-serif" font-size="12" font-weight="700">' + num + '</text>'
        + '</svg></div>',
      iconSize: [30, 40], iconAnchor: [15, 40], popupAnchor: [0, -36]
    });
  }

  var places = {{ accom_json }};
  places.forEach(function(a, i) {
    var popup = '<div class="popup-name">' + a.name + '</div>'
      + '<div class="popup-type">' + a.type_icon + ' ' + a.type
      + (a.stars ? ' · ' + a.stars + '★' : '') + '</div>'
      + '<div class="popup-detail">' + a.distance_mi + ' mi from resort</div>';
    if (a.addr) popup += '<div class="popup-detail">' + a.addr + '</div>';
    if (a.phone) popup += '<div class="popup-detail">📞 ' + a.phone + '</div>';
    if (a.website) popup += '<div class="popup-detail"><a href="' + a.website + '" target="_blank">Visit Website ↗</a></div>';
    L.marker([a.lat, a.lon], { icon: makeAccomIcon(i + 1) }).addTo(map).bindPopup(popup);
    bounds.extend([a.lat, a.lon]);
  });

  map.fitBounds(bounds.pad(0.15));
})();
{% endif %}

{% if ai_button %}
(function() {
  var btn = document.getElementById('aiSuggestBtn');
  var out = document.getElementById('aiSuggestOut');
  if (!btn || !out) return;
  var origHTML = btn.innerHTML;
  btn.addEventListener('click', function() {
    var prev = out.querySelector('.ai-error');
    if (prev) prev.remove();
    btn.disabled = true;
    btn.textContent = 'Generating…';
    var resort = btn.getAttribute('data-resort') || '';
    fetch('/suggest?resort=' + encodeURIComponent(resort))
      .then(function(r) { return r.json(); })
      .then(function(data) {
        if (data && data.ok) {
          out.innerHTML = '<div class="summary-card">' + data.html + '</div>';
          btn.style.display = 'none';
        } else {
          showError((data && data.error) || 'Something went wrong. Please try again.');
        }
      })
      .catch(function() {
        showError('Could not reach the suggestion service. Please try again.');
      });
  });
  function showError(msg) {
    btn.disabled = false;
    btn.innerHTML = origHTML;
    var existing = out.querySelector('.ai-error');
    if (existing) existing.remove();
    var div = document.createElement('div');
    div.className = 'ai-error';
    div.textContent = msg;
    out.appendChild(div);
  }
})();
{% endif %}
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


def _build_temp_chart_svg(days: list[dict]) -> str:
    """Build an inline SVG temperature trend chart."""
    if not days or len(days) < 2:
        return ""
    W, H = 360, 130
    PL, PR, PT, PB = 32, 10, 16, 24
    highs = [d.get("temp_high_f", 0) for d in days]
    lows = [d.get("temp_low_f", 0) for d in days]
    labels = [d.get("day_name", "")[:3] for d in days]
    t_min = min(min(lows), min(highs)) - 4
    t_max = max(max(highs), max(lows)) + 4
    t_range = t_max - t_min or 1
    pw, ph = W - PL - PR, H - PT - PB
    n = len(days)
    step = pw / max(n - 1, 1)

    def tx(i): return PL + i * step
    def ty(t): return PT + (1 - (t - t_min) / t_range) * ph

    hp = [(tx(i), ty(t)) for i, t in enumerate(highs)]
    lp = [(tx(i), ty(t)) for i, t in enumerate(lows)]
    high_line = " ".join(f"{x:.1f},{y:.1f}" for x, y in hp)
    low_line = " ".join(f"{x:.1f},{y:.1f}" for x, y in lp)
    fill_pts = high_line + " " + " ".join(f"{x:.1f},{y:.1f}" for x, y in reversed(lp))

    grid = ""
    for t in range(int(t_min // 10 * 10), int(t_max) + 10, 10):
        if t_min < t < t_max:
            y = ty(t)
            grid += f'<line x1="{PL}" y1="{y:.1f}" x2="{W-PR}" y2="{y:.1f}" stroke="var(--chart-grid)" stroke-width="0.5"/>'
            grid += f'<text x="{PL-4}" y="{y+3:.1f}" text-anchor="end" fill="var(--chart-label)" font-size="10">{t:.0f}°</text>'

    dots = ""
    for i, (x, y) in enumerate(hp):
        dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="var(--chart-high)"/>'
        dots += f'<text x="{x:.1f}" y="{y-6:.1f}" text-anchor="middle" fill="var(--chart-high)" font-size="9" font-weight="500">{highs[i]:.0f}°</text>'
    for i, (x, y) in enumerate(lp):
        dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" fill="var(--chart-low)"/>'
        dots += f'<text x="{x:.1f}" y="{y+12:.1f}" text-anchor="middle" fill="var(--chart-low)" font-size="9">{lows[i]:.0f}°</text>'

    dlabels = ""
    for i, label in enumerate(labels):
        dlabels += f'<text x="{tx(i):.1f}" y="{H-5}" text-anchor="middle" fill="var(--chart-day)" font-size="10">{label}</text>'

    return (
        f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto">'
        f'{grid}'
        f'<polygon points="{fill_pts}" fill="var(--chart-fill)"/>'
        f'<polyline points="{high_line}" fill="none" stroke="var(--chart-high)" stroke-width="1.5"/>'
        f'<polyline points="{low_line}" fill="none" stroke="var(--chart-low)" stroke-width="1.5" stroke-dasharray="4,3"/>'
        f'{dots}{dlabels}'
        f'</svg>'
    )


def _build_snow_chart_svg(days: list[dict]) -> str:
    """Build an inline SVG snowfall bar chart."""
    if not days:
        return ""
    W, H = 360, 130
    PL, PR, PT, PB = 32, 10, 16, 24
    snowfalls = [d.get("snowfall_in", 0) or 0 for d in days]
    labels = [d.get("day_name", "")[:3] for d in days]
    s_max = max(snowfalls) if any(s > 0 for s in snowfalls) else 1
    n = len(days)
    pw, ph = W - PL - PR, H - PT - PB
    gap = pw / n
    bw = gap * 0.55

    grid = ""
    if s_max > 0:
        step = max(1, round(s_max / 3))
        for v in range(0, int(s_max) + step + 1, step):
            if v > s_max * 1.1:
                break
            y = PT + ph - (v / s_max) * ph if s_max else PT + ph
            grid += f'<line x1="{PL}" y1="{y:.1f}" x2="{W-PR}" y2="{y:.1f}" stroke="var(--chart-grid)" stroke-width="0.5"/>'
            if v > 0:
                grid += f'<text x="{PL-4}" y="{y+3:.1f}" text-anchor="end" fill="var(--chart-label)" font-size="10">{v}"</text>'

    bars = ""
    for i, (snow, label) in enumerate(zip(snowfalls, labels)):
        cx = PL + i * gap + gap / 2
        bx = cx - bw / 2
        if snow > 0:
            bh = (snow / s_max) * ph
            by = PT + ph - bh
            bars += f'<rect x="{bx:.1f}" y="{by:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="3" fill="var(--chart-accent)" opacity="0.75"/>'
            bars += f'<text x="{cx:.1f}" y="{by-4:.1f}" text-anchor="middle" fill="var(--chart-accent)" font-size="10" font-weight="500">{snow}"</text>'
        else:
            bars += f'<rect x="{bx:.1f}" y="{PT+ph-2:.1f}" width="{bw:.1f}" height="2" rx="1" fill="var(--chart-bar-empty)"/>'
        bars += f'<text x="{cx:.1f}" y="{H-5}" text-anchor="middle" fill="var(--chart-day)" font-size="10">{label}</text>'

    return (
        f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto">'
        f'{grid}{bars}'
        f'</svg>'
    )


def _build_depth_chart_svg(days: list[dict]) -> str:
    """Build an inline SVG snow depth area chart."""
    if not days:
        return ""
    depths = []
    for d in days:
        sd = d.get("snow_depth_in")
        if sd is None:
            sd = d.get("snow_depth_cm", 0)
            if sd:
                sd = round(sd / 2.54, 1)
        depths.append(sd or 0)
    if not any(v > 0 for v in depths):
        return ""
    W, H = 360, 130
    PL, PR, PT, PB = 32, 10, 16, 24
    labels = [d.get("day_name", "")[:3] for d in days]
    d_max = max(depths) * 1.15 or 1
    pw, ph = W - PL - PR, H - PT - PB
    n = len(days)
    step = pw / max(n - 1, 1)

    def tx(i): return PL + i * step
    def ty(v): return PT + (1 - v / d_max) * ph

    pts = [(tx(i), ty(v)) for i, v in enumerate(depths)]
    line = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    baseline = PT + ph
    fill_pts = f"{pts[0][0]:.1f},{baseline} " + line + f" {pts[-1][0]:.1f},{baseline}"

    grid = ""
    g_step = max(1, round(d_max / 3))
    for v in range(0, int(d_max) + g_step + 1, g_step):
        if v > d_max:
            break
        y = ty(v)
        grid += f'<line x1="{PL}" y1="{y:.1f}" x2="{W-PR}" y2="{y:.1f}" stroke="var(--chart-grid)" stroke-width="0.5"/>'
        if v > 0:
            grid += f'<text x="{PL-4}" y="{y+3:.1f}" text-anchor="end" fill="var(--chart-label)" font-size="10">{v}"</text>'

    dots = ""
    for i, (x, y) in enumerate(pts):
        if depths[i] > 0:
            dots += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="var(--chart-accent)"/>'
            dots += f'<text x="{x:.1f}" y="{y-6:.1f}" text-anchor="middle" fill="var(--chart-accent)" font-size="9" font-weight="500">{depths[i]:.0f}"</text>'

    dlabels = ""
    for i, label in enumerate(labels):
        dlabels += f'<text x="{tx(i):.1f}" y="{H-5}" text-anchor="middle" fill="var(--chart-day)" font-size="10">{label}</text>'

    return (
        f'<svg viewBox="0 0 {W} {H}" xmlns="http://www.w3.org/2000/svg" style="width:100%;height:auto">'
        f'{grid}'
        f'<polygon points="{fill_pts}" fill="var(--chart-fill)"/>'
        f'<polyline points="{line}" fill="none" stroke="var(--chart-accent)" stroke-width="1.5"/>'
        f'{dots}{dlabels}'
        f'</svg>'
    )


def render_report(
    resort: dict,
    forecast: dict,
    accommodations: list[dict],
    summary: str | None,
    config: dict,
    ai_button: bool = False,
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

    zoom = 13
    generated_at = datetime.now().strftime("%B %d, %Y at %I:%M %p")

    llm_cfg = config.get("llm", {})
    llm_model = llm_cfg.get("model", "") if llm_cfg.get("enabled") and summary else ""
    llm_provider_icon = _provider_icon(llm_cfg.get("api_base", "")) if llm_model else ""

    accom_json = json.dumps([
        {k: a[k] for k in ("name", "type", "type_icon", "lat", "lon",
                            "distance_mi", "phone", "website", "stars", "addr")}
        for a in accommodations
    ], ensure_ascii=False)

    days = forecast.get("daily", [])
    temp_chart_svg = _build_temp_chart_svg(days)
    snow_chart_svg = _build_snow_chart_svg(days)
    depth_chart_svg = _build_depth_chart_svg(days)

    template = Template(TEMPLATE)
    html = template.render(
        resort=resort,
        forecast=forecast,
        accommodations=accommodations,
        summary=summary,
        ai_button=ai_button,
        generated_at=generated_at,
        search_radius_mi=search_radius_mi,
        zoom=zoom,
        llm_model=llm_model,
        llm_provider_icon=llm_provider_icon,
        accom_json=accom_json,
        temp_chart_svg=temp_chart_svg,
        snow_chart_svg=snow_chart_svg,
        depth_chart_svg=depth_chart_svg,
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
        f"  Coordinates: {abs(resort['lat'])}°{'N' if resort['lat'] >= 0 else 'S'}, {abs(resort['lon'])}°{'E' if resort['lon'] >= 0 else 'W'}",
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
        "  6-DAY FORECAST",
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
    base_d = snow.get("base_depth_in")
    summit_d = snow.get("summit_depth_in")
    base_str = f'{base_d}"' if base_d is not None else "--"
    summit_str = f'{summit_d}"' if summit_d is not None else "--"

    lines += [
        "",
        f"  Total snowfall: {snow.get('total_snowfall_in', 0)}\"  |  "
        f"Snow days: {snow.get('snow_days_count', 0)}  |  "
        f"Best powder day: {best_str}",
        f"  Base depth: {base_str}  |  Summit depth: {summit_str}",
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
