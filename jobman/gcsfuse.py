

class GCSFUSE:
    
    def __init__(self, cfg):
        
        self.bucket_name = cfg.gcsfuse.bucket_name
        self.mount_path = cfg.gcsfuse.mount_path
        
    def setup(self, cfg):
        pass
    
    def test(self, cfg):
        pass