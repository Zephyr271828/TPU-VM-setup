#!/bin/bash

set -euo pipefail

cd /home/zephyr

# === Install podrun ===
echo "Installing podrun..."
wget https://raw.githubusercontent.com/ayaka14732/llama-2-jax/18e9625f7316271e4c0ad9dea233cfe23c400c9b/podrun
chmod +x podrun

# === Read host IPs ===
# read -p "Enter your host1 internal ip:" host1_ip
# read -p "Enter your host2 internal ip:" host2_ip
# read -p "Enter your host3 internal ip:" host3_ip

# === Save IPs to file ===
echo -e "\n$host1_ip\n$host2_ip\n$host3_ip" >> ~/podips.txt
echo "Saved pod IPs to ~/podips.txt"

# === Update and install packages on remote hosts ===
echo "Updating packages and installing nfs-common on all hosts..."
~/podrun -i -- sudo apt-get update -y -qq
~/podrun -i -- sudo apt-get upgrade -y -qq
~/podrun -- sudo apt-get install -y -qq nfs-common

# === Install NFS server locally ===
echo "Installing NFS server on host0..."
sudo apt-get install -y -qq nfs-kernel-server

# === Setup shared directory ===
sudo mkdir -p /nfs_share
sudo chown -R nobody:nogroup /nfs_share
sudo chmod 777 /nfs_share
echo "Created /nfs_share with open permissions."

# === Configure /etc/exports ===
subnet_prefix=${host0_ip%.*}.0/24
export_line="/nfs_share  ${subnet_prefix}(rw,sync,no_subtree_check)"
echo "$export_line" | sudo tee -a /etc/exports > /dev/null

echo "Added NFS export rule:"
echo "$export_line"

sudo exportfs -a
sudo systemctl restart nfs-kernel-server

# === Mount on remote hosts ===
~/podrun -- sudo mkdir -p /nfs_share
~/podrun -- sudo mount 172.21.12.2:/nfs_share /nfs_share
~/podrun -i -- ln -sf /nfs_share ~/nfs_share

touch ~/nfs_share/meow
~/podrun -i -- ls -la ~/nfs_share/meow

mkdir -p ~/nfs_share
cat <<EOF >> ~/nfs_share/setup.sh
#!/bin/bash
set -euo pipefail

export DEBIAN_FRONTEND=noninteractive

sudo apt-get update -y -qq
sudo apt-get upgrade -y -qq
sudo apt-get install -y -qq golang neofetch zsh byobu
sudo apt-get install -y -qq software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
EOF

cat setup_conda.sh >> ~/nfs_share/setup.sh
cat setup_gcsfuse.sh >> ~/nfs_share/setup.sh
chmod +x ~/nfs_share/setup.sh

# === Run setup on remote nodes ===
~/podrun -i ~/nfs_share/setup.sh