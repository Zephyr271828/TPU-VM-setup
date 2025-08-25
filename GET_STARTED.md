# Get Started

This is the doc for you to understand the basics about TPUs and create your first job with jobman! 

## Table of Contents


## TPU Basics
Before start working with Jobman, let's go through some basics concepts in TPU:
- TPU (Tensor Processing Unit): Google’s hardware for fast machine learning (like a GPU, but optimized for deep learning).
- TPU VM: The machine you log into to run code directly on TPUs.
- TPU Pod: A cluster of many TPUs connected together for large-scale training.
- Host: The CPU machine that manages a TPU (in a pod, there are multiple hosts).
- External IP: Used to log in (SSH) from your computer.
- Internal IP: Used for TPUs to talk to each other inside a pod.
- Bucket: Google Cloud Storage (GCS) where you put datasets, logs, and checkpoints. Note you only have 100G disk space on each TPU VM (host), so it's necessary to store your large files in a bucket first, then access it by mounting to your VM or by using [gsutil](https://cloud.google.com/storage/docs/gsutil).
- SSH Key: Needed to securely connect to TPU hosts (and to let them connect to each other in multi-host jobs).
- Region: A large geographic area (e.g., us-central1, europe-west4) that contains Google Cloud resources. **Buckets are tied to a specific region, meaning data is physically stored there**.
- Zone: A smaller location within a region (e.g., us-central1-b). **TPUs are created in zones**.

```
                ┌──────────────────────────────────────────────┐
                │                 REGION                       │
                │              (e.g., us-central1)             │
                │                                              │
                │  ┌────────────────┐     ┌─────────────────┐  │
GCS Bucket ───▶ │  │  GCS BUCKET    │     │     ZONE A      │  │
 (lives at      │  │ (llm_pruning_  │     │ (us-central1-a) │  │
 region level)  │  │  us_central1)  │     │  ┌──────────┐   │  │
                │  └────────────────┘     │  │ TPU VM 1 │   │  │
                │                         │  └──────────┘   │  │
                │                         │  ┌──────────┐   │  │
                │                         │  │ TPU VM 2 │   │  │
                │                         │  └──────────┘   │  │
                │                         └─────────────────┘  │
                │                                              │
                │                         ┌─────────────────┐  │
                │                         │     ZONE B      │  │
                │                         │ (us-central1-b) │  │
                │                         │  ┌──────────┐   │  │
                │                         │  │ TPU VM 3 │   │  │
                │                         │  └──────────┘   │  │
                │                         └─────────────────┘  │
                └──────────────────────────────────────────────┘
```

<!-- ```mermaid
flowchart TB
  subgraph REG[REGION: us-central1]
    B[(GCS Bucket)]
    subgraph ZA[ZONE: us-central1-a]
      A1[TPU VM 1]
      A2[TPU VM 2]
    end
    subgraph ZB[ZONE: us-central1-b]
      B1[TPU VM 3]
    end
  end

  %% Data/access paths
  B --- A1
  B --- A2
  B -.cross-zone ok but stay in region.-> B1

  %% Annotations
  classDef good fill:#eaffea,stroke:#2ca02c,color:#2c3e50;
  classDef warn fill:#fff6e5,stroke:#ff9900,color:#2c3e50;

  class A1,A2,B good
  class B1 warn
``` -->

## Configuration

# Jobman Configuration Guide

This guide explains each part of the configuration file and how to customize it for your own TPU jobs. You may build upon [configs/template.yaml](configs/template.yaml) to create your own config.

---

### `job`
Defines global job behavior.

- **`name`**: A human-readable label for the run. Shows up in dashboards/logs.  
  *Tip:* Encode model, scale, and purpose (e.g., `pretrain-llama3-8b-200b-tune`).
- **`env_type`**: Runtime environment. `docker` means all work happens inside a container. You may also choose `conda` or `venv`.
- **`loop`**: If `true`, the job restarts automatically on exit (useful for spot/preemptible TPUs or iterative jobs).

e.g.
```yml
job:
  name: pretrain-llama3-8b-200b-tune
  env_type: docker # docker | conda | venv
  loop: true
```
---

### `tpu`
Requests and configures TPU resources.

- **`allocation_mode`**:  
  - `tpu-vm`: direct, legacy style allocation.  
  - `queued-resources`: recommended; queues the request until capacity is available.
- **`accelerator`**: TPU type/size (e.g., `v4-8`, `v4-32`, `v4-128`). Pick based on model/global batch and budget.
- **`name`**: TPU resource name. Interpolates variables (e.g., `yufeng-${tpu.accelerator}`) so names stay descriptive.
- **`zone`**: Compute *zone* (e.g., `us-central2-b`).  
  *Rule of thumb:* Keep your **bucket** in the same **region** (here: `us-central2`) to reduce latency and egress costs.
- **`version`**: Base TPU VM image (e.g., `tpu-ubuntu2204-base`).
- **`pricing`**:  
  - `spot`: cheapest; can be evicted.  
  - `ondemand`: standard pricing.  
  - `preemptible`: legacy term on some platforms; similar to spot.
- **`startup_script`**: Optional path to a script run on VM boot (e.g., install OS packages). Use `null` to skip.
- **`tags`**: Freeform labels (e.g., `["jobman","experiment"]`) for filtering.
- **`metadata`**: Key–value metadata stored on the TPU resource (e.g., `owner`, `purpose`) for team accounting/search.

e.g
```yml
tpu:
  allocation_mode: "queued-resources"    # tpu-vm | queued-resources
  accelerator: v4-128
  name: yufeng-${tpu.accelerator}
  zone: us-central2-b
  version: tpu-ubuntu2204-base
  pricing: spot
  # spot | ondemand | preemptible
  startup_script: null
  tags: ["jobman", "experiment"]
  metadata:
    owner: "yufeng"
    # owner can be used to map tpus to user I think
    purpose: "pretrain"
```
---

