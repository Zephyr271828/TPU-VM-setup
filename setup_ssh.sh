#!/bin/bash

echo "Setting up SSH keys..."

source keys.sh

echo "$id_rsa" > ~/.ssh/id_rsa
chmod 600 ~/.ssh/id_rsa

echo "$id_rsa_pub" > ~/.ssh/id_rsa.pub
chmod 644 ~/.ssh/id_rsa.pub

# ED25519 key for GitHub
echo "$id_ed25519" > ~/.ssh/id_ed25519_github
chmod 600 ~/.ssh/id_ed25519_github

echo "$id_ed25519_pub" > ~/.ssh/id_ed25519_github.pub
chmod 644 ~/.ssh/id_ed25519_github.pub

read -p "Enter your host0 internal ip:" host0_ip
host0_prefix=${host0_ip%.*}.*  

echo "Updating ~/.ssh/config..."

cat <<EOF >> ~/.ssh/config
# GitHub SSH access
Host github.com
  HostName github.com
  User git
  IdentityFile ~/.ssh/id_ed25519_github

# Internal cluster access
Host $host0_prefix 127.0.0.1
  StrictHostKeyChecking no
  UserKnownHostsFile /dev/null
  LogLevel ERROR
EOF

chmod 600 ~/.ssh/config

echo "✅ SSH setup complete."