#!/bin/bash

set -euo pipefail

source ~/miniconda3/etc/profile.d/conda.sh

echo "Creating 'fms' Conda environment..."
conda create -p ~/conda_envs/fms python=3.10 -y

echo "Installing packages..."
conda activate ~/conda_envs/fms
pip install --upgrade pip
pip install torch==2.7.0 'torch_xla[tpu]==2.7.0'
pip install hydra-core omegaconf fire pyarrow torchdata datasets transformers==4.46.2

conda deactivate

echo "✅ Environment setup complete. Activate it with:"
echo "conda activate ~/conda_envs/fms"