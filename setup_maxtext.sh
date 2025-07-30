#!/bin/bash

source config.sh

gcloud alpha compute tpus tpu-vm ssh $TPU_NAME \
  --zone=$ZONE \
  --ssh-key-file='~/.ssh/id_rsa' \
  --worker=all \
  --command "
    source ~/miniconda3/etc/profile.d/conda.sh 
    conda create -p ~/conda_envs/maxtext python=3.10 -y

    conda activate ~/conda_envs/maxtext
    cd ~/gcs-bucket/maxtext
    bash setup.sh
    pip install grain
    pip install tensorflow
    pip install psutil
    "