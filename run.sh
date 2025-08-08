#!/bin/bash

set -euo pipefail
# set -x

required_vars=(
    "ACCELERATOR" 
    "BUCKET_DIR"
    "BUCKET_NAME"
    "COMMAND"
    "JOB_NAME" 
    "NUM_WORKERS" 
    "TPU_NAME" 
    "VERSION"
    "WORK_DIR"
    "ZONE" 
)
for var in "${required_vars[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    echo "[ERROR] $var is not set"
    exit 1
  fi
done

NOHUP_MODE=false
LOOP_MODE=false


for arg in "$@"; do
  if [[ "$arg" == "nohup" ]]; then
    NOHUP_MODE=true
  elif [[ "$arg" == "loop" ]]; then
    LOOP_MODE=true
  fi
done

mkdir -p jobs/$JOB_NAME

bash lib/write_meta.sh

timestamp() {
    date +"[%Y-%m-%d %H:%M:%S]"
}

run_job_steps() {
    bash lib/request_vm.sh
    bash lib/setup_ssh.sh
    sleep 60 && bash lib/setup_gcsfuse.sh
    sleep 60 && bash lib/setup_docker.sh
    bash lib/get_ips.sh
    bash lib/run_w_docker.sh
}

run_job() {
    if [ "$LOOP_MODE" = true ]; then
        SLEEP_INTERVAL=60
        while true; do
            STATE=$(gcloud alpha compute tpus tpu-vm describe "$TPU_NAME" --zone="$ZONE" \
                    --format='value(state)' 2>/dev/null || echo "NOT_FOUND")
            echo "$(timestamp) [STATUS] TPU $TPU_NAME state: ${STATE}"

            if [[ "$STATE" == "PREEMPTED" || "$STATE" == "STOPPED" || "$STATE" == "NOT_FOUND" || "$STATE" == "SUSPENDED" || -z "$STATE" ]]; then
                echo "$(timestamp) [INFO] TPU state=$STATE, running job steps..."
                run_job_steps
            elif [[ "$STATE" == "DELETING" || "$STATE" == "CREATING" ]]; then
                echo "$(timestamp) [INFO] TPU state=$STATE, waiting..."
            else
                echo "$(timestamp) [INFO] TPU in state=$STATE, assuming healthy or finished."
            fi
            sleep "$SLEEP_INTERVAL"
        done
    else
        run_job_steps
    fi
}

if [ "$NOHUP_MODE" = true ]; then
    run_job >> "jobs/$JOB_NAME/run.log" 2>&1 &
    echo "kill -9 $!" > jobs/$JOB_NAME/cancel.sh
    echo "[INFO] Job launched in background. Logs at jobs/$JOB_NAME/run.log"
    echo "[INFO] Run 'bash jobs/$JOB_NAME/cancel.sh' to kill the job."
else
    run_job
fi