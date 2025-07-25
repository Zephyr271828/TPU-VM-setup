#!/bin/bash

cd /home/zephyr/gcs-bucket/pruning
git clone -b minitron-tpu git@github.com:jiachenzhu/fms.git fms-grad-accum
bash ~/gcs-bucket/pruning/fms-grad-accum/scripts/finetuning.sh
