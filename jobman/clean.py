import subprocess
import os
from pathlib import Path
from omegaconf import OmegaConf
from jobman.utils import log

JOBS_DIR = Path("jobs")

def delete_tpu_vm(tpu_name: str, zone: str, allocation_mode: str):
    try:
        log(f"Deleting TPU VM: {tpu_name}...", "INFO")
        if allocation_mode == "tpu-vm":
            subprocess.run(["gcloud", "alpha", "compute", "tpus", "tpu-vm", "delete", tpu_name, "--zone", zone, "--quiet"])
        elif allocation_mode == "queued-resources":
            subprocess.run(["gcloud", "compute", "tpus", "tpu-vm", "delete", tpu_name, "--zone", zone, "--quiet"])
            subprocess.run(["gcloud", "compute", "tpus", "queued-resources", "delete", tpu_name, "--zone", zone, "--quiet"])
        log(f"TPU VM {tpu_name} deleted successfully.", "INFO")
    except subprocess.CalledProcessError:
        log(f"Failed to delete TPU VM {tpu_name}. It may not exist.", "WARNING")

def clean_single(job_id: str):
    job_dir = JOBS_DIR / job_id
    if not job_dir.exists():
        log(f"Job {job_id} does not exist.", "ERROR")
        return

    config_path = job_dir / "config.yaml"
    if not config_path.exists():
        log(f"No config.yaml found in job {job_id}, skipping TPU deletion", "WARNING")
    else:
        cfg = OmegaConf.load(config_path)
        tpu_name = cfg.get("tpu", {}).get("name", None)
        zone = cfg.get("tpu", {}).get("zone", None)
        allocation_mode = cfg.get("tpu", {}).get("allocation_mode", None)
        if tpu_name and zone and allocation_mode:
            delete_tpu_vm(tpu_name, zone, allocation_mode)

    log("Killing any process holding log files...", "INFO")
    logs_dir = job_dir / "logs"
    for log_file in logs_dir.glob("*.log"):
        try:
            pid_output = subprocess.check_output(["lsof", "-t", str(log_file)])
            for pid in pid_output.decode().splitlines():
                os.kill(int(pid), 9)
        except subprocess.CalledProcessError:
            continue  # No process found

    log("Deleting entire job folder...", "INFO")
    subprocess.run(["rm", "-rf", str(job_dir)])

    log(f"Cleaned up job {job_id}", "INFO")

def clean_all():
    for job_dir in JOBS_DIR.iterdir():
        if job_dir.is_dir() and job_dir.name.isdigit():
            clean_single(job_dir.name)