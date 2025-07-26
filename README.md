# TPU-VM-setup

## Configuration
Configure `config.sh` as you want. For example:
```bash
export TPU_NAME=llm-pruning-v3-p
export ZONE=europe-west4-a
export ACCELERATOR=v3-32
export VERSION=tpu-ubuntu2204-base

export BUCKET_NAME=llm_pruning
export BUCKET_DIR='/home/zephyr/gcs-bucket'
```

## Running
Run `start.sh`, which does 3 things:
- if the vm has not been created, request 1
- do conda and gcsfuse set up. If you prefer other package manager, feel free to replace `setup_conda.sh` with your own version.
- execute the desired training command on all hosts. Replace with your own script.