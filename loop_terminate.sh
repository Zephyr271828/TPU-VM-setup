#!/bin/bash

PID_FILE="tpu_monitor.pid"

if [[ -f "$PID_FILE" ]]; then
  PID=$(cat "$PID_FILE")
  if kill -0 "$PID" 2>/dev/null; then
    kill "$PID"
    echo "TPU monitor (PID=$PID) stopped."
  else
    echo "No active monitor found (PID=$PID is not running)."
  fi
  rm -f "$PID_FILE"
else
  echo "No monitor PID file found."
fi