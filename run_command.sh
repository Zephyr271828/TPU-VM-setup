#!/bin/bash

source config.sh

# cd /home/zephyr/gcs-bucket/pruning
gcloud alpha compute tpus tpu-vm ssh $TPU_NAME \
  --zone=$ZONE \
  --ssh-key-file='~/.ssh/id_rsa' \
  --worker=all \
  --command "
  sudo pkill -f python
  bash ~/gcs-bucket/pruning/fms-grad-accum/scripts/finetuning.sh
  "
