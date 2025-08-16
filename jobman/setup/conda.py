import argparse
import subprocess
import concurrent.futures
from pathlib import Path
from omegaconf import OmegaConf
from jobman.utils import log, infer_num_workers

def setup_conda(cfg, logs_dir):
    tpu_name = cfg.tpu.name
    zone = cfg.tpu.zone
    accelerator = cfg.tpu.accelerator
    num_workers = infer_num_workers(accelerator)
    
    conda_cfg = cfg.get("conda", {})
    if not conda_cfg.get("enabled", False):
        return

    env_name = conda_cfg.get("env_name", "jobman_env")
    env_file = Path(conda_cfg.get("yaml_file", "")).expanduser()
    remote_env_file = f"~/{env_file.name}"

    if not env_file.exists():
        log(f"Conda env file not found: {env_file}", "ERROR")
        return
    
    def setup_worker_conda(i):
        log(f"Setting up Conda on worker {i}...", "INFO")

        py_ver_cmd = f"python={python_version}" if python_version else ""
        
        scp_cmd = [
            "gcloud", "alpha", "compute", "tpus", "tpu-vm", "scp",
            str(env_file),  # local path
            f"{tpu_name}:{remote_env_file}",  # remote path
            "--zone", zone,
            f"--worker={i}",
            "--ssh-key-file", cfg.ssh.tpu_private_key,
            "--quiet",
        ]
        
        remote_cmd = f'''
            wget -q https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh -O miniconda.sh && \
            bash miniconda.sh -b -p $HOME/miniconda && \
            source "$HOME/miniconda/etc/profile.d/conda.sh" && \
            conda env create -n {env_name} -f {remote_env_file} --yes
        '''

        ssh_cmd = [
            "gcloud", "alpha", "compute", "tpus", "tpu-vm", "ssh", tpu_name,
            "--zone", zone,
            f"--worker={i}",
            "--command", remote_cmd,
            "--ssh-key-file", cfg.ssh.tpu_private_key,
            "--quiet",
        ]

        log_file = logs_dir / f"worker_{i}_conda_setup.log"
        with open(log_file, "w") as f:
            subprocess.run(scp_cmd, stdout=f, stderr=f)
            subprocess.run(ssh_cmd, stdout=f, stderr=f)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = []
        for i in range(num_workers):
            futures.append(executor.submit(setup_worker_conda, i))

        # Optionally wait and raise if any thread fails
        for future in concurrent.futures.as_completed(futures):
            if exc := future.exception():
                log(f"Worker thread failed: {exc}", "ERROR")

    log("✅ Conda setup complete on all workers.", "INFO")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--job-id", required=True)
    args = parser.parse_args()

    job_dir = Path(f"jobs/{args.job_id}")
    cfg = OmegaConf.load(job_dir / "config.yaml")
    logs_dir = job_dir / "logs"

    setup_conda(cfg, logs_dir)
   