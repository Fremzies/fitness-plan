#!/bin/bash
# start.command — double-click in Finder to launch the sync helper and open
# fitness_plan.html. Safe to run repeatedly: it no-ops if the helper is
# already running. The helper exits itself after 10 min of tab inactivity.

set -u
cd "$(dirname "$0")" || exit 1

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 not found."
  echo "Install with: xcode-select --install"
  read -n 1 -s -r -p "Press any key to close."
  exit 1
fi

if lsof -ti tcp:7777 >/dev/null 2>&1; then
  echo "✓ sync helper already running on port 7777."
else
  echo "starting sync helper..."
  nohup python3 sync.py > sync.log 2>&1 &
  # Give it a moment to bind the port before we trust it's up.
  sleep 0.5
  if ! lsof -ti tcp:7777 >/dev/null 2>&1; then
    echo "ERROR: sync helper did not start. Last lines of sync.log:"
    tail -20 sync.log 2>/dev/null
    read -n 1 -s -r -p "Press any key to close."
    exit 1
  fi
  echo "✓ sync helper started (logs: sync.log)"
fi

echo "opening fitness_plan.html..."
open fitness_plan.html

echo
echo "  Ready. You can close this terminal window."
echo "  The helper will auto-stop ~10 min after you close the page."
