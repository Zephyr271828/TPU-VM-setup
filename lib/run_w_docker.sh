#!/bin/bash

set -euo pipefail

timestamp() {
  date +"[%Y-%m-%d %H:%M:%S]"
}

run_docker_worker() {
    local i=$1
    echo "$(timestamp) Running main command on worker $i"
    gcloud alpha compute tpus tpu-vm ssh "$TPU_NAME" \
        --worker=0 \
        --zone="$ZONE" \
        --ssh-key-file="$HOME/.ssh/id_rsa" \
        --ssh-flag="-o ConnectTimeout=15" \
        --ssh-flag="-o StrictHostKeyChecking=no" \
        --ssh-flag="-o UserKnownHostsFile=/dev/null" \
        --command "
            sudo rm -rf $WORK_DIR/maxtext
            cp -r $WORK_DIR/gcs-bucket/maxtext $WORK_DIR/maxtext
            mkdir -p $WORK_DIR/maxtext/logs

            sudo docker run \
            --privileged \
            --network=host \
            -v $WORK_DIR:$WORK_DIR \
            -v $WORK_DIR/.config/gcloud:/root/.config/gcloud \
            -v /dev:/dev \
            -v /run:/run \
            -w $WORK_DIR/maxtext \
            yx3038/maxtext_base_image:latest bash -c \"$COMMAND\"
        "
}

log_file="jobs/$JOB_NAME/main_command.log"
(run_docker_worker 0) >> "$log_file" 2>&1