import argparse
import subprocess
import concurrent.futures
from pathlib import Path
from textwrap import dedent
from omegaconf import OmegaConf
from jobman.utils import setup_logger

class SSH:
    
    def __init__(self, cfg):
        
        self.cfg = cfg
        self.private_key = Path(self.cfg.ssh.private_key).expanduser()
        self.public_key = Path(self.cfg.ssh.public_key).expanduser()
        
        self.logger = setup_logger(log_file=cfg.job.dir / 'logs' / 'job.log')
        
    def setup(self):
        self.logger.info(f"Copying SSH keys to TPU workers: private={str(self.private_key)}, public={str(self.public_key)}")

        any_failed = False
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.cfg.tpu.num_workers) as executor:
            futures = [executor.submit(self.setup_worker, i) for i in range(self.cfg.tpu.num_workers)]
            for future in concurrent.futures.as_completed(futures):
                if exc := future.exception():
                    self.logger.error(f"Worker SSH thread failed: {exc}")
                    any_failed = True

        if any_failed:
            self.logger.warning("SSH setup completed with at least one worker failed.")
        else:
            self.logger.info("SSH setup completed successfully on all workers.")
        return not any_failed
        
    def setup_worker(self, i):
        self.logger.info(f"Worker {i}: Setting up SSH")
        key_filename = self.private_key.name
        log_file = self.cfg.job.dir / "logs" / f"ssh_worker_{i}.log"

        if not self.private_key.exists() or not self.public_key.exists():
            self.logger.error(f"SSH key files not found: {self.private_key} or {self.public_key}")
            return
        
        with open(log_file, "w") as f:
            for key_file in (self.private_key, self.public_key):
                self._copy_key_to_worker(i, key_file, f)

            self._configure_remote_ssh(i, key_filename, f)
        
    def _copy_key_to_worker(self, i, key_file, f):
        target_path = f"{self.cfg.tpu.name}:~/.ssh/{key_file.name}"
        scp_cmd = [
            "gcloud", "compute", "tpus", "tpu-vm", "scp", str(key_file), target_path,
            "--worker", str(i), "--zone", self.cfg.tpu.zone,
            "--ssh-key-file", str(self.private_key),
            "--scp-flag=-o ConnectTimeout=15",
            "--scp-flag=-o StrictHostKeyChecking=no",
            "--scp-flag=-o UserKnownHostsFile=/dev/null",
            "--quiet",
        ]
        self.logger.debug("Using scp command:")
        self.logger.debug(" ".join(scp_cmd))
        try:
            subprocess.run(scp_cmd, check=True, stdout=f, stderr=f)
            self.logger.debug(f"Worker {i}: Copied {key_file.name}")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Worker {i}: Failed to copy {key_file.name}: {e}")
            
    def _configure_remote_ssh(self, i, key_filename, f):
        ssh_config_entry = dedent(f"""\
            Host 10.*
                IdentityFile ~/.ssh/{key_filename}
                IdentitiesOnly yes
        """)
        escaped_entry = ssh_config_entry.replace('\n', '\\n').replace('"', '\\"')
        cmd = f"""
            mkdir -p ~/.ssh;
            chmod 700 ~/.ssh;
            cat ~/.ssh/{key_filename}.pub >> ~/.ssh/authorized_keys;
            printf \"{escaped_entry}\\n\" >> ~/.ssh/config;
            chmod 600 ~/.ssh/authorized_keys;
            chmod 600 ~/.ssh/{key_filename};
            chmod 644 ~/.ssh/{key_filename}.pub;
        """
        ssh_cmd = [
            "gcloud", "alpha", "compute", "tpus", "tpu-vm", "ssh", self.cfg.tpu.name,
            "--worker", str(i), "--zone", self.cfg.tpu.zone,
            "--command", cmd,
            "--ssh-key-file", str(self.private_key),
            "--ssh-flag=-o ConnectTimeout=15",
            "--ssh-flag=-o StrictHostKeyChecking=no",
            "--ssh-flag=-o UserKnownHostsFile=/dev/null",
            "--quiet",
        ]
        try:
            subprocess.run(ssh_cmd, check=True, stdout=f, stderr=f)
            self.logger.debug(f"Worker {i}: Remote SSH configured")
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Worker {i}: Remote SSH config failed: {e}")
            
    def test(self):
        pass
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    
    cfg = OmegaConf.load(f"jobs/{args.job_id}/config.yaml")
    ssh = SSH(cfg)
    
    ssh.setup()
