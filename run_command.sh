#!/bin/bash

source config.sh

mkdir -p logs

LOG_FILE="logs/finetune_$(date +%Y%m%d_%H%M%S).log"

# cd /home/zephyr/gcs-bucket/pruning
nohup gcloud alpha compute tpus tpu-vm ssh $TPU_NAME \
  --zone=$ZONE \
  --ssh-key-file='~/.ssh/id_rsa' \
  --worker=all \
  --command "bash ~/gcs-bucket/pruning/fms-grad-accum/scripts/finetuning.sh" \
  > "$LOG_FILE" 2>&1 &
