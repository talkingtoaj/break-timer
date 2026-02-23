#!/usr/bin/env bash
# Use system Python on Linux/WSL to avoid xcb/XInitThreads crash with uv-managed Python.
# On Windows, use the venv or default python.
set -e
cd "$(dirname "$0")"
if [[ "$OSTYPE" == "linux-gnu"* ]] && [[ -x /usr/bin/python3 ]]; then
  exec /usr/bin/python3 break_timer.py "$@"
fi
if [[ -d .venv ]]; then
  exec .venv/bin/python break_timer.py "$@"
fi
exec python break_timer.py "$@"
