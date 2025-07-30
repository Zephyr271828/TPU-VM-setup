#!/bin/bash

set -euo pipefail

source config.sh

export bucket_name=$BUCKET_NAME
export bucket_dir=$BUCKET_DIR
export GCSFUSE_REPO=gcsfuse-`lsb_release -c -s`

gcloud alpha compute tpus tpu-vm ssh $TPU_NAME \
  --zone=$ZONE \
  --ssh-key-file='~/.ssh/id_rsa' \
  --worker=all \
  --command "

    # sudo systemctl stop unattended-upgrades
    # sudo systemctl disable unattended-upgrades

    # Enable Google Cloud package repository
    echo 'Adding gcsfuse repo...'
    echo 'deb [signed-by=/usr/share/keyrings/cloud.google.asc] https://packages.cloud.google.com/apt $GCSFUSE_REPO main' | sudo tee /etc/apt/sources.list.d/gcsfuse.list

    # Import the GPG key
    echo 'Add GPG key non-interactively'
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo tee /usr/share/keyrings/cloud.google.asc

    # Update package list and install gcsfuse
    echo 'Installing gcsfuse...'
    sudo apt-get update
    sudo apt-get install -y gcsfuse

    # Create mount directory
    mkdir -p '$bucket_dir'

    # Mount the bucket
    echo 'Mounting bucket $bucket_name to $bucket_dir ...'
    sleep 1
    gcsfuse --implicit-dirs --dir-mode=777 --file-mode=777 '$bucket_name' '$bucket_dir'

    echo '✅ Mounted successfully. Contents:'
    ls -la '$bucket_dir'
    "