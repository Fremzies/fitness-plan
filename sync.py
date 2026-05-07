#!/usr/bin/env python3
"""Local helper that bakes browser edits into fitness_plan.html and pushes to GitHub.

Usage:
    python3 sync.py

The HTML page POSTs its localStorage state to http://localhost:7777/sync.
This script writes the state into the <script id="user-data"> block,
git-commits the change, and pushes to origin/main.

Stdlib only — no pip install needed.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

REPO = Path(__file__).resolve().parent
HTML = REPO / "fitness_plan.html"
PORT = 7777

DATA_BLOCK_RE = re.compile(
    r'(<script type="application/json" id="user-data">)(.*?)(</script>)',
    re.DOTALL,
)


def bake(payload: dict) -> bool:
    """Write payload into the user-data block. Return True if the file changed."""
    html = HTML.read_text(encoding="utf-8")
    new_json = json.dumps(payload, indent=2, ensure_ascii=False)
    replacement = lambda m: f"{m.group(1)}\n{new_json}\n{m.group(3)}"
    new_html, n = DATA_BLOCK_RE.subn(replacement, html)
    if n == 0:
        raise RuntimeError(
            'user-data block not found in fitness_plan.html. '
            'Expected <script type="application/json" id="user-data">…</script>.'
        )
    if new_html == html:
        return False
    HTML.write_text(new_html, encoding="utf-8")
    return True


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["git", "-C", str(REPO), *args],
        capture_output=True, text=True, check=check,
    )


def commit_and_push() -> bool:
    """Stage, commit, push fitness_plan.html. Return True if a commit was made."""
    git("add", str(HTML.name))
    status = git("status", "--porcelain", str(HTML.name)).stdout.strip()
    if not status:
        return False
    git("commit", "-m", "Sync user edits from browser")
    git("push", "origin", "main")
    return True


class Handler(BaseHTTPRequestHandler):
    def _cors(self) -> None:
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")

    def do_OPTIONS(self) -> None:
        self.send_response(204)
        self._cors()
        self.end_headers()

    def do_POST(self) -> None:
        if self.path.rstrip("/") != "/sync":
            self.send_response(404)
            self.end_headers()
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            body = self.rfile.read(length).decode("utf-8")
            payload = json.loads(body)
            changed = bake(payload)
            committed = commit_and_push() if changed else False
            self._reply(200, {"ok": True, "changed": changed, "committed": committed})
        except subprocess.CalledProcessError as e:
            err = (e.stderr or e.stdout or str(e)).strip()
            self._reply(500, {"ok": False, "error": f"git: {err}"})
        except Exception as e:
            self._reply(500, {"ok": False, "error": str(e)})

    def _reply(self, code: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self._cors()
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, fmt: str, *args) -> None:
        sys.stderr.write(f"[{self.log_date_time_string()}] {fmt % args}\n")


def main() -> None:
    if not HTML.exists():
        print(f"error: {HTML} not found", file=sys.stderr)
        sys.exit(1)
    if not (REPO / ".git").exists():
        print(f"error: {REPO} is not a git repo", file=sys.stderr)
        sys.exit(1)
    print(f"sync helper listening on http://localhost:{PORT}/sync")
    print(f"watching: {HTML}")
    print("press Ctrl-C to stop\n")
    try:
        HTTPServer(("localhost", PORT), Handler).serve_forever()
    except KeyboardInterrupt:
        print("\nstopped.")


if __name__ == "__main__":
    main()
