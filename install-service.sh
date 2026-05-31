#!/usr/bin/env bash
set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

install_macos() {
  local label="dev.odysseus.ui"
  local plist="$HOME/Library/LaunchAgents/${label}.plist"
  local uvicorn_bin="$SCRIPT_DIR/.venv/bin/uvicorn"
  local port="${ODYSSEUS_PORT:-7001}"

  if [ ! -x "$uvicorn_bin" ]; then
    uvicorn_bin="$SCRIPT_DIR/venv/bin/uvicorn"
  fi
  if [ ! -x "$uvicorn_bin" ]; then
    echo "Error: no project uvicorn found. Run scripts/setup-macos.sh first."
    exit 1
  fi

  mkdir -p "$HOME/Library/LaunchAgents" "$SCRIPT_DIR/logs"

  cat > "$plist" <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
  <key>Label</key>
  <string>${label}</string>
  <key>WorkingDirectory</key>
  <string>${SCRIPT_DIR}</string>
  <key>ProgramArguments</key>
  <array>
    <string>${uvicorn_bin}</string>
    <string>app:app</string>
    <string>--host</string>
    <string>127.0.0.1</string>
    <string>--port</string>
    <string>${port}</string>
  </array>
  <key>EnvironmentVariables</key>
  <dict>
    <key>PATH</key>
    <string>/opt/homebrew/bin:/opt/homebrew/sbin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin</string>
    <key>ODYSSEUS_PORT</key>
    <string>${port}</string>
    <key>ODYSSEUS_INTERNAL_BASE_URL</key>
    <string>http://127.0.0.1:${port}</string>
  </dict>
  <key>RunAtLoad</key>
  <true/>
  <key>KeepAlive</key>
  <true/>
  <key>StandardOutPath</key>
  <string>${SCRIPT_DIR}/logs/launchd.out.log</string>
  <key>StandardErrorPath</key>
  <string>${SCRIPT_DIR}/logs/launchd.err.log</string>
</dict>
</plist>
EOF

  launchctl bootout "gui/$(id -u)" "$plist" >/dev/null 2>&1 || true
  launchctl bootstrap "gui/$(id -u)" "$plist"
  launchctl kickstart -k "gui/$(id -u)/${label}"
  echo "Installed and started macOS LaunchAgent: $plist"
  echo "Open http://localhost:${port}"
}

install_systemd() {
  local service_file="$SCRIPT_DIR/odysseus-ui.service"

  if [ ! -f "$service_file" ]; then
    echo "Error: odysseus-ui.service not found in $SCRIPT_DIR"
    exit 1
  fi

  echo "Installing Odysseus UI systemd service..."
  echo "Make sure you've edited odysseus-ui.service with your username and paths first."
  echo ""

  sudo cp "$service_file" /etc/systemd/system/
  sudo systemctl daemon-reload
  sudo systemctl enable odysseus-ui
  sudo systemctl start odysseus-ui
  sudo systemctl status odysseus-ui
}

case "$(uname -s)" in
  Darwin)
    install_macos
    ;;
  Linux)
    install_systemd
    ;;
  *)
    echo "Unsupported OS: $(uname -s)"
    echo "Run manually with: ODYSSEUS_PORT=7001 .venv/bin/uvicorn app:app --host 127.0.0.1 --port 7001"
    exit 1
    ;;
esac
