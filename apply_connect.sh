#!/bin/bash

source config.sh
source keys.sh

# until \
#     gcloud alpha compute tpus tpu-vm create $TPU_NAME \
#     --zone=$ZONE \
#     --accelerator-type=$ACCELERATOR \
#     --version=$VERSION \
#     --preemptible; \
# do : ; done

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

# echo ${external_ips[0]} 
# echo ${internal_ips[0]}

# ssh zephyr@${external_ips[0]}  -y
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null zephyr@${external_ips[0]} << EOF
cd ~
git clone https://github.com/Zephyr271828/TPU-VM-setup.git
export host0_ip=${internal_ips[0]}
export host1_ip=${internal_ips[1]}
export host2_ip=${internal_ips[2]}
export host3_ip=${internal_ips[3]}
export bucket_name=$BUCKET_NAME
export tpu_key=$tpu_key
export tpu_key_pub=$tpu_key_pub
export github_key=$github_key
export github_key_pub=$github_key_pub
export bucket_dir=$BUCKET_DIR
cd TPU-VM-setup
bash main.sh
EOF