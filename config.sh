#!/bin/bash

export TPU_NAME=llm-pruning-v3-p
export ZONE=europe-west4-a
export ACCELERATOR=v3-32
export VERSION=tpu-ubuntu2204-base

export BUCKET_NAME=llm_pruning
export BUCKET_DIR='/mnt/gcs-bucket'