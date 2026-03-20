<div align="center">

# Skicom

### `the only ski trip planner you need — if you'd rather run a script than open a travel site.`

[![Python](https://img.shields.io/badge/python-3.9+-3776AB?logo=python&logoColor=white)](#quick-start)
[![License: MIT](https://img.shields.io/badge/license-MIT-d4a574)](#license)
[![Resorts](https://img.shields.io/badge/resorts-386-7eb8d8)](#resort-database)
[![No API key needed](https://img.shields.io/badge/API%20keys-none%20required*-8fbc8f)](#stack)

**One command. 386 resorts. Trail maps, snow forecasts, lodging, AI brief. Done.**

```bash
python3 skicom.py "Jackson Hole"
```

</div>

![Hero — Resort overview with trail map](docs/skicom_hero.png)

---

## Contents

- [Why Skicom](#why-skicom)
- [What You Get](#what-you-get)
- [Quick Start](#quick-start) *(3 lines)*
- [Usage](#usage)
- [Config](#config)
- [Resort Database](#resort-database)
- [Stack](#stack)
- [License](#license)

---

## Why Skicom

You `grep` logs before breakfast. You think in pipes. You'd mass-rename 400 files before opening a GUI.

But when Friday rolls around and the forecast says *powder* — you're stuck scrolling ad-heavy resort sites, juggling weather tabs, and comparing hotels like it's 2005.

**Skicom fixes that.** One command, one report, everything you need:

> trail map + 7-day snow forecast + nearby stays + AI trip brief → browser

No accounts. No ads. No tracking. Open source, open data, runs offline (except the APIs). This is how skiers who write code plan trips.

---

## What You Get

**Trail map** — OpenSkiMap embed centered on your resort. Runs, lifts, terrain at a glance.

**7-day snow & weather** — daily forecast cards from Open-Meteo. Snow days glow amber. Best powder day pinned by exact date.

![Forecast — 7-day weather cards with snow summary banner](docs/skicom_forecast.png)

**Nearby stays** — hotels, chalets, hostels from OpenStreetMap. Distance, address, phone, and a "Visit Website" button.

![Stays — Accommodation cards with map and visit buttons](docs/skicom_stays.png)

**AI trip brief** — plug in any OpenAI-compatible LLM. One-paragraph answer: best ski days, what to pack, where to sleep.

![Summary — AI-generated trip advisor card](docs/skicom_summary.png)

**Dual output** — HTML report with Nordic dark UI + falling snow, and a `.txt` you can `cat`, email, or paste into Slack.

---

## Quick Start

```bash
git clone https://github.com/KumaKuma2002/Skicom.git && cd Skicom
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python3 skicom.py "Mammoth"
```

That's it. Works instantly — no config, no API keys. The AI summary is optional (see [Config](#config)).

> **Windows?** Use `.venv\Scripts\activate` instead.

---

## Usage

```bash
python3 skicom.py                        # interactive picker
python3 skicom.py "Vail"                 # direct search
python3 skicom.py "Crystal Mountain WA"  # state hint to disambiguate
python3 skicom.py "breck"                # aliases work
python3 skicom.py --no-open "Stowe"      # generate without opening browser
```

---

## Config

Only needed if you want the AI trip summary. Everything else works without it.

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml`:

```yaml
llm:
  enabled: true
  api_base: "https://api.openai.com/v1"  # or http://localhost:11434/v1 for Ollama
  api_key: "sk-..."
  model: "gpt-5-mini"
  max_tokens: 4096
```

Other settings (weather days, search radius, output directory) have sensible defaults — see `config.example.yaml`.

---

## Resort Database

**386 resorts** across the US and Canada. Fuzzy matching with alias support:

```
"a-basin"       → Arapahoe Basin, CO
"smuggs"        → Smugglers' Notch, VT
"squaw valley"  → Palisades Tahoe, CA
"bachelor"      → Mount Bachelor, OR
"white pass WA" → White Pass Ski Area, WA
```

State hints (`", WA"` or `"washington"`) disambiguate when names collide.

---

## Stack

| What | How | Cost |
|------|-----|------|
| Weather & snow | [Open-Meteo](https://open-meteo.com) | Free |
| Trail maps | [OpenSkiMap](https://openskimap.org) | Free |
| Accommodations | [OpenStreetMap / Overpass](https://overpass-api.de) | Free |
| AI summary | Any OpenAI-compatible API | BYOK |
| Resort search | [thefuzz](https://github.com/seatgeek/thefuzz) | Free |
| UI | Jinja2 + hand-rolled Nordic CSS | Free |

*\*No API keys needed except for the optional LLM summary.*

---

## License

MIT
