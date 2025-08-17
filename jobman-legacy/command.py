import os
import argparse
import subprocess
from pathlib import Path
from omegaconf import OmegaConf
from jobman.utils import log, infer_num_workers

from collections.abc import Iterable
from jobman.utils import log, infer_num_workers

def infer_workers(cfg):
    accelerator = cfg.tpu.accelerator
    num_workers = infer_num_workers(accelerator)
    worker_spec = cfg.command.get("workers", "all")

    if worker_spec == "all":
        return list(range(num_workers))

    elif isinstance(worker_spec, int):
        if not (0 <= worker_spec < num_workers):
            log(f"Invalid worker index: {worker_spec}. Only {num_workers} workers available.", "ERROR")
            return []
        return [worker_spec]

    elif isinstance(worker_spec, Iterable):
        workers = []
        seen = set()
        for w in worker_spec:
            if not isinstance(w, int) or not (0 <= w < num_workers):
                log(f"Invalid worker index in list: {w}. Only {num_workers} workers available.", "ERROR")
                return []
            if w in seen:
                log(f"Duplicate worker index specified: {w}.", "ERROR")
                return []
            seen.add(w)
            workers.append(w)
        return workers

    else:
        log(f"Invalid type for 'worker': {type(worker_spec)}. Must be 'all', int, or list of int.", "ERROR")
        return []

def run(cfg, logs_dir, env_type=None):
    tpu_name = cfg.tpu.name
    zone = cfg.tpu.zone
    
    user_command = cfg.command.get("run", None)
    if not user_command:
        log("No command specified to run.", "ERROR")
        return
    
    workers = infer_workers(cfg)
    all_success = True
    
    def run_command_worker(i):
        log(f"Running command on worker {i}...", "INFO")

        # Build prefix based on env_type
        if env_type == "docker":
            image = cfg.docker.get("image")
            flags = " ".join(cfg.docker.get("flags", []))
            mount_dirs = cfg.docker.get("mount_dirs", [])
            
            volume_flags = []
            for d in mount_dirs:
                d = str(Path(d).expanduser())  # ensure ~ is expanded
                if ":" in d:
                    host_path, container_path = d.split(":", 1)
                else:
                    host_path = container_path = d
                volume_flags.append(f"-v {host_path}:{container_path}")
            volume_flags = " ".join(volume_flags)
            workdir = cfg.docker.get("workdir", None)
            if workdir:
                workdir = str(Path(workdir).expanduser())
                workdir_flag = f"-w {workdir}"
            else:
                workdir_flag = ""
            
            remote_cmd = f"""
                docker run {flags} {volume_flags} {workdir_flag} {image} bash -c "{user_command}"
            """
        elif env_type == "conda":
            conda_env = cfg.conda.get("env_name")
            remote_cmd = f'conda run -n {conda_env} bash -c "{user_command}"'
        elif env_type == "venv":
            venv_path = cfg.venv.get("path")
            remote_cmd = f'bash -c "source {venv_path}/bin/activate && {user_command}"'
        else:
            remote_cmd = user_command  # no prefix

        ssh_cmd = [
            "gcloud", "alpha", "compute", "tpus", "tpu-vm", "ssh", tpu_name,
            "--zone", zone,
            f"--worker={i}",
            "--ssh-key-file", cfg.ssh.tpu_private_key,  # or id_ed25519
            "--ssh-flag=-o ConnectTimeout=15",
            "--ssh-flag=-o StrictHostKeyChecking=no",
            "--ssh-flag=-o UserKnownHostsFile=/dev/null",
            "--command", remote_cmd,
            "--quiet",
        ]
        
        log(f"SSH command for worker {i}:\n  {' '.join(ssh_cmd)}", "DEBUG")
        
        log_file = logs_dir / f"main_command_worker_{i}.log"

        with open(log_file, "w") as f:
            result = subprocess.run(ssh_cmd, stdout=f, stderr=f)
            if result.returncode != 0:
                log(f"Command failed on worker {i}.", "ERROR")
                all_success = False

    for i in workers:
        run_command_worker(i)

    if all_success:
        log("Main command launched on all workers.", "INFO")
    else:
        log("Main command failed on one or more workers.", "ERROR")
    
    return all_success

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    
    job_dir = Path(f"jobs/{args.job_id}")
    cfg = OmegaConf.load(job_dir / "config.yaml")
    logs_dir = job_dir / "logs"
    
    run(cfg, logs_dir, env_type="docker")