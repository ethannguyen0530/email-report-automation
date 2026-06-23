#!/bin/bash
# Production startup — builds React and runs gunicorn (single process, no terminal needed)
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

# Find node/npm
NPM=""
for candidate in \
    "/tmp/node-v22.16.0-darwin-arm64/bin/npm" \
    "/usr/local/bin/npm" \
    "/opt/homebrew/bin/npm" \
    "$(which npm 2>/dev/null)"; do
    if [ -x "$candidate" ]; then
        NPM="$candidate"
        break
    fi
done

# Build React if dist is missing or source is newer
if [ -n "$NPM" ]; then
    if [ ! -d "$ROOT/frontend/dist" ] || find "$ROOT/frontend/src" -newer "$ROOT/frontend/dist/index.html" -name "*.jsx" -o -name "*.css" 2>/dev/null | grep -q .; then
        echo "Building React frontend..."
        cd "$ROOT/frontend" && "$NPM" run build
        cd "$ROOT"
    fi
else
    echo "Warning: npm not found. Using existing frontend/dist (if present)."
fi

mkdir -p "$ROOT/logs"

echo "Starting server on http://localhost:5001"
exec python3 -m gunicorn \
    dashboard.app:app \
    --bind 0.0.0.0:5001 \
    --workers 1 \
    --timeout 120 \
    --access-logfile "$ROOT/logs/access.log" \
    --error-logfile "$ROOT/logs/error.log" \
    --log-level info
