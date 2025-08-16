import os
import argparse
import subprocess
import concurrent.futures
from pathlib import Path
from textwrap import dedent
from omegaconf import OmegaConf
from jobman.utils import log, infer_num_workers
    
def setup(cfg, logs_dir):
    tpu_name = cfg.tpu.name
    zone = cfg.tpu.zone
    accelerator = cfg.tpu.accelerator
    num_workers = infer_num_workers(accelerator)
    
    private_key = Path(cfg.ssh.tpu_private_key).expanduser()
    public_key = Path(cfg.ssh.tpu_public_key).expanduser()
    key_filename = private_key.name

    if not private_key.exists() or not public_key.exists():
        log(f"SSH key files not found: {private_key} or {public_key}", "ERROR")
        return
    
    ssh_config_entry = dedent(f"""\
        Host 10.*
            IdentityFile ~/.ssh/{key_filename}
            IdentitiesOnly yes
    """)
    
    escaped_ssh_config_entry = ssh_config_entry.replace('\n', '\\n').replace('"', '\\"')

    log("Copying existing SSH keys to TPU workers...", "INFO")

    def setup_worker_ssh(i):
        log(f"Worker {i}: Copying SSH key and setting permissions", "INFO")

        log_file = logs_dir / f"ssh_worker_{i}.log"
        with open(log_file, "w") as f:
            # SCP private key to remote host
            scp_cmd_priv = [
                "gcloud", "compute", "tpus", "tpu-vm", "scp",
                str(private_key), f"{tpu_name}:~/.ssh/{key_filename}",
                "--worker", str(i),
                "--zone", zone,
                "--ssh-key-file", str(private_key),
                "--scp-flag=-o ConnectTimeout=15",
                "--scp-flag=-o StrictHostKeyChecking=no",
                "--scp-flag=-o UserKnownHostsFile=/dev/null",
                "--quiet",
            ]
            subprocess.run(scp_cmd_priv, check=True, stdout=f, stderr=f)

            # SCP public key to remote host
            scp_cmd_pub = [
                "gcloud", "compute", "tpus", "tpu-vm", "scp",
                str(public_key), f"{tpu_name}:~/.ssh/{key_filename}.pub",
                "--worker", str(i),
                "--zone", zone,
                "--ssh-key-file", str(private_key),
                "--scp-flag=-o ConnectTimeout=15",
                "--scp-flag=-o StrictHostKeyChecking=no",
                "--scp-flag=-o UserKnownHostsFile=/dev/null",
                "--quiet",
            ]
            subprocess.run(scp_cmd_pub, check=True, stdout=f, stderr=f)

            # Then on the remote host, add the pub key to authorized_keys, and set permissions
            remote_cmd = f"""
                mkdir -p ~/.ssh;
                chmod 700 ~/.ssh;
                cat ~/.ssh/{key_filename}.pub >> ~/.ssh/authorized_keys;
                printf "{escaped_ssh_config_entry}\\n" >> ~/.ssh/config;
                chmod 600 ~/.ssh/authorized_keys;
                chmod 600 ~/.ssh/{key_filename};
                chmod 644 ~/.ssh/{key_filename}.pub;
            """

            subprocess.run([
                "gcloud", "alpha", "compute", "tpus", "tpu-vm", "ssh", tpu_name,
                "--worker", str(i),
                "--zone", zone,
                "--command", remote_cmd,
                "--ssh-key-file", str(private_key),
                "--ssh-flag=-o ConnectTimeout=15",
                "--ssh-flag=-o StrictHostKeyChecking=no",
                "--ssh-flag=-o UserKnownHostsFile=/dev/null",
                "--quiet",
            ], check=True, stdout=f, stderr=f)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for i in range(num_workers):
            futures.append(executor.submit(setup_worker_ssh, i))

        # Optionally wait and raise if any thread fails
        for future in concurrent.futures.as_completed(futures):
            if exc := future.exception():
                log(f"Worker thread failed: {exc}", "ERROR")
        
    log("SSH setup complete for all workers.", "INFO")
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()
    
    job_dir = Path(f"jobs/{args.job_id}")
    cfg = OmegaConf.load(job_dir / "config.yaml")
    logs_dir = job_dir / "logs"
    
    setup(cfg, logs_dir)