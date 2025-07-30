#!/bin/bash

source config.sh

mkdir -p logs

LOG_FILE="logs/maxtext_$(date +%Y%m%d_%H%M%S).log"

gcloud alpha compute tpus tpu-vm ssh $TPU_NAME \
  --zone=$ZONE \
  --ssh-key-file='~/.ssh/id_rsa' \
  --worker=0 \
  --command "
  gcloud config set project vision-mix
  gcloud config set compute/zone us-east1-d
  "

# cd /home/zephyr/gcs-bucket/pruning
nohup gcloud alpha compute tpus tpu-vm ssh $TPU_NAME \
  --zone=$ZONE \
  --ssh-key-file='~/.ssh/id_rsa' \
  --worker=0 \
  --command "

  echo 'copying maxtext...'
  rm -rf ~/maxtext
  cp -r ~/gcs-bucket/maxtext ~/maxtext
  echo 'copy completed'

  cd ~/maxtext
  mkdir -p logs
  export TPU_PREFIX=llm-pruning-v6e
  bash scripts/finetune_llama3.1_4b_width.sh" \
  > "$LOG_FILE" 2>&1 &