#!/bin/bash

source config.sh

gcloud alpha compute tpus tpu-vm list --zone=$ZONE --format="value(name)" | grep -q "^$TPU_NAME$"
if [ $? -ne 0 ]; then
  until \
      gcloud alpha compute tpus tpu-vm create $TPU_NAME \
      --zone=$ZONE \
      --accelerator-type=$ACCELERATOR \
      --version=$VERSION \
      --preemptible; \
  do : ; done
fi

# sleep 60

bash setup_conda.sh

sleep 30

source keys.sh
bash setup_ssh.sh

sleep 60

bash setup_gcsfuse.sh

sleep 60

bash setup_maxtext.sh

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
echo "Use 'ssh $USER@${external_ips[0]}' to access the remote host"
echo "****************************"

sleep 60

bash run_maxtext.sh

# bash run_fms.sh
