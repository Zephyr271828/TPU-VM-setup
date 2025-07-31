#!/bin/bash

source config.sh

MAX_RETRIES=5
RETRY_DELAY=5

copy_ssh_keys_to_worker() {
  local worker=$1
  local attempt=0

  while (( attempt < MAX_RETRIES )); do
    echo "[INFO] Worker $worker: Attempt $((attempt+1)) to set up ~/.ssh..."

    if gcloud alpha compute tpus tpu-vm ssh "$TPU_NAME" \
      --zone="$ZONE" \
      --worker="$worker" \
      --command "mkdir -p ~/.ssh && chmod 700 ~/.ssh"; then
      break
    fi

    echo "[WARN] Worker $worker: mkdir ~/.ssh failed. Retrying..."
    sleep $RETRY_DELAY
    ((attempt++))
  done

  for file in id_rsa id_rsa.pub id_ed25519_github id_ed25519_github.pub config; do
    attempt=0
    while (( attempt < MAX_RETRIES )); do
      echo "[INFO] Worker $worker: Copying $file"

      if gcloud alpha compute tpus tpu-vm scp "$HOME/.ssh/$file" "$TPU_NAME:~/.ssh/" \
        --zone="$ZONE" \
        --ssh-key-file="$HOME/.ssh/id_rsa" \
        --worker="$worker" \
        --quiet; then
        break
      fi

      echo "[WARN] Worker $worker: Failed to copy $file. Retrying..."
      sleep $RETRY_DELAY
      ((attempt++))
    done
  done

  attempt=0
  while (( attempt < MAX_RETRIES )); do
    echo "[INFO] Worker $worker: Setting permissions"

    if gcloud alpha compute tpus tpu-vm ssh "$TPU_NAME" \
      --zone="$ZONE" \
      --ssh-key-file="$HOME/.ssh/id_rsa" \
      --worker="$worker" \
      --command "
        set -euo pipefail
        chmod 600 ~/.ssh/id*
        chmod 600 ~/.ssh/config
        echo '✅ Worker $worker SSH setup complete.'
      "; then
      return 0
    fi

    echo "[WARN] Worker $worker: chmod failed. Retrying..."
    sleep $RETRY_DELAY
    ((attempt++))
  done

  echo "[ERROR] Worker $worker: SSH key setup failed after $MAX_RETRIES attempts."
  return 1
}

# Launch all workers in parallel
for ((worker=0; worker<NUM_WORKERS; worker++)); do
  copy_ssh_keys_to_worker "$worker" &
done

wait
echo "[DONE] All SSH key setup processes completed."