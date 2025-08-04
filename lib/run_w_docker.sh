#!/bin/bash

set -euo pipefail

run_docker_worker() {
    local i=$1
    echo "Running main command on worker $i"
    gcloud alpha compute tpus tpu-vm ssh "$TPU_NAME" \
        --zone="$ZONE" \
        --ssh-key-file="$HOME/.ssh/id_rsa" \
        --worker=0 \
        --command "
            sudo rm -rf /home/zephyr/maxtext
            cp -r /home/zephyr/gcs-bucket/maxtext /home/zephyr/maxtext
            mkdir -p /home/zephyr/maxtext/logs

            sudo docker run \
            --privileged \
            --network=host \
            -v /home/zephyr:/home/zephyr \
            -v /home/zephyr/.config/gcloud:/root/.config/gcloud \
            -v /dev:/dev \
            -v /run:/run \
            -w /home/zephyr/maxtext \
            yx3038/maxtext_base_image:latest bash -c \"$COMMAND\"
        "
}

log_file="jobs/$JOB_NAME/main_command.log"
(run_docker_worker 0) >> "$log_file" 2>&1 &