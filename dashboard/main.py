from fastapi import FastAPI
from pathlib import Path
from omegaconf import OmegaConf
import json

app = FastAPI()

@app.get("/jobs")
def list_jobs():
    jobs_root = Path("jobs/")
    jobs = [job.name for job in jobs_root.iterdir() if job.is_dir()]
    return {"jobs": jobs}

@app.get("/jobs/{job_id}")
def job_info(job_id: str):
    job_dir = Path(f"jobs/{job_id}")
    config = OmegaConf.load(job_dir / "config.yaml")
    logs = list((job_dir / "logs").glob("*.log"))
    status = (job_dir / "status.txt").read_text() if (job_dir / "status.txt").exists() else "UNKNOWN"
    return {
        "config": OmegaConf.to_container(config),
        "logs": [log.name for log in logs],
        "status": status.strip(),
    }