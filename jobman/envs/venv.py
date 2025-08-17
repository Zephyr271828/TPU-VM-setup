import argparse
import subprocess
import concurrent.futures
from pathlib import Path
from omegaconf import OmegaConf

from jobman.envs.base import ENV
from jobman.utils import setup_logger

class VENV(ENV):
    
    def __init__(self, cfg):
        self.cfg = cfg
        self.env_name = cfg.venv.name
        self.requirements_file = cfg.venv.requirements_file
        self.python = cfg.venv.get('python', 'python3.10')
        
        self.logger = setup_logger(log_file=cfg.job.dir / "logs" / "job.log")
        
    def setup(self):
        self.logger.info(f"Setting up Venv environment on TPU workers: venv_name={self.env_name}, requirements_file={self.requirements_file}, python={self.python}")

        any_failed = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.cfg.tpu.num_workers) as executor:
            futures = [executor.submit(self.setup_worker, i) for i in range(self.cfg.tpu.num_workers)]
            for future in concurrent.futures.as_completed(futures):
                if exc := future.exception():
                    self.logger.error(f"Worker thread failed: {exc}")
                    any_failed = True

        if any_failed:
            self.logger.warning("Venv setup completed with at least one worker failed.")
        else:
            self.logger.info("Venv setup completed successfully on all workers.")
        return not any_failed
    
    def setup_worker(self, i):
        self.logger.info(f"Worker {i}: Setting up VENV...")
        log_file = self.cfg.job.dir / "logs" / f"venv_worker_{i}.log"
        remote_venv_dir = f"~/venv/{self.env_name}"
        remote_req_file = f"~/requirements_{self.env_name}.txt"
        local_req_file = self.requirements_file

        with open(log_file, "w") as f:
            try:
                # Step 1: Copy requirements.txt to remote
                scp_cmd = [
                    "gcloud", "alpha", "compute", "tpus", "tpu-vm", "scp",
                    str(local_req_file),
                    f"{self.cfg.tpu.name}:{remote_req_file}",
                    "--zone", self.cfg.tpu.zone,
                    f"--worker={i}",
                    "--ssh-key-file", str(self.cfg.ssh.private_key),
                    "--quiet",
                ]
                subprocess.run(scp_cmd, check=True, stdout=f, stderr=f)

                # Step 2: Create virtualenv and install requirements
                remote_cmd = f"""
                    sudo apt install {self.python}-venv -y
                    {self.python} -m venv {remote_venv_dir} || true && \
                    source {remote_venv_dir}/bin/activate && \
                    pip install --upgrade pip && \
                    pip install -r {remote_req_file}
                """
                ssh_cmd = [
                    "gcloud", "alpha", "compute", "tpus", "tpu-vm", "ssh", self.cfg.tpu.name,
                    "--zone", self.cfg.tpu.zone,
                    f"--worker={i}",
                    "--command", remote_cmd,
                    "--ssh-key-file", str(self.cfg.ssh.private_key),
                    "--quiet",
                ]
                subprocess.run(ssh_cmd, check=True, stdout=f, stderr=f)

            except Exception as e:
                self.logger.error(f"Worker {i} venv setup failed: {e}")
                raise
    
    def patch_command(self, cmd):
        return f'bash -c "source {self.path}/bin/activate && {cmd}"'
        
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()

    cfg = OmegaConf.load(f"jobs/{args.job_id}/config.yaml")
    venv = VENV(cfg)

    venv.setup()