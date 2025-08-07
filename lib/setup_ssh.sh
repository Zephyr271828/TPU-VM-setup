#!/bin/bash
set -euo pipefail

timestamp() {
  date +"[%Y-%m-%d %H:%M:%S]"
}

setup_ssh_worker() {
    local i=$1

    echo "$(timestamp) [INFO] Creating ~/.ssh on worker $i..."
    gcloud alpha compute tpus tpu-vm ssh "$TPU_NAME" \
        --worker=$i \
        --zone="$ZONE" \
        --ssh-key-file="$HOME/.ssh/id_rsa" \
        --ssh-flag="-o ConnectTimeout=15" \
        --ssh-flag="-o StrictHostKeyChecking=no" \
        --ssh-flag="-o UserKnownHostsFile=/dev/null" \
        --command "mkdir -p ~/.ssh && chmod 700 ~/.ssh"

    for file in id_rsa id_rsa.pub id_ed25519_git id_ed25519_git.pub config; do
        if [ -f "$HOME/.ssh/$file" ]; then
            echo "$(timestamp) [INFO] Copying $file to worker $i..."
            gcloud alpha compute tpus tpu-vm scp "$HOME/.ssh/$file" "$TPU_NAME:~/.ssh/" \
                --worker=$i \
                --zone="$ZONE" \
                --ssh-key-file="$HOME/.ssh/id_rsa" \
                --scp-flag="-o ConnectTimeout=15" \
                --scp-flag="-o StrictHostKeyChecking=no" \
                --scp-flag="-o UserKnownHostsFile=/dev/null" \
                
            echo "$(timestamp) [INFO] Setting permissions for $file on worker $i..."
            if [[ "$file" == *.pub || "$file" == config ]]; then
                perm="644"
            else
                perm="600"
            fi
            gcloud alpha compute tpus tpu-vm ssh "$TPU_NAME" \
                --worker=$i \
                --zone="$ZONE" \
                --ssh-key-file="$HOME/.ssh/id_rsa" \
                --ssh-flag="-o ConnectTimeout=15" \
                --ssh-flag="-o StrictHostKeyChecking=no" \
                --ssh-flag="-o UserKnownHostsFile=/dev/null" \
                --command "chmod $perm ~/.ssh/$file" 
        else
            echo "$(timestamp) [WARN] $file not found locally. Skipping..."
        fi
    done
}


for i in $(seq 0 $((NUM_WORKERS-1))); do
    log_file="jobs/$JOB_NAME/worker_${i}_setup.log"
    (setup_ssh_worker $i) >> "$log_file" 2>&1 &
done

wait

echo "$(timestamp) [INFO] All workers SSH key setup completed."