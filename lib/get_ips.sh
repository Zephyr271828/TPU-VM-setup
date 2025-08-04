#!/bin/bash

# Split into arrays
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

echo "****************************"
for ((i = 0; i < ${#external_ips[@]}; i++)); do
  echo "host $i external ip: ${external_ips[$i]} internal ip: ${internal_ips[$i]}"
done
echo "****************************"