### `gcsfuse`
Mounts a GCS bucket into the VM filesystem.

- **`bucket_name`**: Your GCS bucket (e.g., `llm_pruning_us_central2_b`).  
  *Note:* Bucket lives at **region** scope; choose same region as the TPU’s zone’s region.
- **`mount_path`**: Local path where the bucket will appear (e.g., `/home/zephyr/gcs-bucket`).  
  *Use cases:* datasets, checkpoints, scripts.

e.g.
```yml
gcsfuse:
  bucket_name: llm_pruning_us_central2_b
  mount_path: /home/zephyr/gcs-bucket
```
---

### `ssh`
Prepares SSH keys and host configs on the TPU VM(s).

- **`private_key`**: Default SSH private key you use to connect to the VM from local machine (e.g., `~/.ssh/id_rsa`).
- **`identities`**: Additional identities and inline `ssh_config` snippets.
  - `config_entry` blocks let you preconfigure hosts (e.g., `Host 10.*` for intra-pod SSH, `Host github.com` for git).
  - Ensures multi-host jobs can SSH among nodes; also avoids manual `ssh-add`.

e.g.
```yml
ssh:
  private_key: ~/.ssh/id_rsa
  identities:
    - private_key: ~/.ssh/id_rsa
      public_key: ~/.ssh/id_rsa.pub
      config_entry: | 
        Host 10.*
          IdentityFile ~/.ssh/id_rsa
          IdentitiesOnly yes
    - private_key: ~/.ssh/id_ed25519_github
      public_key: ~/.ssh/id_ed25519_github.pub
      config_entry: |
        Host github.com
          User git
          IdentityFile ~/.ssh/id_ed25519_github
          IdentitiesOnly yes
```
---

### `docker`
Container runtime settings for reproducible environments.

- **`image`**: Docker image to run (e.g., `yx3038/maxtext_base_image:latest`). Pin versions for reproducibility.
- **`env_vars`**: Environment variables injected into the container (e.g., `HOME=/home/zephyr`).
- **`mount_dirs`**: Host paths mounted inside the container.  
  - Common mounts: home dir, `/dev`, `/run`, GCloud config, SSH (if you need `git clone` over SSH).
- **`workdir`**: Default working directory inside the container.
- **`flags`**: Extra `docker run` flags.  
  - `--privileged`: grants extended privileges (needed for some low-level ops).  
  - `--network=host`: shares host network (useful for TPU comms, faster GCS access).

e.g.
```yml
docker:
  image: yx3038/maxtext_base_image:latest
  env_vars:
    - HOME=/home/zephyr
  mount_dirs:
    - /home/zephyr
    - /dev
    - /run
    - /home/zephyr/.config/gcloud:/root/.config/gcloud
    # - /home/zephyr/.ssh:/root/.ssh
  workdir: /home/zephyr
  flags: ["--privileged", "--network=host"]
```

---

### `conda`
(Optional) Create/use a Conda env inside the container.

- **`name`**: Conda env name (e.g., `fms`).
- **`config_file`**: Path to an `environment.yaml` with Conda deps.  
  *Tip:* Use either Conda *or* venv—keeping both increases maintenance.

e.g.
```yml
conda:
  name: fms
  config_file: assets/fms.yaml
```

---

### `venv`
(Optional) Create/use a Python virtualenv inside the container.

- **`name`**: Venv name (e.g., `maxtext`).
- **`requirements_file`**: `pip` requirements file path.
- **`python`**: Python version for the venv (e.g., `"3.9"`).  
  *Tip:* Match your framework’s supported versions (JAX/TF/PyTorch constraints).

e.g.
```yml
venv:
  name: maxtext
  requirements_file: assets/requirements.txt  
  python: "python3.9" 
```
---

### `command`
The actual workload to run on the TPU VM (inside the container).

- **`cmd`**: A shell script block that orchestrates your run. In your example, it:
  1. Resets `/home/zephyr/maxtext`.
  2. Copies project code from the mounted GCS bucket into local disk (faster local I/O).
  3. Creates a `logs` dir.
  4. Sets `gcloud` project and zone (keeps CLI aligned with the TPU location).
  5. Exports `TPU_PREFIX` (TPU resource name) and `BUCKET_NAME` for downstream scripts.
  6. Runs `pretrain/llama3_8b_L200_1e-4.sh` to launch training.  
     *(Commented)* Shows how you might run lm-eval afterward.
- **`workers`**: Which hosts run the command.  
  - `[0]`: only the first host (controller).  
  - `"all"`: run on all hosts (for symmetric multi-host jobs).  
  - `[0,1,…]`: explicit list if needed.

e.g.
```yml
command:
  cmd: |
    pip show flax
    pip show jax
  workers: [0] # int | list | "all"
```
---

### Minimal Checklist Before You Run
- Bucket exists and is in the **same region** as your TPU (e.g., `us-central2`).
- SSH keys are valid; `config_entry` patterns are correct.

## Commands Mannual
Below are the most common cli commands you may find useful in jobman.

### Basic Commands
| Purpose | Command |
|:--:|:--:|
| Create a new job | `jobman create <config_path>` |
| Check all jobs status | `jobman list` |
| Resume an existing job | `jobman resume <job_id>` |
| Cancel a specific job | `jobman cancel <job_id>` |
| Cancel and delete a specific job | `jobman delete <job_id>` |

### Debugging Commands
| Run docker setup job | e.g: `python -m jobman.envs.docker <job_id>` |
| Run docker setup job | e.g: `python -m jobman.envs.docker <job_id>` |
| Run command on a specific job | e.g: `python -m jobman.job <job_id> --cmd-only` |