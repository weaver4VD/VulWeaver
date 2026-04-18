
import logging
import logging.config
from typing import Dict, Any


def setup_logging(config: Dict[str, Any], verbose: bool = False):
    if verbose:
        config = config.copy()
        config['handlers']['console']['level'] = 'DEBUG'
    
    logging.config.dictConfig(config)


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)