#!/bin/bash

# Use flatten to extract each network endpoint individually
internal_ips=()
external_ips=()

internal_ips=()
external_ips=()

# Skip the header line using `tail -n +2`
while IFS=',' read -r internal external; do
  # Trim quotes if present (csv format may wrap strings in quotes)
  internal=${internal//\"/}
  external=${external//\"/}
  internal_ips+=("$internal")
  external_ips+=("${external:-N/A}")
done < <(
  gcloud alpha compute tpus tpu-vm describe "$TPU_NAME" \
    --zone="$ZONE" \
    --flatten="networkEndpoints[]" \
    --format="csv(networkEndpoints.ipAddress,networkEndpoints.accessConfig.externalIp)" \
    | tail -n +2
)

# Aligned output
echo "****************************"
for ((i = 0; i < ${#external_ips[@]}; i++)); do
  printf "host %-2d  external ip: %-15s  internal ip: %-15s\n" "$i" "${external_ips[$i]}" "${internal_ips[$i]}"
done
echo "****************************"