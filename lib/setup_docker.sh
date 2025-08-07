#!/bin/bash

set -euo pipefail

timestamp() {
  date +"[%Y-%m-%d %H:%M:%S]"
}

setup_docker_worker() {
    local i=$1
    echo "$(timestamp) [INFO] Setting up Docker and installing flax on worker $i..."

    gcloud alpha compute tpus tpu-vm ssh "$TPU_NAME" \
        --worker=$i \
        --zone="$ZONE" \
        --ssh-key-file="$HOME/.ssh/id_rsa" \
        --ssh-flag="-o ConnectTimeout=15" \
        --ssh-flag="-o StrictHostKeyChecking=no" \
        --ssh-flag="-o UserKnownHostsFile=/dev/null" \
        --command "
        sudo docker pull yx3038/maxtext_base_image:latest
        sudo docker run \
            --privileged \
            -v $WORK_DIR:$WORK_DIR \
            -w $WORK_DIR/maxtext \
            yx3038/maxtext_base_image:latest bash -c \
            \"pip install flax\"
        "
}

for i in $(seq 0 $((NUM_WORKERS - 1))); do
    log_file="jobs/$JOB_NAME/worker_${i}_setup.log"
    (setup_docker_worker $i) >> "$log_file" 2>&1 &
done

wait
echo "$(timestamp) [INFO] Docker environment setup complete on all workers."