#!/bin/bash

source config.sh

gcloud alpha compute tpus tpu-vm delete $TPU_NAME --zone=$ZONE -q