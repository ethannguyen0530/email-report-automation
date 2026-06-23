#!/bin/bash
# Start both Flask API and React dashboard with one command

export PATH="/tmp/node-v22.16.0-darwin-arm64/bin:$PATH"
ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "Starting Flask API on port 5001..."
cd "$ROOT"
python3 -c "
import sys
sys.path.insert(0, '.')
from dashboard.app import app
app.run(debug=False, port=5001, use_reloader=False)
" &
FLASK_PID=$!

sleep 1
echo "Starting React dashboard on port 3000..."
cd "$ROOT/frontend"
npm run dev &
REACT_PID=$!

echo ""
echo "  Flask API  → http://localhost:5001"
echo "  Dashboard  → http://localhost:3000"
echo ""
echo "Press Ctrl+C to stop both servers."

trap "kill $FLASK_PID $REACT_PID 2>/dev/null; echo 'Stopped.'" INT TERM
wait
