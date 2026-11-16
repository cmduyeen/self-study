#!/usr/bin/env python3
"""
Zero-Dependency Live Server (VS Code Live Server style)
- Serves HTML/CSS/JS on http://127.0.0.1:5500 (default)
- Automatically injects a tiny live-reload script into HTML responses in memory
  (never modifies your files on disk)
- Whenever any .html, .css, or .js file is saved (Ctrl+S in Micro),
  the browser reloads automatically within ~300ms!
"""

import argparse
import http.server
import json
import os
import socket
import socketserver
import sys
import time
from pathlib import Path
from urllib.parse import unquote

LIVE_RELOAD_SNIPPET = """
<!-- Injected by Self-Study Live Server -->
<script>
(function() {
    let lastVersion = null;
    async function checkReload() {
        try {
            const res = await fetch("/__live_check?t=" + Date.now(), { cache: "no-store" });
            const data = await res.json();
            if (lastVersion === null) {
                lastVersion = data.mtime;
            } else if (data.mtime !== lastVersion) {
                lastVersion = data.mtime;
                window.location.reload();
            }
        } catch (e) {}
    }
    setInterval(checkReload, 350);
    checkReload();
})();
</script>
"""


def get_latest_mtime(root_dir: Path) -> int:
    latest = 0
    try:
        for p in root_dir.rglob("*"):
            if p.is_file() and p.suffix.lower() in (".html", ".htm", ".css", ".js", ".json", ".svg"):
                try:
                    m = p.stat().st_mtime_ns
                    if m > latest:
                        latest = m
                except OSError:
                    pass
    except Exception:
        pass
    return latest


class LiveReloadHandler(http.server.SimpleHTTPRequestHandler):
    root_dir: Path = Path.cwd()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(self.root_dir), **kwargs)

    def log_message(self, format, *args):
        # Suppress noisy polling logs
        if len(args) > 0 and "/__live_check" in str(args[0]):
            return
        super().log_message(format, *args)

    def end_headers(self):
        # Disable browser caching so edits always show immediately
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0")
        self.send_header("Pragma", "no-cache")
        self.send_header("Expires", "0")
        super().end_headers()

    def do_GET(self):
        if self.path.startswith("/__live_check"):
            mtime = get_latest_mtime(self.root_dir)
            payload = json.dumps({"mtime": mtime}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if self.path.startswith("/__live_info"):
            payload = json.dumps({"root": str(self.root_dir.resolve())}).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        # Check if request resolves to an HTML file so we can inject LIVE_RELOAD_SNIPPET
        clean_path = unquote(self.path.split("?", 1)[0].split("#", 1)[0]).lstrip("/")
        target = self.root_dir / clean_path
        if target.is_dir():
            for idx_name in ("index.html", "index.htm"):
                if (target / idx_name).is_file():
                    target = target / idx_name
                    break

        if target.is_file() and target.suffix.lower() in (".html", ".htm"):
            try:
                content = target.read_text(encoding="utf-8", errors="replace")
                if "</body>" in content.lower():
                    idx = content.lower().rfind("</body>")
                    content = content[:idx] + LIVE_RELOAD_SNIPPET + content[idx:]
                else:
                    content = content + LIVE_RELOAD_SNIPPET
                data = content.encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)
                return
            except Exception:
                pass

        super().do_GET()


class ThreadedHTTPServer(socketserver.ThreadingMixIn, http.server.HTTPServer):
    daemon_threads = True
    allow_reuse_address = True


def main():
    parser = argparse.ArgumentParser(description="Self-Study Live Server with Auto-Reload")
    parser.add_argument("-d", "--directory", default=".", help="Root directory to serve")
    parser.add_argument("-p", "--port", type=int, default=5500, help="Port (default: 5500)")
    args = parser.parse_args()

    root = Path(args.directory).resolve()
    LiveReloadHandler.root_dir = root

    with ThreadedHTTPServer(("127.0.0.1", args.port), LiveReloadHandler) as httpd:
        print(f"⚡ Live Server đang chạy tại: http://127.0.0.1:{args.port}")
        print(f"📂 Thư mục theo dõi tự động: {root}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
