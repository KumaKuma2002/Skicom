"""Skicom local web app — browse/select + search resorts, generate reports.

Starts a tiny stdlib HTTP server (no extra deps) that serves a cozy home page
where you can search or browse the resort catalog, then click a resort to
generate its full Skicom report on the fly.

Run directly:   python server.py            (opens your browser)
Or via the CLI:  python skicom.py --serve
"""
import copy
import json
import os
import tempfile
import threading
import webbrowser
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import yaml

from resorts import load_resorts, find_resort
from weather import get_full_forecast
from accommodations import fetch_accommodations
from llm import generate_summary
from renderer import render_report

EMPTY_FORECAST = {
    "daily": [],
    "snow_summary": {"total_snowfall_in": 0, "snow_days_count": 0, "best_powder_day": None,
                     "base_depth_in": None, "summit_depth_in": None, "depth_source_ft": 0},
    "timezone": "",
    "elevation_m": None,
}

# Caches the fetched (forecast, accommodations) per resort so the opt-in
# /suggest (AI brief) endpoint doesn't have to re-hit the weather / OSM APIs.
_PIPELINE_CACHE: dict = {}


def _escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _summary_to_html(text: str) -> str:
    """Turn an LLM brief (plain text / light markdown) into simple safe HTML."""
    import re
    out = []
    for para in (p.strip() for p in text.split("\n\n")):
        if not para:
            continue
        para = _escape(para)
        para = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", para)
        out.append("<p>%s</p>" % para.replace("\n", "<br>"))
    return "".join(out)


def load_config(path: str = "config.yaml") -> dict:
    # Search the given path (cwd-relative) first, then a standard private
    # location. The bundled .app has no cwd config, so ~/.config/skicom lets you
    # enable the AI brief there without ever putting your key in the bundle.
    candidates = [path, os.path.expanduser("~/.config/skicom/config.yaml")]
    for p in candidates:
        if p and os.path.exists(p):
            with open(p, "r") as f:
                return yaml.safe_load(f) or {}
    return {}


def _fetch_pipeline(resort: dict, config: dict):
    """Fetch (forecast, accommodations) for a resort, with graceful fallbacks.

    The two network calls are independent, so we run them concurrently — the
    report comes back in ~max(weather, overpass) instead of the sum.
    """
    from concurrent.futures import ThreadPoolExecutor

    weather_days = config.get("weather", {}).get("forecast_days", 6)
    radius = config.get("accommodations", {}).get("search_radius_m", 15000)
    max_accom = config.get("accommodations", {}).get("max_results", 12)

    def _weather():
        try:
            return get_full_forecast(resort["lat"], resort["lon"], days=weather_days, resort=resort)
        except Exception:
            return copy.deepcopy(EMPTY_FORECAST)

    def _accom():
        try:
            return fetch_accommodations(resort["lat"], resort["lon"], radius_m=radius, max_results=max_accom)
        except Exception:
            return []

    with ThreadPoolExecutor(max_workers=2) as ex:
        f_fut, a_fut = ex.submit(_weather), ex.submit(_accom)
        return f_fut.result(), a_fut.result()


def build_report(resort: dict, config: dict) -> str:
    """Run the pipeline for a resort and return the generated HTML path.

    The AI brief is NOT generated here — it's opt-in via the report's
    "AI Suggest" button (the /suggest endpoint). We cache the fetched
    forecast/accommodations so /suggest needn't re-hit the APIs.
    """
    forecast, accommodations = _fetch_pipeline(resort, config)
    if len(_PIPELINE_CACHE) >= 50:  # simple bound — evict oldest
        _PIPELINE_CACHE.pop(next(iter(_PIPELINE_CACHE)), None)
    _PIPELINE_CACHE[resort["full_name"]] = (forecast, accommodations)

    # Served reports are ephemeral — write them to a writable temp dir. This
    # also keeps a bundled .app working (its cwd is '/', so "./reports" fails).
    reports_dir = os.path.join(tempfile.gettempdir(), "skicom-reports")
    os.makedirs(reports_dir, exist_ok=True)
    cfg = {**config, "output": {**config.get("output", {}), "auto_open": False, "directory": reports_dir}}
    html_path, _txt_path = render_report(resort, forecast, accommodations, None, cfg, ai_button=True)
    return html_path


ERROR_HTML = """<!DOCTYPE html><html><head><meta charset="utf-8">
<title>Skicom</title><style>body{{font-family:-apple-system,sans-serif;background:#FAF6EF;
color:#2B2622;display:flex;min-height:100vh;align-items:center;justify-content:center;text-align:center}}
a{{color:#D97757}}</style></head><body><div><h1>{title}</h1><p>{msg}</p>
<p><a href="/">&larr; Back to Skicom</a></p></div></body></html>"""

# Fields the home page actually uses — keeps the injected payload lean.
_CARD_FIELDS = ("name", "full_name", "state", "country", "region",
                "lat", "lon", "elevation_ft", "vertical_ft", "lifts", "acres")

_HOME_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates", "home.html")

# Curated marquee resorts shown by default (instead of dumping all 527).
# Resolved through fuzzy search so small name differences still match.
_FEATURED_QUERIES = [
    "Vail", "Aspen Snowmass", "Jackson Hole", "Palisades Tahoe", "Park City", "Mammoth",
    "Zermatt", "Chamonix", "Val d'Isere", "St. Anton", "Cortina d'Ampezzo", "Verbier",
    "Niseko", "Hakuba", "Whistler Blackcomb", "Banff Sunshine", "Cerro Catedral", "Thredbo",
]


