"""Main entry point for the Text-to-SQL agent application."""

import os
import sys
from pathlib import Path

from loguru import logger

from .utils.config import load_config
from .utils.logger import setup_logging
from .agent.agent import TextToSQLAgent
from .api.api import start_api


def main():
    """Main entry point."""
    # Load configuration
    config = load_config()
    
    # Setup logging
    setup_logging(
        log_level=config.app.log_level,
        log_file="logs/app.log" if not config.app.debug else None,
        debug=config.app.debug
    )
    
    logger.info(f"Starting {config.app.name} v{config.app.version}")
    
    # Start API server
    start_api()


if __name__ == "__main__":
    main()
