from jobman.envs.base import ENV

class CONDA(ENV):
    
    def __init__(self, cfg):
        self.name = cfg.conda.name
        self.config_file = cfg.conda.config_file
        
    def setup(self):
        pass
    
    def run(self):
        pass