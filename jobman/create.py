from pathlib import Path
from datetime import datetime
import fcntl
import json

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

def create(name, accelerator, zone, tpu_name):
    job_id = get_next_job_id()
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # fallback to name from accelerator
    job_name = f"{name}_{timestamp}"

    if not tpu_name:
        tpu_name = f"tpu-{job_id}"

    job_dir = Path("jobs") / job_id
    job_dir.mkdir(parents=True)

    meta = {
        "id": job_id,
        "name": job_name,
        "start_time": timestamp,
        "accelerator": accelerator,
        "zone": zone,
        "tpu_name": tpu_name,
    }

    (job_dir / "meta.json").write_text(json.dumps(meta, indent=2))
    print(f"✅ Created job: {job_name}")