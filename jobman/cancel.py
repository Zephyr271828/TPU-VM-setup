# jobman/cancel.py
from pathlib import Path
import subprocess
import os
import signal
from jobman.utils import log

def cancel(job_id):
    jobs_root = Path("jobs")
    matches = sorted(jobs_root.glob(f"{job_id}"))
    if not matches:
        log(f"No job found with ID {job_id}", "ERROR")
        return

    job_dir = matches[0]
    logs_dir = job_dir / "logs"
    if not logs_dir.exists():
        log(f"No logs/ directory found in {job_dir}, skipping lsof check.", "WARNING")
        logs_dir = []

    killed_pids = set()
    for log_file in logs_dir.glob("*.log"):
        try:
            # Run lsof -t to get PID using this log file
            result = subprocess.run(["lsof", "-t", str(log_file)], capture_output=True, text=True)
            pids = [int(pid) for pid in result.stdout.strip().split("\n") if pid.strip()]
            for pid in pids:
                try:
                    os.kill(pid, signal.SIGTERM)
                    log(f"Killed process {pid} (log: {log_file.name})", "INFO")
                    killed_pids.add(pid)
                except ProcessLookupError:
                    log(f"Process {pid} already dead.")
        except Exception as e:
            log(f"Error inspecting {log_file.name}: {e}", "ERROR")

    # Mark status.txt
    status_file = job_dir / "status.txt"
    if status_file.exists():
        status_file.write_text("CANCELLED\n")

    log(f"Job {job_id} cancelled. {len(killed_pids)} processes killed.")
    log(f"See logs at jobs/{job_id}. Run 'jobman clean {job_id}' to clean logs, TPU VM, and Queued Resources.")
    
    