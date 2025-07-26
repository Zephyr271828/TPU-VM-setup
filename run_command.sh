#!/bin/bash

# cd /home/zephyr/gcs-bucket/pruning
TARGET_DIR=~/gcs-bucket/pruning/fms-grad-accum
if [ ! -d "$TARGET_DIR" ]; then
    hostname=$(hostname)
    if [[ "$hostname" =~ 0$ ]]; then
        echo "Hostname ends with 0 — cloning repository..."
        git clone -b minitron-tpu git@github.com:jiachenzhu/fms.git "$TARGET_DIR"
    else
        echo "Directory not found and hostname does not end with 0 — sleeping 60 seconds..."
        sleep 60
    fi
else
    echo "Directory already exists: $TARGET_DIR"
fi

bash ~/gcs-bucket/pruning/fms-grad-accum/scripts/finetuning.sh
