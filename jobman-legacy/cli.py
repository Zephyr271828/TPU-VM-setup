# jobman/cli.py
import click
from jobman import create, cancel, status, clean

@click.group()
def main():
    """TPU Job Manager CLI"""
    pass

@main.command(name="create")
@click.option("--config", type=click.Path(exists=True), required=True)
def create_(config):
    """Create a new job"""
    create.create(config_path=config)

@main.command(name="status")
@click.argument("job_id", required=False)
def status_(job_id):
    """Check status of jobs (or one specific job)"""
    if job_id:
        status.status_single(job_id)
    else:
        status.status_all()

@main.command(name="cancel")
@click.argument("job_id")
def cancel_(job_id):
    """Cancel a job"""
    cancel.cancel(job_id)
    
@main.command("clean")
@click.argument("job_id", required=False)
@click.option("--all", is_flag=True, help="Delete only logs but keep job folder")
def clean_cmd(job_id=None, all=False):
    assert (job_id is None) ^ (all == False)
    if job_id:
        clean.clean_single(job_id)
    elif all:
        clean.clean_all()