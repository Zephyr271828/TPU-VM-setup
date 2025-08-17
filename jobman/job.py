import os
import json
import time
import logging
import argparse
import subprocess
from omegaconf import OmegaConf

from jobman.tpu import TPU
from jobman.ssh import SSH
from jobman.gcsfuse import GCSFUSE 
from jobman.envs.docker import DOCKER
from jobman.envs.conda import CONDA 
from jobman.envs.venv import VENV

from jobman.utils import setup_logger

class Job:
    
    def __init__(self, cfg):
        
        self.cfg = cfg
       
        self.id = cfg.job.id
        self.name = cfg.job.name
        self.dir = cfg.job.dir
        self.loop = cfg.job.get('loop', False)
       
        self.tpu = TPU(cfg)
        self.ssh = SSH(cfg)
        self.gcsfuse = GCSFUSE(cfg)
        
        self.env_type = cfg.job.env_type
        if self.env_type == 'docker':
            self.env = DOCKER(cfg)
        elif self.env_type == 'conda':
            self.env = CONDA(cfg)
        elif self.env_type == 'venv':
            self.env = VENV(cfg)
        else:
            raise ValueError(f"Invalid env type {env_type}")
        
        self.log_file = self.dir / 'logs' / 'job.log'
        self.logger = setup_logger(log_file=self.log_file)

    def setup(self):
        self.ssh.setup()
        self.gcsfuse.setup()
        self.env.setup()
    
    def run(self):
        try:
            self.logger.info("Requesting TPU...")
            success = self.tpu.request()
            if not success:
                self.logger.error("TPU allocation failed.")
                pass
            
            self.logger.info("Running setup steps (SSH, GCSFuse, ENV)...")
            self.setup()
            
            self.logger.info(f"Job {self.id} finished successfully")

        except KeyboardInterrupt:
            self.logger.warning("Job interrupted by user")
        except Exception as e:
            self.logger.exception(f"Job failed with error: {e}")
            
    def delete(self):
        self.logger = setup_logger(stdout=True)
        self.logger.info(f"Deleting job {self.id}...")

        if self.tpu.log_file.exists():
            try:
                self.tpu.delete()
                self.logger.info(f"Deleted TPU for job {self.id}")
            except Exception as e:
                self.logger.warning(f"Failed to delete TPU for job {self.id}: {e}")
        else:
            self.logger.info(f"TPU log file not found. Skipping TPU deletion.")
            
        if self.log_file.exists():
            try:
                self.log_file.unlink()
                self.logger.info(f"Deleted log file: {self.log_file}")
            except Exception as e:
                self.logger.warning(f"Failed to delete log file: {e}")
    
if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("config_path", type=str, help="Path to job config YAML file")
    args = parser.parse_args()

    cfg = OmegaConf.load(args.config_path)
    job = Job(cfg)
    job.run()
        
        
        
        
        