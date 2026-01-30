"""
Application configuration module.

Provides a centralized entry point for loading and accessing
application configuration from JSON files.
"""

from src.config.loader import load_config, merge_configs, get_config_path
