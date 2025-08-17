from jobman.envs.base import ENV

class VENV(ENV):
    
    def __init__(self, cfg):
        self.path = cfg.venv.path
        self.requirements_file = cfg.venv.requirements_file
        self.python = cfg.venv.get('python', None)
        
    def setup(self):
        pass
    
    def run(self):
        pass