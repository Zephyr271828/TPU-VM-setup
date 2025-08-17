import argparse
import subprocess
import concurrent.futures
from pathlib import Path
from textwrap import dedent
from omegaconf import OmegaConf
from jobman.utils import setup_logger

class GCSFUSE:
    def __init__(self, cfg):
        self.cfg = cfg
        self.bucket = cfg.gcsfuse.bucket_name
        self.mount_path = cfg.gcsfuse.mount_path

        self.logger = setup_logger(log_file=cfg.job.dir / "logs" / "job.log")
        
    def setup(self):
        self.logger.info(f"Setting up GCSFuse and mounting bucket to TPU workers: bucket={self.bucket}, mount={self.mount_path}")

        if not self.bucket or not self.mount_path:
            self.logger.error("GCSFuse config missing `bucket_name` or `mount_path`.")
            return False
        
        any_failed = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.cfg.tpu.num_workers) as executor:
            futures = [executor.submit(self.setup_worker, i) for i in range(self.cfg.tpu.num_workers)]
            for future in concurrent.futures.as_completed(futures):
                if exc := future.exception():
                    self.logger.error(f"Worker thread failed: {exc}")
                    any_failed = True

        if any_failed:
            self.logger.warning("GCSFuse setup completed with at least one worker failed.")
        else:
            self.logger.info("GCSFuse setup completed successfully on all workers.")
        return not any_failed

    def setup_worker(self, i):
        self.logger.info(f"Worker {i}: Setting up GCSFuse...")
        log_file = self.cfg.job.dir / "logs" / f"gcsfuse_worker_{i}.log"

        gcsfuse_script = dedent(f"""
            set -e
            GCSFUSE_REPO=gcsfuse-$(lsb_release -c -s)
            echo '[INFO] Adding gcsfuse repo...'
            echo "deb [signed-by=/usr/share/keyrings/cloud.google.asc] https://packages.cloud.google.com/apt ${{GCSFUSE_REPO}} main" | sudo tee /etc/apt/sources.list.d/gcsfuse.list

            echo '[INFO] Downloading GPG key...'
            sudo curl -s https://packages.cloud.google.com/apt/doc/apt-key.gpg | sudo tee /usr/share/keyrings/cloud.google.asc >/dev/null

            echo '[INFO] Updating packages and installing gcsfuse...'
            sudo apt-get update -y && sudo apt-get install -y gcsfuse

            if ! command -v gcsfuse &> /dev/null; then
                echo '[ERROR] gcsfuse install failed!'
                exit 1
            fi

            echo '[INFO] Creating mount path...'
            sudo mkdir -p {self.mount_path}

            echo '[INFO] Mounting bucket...'
            mountpoint -q {self.mount_path} || sudo gcsfuse --implicit-dirs --dir-mode=777 --file-mode=777 --o allow_other {self.bucket} {self.mount_path}

            echo '[INFO] Listing contents...'
            ls -la {self.mount_path}
        """)

        ssh_cmd = [
            "gcloud", "compute", "tpus", "tpu-vm", "ssh", self.cfg.tpu.name,
            f"--worker={i}",
            f"--zone={self.cfg.tpu.zone}",
            f"--ssh-key-file={self.cfg.ssh.private_key}",
            "--ssh-flag=-o ConnectTimeout=15",
            "--ssh-flag=-o StrictHostKeyChecking=no",
            "--ssh-flag=-o UserKnownHostsFile=/dev/null",
            "--command", gcsfuse_script,
            "--quiet",
        ]

        with open(log_file, "w") as f:
            try:
                subprocess.run(ssh_cmd, check=True, stdout=f, stderr=f)
                self.logger.info(f"Worker {i}: GCSFuse setup complete.")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"Worker {i}: GCSFuse setup failed: {e}")

    def test(self):
        pass

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    
    cfg = OmegaConf.load(f"jobs/{args.job_id}/config.yaml")
    gcsfuse = GCSFUSE(cfg)
    
    gcsfuse.setup()
