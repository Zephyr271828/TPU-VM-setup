#!/bin/bash

jobman create \
    --name test \
    --accelerator v4-256 \
    --zone us-central2-b \
    --tpu-name yufeng-v4-256 \