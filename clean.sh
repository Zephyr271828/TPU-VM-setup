#!/bin/bash

# set -euo pipefail

source config.sh

gcloud alpha compute tpus tpu-vm ssh $TPU_NAME \
  --zone=$ZONE \
  --ssh-key-file='~/.ssh/id_rsa' \
  --worker=all \
  --command "
  echo '🔹 Cleaning setup scripts...'
  rm -rf ~/setup*

  echo '🔹 Unmounting GCSFuse from $BUCKET_DIR...'
  if mount | grep '$BUCKET_DIR'; then
    sudo fusermount -u '$BUCKET_DIR' || sudo umount -l '$BUCKET_DIR'
    echo 'unmounted $BUCKET_DIR'
  fi
  rm -rf '$BUCKET_DIR'
  sudo apt-get remove -y gcsfuse

  echo '🔹 Cleaning Conda...'
  rm -rf ~/conda_envs ~/conda_pkgs ~/miniconda3
  "