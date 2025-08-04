#!/bin/bash

set -euo pipefail

export GCSFUSE_REPO=gcsfuse-`lsb_release -c -s`

setup_gcsfuse_worker() {
    local i=$1
    echo "[INFO] Installing gcsfuse and mounting bucket on worker $i..."

    gcloud alpha compute tpus tpu-vm ssh "$TPU_NAME" \
        --zone="$ZONE" \
        --ssh-key-file="$HOME/.ssh/id_rsa" \
        --worker=$i \
        --command "

            echo 'deb [signed-by=/usr/share/keyrings/cloud.google.asc] https://packages.cloud.google.com/apt $GCSFUSE_REPO main' | sudo tee /etc/apt/sources.list.d/gcsfuse.list

            curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo tee /usr/share/keyrings/cloud.google.asc >/dev/null

            sudo apt-get update -y && sudo apt-get install -y gcsfuse

            mkdir -p '$BUCKET_DIR'
            sudo gcsfuse --implicit-dirs --dir-mode=777 --file-mode=777 --o allow_other '$BUCKET_NAME' '$BUCKET_DIR'

            ls -la '$BUCKET_DIR'
        "

    echo "[INFO] gcsfuse setup completed on worker $i."
}

for i in $(seq 0 $((NUM_WORKERS-1))); do
    log_file="jobs/$JOB_NAME/worker_${i}_setup.log"
    (setup_gcsfuse_worker $i) >> "$log_file" 2>&1 &
done

wait
echo "[INFO] All workers completed gcsfuse setup."