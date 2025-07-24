#!/bin/bash


set -e 


# === Conda Setup ===
bash setup_conda.sh

# === GCSFuse Setup ===
bash setup_gcsfuse.sh

# === SSH Setup ===
source keys.sh
bash setup_ssh.sh

# === Podrun Setup ===
bash setup_podrun.sh

