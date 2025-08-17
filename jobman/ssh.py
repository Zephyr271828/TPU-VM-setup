


class SSH:
    
    def __init__(self, cfg):
        self.private_key = cfg.ssh.private_key
        self.public_key = cfg.ssh.public_key
        
    def setup(self, cfg):
        pass
    
    def test(self, cfg):
        pass