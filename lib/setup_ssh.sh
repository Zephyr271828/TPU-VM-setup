#!/bin/bash
set -euo pipefail

setup_ssh_worker() {
    local i=$1

    echo "[INFO] Creating ~/.ssh on worker $i..."
    gcloud alpha compute tpus tpu-vm ssh "$TPU_NAME" \
        --zone="$ZONE" \
        --worker=$i \
        --command "mkdir -p ~/.ssh && chmod 700 ~/.ssh"

    for file in id_rsa id_rsa.pub id_ed25519_github id_ed25519_github.pub config; do
        if [ -f "$HOME/.ssh/$file" ]; then
            echo "[INFO] Copying $file to worker $i..."
            gcloud alpha compute tpus tpu-vm scp "$HOME/.ssh/$file" "$TPU_NAME:~/.ssh/" \
                --zone="$ZONE" \
                --ssh-key-file="$HOME/.ssh/id_rsa" \
                --worker=$i
        else
            echo "[WARN] $file not found locally. Skipping..."
        fi
    done

    echo "[INFO] Setting permissions on worker $i..."
    gcloud alpha compute tpus tpu-vm ssh "$TPU_NAME" \
        --zone="$ZONE" \
        --ssh-key-file="$HOME/.ssh/id_rsa" \
        --worker=$i \
        --command "
        chmod 600 ~/.ssh/id_rsa ~/.ssh/id_rsa.pub ~/.ssh/id_ed25519_github ~/.ssh/id_ed25519_github.pub ~/.ssh/config
        echo '[INFO] SSH setup complete on worker $i.'
        "
}


for i in $(seq 0 $((NUM_WORKERS-1))); do
    log_file="jobs/$JOB_NAME/worker_${i}_setup.log"
    (setup_ssh_worker $i) >> "$log_file" 2>&1 &
done

wait

echo "[INFO] All workers SSH key setup completed."