import os
import json
import fcntl
import shutil
import subprocess
from pathlib import Path
from datetime import datetime
from omegaconf import OmegaConf

from jobman import tpu, command
from jobman.utils import log, infer_num_workers
from jobman.setup import gcsfuse, ssh, docker, conda, venv

def get_next_job_id():
    counter_file = Path("jobs/.state/next_job_id.txt")
    lock_file = Path("jobs/.state/lock")
    counter_file.parent.mkdir(parents=True, exist_ok=True)
    if not counter_file.exists():
        counter_file.write_text("0")

    with open(lock_file, "w") as lock_fp:
        fcntl.flock(lock_fp, fcntl.LOCK_EX)
        current = int(counter_file.read_text())
        next_id = current + 1
        counter_file.write_text(str(next_id))
        fcntl.flock(lock_fp, fcntl.LOCK_UN)
    return f"{next_id:06d}"

def validate_modules(modules: list[str]) -> str:
    envs = {"docker", "conda", "venv", "virtualenv"}
    used = [m for m in modules if m in envs]
    if len(used) > 1:
        raise ValueError(f"Multiple environments found: {used}")

def get_tpu_ips(tpu_name: str, zone: str):
    """Get internal and external IPs of all TPU workers."""
    try:
        # Call gcloud to get TPU VM info in JSON
        result = subprocess.run(
            [
                "gcloud", "alpha", "compute", "tpus", "tpu-vm", "describe",
                tpu_name, "--zone", zone, "--format=json"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=True
        )
        data = json.loads(result.stdout)
        workers = data.get("networkEndpoints", [])

        ip_info = []
        for i, w in enumerate(workers):
            external_ip = w.get("accessConfig", {}).get("externalIp", "-")
            internal_ip = w.get("ipAddress", "-")
            ip_info.append({
                "worker": i,
                "internal_ip": internal_ip,
                "external_ip": external_ip
            })

        return ip_info

    except subprocess.CalledProcessError as e:
        print(f"Failed to describe TPU: {e.stderr}")
        return []
    except Exception as e:
        print(f"Unexpected error: {e}")
        return []

def create(config_path: str):
    cfg = OmegaConf.load(config_path)
    
    job_id = get_next_job_id()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    cfg.job.name = f"{cfg.job.name}_{timestamp}"
    cfg.tpu.name = f"{cfg.tpu.name}_{timestamp}"
    job_dir = Path("jobs") / job_id
    logs_dir = job_dir / "logs"
    job_dir.mkdir(parents=True)
    logs_dir.mkdir(parents=True)
    (job_dir / "status.txt").write_text("INIT\n")
    
    OmegaConf.save(cfg, job_dir / "config.yaml")
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    (job_dir / "start_time.txt").write_text(start_time)

    # Step 1: request TPU
    tpu_created = tpu.request_tpu(
        tpu_name=cfg.tpu.name,
        zone=cfg.tpu.zone,
        accelerator=cfg.tpu.accelerator,
        version=cfg.tpu.version,
        pricing=cfg.tpu.get("pricing", "spot"),
        startup_script=cfg.tpu.get("startup_script", None),
        metadata=cfg.tpu.get("metadata", {}),
        tags=cfg.tpu.get("tags", []),
        logfile=logs_dir / "request_vm.log",
        allocation_mode=cfg.tpu.get("allocation_mode", "tpu-vm"),
    )
    if not tpu_created:
        log(f"Failed to create TPU. Aborting. See logs at {logs_dir / 'request_vm.log'}", "ERROR")
        (job_dir / "status.txt").write_text("FAILED\n")
        return
    ip_info = get_tpu_ips(cfg.tpu.name, cfg.tpu.zone)

    with open(job_dir / "ips.json", "w") as f:
        json.dump(ip_info, f, indent=2)
    
    # Step 2: setup module registry
    modules = cfg.setup.modules
    module_map = {
        "gcsfuse": lambda: gcsfuse.setup(cfg, logs_dir),
        "ssh": lambda: ssh.setup(cfg, logs_dir),
        "docker": lambda: docker.setup(cfg, logs_dir),
        "conda": lambda: conda.setup(cfg, logs_dir),
        "venv": lambda: venv.setup(cfg, logs_dir),
    }
    
    env_type_map = {
        "docker": "docker",
        "conda": "conda",
        "venv": "venv",
    }

    modules = cfg.setup.modules
    env_type = validate_modules(modules)
    
    # Step 3: execute setup modules
    for module in modules:
        if module == "command":
            continue
        if module not in module_map:
            log(f"Unknown module: {module}", "WARNING")
            continue

        log(f"Running setup module: {module}")
        module_map[module]()  # call the lambda
        if module in env_type_map:
            env_type = env_type_map[module]

    # Step 4: run main command
    if "command" in modules:
        if env_type is None:
            log("No environment (docker/conda/venv) specified before 'command'", "WARNING")
            (job_dir / "status.txt").write_text("FAILED\n")
            return
        log("Running main command...", "INFO")
        command.run(cfg, logs_dir, env_type=env_type)

    (job_dir / "status.txt").write_text("RUNNING\n")
    log(f"Job {cfg.job.name} launched.", "INFO")