#!/bin/bash

export num_chips=1
timestamp="$(date +%Y%m%d_%H%M%S)"

export NUM_WORKERS=$(( (num_chips + 3) / 4 ))
export TPU_NAME="llm-pruning-v6e-${num_chips}-${timestamp}"
export ZONE="us-east1-d"
export ACCELERATOR="v6e-${num_chips}"
export VERSION="v2-alpha-tpuv6e"
export JOB_NAME="llama3.1_4b_width_50B_${timestamp}"
export BUCKET_NAME="llm_pruning_us_east1_d"
export BUCKET_DIR="/home/zephyr/gcs-bucket"
export WORK_DIR="/home/zephyr"

# export COMMAND="
#     pip show jax
#     pip show libtpu
#     pip show flax
#     "

export COMMAND="
    gcloud config set project vision-mix
    gcloud config set compute/zone us-east1-d
    export TPU_PREFIX=$TPU_NAME
    export BUCKET_NAME=$BUCKET_NAME
    bash scripts/finetune_llama3.1_4b_width_50B.sh
"

bash run.sh nohup loop

