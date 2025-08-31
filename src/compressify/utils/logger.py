"""
Logging configuration and utilities.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler


def setup_logger(
    name: str = "compressify",
    level: str = "INFO",
    log_file: Optional[Path] = None,
    console: Optional[Console] = None
) -> logging.Logger:
    """
    Set up logger with Rich formatting.
    
    Args:
        name: Logger name
        level: Logging level
        log_file: Optional log file path
        console: Optional Rich console instance
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Rich console handler
    if console is None:
        console = Console()
    
    rich_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        rich_tracebacks=True,
        markup=True
    )
    rich_handler.setFormatter(
        logging.Formatter(
            "%(message)s",
            datefmt="[%X]"
        )
    )
    logger.addHandler(rich_handler)
    
    # File handler (optional)
    if log_file:
        try:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(
                logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                    datefmt="%Y-%m-%d %H:%M:%S"
                )
            )
            logger.addHandler(file_handler)
        except (OSError, PermissionError) as e:
            logger.warning(f"Could not create log file {log_file}: {e}")
    
    return logger


class ProgressLogger:
    """Logger for tracking compression progress."""
    
    def __init__(self, logger: logging.Logger, console: Console):
        self.logger = logger
        self.console = console
        self.processed_files = 0
        self.total_files = 0
        self.failed_files = []
        self.skipped_files = []
    
    def set_total_files(self, total: int):
        """Set total number of files to process."""
        self.total_files = total
        self.processed_files = 0
        self.failed_files.clear()
        self.skipped_files.clear()
    
    def log_file_start(self, file_path: Path):
        """Log start of file processing."""
        self.logger.info(f"Processing: {file_path.name}")
    
    def log_file_success(self, file_path: Path, savings: dict):
        """Log successful file processing."""
        self.processed_files += 1
        self.logger.info(
            f"✅ {file_path.name} - Saved {savings.get('percentage', 'N/A')} "
            f"({savings.get('mb', 'N/A')})"
        )
    
    def log_file_skip(self, file_path: Path, reason: str):
        """Log skipped file."""
        self.skipped_files.append((file_path, reason))
        self.logger.warning(f"⏭️  Skipped {file_path.name}: {reason}")
    
    def log_file_error(self, file_path: Path, error: str):
        """Log file processing error."""
        self.failed_files.append((file_path, error))
        self.logger.error(f"❌ Failed {file_path.name}: {error}")
    
    def get_summary(self) -> dict:
        """Get processing summary."""
        return {
            "total": self.total_files,
            "processed": self.processed_files,
            "failed": len(self.failed_files),
            "skipped": len(self.skipped_files),
            "failed_files": self.failed_files,
            "skipped_files": self.skipped_files
        }
