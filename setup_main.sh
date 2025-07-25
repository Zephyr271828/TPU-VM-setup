#!/bin/bash

set -euo pipefail

# === Conda Setup ===
bash setup_conda.sh

# === GCSFuse Setup ===
# sleep 120
bash setup_gcsfuse.sh

# === SSH Setup ===
bash setup_ssh.sh

# === Podrun Setup ===
bash setup_podrun.sh

# === multihost conda setup ===
~/podrun -i -- bash -c '
cd ~
git clone https://github.com/Zephyr271828/TPU-VM-setup.git
cd TPU-VM-setup
bash setup_conda.sh
bash setup_conda2.sh
'