def _slim(r: dict) -> dict:
    return {k: r[k] for k in _CARD_FIELDS if k in r}


def _featured() -> list:
    out, seen = [], set()
    for q in _FEATURED_QUERIES:
        r = find_resort(q)
        if r and r["full_name"] not in seen:
            seen.add(r["full_name"])
            out.append(_slim(r))
    return out


def _safe_json(obj) -> str:
    """JSON for inline <script> injection — neutralize </script> & line seps."""
    s = json.dumps(obj, ensure_ascii=False)
    return (s.replace("</", "<\\/")
             .replace(" ", "\\u2028")
             .replace(" ", "\\u2029"))


def _load_home_template() -> str:
    if not os.path.exists(_HOME_PATH):
        raise FileNotFoundError("home.html template missing at %s" % _HOME_PATH)
    with open(_HOME_PATH, encoding="utf-8") as f:
        return f.read()


def _home_page() -> bytes:
    tpl = _load_home_template()
    html = (tpl.replace("__RESORTS_JSON__", _safe_json([_slim(r) for r in load_resorts()]))
               .replace("__FEATURED_JSON__", _safe_json(_featured())))
    return html.encode("utf-8")


class Handler(BaseHTTPRequestHandler):
    config = {}

    def _send(self, body: bytes, status: int = 200, ctype: str = "text/html; charset=utf-8"):
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        parsed = urlparse(self.path)
        path = parsed.path
        if path == "/" or path == "/index.html":
            self._send(_home_page())
        elif path == "/report":
            self._handle_report(parse_qs(parsed.query))
        elif path == "/suggest":
            self._handle_suggest(parse_qs(parsed.query))
        elif path == "/favicon.ico":
            self._send(b"", 204, "image/x-icon")
        else:
            self._send(ERROR_HTML.format(title="Not found", msg="That page doesn't exist.").encode(), 404)

    def _handle_report(self, qs):
        name = (qs.get("resort") or [""])[0]
        if not name:
            self._send(ERROR_HTML.format(title="No resort", msg="No resort was specified.").encode(), 400)
            return
        resort = find_resort(name)
        if not resort:
            self._send(ERROR_HTML.format(
                title="Resort not found",
                msg='Couldn\'t match &ldquo;%s&rdquo;.' % name).encode(), 404)
            return
        try:
            html_path = build_report(resort, self.config)
            with open(html_path, "rb") as f:
                self._send(f.read())
        except Exception as e:  # pragma: no cover - defensive
            self._send(ERROR_HTML.format(
                title="Something went wrong",
                msg="Could not build the report: %s" % e).encode(), 500)

    def _handle_suggest(self, qs):
        """On-demand AI brief (opt-in via the report's 'AI Suggest' button)."""
        def reply(obj, status=200):
            self._send(json.dumps(obj).encode(), status, "application/json; charset=utf-8")

        name = (qs.get("resort") or [""])[0]
        resort = find_resort(name) if name else None
        if not resort:
            reply({"ok": False, "error": "Resort not found."}, 404)
            return
        if not self.config.get("llm", {}).get("enabled", False):
            reply({"ok": False, "error": "AI brief isn't set up. Add an LLM to config.yaml "
                                          "(see the README), then restart Skicom."})
            return

        cached = _PIPELINE_CACHE.get(resort["full_name"])
        forecast, accommodations = cached if cached else _fetch_pipeline(resort, self.config)
        try:
            text = generate_summary(resort, forecast, accommodations, self.config)
        except Exception as e:  # pragma: no cover - defensive
            reply({"ok": False, "error": "AI request failed: %s" % e})
            return
        if not text:
            reply({"ok": False, "error": "The AI brief came back empty — check your LLM settings."})
            return
        reply({"ok": True, "html": _summary_to_html(text)})

    def log_message(self, fmt, *args):  # quieter console
        pass


def start_in_thread(port: int = 0, config_path: str = "config.yaml"):
    """Start the server on a daemon thread (port 0 = OS-chosen free port).

    Returns (httpd, base_url). Used by the native desktop app (app.py).
    """
    Handler.config = load_config(config_path)
    load_resorts()  # warm the cache before requests arrive
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    base_url = "http://127.0.0.1:%d/" % httpd.server_address[1]
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd, base_url


def serve(port: int = 8765, open_browser: bool = True, config_path: str = "config.yaml"):
    Handler.config = load_config(config_path)
    httpd = ThreadingHTTPServer(("127.0.0.1", port), Handler)
    url = "http://127.0.0.1:%d/" % port
    n = len(load_resorts())
    print("\n  ⛷  Skicom is running at  %s" % url)
    print("     %d resorts ready to browse. Press Ctrl+C to stop.\n" % n)
    if open_browser:
        threading.Timer(0.6, lambda: webbrowser.open(url)).start()
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n  Bye! ⛄\n")
        httpd.shutdown()


if __name__ == "__main__":
    import argparse
    p = argparse.ArgumentParser(description="Skicom local web app")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--no-open", action="store_true")
    p.add_argument("--config", "-c", default="config.yaml")
    a = p.parse_args()
    serve(port=a.port, open_browser=not a.no_open, config_path=a.config)
