#!/bin/bash

# set -euo pipefail

set -x

gcloud alpha compute tpus tpu-vm list --zone=$ZONE --format="value(name)" | grep -q "^$TPU_NAME"
if [ $? -ne 0 ]; then
  echo "[INFO] Creating TPU: name=$TPU_NAME, zone=$ZONE, accelerator=$ACCELERATOR, version=$VERSION (preemptible=true)"
  until \
    gcloud alpha compute tpus tpu-vm create $TPU_NAME \
    --zone=$ZONE \
    --accelerator-type=$ACCELERATOR \
    --version=$VERSION \
    --preemptible; \
  do : ; done
fi
