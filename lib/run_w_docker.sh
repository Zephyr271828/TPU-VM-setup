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
(run_docker_worker 0) >> "$log_file" 2>&1 &