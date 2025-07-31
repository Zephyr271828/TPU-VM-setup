#!/bin/bash

source config.sh

MAX_RETRIES=5
RETRY_DELAY=10

setup_worker_conda() {
  local worker=$1
  local attempt=0

  while (( attempt < MAX_RETRIES )); do
    echo "[INFO] Worker $worker attempt $((attempt+1))/$MAX_RETRIES"

    if gcloud alpha compute tpus tpu-vm ssh "$TPU_NAME" \
      --zone="$ZONE" \
      --ssh-key-file="$HOME/.ssh/id_rsa" \
      --worker="$worker" \
      --command "
        set -euo pipefail

        echo 'Installing Miniconda on worker $worker...'
        mkdir -p ~/miniconda3 
        wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
        bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
        rm ~/miniconda3/miniconda.sh

        source ~/miniconda3/etc/profile.d/conda.sh
        conda init

        mkdir -p ~/conda_envs ~/conda_pkgs
        export CONDA_ENVS_PATH=~/conda_envs
        export CONDA_PKGS_PATH=~/conda_pkgs

        conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
        conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r

        conda create -p ~/conda_envs/fms python=3.10 -y

        source ~/miniconda3/etc/profile.d/conda.sh
        conda activate ~/conda_envs/fms
        pip install --upgrade pip
        pip install torch==2.7.0 torch_xla[tpu]==2.7.0
        pip install hydra-core omegaconf fire pyarrow torchdata datasets transformers==4.46.2 wandb

        conda env list
        pip show torch-xla

        echo '✅ Worker $worker setup complete.'
      "; then
      echo "[SUCCESS] Worker $worker setup succeeded."
      return 0
    else
      echo "[WARN] Worker $worker setup failed. Retrying in $RETRY_DELAY seconds..."
      sleep $RETRY_DELAY
      ((attempt++))
    fi
  done

  echo "[ERROR] Worker $worker failed all $MAX_RETRIES setup attempts."
  return 1
}

# Launch all in parallel
for ((worker=0; worker<NUM_WORKERS; worker++)); do
  setup_worker_conda "$worker" &
done

wait
echo "[DONE] All workers finished setup attempts."