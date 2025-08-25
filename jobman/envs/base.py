
class ENV:
    
    def __init__(self, cfg):
        pass
    
    def setup(self):
        pass
    
    def _setup_worker(self, i):
        return False
    
    def check(self):
        pass
    
    def _check_worker(self, i):
        return False
    
    def patch_command(self, cmd):
        return cmd

    