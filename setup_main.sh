#!/bin/bash

set -euo pipefail

# === Conda Setup ===
bash setup_conda.sh

# === GCSFuse Setup ===
bash setup_gcsfuse.sh

# === Conda Setup ===
bash setup_conda2.sh