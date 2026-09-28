#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python3 -m venv .venv 2>/dev/null || true
source .venv/bin/activate
python -m pip install -r requirements.txt
uvicorn backend.main:app --host 127.0.0.1 --port 8000 &
sleep 3
if command -v xdg-open >/dev/null; then xdg-open http://127.0.0.1:8000
elif command -v open >/dev/null; then open http://127.0.0.1:8000
fi
wait
