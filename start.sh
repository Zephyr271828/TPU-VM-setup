#!/bin/bash

source config.sh

gcloud alpha compute tpus tpu-vm list --zone=$ZONE --format="value(name)" | grep -q "^$TPU_NAME$"
if [ $? -ne 0 ]; then
  until \
      gcloud alpha compute tpus tpu-vm create $TPU_NAME \
      --zone=$ZONE \
      --accelerator-type=$ACCELERATOR \
      --version=$VERSION \
      --preemptible; \
  do : ; done
fi

gcloud alpha compute tpus tpu-vm scp setup_conda.sh $TPU_NAME:~/ \
  --zone=$ZONE --ssh-key-file='~/.ssh/id_rsa' --worker=all   
gcloud alpha compute tpus tpu-vm scp setup_gcsfuse.sh $TPU_NAME:~/ \
  --zone=$ZONE --ssh-key-file='~/.ssh/id_rsa' --worker=all
gcloud alpha compute tpus tpu-vm ssh $TPU_NAME \
  --zone=$ZONE \
  --ssh-key-file='~/.ssh/id_rsa' \
  --worker=all \
  --command "
  bash setup_conda.sh

  sleep 60

  export bucket_name=$BUCKET_NAME
  export bucket_dir=$BUCKET_DIR
  bash setup_gcsfuse.sh
  "

sleep 60

bash run_command.sh
