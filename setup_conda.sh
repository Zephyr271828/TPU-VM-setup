#!/bin/bash

set -euo pipefail

echo "Installing Miniconda..."
mkdir -p ~/miniconda3 
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm ~/miniconda3/miniconda.sh

source ~/miniconda3/etc/profile.d/conda.sh
conda init

echo "Setting custom Conda paths..."
mkdir -p ~/conda_envs
export CONDA_ENVS_PATH=~/conda_envs
mkdir -p ~/conda_pkgs
export CONDA_PKGS_PATH=~/conda_pkgs

echo "Accept terms of service..."
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/main
conda tos accept --override-channels --channel https://repo.anaconda.com/pkgs/r