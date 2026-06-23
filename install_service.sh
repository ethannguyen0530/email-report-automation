#!/bin/bash
# Install as a macOS login service (auto-starts on login, restarts on crash)
# Usage: bash install_service.sh
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"
PLIST="$HOME/Library/LaunchAgents/com.emailreport.plist"
PYTHON="$(which python3)"

if [ -z "$PYTHON" ]; then
    echo "Error: python3 not found in PATH"
    exit 1
fi

echo "Installing email-report-automation as a macOS service..."
echo "  Project: $ROOT"
echo "  Python:  $PYTHON"

# Install Python dependencies
echo "Installing Python dependencies..."
pip3 install -q -r "$ROOT/requirements.txt"

# Find npm and build React frontend
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

if [ -n "$NPM" ]; then
    echo "Building React frontend..."
    export PATH="$(dirname "$NPM"):$PATH"
    cd "$ROOT/frontend" && "$NPM" run build
    cd "$ROOT"
else
    echo "Warning: npm not found — using existing frontend/dist if present."
fi

if [ ! -f "$ROOT/frontend/dist/index.html" ]; then
    echo "Error: frontend/dist/index.html not found. Please build the frontend first:"
    echo "  cd $ROOT/frontend && npm run build"
    exit 1
fi

mkdir -p "$ROOT/logs"

# Determine Python's bin dir so gunicorn is found
PYTHON_BIN="$(dirname "$PYTHON")"

cat > "$PLIST" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.emailreport</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON</string>
        <string>-m</string>
        <string>gunicorn</string>
        <string>dashboard.app:app</string>
        <string>--bind</string>
        <string>127.0.0.1:5001</string>
        <string>--workers</string>
        <string>1</string>
        <string>--timeout</string>
        <string>120</string>
        <string>--access-logfile</string>
        <string>$ROOT/logs/access.log</string>
        <string>--error-logfile</string>
        <string>$ROOT/logs/error.log</string>
    </array>
    <key>WorkingDirectory</key>
    <string>$ROOT</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>PATH</key>
        <string>$PYTHON_BIN:/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
    </dict>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$ROOT/logs/server.log</string>
    <key>StandardErrorPath</key>
    <string>$ROOT/logs/server.log</string>
    <key>ThrottleInterval</key>
    <integer>10</integer>
</dict>
</plist>
EOF

launchctl unload "$PLIST" 2>/dev/null || true
launchctl load "$PLIST"

echo ""
echo "Service installed and running."
echo "  Dashboard: http://localhost:5001"
echo "  Logs:      $ROOT/logs/server.log"
echo ""
echo "Commands:"
echo "  Stop:      launchctl unload $PLIST"
echo "  Restart:   launchctl unload $PLIST && launchctl load $PLIST"
echo "  Uninstall: launchctl unload $PLIST && rm $PLIST"
