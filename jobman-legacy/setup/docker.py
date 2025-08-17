import os
import argparse
import subprocess
import concurrent.futures
from pathlib import Path
from omegaconf import OmegaConf
from jobman.utils import log, infer_num_workers

def setup(cfg, logs_dir):
    tpu_name = cfg.tpu.name
    zone = cfg.tpu.zone
    accelerator = cfg.tpu.accelerator
    num_workers = infer_num_workers(accelerator)

    image = cfg.docker.get("image", None)

    if not image:
        log("Docker image not specified in config.", "ERROR")
        return

    log(f"Setting up Docker with image: {image}", "INFO")
    
    def setup_worker_docker(i):
        log(f"Configuring Docker on worker {i}...", "INFO")

        log_file = logs_dir / f"docker_worker_{i}.log"
        with open(log_file, "w") as f:
            # Step 1: Add user to docker group
            subprocess.run([
                "gcloud", "alpha", "compute", "tpus", "tpu-vm", "ssh", tpu_name,
                "--zone", zone,
                f"--worker={i}",
                "--command", "sudo usermod -aG docker $USER && sudo systemctl restart docker",
                "--quiet",
            ], stdout=f, stderr=f)

            # Step 2: Pull docker image
            subprocess.run([
                "gcloud", "alpha", "compute", "tpus", "tpu-vm", "ssh", tpu_name,
                "--zone", zone,
                f"--worker={i}",
                "--command", f"sudo docker pull {image}",
                "--quiet",
            ], stdout=f, stderr=f)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for i in range(num_workers):
            futures.append(executor.submit(setup_worker_docker, i))

        # Optionally wait and raise if any thread fails
        for future in concurrent.futures.as_completed(futures):
            if exc := future.exception():
                log(f"Worker thread failed: {exc}", "ERROR")

    log("Docker setup complete on all workers.", "INFO")
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    
    job_dir = Path(f"jobs/{args.job_id}")
    cfg = OmegaConf.load(job_dir / "config.yaml")
    logs_dir = job_dir / "logs"
    
    setup(cfg, logs_dir)
