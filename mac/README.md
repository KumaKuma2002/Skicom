# Skicom for macOS ⛷️

Skicom is a cozy, **local** ski-trip planner. On a Mac it runs as a **native desktop window** (via [pywebview](https://pywebview.flowrl.com/)) — not a website. Everything stays on your machine: the app serves on `127.0.0.1` only and is never exposed to your network.

Search or browse the world's ski resorts, pick one, and get a full report: a 6-day forecast, charts, nearby places to stay, and an optional AI brief.

## Build it

```bash
./mac/build_app.sh
```

This produces a **self-contained `Skicom.app`** on your Desktop. The bundle carries its own Python venv and a copy of the app code inside it, so macOS doesn't block it from reading your Desktop. The first build downloads and installs dependencies — give it about a minute.

> Build at a custom location with `./mac/build_app.sh /path/to/Foo.app`. Re-running rebuilds the bundle from scratch.

## Run it

Double-click **`Skicom.app`**.

First launch of an unsigned app can trip macOS Gatekeeper, which may say the app "cannot be opened." Two ways around it:

- **Right-click** the app → **Open** → **Open**, or
- Run `./mac/sign_local.sh` once to ad-hoc-sign and de-quarantine it.

If the window doesn't appear, check the log at `~/Library/Logs/Skicom.log`.

## Terminal usage

The build also installs a `skicom` command on your PATH (a symlink into `~/.local/bin`):

| Command | What it does |
| --- | --- |
| `skicom` | Interactive resort picker in the terminal |
| `skicom "Zermatt"` | Generate a report for a resort |
| `skicom --app` | Open the native desktop window |
| `skicom --serve` | Open the web app in your browser instead (fallback) |

> If `~/.local/bin` isn't on your `PATH`, either add it or run the launcher directly from `mac/skicom`.

## How it works

The app starts a tiny Python stdlib HTTP server bound to `127.0.0.1` on a random free port, then opens a native window pointed at it. The home screen lets you search or browse resorts by region and pick one; clicking a resort generates a full report (6-day forecast, charts, nearby stays, and an optional AI brief). The AI brief is **off by default** — click **"AI Suggest"** on a report to generate it (this requires an LLM configured in `config.yaml`).

## Plan B: a fully-frozen app

If you'd rather not rely on a system Python at all:

```bash
./mac/build_pyinstaller.sh
```

This builds a fully-frozen alternative app at `mac/dist/Skicom.app` (no system Python needed).

## Secrets

Your LLM API key lives only in `config.yaml`, which is git-ignored. It never leaves your machine.
