#!/bin/bash

set -euo pipefail

# Enable Google Cloud's package repository
echo "Adding gcsfuse repo..."
echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] http://packages.cloud.google.com/apt gcsfuse-bullseye main" | \
  sudo tee /etc/apt/sources.list.d/gcsfuse.list

# Import the GPG key
echo "Importing GPG key..."
curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | \
  sudo gpg --dearmor -o /usr/share/keyrings/cloud.google.gpg

# Update package list and install gcsfuse
echo "Installing gcsfuse..."
sudo apt-get update
sudo apt-get install -y gcsfuse

# Prompt for bucket name
read -p "enter your bucket name:" bucket_name

# Create mount directory
mkdir -p $BUCKET_DIR

# Mount the bucket
echo "Mounting bucket '$bucket_name' to $BUCKET_DIR ..."
gcsfuse --implicit-dirs --dir-mode=777 --file-mode=777 "$bucket_name" $BUCKET_DIR

echo "✅ Mounted successfully. Contents:"
ls -la $BUCKET_DIR