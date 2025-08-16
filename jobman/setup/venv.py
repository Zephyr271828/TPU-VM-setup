import concurrent.futures
import subprocess
from pathlib import Path
from jobman.utils import log, infer_num_workers

def setup_venv(cfg, logs_dir):
    tpu_name = cfg.tpu.name
    zone = cfg.tpu.zone
    accelerator = cfg.tpu.accelerator
    num_workers = infer_num_workers(accelerator)

    venv_cfg = cfg.venv
    venv_path = str(Path(venv_cfg.path).expanduser())
    python_version = venv_cfg.get("python", None)
    requirements_file = Path(venv_cfg.get("requirements_file", "")).expanduser()

    remote_reqs_file = f"~/{requirements_file.name}"
    if not requirements_file.exists():
        log(f"Requirements file not found: {requirements_file}", "ERROR")
        return

    def setup_worker_venv(i):
        log(f"Setting up venv on worker {i}...", "INFO")
        log_file = logs_dir / f"worker_{i}_venv_setup.log"

        with open(log_file, "w") as f:
            # Step 1: SCP requirements file
            scp_cmd = [
                "gcloud", "alpha", "compute", "tpus", "tpu-vm", "scp",
                str(requirements_file),
                f"{tpu_name}:{remote_reqs_file}",
                "--zone", zone,
                f"--worker={i}",
                "--ssh-key-file", cfg.ssh.tpu_private_key,
                "--quiet",
            ]
            subprocess.run(scp_cmd, stdout=f, stderr=f)

            # Step 2: Run setup command remotely
            install_py = f"sudo apt-get update -y && sudo apt-get install -y python{python_version} python{python_version}-venv" if python_version else ""
            py_bin = f"python{python_version}" if python_version else "python3"

            remote_cmd = f'''
                {install_py} && \
                {py_bin} -m venv {venv_path} && \
                source {venv_path}/bin/activate && \
                pip install --upgrade pip && \
                pip install -r {remote_reqs_file}
            '''

            ssh_cmd = [
                "gcloud", "alpha", "compute", "tpus", "tpu-vm", "ssh", tpu_name,
                "--zone", zone,
                f"--worker={i}",
                "--command", remote_cmd,
                "--ssh-key-file", cfg.ssh.tpu_private_key,
                "--quiet",
            ]
            subprocess.run(ssh_cmd, stdout=f, stderr=f)

    with concurrent.futures.ThreadPoolExecutor(max_workers=num_workers) as executor:
        futures = [executor.submit(setup_worker_venv, i) for i in range(num_workers)]
        for future in concurrent.futures.as_completed(futures):
            if exc := future.exception():
                log(f"Worker thread failed: {exc}", "ERROR")

    log("✅ venv setup complete on all workers.", "INFO")