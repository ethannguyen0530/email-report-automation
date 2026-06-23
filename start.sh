#!/bin/bash
# Development startup — Flask dev server + Vite HMR (hot reload)
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Find npm in common locations
NPM=""
for candidate in \
    "/tmp/node-v22.16.0-darwin-arm64/bin/npm" \
    "/usr/local/bin/npm" \
    "/opt/homebrew/bin/npm" \
    "$(which npm 2>/dev/null)"; do
    if [ -x "$candidate" ]; then
        NPM="$candidate"
        export PATH="$(dirname "$candidate"):$PATH"
        break
    fi
done

if [ -z "$NPM" ]; then
    echo "Error: npm not found. Install Node.js from https://nodejs.org"
    exit 1
fi

echo "Starting Flask API on http://localhost:5001..."
python3 -c "
import sys; sys.path.insert(0,'.')
from dashboard.app import app
app.run(debug=False, port=5001, use_reloader=False)
" &
FLASK_PID=$!

sleep 1
echo "Starting React dashboard on http://localhost:3000..."
cd "$ROOT/frontend" && "$NPM" run dev &
REACT_PID=$!

echo ""
echo "  Flask API  → http://localhost:5001"
echo "  Dashboard  → http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop."

trap "kill $FLASK_PID $REACT_PID 2>/dev/null; echo 'Stopped.'" INT TERM
wait
