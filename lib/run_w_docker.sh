#!/bin/bash

set -euo pipefail

timestamp() {
  date +"[%Y-%m-%d %H:%M:%S]"
}

run_docker_worker() {
    local i=$1
    echo "$(timestamp) Running main command on worker $i"
    # gcloud alpha compute tpus tpu-vm ssh "$TPU_NAME" \
    #     --worker=all \
    #     --zone="$ZONE" \
    #     --ssh-key-file="$HOME/.ssh/id_rsa" \
    #     --ssh-flag="-o ConnectTimeout=15" \
    #     --ssh-flag="-o StrictHostKeyChecking=no" \
    #     --ssh-flag="-o UserKnownHostsFile=/dev/null" \
    #     --command "
    #     sudo mkdir -p /home/zephyr/local_ckpts
    #     # gsutil -m cp -r gs://$BUCKET_NAME/model_ckpts/maxtext/llama3_4b_width_orbax /home/zephyr/local_ckpts/
    #     sudo cp -r /home/zephyr/gcs-bucket/model_ckpts/maxtext/llama3_4b_width_orbax /home/zephyr/local_ckpts/
    #     "
    gcloud alpha compute tpus tpu-vm ssh "$TPU_NAME" \
        --worker=0 \
        --zone="$ZONE" \
        --ssh-key-file="$HOME/.ssh/id_rsa" \
        --ssh-flag="-o ConnectTimeout=15" \
        --ssh-flag="-o StrictHostKeyChecking=no" \
        --ssh-flag="-o UserKnownHostsFile=/dev/null" \
        --command "
        sudo docker run \
          --privileged \
          --network=host \
          -v $WORK_DIR:$WORK_DIR \
          -v $WORK_DIR/.config/gcloud:/root/.config/gcloud \
          -v /dev:/dev \
          -v /run:/run \
          yx3038/maxtext_base_image:latest bash -c \"$COMMAND\"
        "
}

log_file="jobs/$JOB_NAME/main_command.log"
(run_docker_worker 0) >> "$log_file" 2>&1