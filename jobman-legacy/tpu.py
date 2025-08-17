import time
import subprocess
from datetime import datetime
from jobman.utils import log

def request_tpu(*, 
                tpu_name, 
                zone, 
                accelerator, 
                version,
                pricing="ondemand", 
                startup_script=None,
                tags=None, 
                metadata=None, 
                logfile=None,
                allocation_mode="tpu-vm",
    ):
    assert allocation_mode in {"tpu-vm", "queued-resources"}
    cmd = [
        "gcloud alpha" if allocation_mode == "tpu-vm" else "gcloud",
        "compute", "tpus",
        "tpu-vm" if allocation_mode == "tpu-vm" else "queued-resources",
        "create", tpu_name,
        "--zone", zone,
        "--accelerator-type", accelerator,
        "--version" if allocation_mode == "tpu-vm" else "--runtime-version", version
    ]
    if allocation_mode == "queued-resources":
        cmd += ["--node-id", tpu_name]
        
    pricing = pricing.lower()
    if pricing == "preemptible":
        cmd += ["--preemptible"]
    elif pricing == "spot":
        cmd += ["--spot"]  # ⚠️ Only if supported by your GCP quota
    elif pricing == "ondemand":
        pass  # no flag
    else:
        raise ValueError(f"Invalid pricing type: {pricing}")

    if startup_script:
        cmd += ["--metadata", f"startup-script={startup_script}"]
    if metadata:
        meta_str = ",".join(f"{k}={v}" for k, v in metadata.items())
        cmd += ["--metadata", meta_str]
    if tags:
        cmd += ["--tags", ",".join(tags)]

    log("Launch command:", "INFO")
    log(" ".join(cmd), "DEBUG")

    if allocation_mode == "tpu-vm":
        return request_tpu_vm(cmd, logfile)
    elif allocation_mode == "queued-resources":
        return request_queued_resource(cmd, logfile, tpu_name, zone)

def request_tpu_vm(cmd, logfile):
    attempt = 1
    while True:
        log(f"Attempt {attempt}: Creating TPU VM...", "INFO")
        with open(logfile, "a") as f:
            result = subprocess.run(cmd, stdout=f, stderr=f)
        if result.returncode == 0:
            log("TPU VM created successfully.", "INFO")
            return True
        log("Failed. Retrying immediately...", "ERROR")
        attempt += 1
        
def check_queued_resource_status(tpu_name: str, zone: str) -> str:
    try:
        result = subprocess.run(
            [
                "gcloud", "alpha", "compute", "tpus", "queued-resources", "describe", tpu_name,
                "--zone", zone,
                "--format=value(state)"
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        result = result.stdout.strip()
        result = result.replace("state=", "")
        return result if result else "NOT FOUND"
    except Exception as e:
        log(f"Error while checking status: {e}", "ERROR")
        return "UNKNOWN"
    
def request_queued_resource(cmd, logfile, tpu_name, zone, poll_interval=30):
    with open(logfile, "w") as f:
        result = subprocess.run(cmd, stdout=f, stderr=f)
        
    if result.returncode != 0:
        log("Failed to submit queued resource.", "ERROR")
        return False

        log("Queued resource submitted.", "INFO")
    log("Polling TPU status until it becomes READY...", "INFO")

    while True:
        status = check_queued_resource_status(tpu_name, zone)
        log(f"Current TPU status: {status}", "DEBUG")

        if status in {"READY", "ACTIVE"}:
            log("TPU is READY!", "INFO")
            return True
        elif status in {"FAILED", "DELETING", "UNSPECIFIED", "NOT FOUND"}:
            log(f"TPU entered failed state: {status}", "ERROR")
            return False
        else:
            time.sleep(poll_interval)