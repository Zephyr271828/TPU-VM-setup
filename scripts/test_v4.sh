#!/bin/bash

export num_chips=64
timestamp="$(date +%Y%m%d_%H%M%S)"

export NUM_WORKERS=$(( (num_chips + 7) / 8 ))
export TPU_NAME="llm-pruning-v4-${num_chips}-${timestamp}"
export ZONE="us-central2-b"
export ACCELERATOR="v4-${num_chips}"
export VERSION="tpu-ubuntu2204-base"
export JOB_NAME="test_v4_${timestamp}"
export BUCKET_NAME="llm_pruning_us_central2_b"
export BUCKET_DIR="/home/zephyr/gcs-bucket"
export WORK_DIR="/home/zephyr"

export COMMAND="
    pip show jax
    pip show libtpu
    pip show flax
    "

# export COMMAND="
#     gcloud config set project vision-mix
#     gcloud config set compute/zone us-east1-d
#     export TPU_PREFIX=$TPU_NAME
#     bash scripts/finetune_llama3.1_4b_width_200B.sh
# "

bash run.sh nohup loop

