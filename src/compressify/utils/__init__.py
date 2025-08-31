"""
Utility functions and helpers for Compressify.

Provides common functionality for file operations, validation,
logging, and other support functions.
"""

from .file_utils import (
    discover_files,
    format_file_size,
    get_file_size,
    is_image_file,
    is_video_file,
    parse_resolution
)
from .logger import setup_logger
from .validators import (
    validate_input_path,
    validate_output_path,
    validate_quality_value
)

__all__ = [
    "discover_files",
    "format_file_size",
    "get_file_size",
    "is_image_file",
    "is_video_file",
    "parse_resolution",
    "setup_logger",
    "validate_input_path",
    "validate_output_path",
    "validate_quality_value"
]