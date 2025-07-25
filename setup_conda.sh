#!/bin/bash

set -euo pipefail

echo "Installing Miniconda..."
mkdir -p ~/miniconda3 
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm ~/miniconda3/miniconda.sh

source ~/miniconda3/etc/profile.d/conda.sh
conda init
source ~/miniconda3/etc/profile.d/conda.sh

echo "Setting custom Conda paths..."
mkdir -p ~/conda_envs
export CONDA_ENVS_PATH=~/conda_envs
mkdir -p ~/conda_pkgs
export CONDA_PKGS_PATH=~/conda_pkgs

echo "Creating 'fms' Conda environment..."
conda create -p ~/conda_envs/fms python=3.10 -y

echo "Installing packages..."
pip install --upgrade pip
pip install torch==2.7.0 'torch_xla[tpu]==2.7.0'
pip install hydra-core omegaconf fire pyarrow torchdata datasets transformers==4.46.2

echo "✅ Environment setup complete. Activate it with:"
echo "conda activate ~/conda_envs/fms"