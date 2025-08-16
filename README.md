# JOBMAN-V2

JOBMAN is a modular and extensible job management system for TPU VMs. JOBMAN-V2 is different from V1 because most of the implementations are now in Python instead of shell to enable more complex logics, modularity, and readability.

## Installation
```bash
pip install -e .
```

## TLDR?
Try the following for quick start!
```
jobman create --config=configs/quick-start.yaml
```

## Overall Structure
JOBMAN treats each job instance as a directory in `jobs/<job_id>`. During the creation of the job, information including IP addresses, config snapshot, start time and life cycle will be saved to this directory. TPU request logs, setup logs, and main command logs will be available at `jobs/<job_id>/logs`. For instance, you can find host 0 gcsfuse setup log at `jobs/<job_id>/logs/gcsfuse_worker_0.log`. 

## Creation
You have 2 options when requesting TPU resources: tpu-vm or queued-resources. Below is an example of how you can configure the TPU you want:
```yaml
tpu:
  allocation_mode: "queued-resources"    # tpu-vm | queued-resources
  accelerator: v6e-1
  name: yufeng-${tpu.accelerator}
  zone: us-east1-d
  version: v2-alpha-tpuv6e
  pricing: spot                   
  # spot | ondemand | preemptible
  startup_script: null
  tags: ["jobman", "experiment"]
  metadata:
    owner: "yufeng"
    # owner can be used to map tpus to user I think
    purpose: "testing jobman"
```

## Setup Modules
Jobman treats different components of the setup stage as modules, and you can combine the modules freely in any order you want. 

### SSH & GCSFUSE
Among those modules, 2 of them are strongly suggested: `ssh` and `gcsfuse`. The former enables convenient connection between TPU hosts, whereas the latter mounts your bucket to the TPU host. You may configure as follows:
SSH
```yaml
ssh:
  tpu_private_key: /u/yx1168/.ssh/id_rsa
  tpu_public_key: /u/yx1168/.ssh/id_rsa.pub
```
GCSFUSE
```yaml
gcsfuse:
  bucket_name: llm_pruning_us_east1_d
  mount_path: /home/zephyr/gcs-bucket
```

### Environment Setup
Jobman enables 3 types of env setup: docker, conda, and venv. You should choose at most 1 among the 3 when choosing the modules you want. For example, you may configure as follows to use docker:
```yaml
setup:
  modules:
    - gcsfuse
    - ssh
    - docker
    - command
docker:
  image: yx3038/maxtext_base_image:latest
  mount_dirs:
    - /home/zephyr
    - /dev
    - /run
    - /home/zephyr/.ssh:/root/.ssh
  workdir: /home/zephyr
  flags: ["--privileged", "--network=host"]
```

## Run your job
You can simply configure your job and jobman automatically starts the corresponding env before running it. For example, you can set your job:
```yaml
command:
  run: |
    pip show jax
    pip show flax
  workers: [0] # int | list | "all"
```
Assume your environment type is docker, then the command will be:
```python
remote_cmd = f"""
    docker run {flags} {volume_flags} {workdir_flag} {image} bash -c "{user_command}"
    """
```

## Dashboard
Coming soon

## FAQ
Coming soon

## Contributions & Feedback
If you have any issues with this project or want to contribute to it, please first open an issue in the `Issues` section. This will be of great help to the maintenance of this project!
