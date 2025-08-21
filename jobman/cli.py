# jobman/cli.py
import click

from jobman.jobman import JobMan

from jobman.profilers.billing_report import main as run_billing_report
from jobman.profilers.quota_report import main as run_quota_report
from jobman.profilers.storage_report import main as run_storage_report


@click.group()
def cli():
    """JobMan CLI: manage TPU jobs."""
    pass

@cli.command()
@click.argument('config_path', type=click.Path(exists=True))
def create(config_path):
    jm = JobMan()  
    job_id = jm.create_job(config_path)
    jm.start_job(job_id)
    
@cli.command(name="resume")
@click.argument("job_id", type=str)
def resume(job_id):
    """Cancel a running job."""
    jm = JobMan()
    jm.start_job(job_id)
    
@cli.command(name="cancel")
@click.argument("job_id", type=str)
def cancel(job_id):
    """Cancel a running job."""
    jm = JobMan()
    jm.cancel_job(job_id)
    
@cli.command(name="delete")
@click.argument("job_id", type=str)
def delete(job_id):
    """Cancel a running job."""
    jm = JobMan()
    jm.delete_job(job_id)

@cli.command(name="list")
def list_jobs():
    """List all jobs and their status."""
    jm = JobMan()
    jm.list_jobs()
    
@cli.command()
def billing():
    """Run billing report profiler."""
    run_billing_report()

@cli.command()
def quota():
    """Run quota usage profiler."""
    run_quota_report()

@cli.command()
def storage():
    """Run storage usage profiler."""
    run_storage_report()