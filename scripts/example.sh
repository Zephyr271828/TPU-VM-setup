#!/bin/bash

#SBATCH --job-name=test_v4_%j
#SBATCH --tpu-name=llm-pruning-v4-64_%j
#SBATCH --tpu-accelerator=v4-64
#SBATCH --tpu-version=tpu-ubuntu2204-base
#SBATCH --tpu-zone=us-central2-b
#SBATCH --tpu-pricing=spot

#SBATCH --bucket-name=llm_pruning_us_central2_b
#SBATCH --bucket-dir=/home/zephyr/gcs-bucket

#SBATCH --loop

setup_ssh()     { echo "setup ssh here"; }
setup_gcsfuse() { echo "setup gcsfuse here"; }
setup_docker()  { echo "setup docker here"; }
setup_conda()   { echo "setup conda here"; }

run_exp() {
  echo "BATCH_SIZE=$BATCH_SIZE  TPU_NAME=$TPU_NAME"
  # your multihost runner or torchrun call here
}