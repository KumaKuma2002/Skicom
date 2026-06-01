<div align="center">

# Skicom

### A cozy, local ski-trip planner for your Mac.

[![Python](https://img.shields.io/badge/python-3.9+-3776AB?logo=python&logoColor=white)](#quick-start)
[![macOS app](https://img.shields.io/badge/macOS-native%20app-2B2622?logo=apple&logoColor=white)](#quick-start)
[![License: MIT](https://img.shields.io/badge/license-MIT-d4a574)](#license)
[![Resorts](https://img.shields.io/badge/resorts-527-7eb8d8)](#what-you-get)

[github.com/KumaKuma2002/Skicom](https://github.com/KumaKuma2002/Skicom)

</div>

![Skicom](docs/skicom_hero.png)

Skicom is a native macOS app for planning ski trips. It runs entirely on your
machine — a small desktop window over a tiny Python server bound to `127.0.0.1`,
not a website. No cloud, no account, no tracking.

Browse **527 ski resorts across 22 countries** — the Alps, Japan, Canada,
Scandinavia, the Southern Hemisphere (ski in July), and more.

---

## Quick Start

```bash
git clone https://github.com/KumaKuma2002/Skicom.git
cd Skicom
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
./mac/build_app.sh
```

This builds `Skicom.app` onto your Desktop. **Double-click it** to open.

First launch (the app is unsigned): right-click `Skicom.app` → **Open**, or run
`./mac/sign_local.sh` once to clear the warning.

---

## What You Get

A friendly home screen with:

- **Search** resorts by name, region, or country
- **Browse by region** — Alps, Japan, Canada, Scandinavia, and more
- **Featured** picks and an **I'm Feeling Lucky** button
- **Map view** — a clickable map with ski trails and lifts
- A **light/dark** theme

Pick a resort and you get a report with:

- A **6-day snow forecast** with charts
- An interactive **trail & stays map**
- **Nearby places to stay**
- An optional one-click **AI Suggest** trip brief (off by default)

---

## Terminal

The build also adds a `skicom` command:

```bash
skicom              # interactive picker
skicom "Zermatt"    # report for a resort
skicom --app        # open the native window
skicom --serve      # open in your browser instead
```

---

## AI brief (optional)

The AI trip brief is **off by default**. To turn it on, add any OpenAI-compatible
API key to `config.yaml`. That file is git-ignored, so your key stays on your
machine and is never committed.

---

## License

[MIT](LICENSE)
