"""
Configuration loader.

This module provides functionality to load configuration from YAML files.
"""
import logging
import yaml
import os

logger = logging.getLogger(__name__)


def load_config(config_path):
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the YAML configuration file
        
    Returns:
        Dict: The configuration as a dictionary
        
    Raises:
        FileNotFoundError: If the config file does not exist
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)
    
    logger.info(f"Configuration loaded from {config_path}")
    return config 