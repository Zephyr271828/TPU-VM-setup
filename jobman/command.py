

class COMMAND:
    
    def __init__(self, cfg):
        self.cmd = cfg.command.cmd
        self.workers = cfg.command.workers
        
    def infer_workers(self):
        pass