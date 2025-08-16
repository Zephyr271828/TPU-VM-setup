import streamlit as st
from pathlib import Path
from omegaconf import OmegaConf

st.title("Jobman Dashboard")

jobs_root = Path("jobs/")
jobs = [p.name for p in jobs_root.iterdir() if p.is_dir()]
job_id = st.selectbox("Select a job", jobs)

if job_id:
    job_dir = jobs_root / job_id
    config = OmegaConf.load(job_dir / "config.yaml")
    st.json(OmegaConf.to_container(config))

    status_file = job_dir / "status.txt"
    if status_file.exists():
        st.write("Status:", status_file.read_text().strip())

    log_files = list((job_dir / "logs").glob("*.log"))
    for log in log_files:
        st.subheader(log.name)
        st.code(log.read_text()[-1000:], language="bash")