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

# clean set up scripts
rm -rf ~/TPU-VM-setup

# clean gcsfuse
echo $BUCKET_DIR
sudo fusermount -u $BUCKET_DIR
rm -rf $BUCKET_DIR

# clean conda
source ~/miniconda3/etc/profile.d/conda.sh
rm -rf ~/conda_envs
rm -rf ~/conda_pkgs
rm -rf ~/miniconda3

EOF