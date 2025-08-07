#!/bin/bash

# set -euo pipefail

# set -x

timestamp() {
  date +"[%Y-%m-%d %H:%M:%S]"
}

echo "$(timestamp) [INFO] Checking if TPU $TPU_NAME exists in zone $ZONE..."
if gcloud alpha compute tpus tpu-vm list --zone="$ZONE" --format="value(name)" | grep -q "^$TPU_NAME$"; then
  echo "$(timestamp) [INFO] TPU $TPU_NAME exists. Deleting..."
  gcloud alpha compute tpus tpu-vm delete "$TPU_NAME" --zone="$ZONE" -q
fi

gcloud alpha compute tpus tpu-vm list --zone=$ZONE --format="value(name)" | grep -q "^$TPU_NAME"
echo "$(timestamp) [INFO] Creating TPU: name=$TPU_NAME, zone=$ZONE, accelerator=$ACCELERATOR, version=$VERSION (preemptible=true)"
until \
  gcloud alpha compute tpus tpu-vm create $TPU_NAME \
  --zone=$ZONE \
  --accelerator-type=$ACCELERATOR \
  --version=$VERSION \
  --preemptible; do
  echo "$(timestamp) [INFO] Retry creating TPU after delay..."
  sleep 5
done

echo "$(timestamp) [INFO] $TPU_NAME creation completed."
