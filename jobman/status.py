# jobman/status.py
import os
import re
import json
import subprocess
from pathlib import Path
from tabulate import tabulate
from concurrent.futures import ProcessPoolExecutor

jobs_dir = Path("jobs")
MAX_NAME_LENGTH = 40

def truncate(name):
    return name if len(name) <= MAX_NAME_LENGTH else name[:MAX_NAME_LENGTH - 3] + "..."

def parse_meta(meta_path):
    try:
        with open(meta_path, "r") as f:
            return json.load(f)
    except Exception:
        return {}

def parse_log(log_path):
    try:
        with open(log_path, "r") as f:
            lines = f.readlines()
        for line in reversed(lines):
            if "completed step" in line:
                step_match = re.search(r"completed step: (\d+)", line)
                loss_match = re.search(r"loss: ([\d\.eE+-]+)", line)
                step = step_match.group(1) if step_match else "-"
                loss = loss_match.group(1) if loss_match else "-"
                return f"step {step}, loss {loss}"
        return "-"
    except Exception:
        return "-"

def get_status(job_name, tpu_name, zone):
    try:
        result = subprocess.run(
            ["gcloud", "alpha", "compute", "tpus", "tpu-vm", "describe", tpu_name, "--zone", zone, "--format=value(state)"],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        return result.stdout.strip() or "-"
    except Exception:
        return "?"

def process_job_dir(job_dir: Path):
    job_name = job_dir.name
    meta_path = job_dir / "meta.json"
    log_path = job_dir / "main_command.log"

    meta = parse_meta(meta_path)
    accelerator = meta.get("accelerator", "-")
    start_time = meta.get("start_time", "-")
    tpu_name = meta.get("tpu_name", "-")
    zone = meta.get("zone", "-")
    status = get_status(job_name, tpu_name, zone) if tpu_name != "-" and zone != "-" else "-"
    notes = parse_log(log_path)

    return {
        "Job Name": truncate(job_name),
        "Accelerator": accelerator,
        "Start Time": start_time,
        "Status": status,
        "Notes": notes
    }

def status_all():
    job_dirs = [d for d in jobs_dir.iterdir() if d.is_dir()]
    with ProcessPoolExecutor(max_workers=16) as executor:
        rows = list(executor.map(process_job_dir, job_dirs))
    rows.sort(key=lambda x: x["Start Time"] if x["Start Time"] != "-" else "", reverse=True)
    print(tabulate(rows, headers="keys", tablefmt="github"))

def status_single(job_id):
    matches = sorted([d for d in jobs_dir.iterdir() if d.name.startswith(job_id)], reverse=True)
    if not matches:
        print(f"No job found with ID: {job_id}")
        return
    row = process_job_dir(matches[0])
    print(tabulate([row], headers="keys", tablefmt="github"))
    print("\nTail of run.log:")
    run_log = matches[0] / "run.log"
    if run_log.exists():
        os.system(f"tail -n 20 {run_log}")
    else:
        print("(no run.log)")