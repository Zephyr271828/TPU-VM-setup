from jobman.envs.base import ENV

class DOCKER(ENV):
    
    def __init__(self, cfg):
        self.image = cfg.docker.image
        self.mount_dirs = cfg.docker.get('mount_dirs', None)
        self.workdir = cfg.docker.get('work_dir', None)
        self.flags = cfg.docker.get('flags', None)
        
    def setup(self):
        pass
    
    def run(self, command):
        pass
        