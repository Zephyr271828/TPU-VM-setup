from datetime import datetime
def log(msg, level="INFO"):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"({ts}) [{level}] {msg}")
    
import re
import math
def infer_num_workers(accelerator: str) -> int:
    """
    Infer number of workers based on accelerator type.
    Examples:
        v4-256 -> 32 workers (256 // 8)
        v5e-32 -> 8 workers (32 // 4)
    """
    match = re.search(r"v(\d+)[a-z]*-(\d+)", accelerator.lower())
    if not match:
        raise ValueError(f"Invalid accelerator format: {accelerator}")
    
    version, chips = int(match.group(1)), int(match.group(2))
    if version in [2, 3, 4]:
        return math.ceil(chips / 8)
    elif version in [5, 6]:
        return math.ceil(chips / 4)
    else:
        raise ValueError(f"Unknown TPU version in accelerator: {accelerator}")
    
if __name__ == '__main__':
    print(infer_num_workers('v3-32'))
    print(infer_num_workers('v4-256'))
    print(infer_num_workers('v5litepod-64'))
    print(infer_num_workers('v6e-64'))