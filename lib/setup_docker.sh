#!/bin/bash

set -euo pipefail

setup_docker_worker() {
    local i=$1
    echo "[INFO] Setting up Docker and installing flax on worker $i..."

    gcloud alpha compute tpus tpu-vm ssh "$TPU_NAME" \
        --zone="$ZONE" \
        --ssh-key-file="$HOME/.ssh/id_rsa" \
        --worker=$i \
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
echo "[INFO] Docker environment setup complete on all workers."