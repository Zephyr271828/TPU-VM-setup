#!/bin/bash

source config.sh
source keys.sh

gcloud alpha compute tpus tpu-vm ssh $TPU_NAME \
  --zone=$ZONE \
  --ssh-key-file='~/.ssh/id_rsa' \
  --worker=all \
  --command "
  set -euo pipefail

  echo 'Setting up SSH keys...'

  rm -rf ~/.ssh/id*
  echo '$tpu_key' > ~/.ssh/id_rsa
  chmod 600 ~/.ssh/id_rsa

  echo '$tpu_key_pub' > ~/.ssh/id_rsa.pub
  chmod 600 ~/.ssh/id_rsa.pub

  # ED25519 key for GitHub
  echo '$github_key' > ~/.ssh/id_ed25519_github
  chmod 600 ~/.ssh/id_ed25519_github

  echo '$github_key_pub' > ~/.ssh/id_ed25519_github.pub
  chmod 600 ~/.ssh/id_ed25519_github.pub 

  echo 'Updating ~/.ssh/config...'
  rm -rf ~/.ssh/config

  printf '%s\n' \
    'Host github.com' \
    '  HostName github.com' \
    '  User git' \
    '  IdentityFile ~/.ssh/id_ed25519_github' >> ~/.ssh/config

  chmod 600 ~/.ssh/config

  echo '✅ SSH setup complete.'
  "