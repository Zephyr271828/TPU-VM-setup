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
    
    bucket = cfg.gcsfuse.bucket_name
    mount_path = cfg.gcsfuse.mount_path

    if not bucket or not mount_path:
        log("gcsfuse config missing bucket_name or mount_path. Skipping.", "ERROR")
        return

    log(f"Setting up gcsfuse on {num_workers} workers: bucket={bucket}, mount_path={mount_path}", "INFO")

    def get_worker_cmd():
        return f"""
            GCSFUSE_REPO=gcsfuse-$(lsb_release -c -s)
            echo '[INFO] Adding gcsfuse repo...'
            echo "deb [signed-by=/usr/share/keyrings/cloud.google.asc] https://packages.cloud.google.com/apt ${{GCSFUSE_REPO}} main" | sudo tee /etc/apt/sources.list.d/gcsfuse.list

            echo '[INFO] Downloading GPG key...'
            sudo curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo tee /usr/share/keyrings/cloud.google.asc >/dev/null

            if sudo fuser /var/lib/dpkg/lock-frontend >/dev/null 2>&1; then
                LOCK_PID=$(sudo lsof -t /var/lib/dpkg/lock-frontend || true)
                if [ -n "$LOCK_PID" ]; then
                    echo "[WARN] Killing process $LOCK_PID holding dpkg lock"
                    sudo kill -9 $LOCK_PID
                    sleep 2
                fi
            fi
            # This is needed because sometimes the lock is occupied and installation fails
            
            echo '[INFO] Installing gcsfuse...'
            sudo apt-get update -y && sudo apt-get install -y gcsfuse && break
            echo '[WARN] gcsfuse install failed, retrying in 10 seconds...'
            sleep 10
            
            if ! command -v gcsfuse &> /dev/null; then
                echo '[ERROR] gcsfuse still not found after install attempts. Exiting.'
                exit 1
            fi

            sudo mkdir -p {mount_path}
            echo '[INFO] Mounting bucket...'
            mountpoint -q {mount_path} || timeout 30 sudo gcsfuse --implicit-dirs --dir-mode=777 --file-mode=777 --o allow_other {bucket} {mount_path}

            sudo ls -la {mount_path}
        """
        
    def setup_worker_gcsfuse(i):
        log(f"Launching gcsfuse setup on worker {i}")
        log_file = logs_dir / f"gcsfuse_worker_{i}.log"
        with open(log_file, "w") as f:
            subprocess.run([
                "gcloud", "compute", "tpus", "tpu-vm", "ssh", tpu_name,
                f"--worker={i}",
                f"--zone={zone}",
                f"--ssh-key-file={cfg.ssh.tpu_private_key}",
                "--ssh-flag=-o ConnectTimeout=15",
                "--ssh-flag=-o StrictHostKeyChecking=no",
                "--ssh-flag=-o UserKnownHostsFile=/dev/null",
                "--command", get_worker_cmd()
            ],  check=True, stdout=f, stderr=f)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for i in range(num_workers):
            futures.append(executor.submit(setup_worker_gcsfuse, i))

        # Optionally wait and raise if any thread fails
        for future in concurrent.futures.as_completed(futures):
            if exc := future.exception():
                log(f"Worker thread failed: {exc}", "ERROR")
        
    log("gcsfuse setup complete on all workers.", "INFO")
            
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    
    job_dir = Path(f"jobs/{args.job_id}")
    cfg = OmegaConf.load(job_dir / "config.yaml")
    logs_dir = job_dir / "logs"
    
    setup(cfg, logs_dir)
