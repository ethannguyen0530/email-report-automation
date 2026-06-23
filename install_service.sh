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

# Install gunicorn and apscheduler if needed
pip3 install -q gunicorn apscheduler

# Build React frontend
echo "Building React frontend..."
bash "$ROOT/run.sh" --build-only 2>/dev/null || true
NPM=""
for candidate in "/tmp/node-v22.16.0-darwin-arm64/bin/npm" "/usr/local/bin/npm" "/opt/homebrew/bin/npm" "$(which npm 2>/dev/null)"; do
    if [ -x "$candidate" ]; then NPM="$candidate"; break; fi
done
if [ -n "$NPM" ]; then
    cd "$ROOT/frontend" && "$NPM" run build
    cd "$ROOT"
fi

mkdir -p "$ROOT/logs"

# Write the launchd plist
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
        <string>0.0.0.0:5001</string>
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
        <string>/usr/local/bin:/usr/bin:/bin:/opt/homebrew/bin</string>
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

# Unload if already running
launchctl unload "$PLIST" 2>/dev/null || true

# Load the service
launchctl load "$PLIST"

echo ""
echo "Service installed and started."
echo "  Dashboard: http://localhost:5001"
echo "  Logs:      $ROOT/logs/server.log"
echo ""
echo "Commands:"
echo "  Stop:      launchctl unload $PLIST"
echo "  Start:     launchctl load $PLIST"
echo "  Restart:   launchctl unload $PLIST && launchctl load $PLIST"
echo "  Uninstall: launchctl unload $PLIST && rm $PLIST"
