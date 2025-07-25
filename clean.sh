#!/bin/bash

# set -euo pipefail

source config.sh

readarray -t ip_lines < <(gcloud alpha compute tpus tpu-vm describe $TPU_NAME --zone=$ZONE \
  | awk '/externalIp:/{eip=$2} /ipAddress:/{print eip, $2}')

# Split into arrays
external_ips=()
internal_ips=()
for line in "${ip_lines[@]}"; do
  read -r ext int <<< "$line"
  external_ips+=("$ext")
  internal_ips+=("$int")
done

ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null zephyr@${external_ips[0]} << EOF

echo "🔹 Cleaning setup scripts..."
rm -rf ~/TPU-VM-setup

echo "🔹 Unmounting GCSFuse from $BUCKET_DIR..."
if mountpoint -q "$BUCKET_DIR"; then
  sudo fusermount -u "$BUCKET_DIR" || sudo umount -l "$BUCKET_DIR"
fi
rm -rf "$BUCKET_DIR"

echo "🔹 Cleaning Conda..."
rm -rf ~/conda_envs ~/conda_pkgs ~/miniconda3

EOF