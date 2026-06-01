"""Skicom desktop app — launch Skicom in a native local window.

This is the cozy, app-like way to run Skicom. It starts the same little
stdlib HTTP server that powers the web version (see server.py), but instead
of opening a browser tab it wraps it in a real desktop window via pywebview.

Run directly:   python app.py
Or pick a port:  python app.py --port 5180 -c config.yaml

If pywebview isn't installed, we gracefully fall back to opening Skicom in
your default browser so the app still works.

Robustness note: when launched from a macOS .app bundle (double-clicked in
Finder), there's no Terminal attached — stdout/stderr are redirected to
~/Library/Logs/Skicom.log. So we log generously (Python executable, version,
whether pywebview imported) and dump a full traceback on any failure, instead
of dying silently with a closed window and no clue why.
"""
import argparse
import sys
import traceback


def launch(port: int = 0, config_path: str = "config.yaml"):
    """Open Skicom in a native desktop window (or the browser as a fallback).

    Designed to be safe to run from a windowless .app bundle: every failure
    path logs a full traceback so the cause is visible in ~/Library/Logs.
    """
    # Up-front diagnostics. When this runs inside a bundle these are the first
    # things you'll want to see in the log to confirm which interpreter and
    # environment actually started — bundles often pick a surprising python.
    print("  Skicom launching…", flush=True)
    print("     python executable: %s" % sys.executable, flush=True)
    print("     python version:    %s" % sys.version.replace("\n", " "), flush=True)

    try:
        _launch(port=port, config_path=config_path)
    except Exception:
        # Catch-all: anything that escapes _launch (server bind failure,
        # pywebview blowing up, etc.) lands here. Dump the full traceback to
        # the log so a windowless bundle isn't a black box.
        print("\n  ✗  Skicom failed to launch. Full traceback follows:", flush=True)
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        raise


def _launch(port: int, config_path: str):
    """Inner launch logic, wrapped by launch() for top-level error logging."""
    # server is imported here (not at module top) so that an import error in
    # the server stack is captured by launch()'s try/except and logged with a
    # traceback, rather than failing at module-import time before logging is up.
    import server

    # pywebview is the only non-stdlib UI dep, and it's optional — import it
    # lazily and fall back to the browser if (and only if) it's MISSING.
    try:
        import webview  # pywebview
        print("     pywebview imported: yes", flush=True)
    except ImportError:
        print("     pywebview imported: no", flush=True)
        print("\n  ⛷  Skicom's native window needs pywebview.", flush=True)
        print("     Install it with:  pip install pywebview", flush=True)
        print("     Opening Skicom in your browser instead…\n", flush=True)
        # serve() blocks (serve_forever) and opens the browser for us.
        server.serve(port=port or 8765, open_browser=True, config_path=config_path)
        return

    # Start the HTTP server on a background daemon thread. It does NOT open a
    # browser; it just binds 127.0.0.1 and hands back the live URL.
    httpd, url = server.start_in_thread(port=port, config_path=config_path)
    print("\n  ⛷  Skicom ready — native window at  %s" % url, flush=True)
    print("     Close the window to quit.\n", flush=True)
    sys.stdout.flush()

    try:
        # Create the desktop window pointed at the local server, then run the
        # pywebview event loop. On macOS pywebview uses the built-in WKWebView
        # (cocoa) backend, so no extra GUI toolkit is needed — calling
        # webview.start() with no gui arg picks that default and brings the
        # window to the foreground. start() blocks until the window closes.
        webview.create_window("Skicom", url, width=1180, height=860,
                              min_size=(820, 620))
        webview.start()
    except Exception:
        # webview imported fine but window creation / the event loop threw.
        # This is NOT a "pywebview missing" situation, so we do NOT silently
        # fall back to the browser — we log the traceback and re-raise so the
        # real WKWebView/cocoa error is visible in the log.
        print("\n  ✗  pywebview is installed but the native window failed:", flush=True)
        traceback.print_exc()
        sys.stdout.flush()
        raise
    finally:
        # Window closed (or something went wrong) — stop the server cleanly so
        # the daemon thread can exit and the port is released.
        httpd.shutdown()
        print("\n  Bye! ⛄\n", flush=True)


def main():
    parser = argparse.ArgumentParser(description="Skicom — native desktop app")
    # 0 lets the OS pick a free port; server.start_in_thread reports the real one.
    parser.add_argument("--port", type=int, default=0,
                        help="Port to bind (0 = pick a free port automatically)")
    parser.add_argument("--config", "-c", default="config.yaml",
                        help="Path to the Skicom config file")
    args = parser.parse_args()
    launch(port=args.port, config_path=args.config)


if __name__ == "__main__":
    main()
