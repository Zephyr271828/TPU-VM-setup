#!/bin/bash

export TPU_NAME=llm-pruning-v6e
export ZONE=us-east1-d
export ACCELERATOR=v6e-16
export VERSION=v2-alpha-tpuv6e
export NUM_WORKERS=4

export BUCKET_NAME=llm_pruning_us_east1_d
export BUCKET_DIR='/home/zephyr/gcs-bucket'