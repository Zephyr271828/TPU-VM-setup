#!/bin/bash

set -euo pipefail

# === Conda Setup ===
bash setup_conda.sh

# === GCSFuse Setup ===
bash setup_gcsfuse.sh

# === SSH Setup ===
bash setup_ssh.sh

# === Podrun Setup ===
bash setup_podrun.sh

# === multihost conda setup ===
~/podrun -i -- bash setup_conda.sh
~/podrun -i -- bash setup_conda2.sh


