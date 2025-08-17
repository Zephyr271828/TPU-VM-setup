import sys
import logging
from pathlib import Path

def setup_logger(log_file: Path = None, level=logging.INFO, stdout=False):
    """Configure global logging to stdout and/or a log file."""
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(level)

    # Prevent duplicate handlers if setup_logger is called more than once
    logger.handlers.clear()

    formatter = logging.Formatter(
        fmt="(%(asctime)s) [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Optional terminal output
    if stdout:
        stream_handler = logging.StreamHandler(sys.stdout)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    # Optional file output
    if log_file is not None:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
    return logger