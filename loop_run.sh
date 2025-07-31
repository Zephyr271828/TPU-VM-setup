#!/bin/bash

# === CONFIGURATION ===
source config.sh
LOG_FILE="tpu_monitor.log"

PID_FILE="tpu_monitor.pid"
SLEEP_INTERVAL=60
RECREATE_TIMEOUT=900  # Timeout in seconds (e.g., 10 minutes)

timestamp() {
  date +"[%Y-%m-%d %H:%M:%S]"
}

check_tpu_status() {
  gcloud alpha compute tpus tpu-vm describe "$TPU_NAME" \
    --zone="$ZONE" \
    --format='value(state)' 2>/dev/null
}

get_external_ip() {
  gcloud compute tpus tpu-vm describe "$TPU_NAME" \
    --zone="$ZONE" \
    --format="value(networkEndpoints[0].accessConfig.externalIp)" 2>/dev/null
}

recreate_tpu() {
  echo "$(timestamp) [INFO] Starting TPU recreate process..."
  
  if gcloud alpha compute tpus tpu-vm describe "$TPU_NAME" --zone="$ZONE" &>/dev/null; then
    echo "$(timestamp) [INFO] TPU VM exists. Running delete.sh..."
    bash delete.sh
  else
    echo "$(timestamp) [INFO] TPU VM does not exist. Skipping deletion."
  fi

  START_LOG="tpu_start_$(timestamp).log"
  if timeout "$RECREATE_TIMEOUT" bash start.sh >"$START_LOG" 2>&1; then
    echo "$(timestamp) [INFO] TPU recreate completed within timeout."
  else
    echo "$(timestamp) [ERROR] TPU recreate timed out after ${RECREATE_TIMEOUT}s. Skipping for now."
  fi
}

# === RUN LOOP IN BACKGROUND ===
run_monitor_loop() {
  echo "$(timestamp) [INFO] Starting TPU monitor for $TPU_NAME in zone $ZONE..."

  while true; do
    STATE=$(check_tpu_status)
    echo "$(timestamp) [STATUS] TPU $TPU_NAME state: ${STATE:-NOT_FOUND}"

    if [[ "$STATE" == "STOPPED" || "$STATE" == "TERMINATED" || "$STATE" == "PREEMPTED" || -z "$STATE" ]]; then
      recreate_tpu
    elif [[ "$STATE" == "DELETING" ]]; then
      echo "$(timestamp) [INFO] TPU is currently deleting. Waiting for deletion to finish..."
    elif [[ "$STATE" == "CREATING" ]]; then
      echo "$(timestamp) [INFO] TPU is currently creating. Waiting for it to be ready..."
    else
      IP=$(get_external_ip)
      echo "$(timestamp) [INFO] TPU is active. Host0 External IP: ${IP:-Unavailable}"
    fi

    sleep "$SLEEP_INTERVAL"
  done
}

run_monitor_loop >>"$LOG_FILE" 2>&1 &

echo $! > "$PID_FILE"
echo "$(timestamp) [INFO] TPU monitor started in background (PID=$!) — logging to $LOG_FILE"