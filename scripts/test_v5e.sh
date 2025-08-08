#!/bin/bash

export num_chips=16
timestamp="$(date +%Y%m%d_%H%M%S)"

export NUM_WORKERS=$(( (num_chips + 3) / 4 ))
export TPU_NAME="llm-pruning-v5e-${num_chips}-${timestamp}"
export ZONE="europe-west4-a"
export ACCELERATOR="v5litepod-${num_chips}"
export VERSION="v2-alpha-tpuv5"
export JOB_NAME="test_v5e_${timestamp}"
export BUCKET_NAME="llm_pruning"
export BUCKET_DIR="/home/zephyr/gcs-bucket"
export WORK_DIR="/home/zephyr"

# export COMMAND="
#     pip show jax
#     pip show libtpu
#     pip show flax
#     "

export COMMAND="
    rm -rf $WORK_DIR/maxtext
    cp -r $WORK_DIR/gcs-bucket/maxtext $WORK_DIR/maxtext
    mkdir -p $WORK_DIR/maxtext/logs

    gcloud config set project vision-mix
    gcloud config set compute/zone $ZONE
    export TPU_PREFIX=$TPU_NAME
    cd $WORK_DIR/maxtext
    bash scripts/finetune_llama3.1_4b_width_50B.sh
"

bash run.sh nohup loop

