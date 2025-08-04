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
if [[ $# -ge 1 && "$1" == "nohup" ]]; then
    NOHUP_MODE=true
fi

mkdir -p jobs/$JOB_NAME

bash lib/write_meta.sh

run_job_steps() {
    bash lib/request_vm.sh
    bash lib/setup_ssh.sh
    bash lib/setup_gcsfuse.sh
    bash lib/setup_docker.sh
    bash lib/run_w_docker.sh
    bash lib/get_ips.sh
}

if [ "$NOHUP_MODE" = true ]; then
    run_job_steps >> "jobs/$JOB_NAME/run.log" 2>&1 &
    echo $! > jobs/$JOB_NAME/pid.txt
    echo "[INFO] Job launched in background. Logs at jobs/$JOB_NAME/run.log"
    echo "[INFO] Run 'kill -9 \$(cat jobs/$JOB_NAME/pid.txt)' to kill the job."
else
    run_job_steps >> "jobs/$JOB_NAME/run.log" 2>&1 &
fi