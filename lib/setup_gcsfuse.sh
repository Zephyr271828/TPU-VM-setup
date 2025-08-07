#!/bin/bash

set -euo pipefail

timestamp() {
  date +"[%Y-%m-%d %H:%M:%S]"
}

setup_gcsfuse_worker() {
    local i=$1
    echo "$(timestamp) [INFO] Installing gcsfuse and mounting bucket on worker $i..."

    gcloud alpha compute tpus tpu-vm ssh "$TPU_NAME" \
        --worker=$i \
        --zone="$ZONE" \
        --ssh-key-file="$HOME/.ssh/id_rsa" \
        --ssh-flag="-o ConnectTimeout=15" \
        --ssh-flag="-o StrictHostKeyChecking=no" \
        --ssh-flag="-o UserKnownHostsFile=/dev/null" \
        --command "
            echo '[INFO] Running inside worker $i'
            GCSFUSE_REPO=gcsfuse-\$(lsb_release -c -s)
            echo '[INFO] Adding gcsfuse repo...'
            echo \"deb [signed-by=/usr/share/keyrings/cloud.google.asc] https://packages.cloud.google.com/apt \${GCSFUSE_REPO} main\" | sudo tee /etc/apt/sources.list.d/gcsfuse.list

            echo '[INFO] Downloading GPG key...'
            sudo curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo tee /usr/share/keyrings/cloud.google.asc >/dev/null

            echo '[INFO] Installing gcsfuse...'
            sudo apt-get update -y && sudo apt-get install -y gcsfuse

            mkdir -p '$BUCKET_DIR'
            echo '[INFO] Mounting bucket...'
            mountpoint -q '$BUCKET_DIR' || timeout 30 sudo gcsfuse --implicit-dirs --dir-mode=777 --file-mode=777 --o allow_other '$BUCKET_NAME' '$BUCKET_DIR'

            ls -la '$BUCKET_DIR'
        "

    echo "$(timestamp) [INFO] gcsfuse setup completed on worker $i."
}

for i in $(seq 0 $((NUM_WORKERS-1))); do
    log_file="jobs/$JOB_NAME/worker_${i}_setup.log"
    (setup_gcsfuse_worker $i) >> "$log_file" 2>&1 &
done

wait
echo "$(timestamp) [INFO] All workers completed gcsfuse setup."