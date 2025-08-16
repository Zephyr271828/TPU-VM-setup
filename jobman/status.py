from pathlib import Path
from omegaconf import OmegaConf
import subprocess
from tabulate import tabulate
from concurrent.futures import ProcessPoolExecutor

jobs_dir = Path("jobs")
MAX_NAME_LENGTH = 40

def truncate(name):
    return name if len(name) <= MAX_NAME_LENGTH else name[:MAX_NAME_LENGTH - 3] + "..."

def parse_log(log_path):
    try:
        with open(log_path, "r") as f:
            lines = f.readlines()
        for line in reversed(lines):
            if "completed step" in line:
                step = re.search(r"completed step: (\d+)", line)
                loss = re.search(r"loss: ([\d\.eE+-]+)", line)
                return f"step {step.group(1) if step else '-'}, loss {loss.group(1) if loss else '-'}"
        return "-"
    except Exception:
        return "-"

def get_status(job_id):
    # try:
    #     result = subprocess.run(
    #         ["gcloud", "alpha", "compute", "tpus", "tpu-vm", "describe", tpu_name, "--zone", zone, "--format=value(state)"],
    #         stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
    #     )
    #     return result.stdout.strip() or "-"
    # except Exception:
    #     return "-"
    path = Path("jobs") / job_id / "status.txt"
    return path.read_text().strip() if path.exists() else "-"

def get_ips(job_id):
    import json
    path = Path("jobs") / job_id / "ips.json"
    try:
        with open(path, "r") as f:
            ips = json.load(f)
            if isinstance(ips, list) and len(ips) > 0:
                host0 = ips[0]
                host0_internal_ip = host0.get("internal_ip", "-")
                host0_external_ip = host0.get("external_ip", "-")
        return host0_external_ip
    except:
        return "-"

def process_job_dir(job_dir: Path):
    config_path = job_dir / "config.yaml"
    start_time_path = job_dir / "start_time.txt"
    log_path = job_dir / "logs" / "main_command.log"

    try:
        cfg = OmegaConf.load(config_path)
    except Exception:
        return None

    job_id = job_dir.name
    accelerator = cfg.get("tpu", {}).get("accelerator", "-")
    tpu_name = cfg.get("tpu", {}).get("name", "-")
    zone = cfg.get("tpu", {}).get("zone", "-")
    job_name = cfg.get("job", {}).get("name", job_dir.name)
    start_time = start_time_path.read_text().strip() if start_time_path.exists() else "-"
    # status = get_status(tpu_name, zone) if tpu_name != "-" and zone != "-" else "-"
    host0_external_ip = get_ips(job_id)
    status = get_status(job_id)
    notes = parse_log(log_path)

    return {
        "Job ID": job_id,
        "Job Name": truncate(job_name),
        "Accelerator": accelerator,
        "Start Time": start_time,
        "Host0 IP": host0_external_ip,
        "Status": status,
        "Notes": notes
    }

def status_all():
    job_dirs = [
        d for d in jobs_dir.iterdir()
        if d.is_dir() and d.name.isdigit() and len(d.name) == 6
    ]

    with ProcessPoolExecutor(max_workers=16) as executor:
        rows = [r for r in executor.map(process_job_dir, job_dirs) if r is not None]

    rows.sort(key=lambda x: x["Start Time"], reverse=True)
    print(tabulate(rows, headers="keys", tablefmt="github"))
    
def status_single(job_id: str):
    job_dir = jobs_dir / job_id
    if not job_dir.exists():
        print(f"❌ No job found with ID {job_id}")
        return

    row = process_job_dir(job_dir)
    if row:
        print(tabulate([row], headers="keys", tablefmt="github"))
    else:
        print(f"⚠️ Could not parse job: {job_id}")

if __name__ == "__main__":
    main()