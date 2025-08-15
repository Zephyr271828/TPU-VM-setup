# jobman/cli.py
import click
from jobman import create, cancel, status

@click.group()
def main():
    """TPU Job Manager CLI"""
    pass

@main.command(name="create")
@click.option("--name", help="Custom job name prefix (default: test_v5e)")
@click.option("--accelerator", default="v5e", show_default=True, help="Accelerator type (e.g., v5e, v4)")
@click.option("--zone", default="us-east1-c", show_default=True, help="TPU zone")
@click.option("--tpu-name", help="TPU name (default: auto-generated)")
def create_(name, accelerator, zone, tpu_name):
    """Create a new job"""
    create.create(
        name=name,
        accelerator=accelerator,
        zone=zone,
        tpu_name=tpu_name,
    )

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