#!/bin/bash

set -euo pipefail

source config.sh

export bucket_name=$BUCKET_NAME
export bucket_dir=$BUCKET_DIR
export GCSFUSE_REPO=gcsfuse-`lsb_release -c -s`

MAX_RETRIES=5
RETRY_DELAY=10

run_setup_for_worker() {
  local worker=$1
  local attempt=0

  while (( attempt < MAX_RETRIES )); do
    echo "🔁 Worker $worker attempt $((attempt+1))/$MAX_RETRIES"

    if gcloud alpha compute tpus tpu-vm ssh "$TPU_NAME" \
      --zone="$ZONE" \
      --ssh-key-file="$HOME/.ssh/id_rsa" \
      --worker="$worker" \
      --command "
        set -euo pipefail
        echo 'Adding gcsfuse repo...'
        echo 'deb [signed-by=/usr/share/keyrings/cloud.google.asc] https://packages.cloud.google.com/apt $GCSFUSE_REPO main' | sudo tee /etc/apt/sources.list.d/gcsfuse.list

        curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo tee /usr/share/keyrings/cloud.google.asc >/dev/null

        sudo apt-get update -y && sudo apt-get install -y gcsfuse

        mkdir -p '$bucket_dir'
        gcsfuse --implicit-dirs --dir-mode=777 --file-mode=777 '$bucket_name' '$bucket_dir'
        ls -la '$bucket_dir'
      "; then
      echo "✅ Worker $worker success"
      return 0
    else
      echo "❌ Worker $worker failed attempt $((attempt+1))"
      sleep $RETRY_DELAY
      ((attempt++))
    fi
  done

  echo "❌ Worker $worker failed after $MAX_RETRIES attempts."
  return 1
}

# Run all workers concurrently
for ((worker=0; worker<NUM_WORKERS; worker++)); do
  run_setup_for_worker "$worker" &
done

# Wait for all background jobs to finish
wait
echo "🏁 All worker setup processes completed."