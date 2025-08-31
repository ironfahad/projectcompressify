"""
Utility functions initialization.
"""

from .file_utils import (
    calculate_space_saved,
    ensure_directory,
    format_file_size,
    get_output_filename,
    get_relative_path,
    get_supported_files,
    is_already_processed,
    safe_filename,
    validate_path,
)
from .logger import ProgressLogger, setup_logger
from .validators import (
    estimate_compression_ratio,
    parse_resolution,
    sanitize_filename,
    validate_bitrate,
    validate_cpu_cores,
    validate_crf_value,
    validate_file_extension,
    validate_output_format,
    validate_path_permissions,
    validate_profile_name,
    validate_quality_percentage,
    validate_resolution,
)

__all__ = [
    # File utilities
    "calculate_space_saved",
    "ensure_directory",
    "format_file_size",
    "get_output_filename",
    "get_relative_path",
    "get_supported_files",
    "is_already_processed",
    "safe_filename",
    "validate_path",
    
    # Logging utilities
    "ProgressLogger",
    "setup_logger",
    
    # Validation utilities
    "estimate_compression_ratio",
    "parse_resolution",
    "sanitize_filename",
    "validate_bitrate",
    "validate_cpu_cores",
    "validate_crf_value",
    "validate_file_extension",
    "validate_output_format",
    "validate_path_permissions",
    "validate_profile_name",
    "validate_quality_percentage",
    "validate_resolution",
]
