#!/bin/bash
# ============================================
#  Cielo House Website — Launcher
#  Double-click this file to open the website.
# ============================================

cd "$(dirname "$0")"
PORT=8000

echo ""
echo "  Cielo House — starting the website..."
echo ""

# Free the port if a previous server is still running on it
lsof -ti "tcp:$PORT" 2>/dev/null | xargs kill -9 2>/dev/null

if command -v python3 >/dev/null 2>&1; then
  python3 chat_server.py >/dev/null 2>&1 &
  SERVER_PID=$!
  sleep 1
  open "http://localhost:$PORT/index.html"
  echo "  The website is now open in your browser:"
  echo "  http://localhost:$PORT"
  echo ""
  echo "  Keep this Terminal window open while viewing the site."
  echo "  To stop: close this window or press Ctrl+C."
  echo ""
  trap "kill $SERVER_PID 2>/dev/null" EXIT
  wait $SERVER_PID
else
  echo "  Opening the website directly in your browser..."
  open "index.html"
fi
