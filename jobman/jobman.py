import json
import fcntl
import shutil
import logging
import subprocess
from pathlib import Path
from datetime import datetime 
from tabulate import tabulate
from omegaconf import OmegaConf

from jobman.job import Job
from jobman.utils import setup_logger

jobs_dir = Path("jobs") 
jobman_dir = jobs_dir / ".jobman"

class JobMan:

    def __init__(self):
        jobman_dir.mkdir(parents=True, exist_ok=True)
        self.meta_file = jobman_dir / "meta.json"
        self.lock_file = jobman_dir / "lock"
        self.cntr_file = jobman_dir / "next_job_id.txt"
        self.meta = self._load()
        self.logger = setup_logger(stdout=True)

    def _load(self):
        if self.meta_file.exists():
            return json.loads(self.meta_file.read_text())
        return {}

    def save(self):
        self.meta_file.write_text(json.dumps(self.meta, indent=2))

    def get_job_meta(self, job_id):
        return self.meta.get(f"job_{job_id}", None)
    
    def get_next_job_id(self):
        if not self.cntr_file.exists():
            self.cntr_file.write_text("0")

        with open(self.lock_file, "w") as lock_fp:
            fcntl.flock(lock_fp, fcntl.LOCK_EX)
            current = int(self.cntr_file.read_text())
            next_id = current + 1
            self.cntr_file.write_text(str(next_id))
            fcntl.flock(lock_fp, fcntl.LOCK_UN)
            return f"{next_id:06d}"    
        
    def create_job(self, config_path):
        job_id = self.get_next_job_id()
        job_dir = Path(f"jobs/{job_id}")
        job_dir.mkdir(parents=True, exist_ok=True)
        
        self.meta[f"job_{job_id}"] = {
            "job_id": job_id,
            "created_at": datetime.now().isoformat(),
            "status": "INIT"
        }
        self.save()
        
        cfg = OmegaConf.load(config_path)
        cfg.job.id = job_id
        cfg.job.dir = job_dir
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        cfg.job.name = f"{cfg.job.name}_{ts}"
        cfg.tpu.name = f"{cfg.tpu.name}_{ts}"
        OmegaConf.save(cfg, job_dir / "config.yaml")
        
        self.logger.info(f"Created job {job_id}. See info at {job_dir}")
        
        return job_id
    
    def start_job(self, job_id):
        job_dir = jobs_dir / job_id
        session_name = f"job_{job_id}"
        
        logs_dir = job_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        log_file = logs_dir / "job.log"
        
        config_path = job_dir / "config.yaml"
        run_cmd = f"python -m jobman.job {config_path}"

        tmux_cmd = f'tmux new-session -d -s {session_name} "{run_cmd} | tee {log_file}"'
        subprocess.run(tmux_cmd, shell=True, check=True)

        self.update_job_meta(
            job_id,
            status="RUNNING",
            backend="tmux",
            session_name=session_name,
            started_at=datetime.now().isoformat(),
            log_file=str(log_file)
        )

        self.logger.info(f"Job {job_id} started. See logs at {logs_dir}/job.log.")
    
    
    def check_tmux_session(self, session_name: str) -> bool:
        return subprocess.run(
            ["tmux", "has-session", "-t", session_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        ).returncode == 0
    
    def cancel_job(self, job_id):
        key = f"job_{job_id}"
        meta = self.meta.get(key)

        if not meta:
            self.logger.warning(f"No metadata found for job {job_id}")
            return False

        session_name = meta.get("session_name")
        if not session_name:
            self.logger.error(f"No tmux session_name found for job {job_id}")
            return False
        
        # First check if session exists
        session_exists = self.check_tmux_session(session_name)

        if not session_exists:
            self.logger.warning(f"Session '{session_name}' does not exist. Nothing to cancel.")
            return False

        # Try to kill the tmux session
        try:
            subprocess.run(["tmux", "kill-session", "-t", session_name], check=True)
            self.update_job_meta(
                job_id,
                status="FAILED",
                ended_at=datetime.now().isoformat()
            )
            self.logger.info(f"Cancelled job {job_id} by killing tmux session {session_name}")
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to kill tmux session {session_name}: {e}")
            return False
            
    def delete_job(self, job_id):
        self.logger.info(f"Deleting job {job_id}...")
    
        try:
            cancelled = self.cancel_job(job_id)
            self.logger.debug(f"cancel_job returned {cancelled}")
        except Exception as e:
            self.logger.warning(f"Failed to cancel job {job_id} before deletion: {e}")

        job_dir = jobs_dir / job_id
        config_path = job_dir/ "config.yaml"
        if config_path.exists():
            try:
                cfg = OmegaConf.load(config_path)
                job = Job(cfg)
                job.delete()
            except Exception as e:
                self.logger.exception(f"Failed to delete job {job_id}: {e}")
        else:
            self.logger.error(f"Job {job_id} config not found at {config_path}")
        
        try:
            shutil.rmtree(job_dir)
            self.logger.info(f"Deleted job directory {job_dir}")
        except Exception as e:
            self.logger.error(f"Failed to delete job directory {job_dir}: {e}")

        # 清除元信息
        self.remove_job_meta(job_id)
        self.logger.info(f"Deleted job {job_id} successfully")
        return True

    def update_job_meta(self, job_id, **kwargs):
        key = f"job_{job_id}"
        if key not in self.meta:
            self.meta[key] = {"job_id": job_id}
        self.meta[key].update(kwargs)
        self.meta[key]["last_seen"] = datetime.now().isoformat()
        self.save()

    def remove_job_meta(self, job_id):
        key = f"job_{job_id}"
        if key in self.meta:
            del self.meta[key]
            self.save()
    
    def print_job_table(self):
        rows = []
        updated = False
        
        for job_key, meta in self.meta.items():
            job_id = meta.get("job_id")
            status = meta.get("status", "UNKNOWN")        
            started = meta.get("started_at", meta.get("created_at", "N/A"))
            session_name = meta.get("session_name", f"job_{job_id}")

            config_path = Path(f"jobs/{job_id}/config.yaml")
            if config_path.exists():
                cfg = OmegaConf.load(config_path)
                job_name = cfg.job.name
                accelerator = cfg.tpu.accelerator
                zone = cfg.tpu.zone
            else:
                job_name = "N/A"
                accelerator = "N/A"
                zone = "N/A"
                
            if status == "RUNNING" and not self.check_tmux_session(session_name):
                status = "DEAD"
                meta["status"] = "DEAD"
                meta["ended_at"] = datetime.now().isoformat()
                updated = True

            rows.append([job_id, job_name, started, accelerator, zone, status])

        if updated:
            self.save()
        
        rows.sort(key=lambda x: x[0])
        headers = ["Job ID", "Name", "Start Time", "Accelerator", "Zone", "Status"]
        print(tabulate(rows, headers=headers, tablefmt="fancy_grid"))