#!/bin/bash

source config.sh

MAX_RETRIES=5
RETRY_DELAY=5

setup_maxtext_worker() {
  local worker=$1
  local attempt=0

  echo "[INFO] Worker $worker: starting setup..."

  while (( attempt < MAX_RETRIES )); do
    echo "[INFO] Worker $worker: Attempt $((attempt+1))"

    if gcloud alpha compute tpus tpu-vm ssh "$TPU_NAME" \
      --zone="$ZONE" \
      --ssh-key-file="$HOME/.ssh/id_rsa" \
      --worker="$worker" \
      --command "
        set -euo pipefail
        source ~/miniconda3/etc/profile.d/conda.sh
        conda create -p ~/conda_envs/maxtext python=3.10 -y

        source ~/miniconda3/etc/profile.d/conda.sh
        conda activate ~/conda_envs/maxtext

        cd ~/gcs-bucket/maxtext
        bash setup.sh

        pip install grain tensorflow psutil
        echo '✅ Worker $worker maxtext setup complete.'
      "; then
      return 0
    fi

    echo "[WARN] Worker $worker: setup failed. Retrying in $RETRY_DELAY seconds..."
    sleep "$RETRY_DELAY"
    ((attempt++))
  done

  echo "[ERROR] Worker $worker: maxtext setup failed after $MAX_RETRIES attempts."
  return 1
}

# Run all workers in parallel
for ((worker=0; worker<NUM_WORKERS; worker++)); do
  setup_maxtext_worker "$worker" &
done

wait
echo "[DONE] All workers finished maxtext environment setup."