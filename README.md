# Skicom

**Plan your ski trip from the terminal.** One command. 386 resorts. No brochures.

```bash
python3 skicom.py "Jackson Hole"
```

![Hero — Resort overview with trail map](docs/skicom_hero.png)

## Why

You check `git status` more than the weather. You'd rather pipe JSON than browse travel sites. But when the snow dumps, you still need to know *where to go, when to go, and where to sleep*.

Skicom pulls it all together in one shot — trail maps, forecasts, lodging, and an AI brief — then drops a clean report in your browser. No accounts. No ads. Just data.

## What You Get

**Trail map** — OpenSkiMap embed, centered on your resort. Runs, lifts, terrain.

**7-day snow & weather** — Open-Meteo forecast with daily cards. Snow days highlighted. Best powder day pinned by date.

![Forecast — 7-day weather cards with snow summary banner](docs/skicom_forecast.png)

**Nearby stays** — Hotels, chalets, hostels from OpenStreetMap within configurable radius. Distance, contact, direct links.

![Stays — Accommodation cards with map and visit buttons](docs/skicom_stays.png)

**AI trip brief** — Plug in any OpenAI-compatible LLM (OpenAI, Ollama, LM Studio, etc). Gets a short "best days to ski / what to pack / where to stay" summary.

![Summary — AI-generated trip advisor card](docs/skicom_summary.png)

**Dual output** — HTML with Nordic dark UI + falling snow, and a plaintext `.txt` for your terminal or clipboard.

## Quick Start

```bash
git clone https://github.com/KumaKuma2002/Skicom.git
cd Skicom
pip install -r requirements.txt

# Optional: enable AI summary
cp config.example.yaml config.yaml
# Edit config.yaml → add your API key, set enabled: true

python3 skicom.py "Mammoth"
```

Works out of the box without config — you just won't get the LLM summary.

### Usage

```bash
python3 skicom.py                        # interactive picker
python3 skicom.py "Vail"                 # direct search
python3 skicom.py "Crystal Mountain WA"  # state hint for disambiguation
python3 skicom.py "breck"                # aliases work too
python3 skicom.py --no-open "Stowe"      # skip auto-open browser
```

## Config

```bash
cp config.example.yaml config.yaml
```

```yaml
llm:
  enabled: true
  api_base: "https://api.openai.com/v1"  # or http://localhost:11434/v1 for Ollama
  api_key: "sk-..."
  model: "gpt-5-mini"
  max_tokens: 4096

weather:
  forecast_days: 7

accommodations:
  search_radius_m: 15000
  max_results: 12

output:
  directory: "./reports"
  auto_open: true
```

## Resort Database

**386 resorts** across the US and Canada. Fuzzy name matching with alias support — `"a-basin"`, `"smuggs"`, `"squaw valley"`, `"bachelor"` all resolve. Add `", WA"` or `"washington"` to disambiguate when names collide (e.g. Crystal Mountain exists in both WA and MI).

## Stack

| What | How | Cost |
|------|-----|------|
| Weather & snow | [Open-Meteo](https://open-meteo.com) | Free |
| Trail maps | [OpenSkiMap](https://openskimap.org) | Free |
| Accommodations | [OpenStreetMap / Overpass](https://overpass-api.de) | Free |
| AI summary | Any OpenAI-compatible API | BYOK |
| Resort search | [thefuzz](https://github.com/seatgeek/thefuzz) | Free |
| UI | Jinja2 + hand-rolled Nordic CSS | Free |

No API keys needed except for the optional LLM summary.

## License

MIT
