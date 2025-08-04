# TPU Job Management System

This is a project for slurm-like job management on TPU pods. 

## Codebase Organization
```
├── README.md
├── get_job_status.py
├── jobs
├── lib
│   ├── get_ips.sh
│   ├── request_vm.sh
│   ├── run_w_docker.sh
│   ├── setup_docker.sh
│   ├── setup_gcsfuse.sh
│   ├── setup_ssh.sh
│   └── write_meta.sh
├── loop_run.sh
├── run.sh
└── scripts
```

## Quick Start
Dependencies:
```bash
pip install tabulate
```
Example:
See `scripts/run_maxtext_llama3.1_4b_width_50B.sh`. You must specify all the environment variables, otherwise the script is going to throw an exeception. You probably need to modify `lib/setup_ssh.sh`, `lib/setup_docker.sh`, `lib/run_w_docker.sh` as well for your custom environment setup and job commands.

## See Job Status
I wrote a simple Python script `get_job_status.py` to get a summary of the job status like slurm. The result looks like follows:
```bash
| Job Name             | Accelerator   | Start Time          | Status   | Notes   |
|----------------------|---------------|---------------------|----------|---------|
| llama3.1_4b_width... | v6e-16        | 2025-08-04 21:36:26 | CREATING | -       |
| llama3.1_4b_width... | v6e-16        | 2025-08-04 21:35:12 | CREATING | -       |
| llama3.1_4b_width... | v6e-16        | 2025-08-04 21:30:08 | -        | -       |
| llama3.1_4b_width... | v6e-16        | 2025-08-04 21:21:04 | -        | -       |
| llama3.1_4b_width... | v6e-1         | 2025-08-04 21:12:32 | READY    | -       |
```
Note most of my jobs are maxtext training, so the "Notes" column shows the training step and loss. You should modify `get_job_status.get_status` for customization.

## Run Jobs in backend
By running `bash run.sh nohup`, you run your job request in a nohup mode. You can run
```bash
kill -9 $(cat jobs/<job_name>/pid.txt)
```
to kill the process if you no longer want it.

## Automatic Queue
Coming soon!