#!/bin/bash

source config.sh

# until \
#     gcloud alpha compute tpus tpu-vm create $TPU_NAME \
#     --zone=$ZONE \
#     --accelerator-type=$ACCELERATOR \
#     --version=$VERSION \
#     --preemptible; \
# do : ; done

# gcloud alpha compute tpus tpu-vm ssh $TPU_NAME \
#   --zone=$ZONE \
#   --ssh-key-file='~/.ssh/id_rsa' \
#   --worker=all \
#   --command "
#   cd ~
#   git clone -b main https://github.com/Zephyr271828/TPU-VM-setup.git
#   cd TPU-VM-setup
#   git pull origin main

#   bash setup_conda.sh

#   export bucket_name=$BUCKET_NAME
#   export bucket_dir=$BUCKET_DIR
#   bash setup_gcsfuse.sh

#.  bash start.sh
#   "

gcloud alpha compute tpus tpu-vm ssh $TPU_NAME \
  --zone=$ZONE \
  --ssh-key-file='~/.ssh/id_rsa' \
  --worker=all \
  --command "
  cd ~/TPU-VM-setup
  bash run_command.sh
  "