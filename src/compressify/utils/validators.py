"""
Utility functions for validation and type checking.
"""

import re
from pathlib import Path
from typing import Any, Optional, Union

from ..config import (
    IMAGE_EXTENSIONS,
    VIDEO_EXTENSIONS,
    VideoFormat,
    ImageFormat,
    VideoResolution,
    QualityLevel
)


def validate_crf_value(crf: int) -> bool:
    """
    Validate CRF (Constant Rate Factor) value.
    
    Args:
        crf: CRF value to validate
        
    Returns:
        True if valid, False otherwise
    """
    return 0 <= crf <= 51


def validate_bitrate(bitrate: str) -> bool:
    """
    Validate bitrate string format (e.g., "2M", "500k", "1000").
    
    Args:
        bitrate: Bitrate string to validate
        
    Returns:
        True if valid, False otherwise
    """
    pattern = r'^\d+[kmgtKMGT]?$'
    return bool(re.match(pattern, bitrate))


def validate_resolution(resolution: str) -> bool:
    """
    Validate resolution string format (e.g., "1920x1080").
    
    Args:
        resolution: Resolution string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if resolution in [res.value for res in VideoResolution]:
        return True
    
    pattern = r'^\d+x\d+$'
    return bool(re.match(pattern, resolution))


def validate_quality_percentage(quality: int) -> bool:
    """
    Validate quality percentage (1-100).
    
    Args:
        quality: Quality percentage to validate
        
    Returns:
        True if valid, False otherwise
    """
    return 1 <= quality <= 100


def validate_cpu_cores(cores: int) -> bool:
    """
    Validate CPU cores count.
    
    Args:
        cores: Number of cores to validate
        
    Returns:
        True if valid, False otherwise
    """
    import os
    max_cores = os.cpu_count() or 1
    return 1 <= cores <= max_cores


def validate_file_extension(file_path: Path, file_type: str) -> bool:
    """
    Validate if file has supported extension for given type.
    
    Args:
        file_path: File path to check
        file_type: Type ("video" or "image")
        
    Returns:
        True if extension is supported, False otherwise
    """
    ext = file_path.suffix.lower()
    
    if file_type == "video":
        return ext in VIDEO_EXTENSIONS
    elif file_type == "image":
        return ext in IMAGE_EXTENSIONS
    
    return False


def validate_output_format(format_str: str, file_type: str) -> bool:
    """
    Validate output format for given file type.
    
    Args:
        format_str: Format string to validate
        file_type: Type ("video" or "image")
        
    Returns:
        True if format is supported, False otherwise
    """
    if file_type == "video":
        return format_str in [fmt.value for fmt in VideoFormat]
    elif file_type == "image":
        return format_str in [fmt.value for fmt in ImageFormat]
    
    return False


def validate_profile_name(name: str) -> tuple[bool, Optional[str]]:
    """
    Validate profile name format.
    
    Args:
        name: Profile name to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not name:
        return False, "Profile name cannot be empty"
    
    if len(name) > 50:
        return False, "Profile name must be 50 characters or less"
    
    # Check for invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    if re.search(invalid_chars, name):
        return False, "Profile name contains invalid characters"
    
    # Check for reserved names
    reserved_names = ["con", "prn", "aux", "nul"] + [f"com{i}" for i in range(1, 10)] + [f"lpt{i}" for i in range(1, 10)]
    if name.lower() in reserved_names:
        return False, "Profile name is reserved"
    
    return True, None


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing invalid characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove invalid characters
    invalid_chars = r'[<>:"/\\|?*]'
    sanitized = re.sub(invalid_chars, '_', filename)
    
    # Remove leading/trailing whitespace and dots
    sanitized = sanitized.strip(' .')
    
    # Ensure not empty
    if not sanitized:
        sanitized = "output"
    
    return sanitized


def parse_resolution(resolution_str: str) -> tuple[int, int]:
    """
    Parse resolution string to width and height.
    
    Args:
        resolution_str: Resolution string (e.g., "1920x1080")
        
    Returns:
        Tuple of (width, height)
        
    Raises:
        ValueError: If resolution string is invalid
    """
    # Handle predefined resolutions
    resolution_map = {
        VideoResolution.UHD_4K.value: (3840, 2160),
        VideoResolution.QHD_1440P.value: (2560, 1440),
        VideoResolution.FHD_1080P.value: (1920, 1080),
        VideoResolution.HD_720P.value: (1280, 720),
        VideoResolution.SD_480P.value: (854, 480),
        VideoResolution.SD_360P.value: (640, 360),
    }
    
    if resolution_str in resolution_map:
        return resolution_map[resolution_str]
    
    # Parse custom resolution
    try:
        width, height = resolution_str.split('x')
        return int(width), int(height)
    except ValueError:
        raise ValueError(f"Invalid resolution format: {resolution_str}")


def validate_path_permissions(path: Path, operation: str = "read") -> tuple[bool, Optional[str]]:
    """
    Validate path permissions for given operation.
    
    Args:
        path: Path to validate
        operation: Operation type ("read", "write", or "both")
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if not path.exists():
            if operation in ("write", "both"):
                # Check if parent directory is writable
                parent = path.parent
                if not parent.exists():
                    return False, f"Parent directory does not exist: {parent}"
                if not parent.is_dir():
                    return False, f"Parent is not a directory: {parent}"
                # Try creating a temporary file to test write permissions
                try:
                    temp_file = parent / ".compressify_test"
                    temp_file.touch()
                    temp_file.unlink()
                    return True, None
                except (OSError, PermissionError):
                    return False, f"No write permission in directory: {parent}"
            else:
                return False, f"Path does not exist: {path}"
        
        if operation in ("read", "both"):
            if not path.is_readable():
                return False, f"No read permission: {path}"
        
        if operation in ("write", "both"):
            if path.is_file() and not path.is_writeable():
                return False, f"No write permission: {path}"
            elif path.is_dir():
                # Test write permission in directory
                try:
                    temp_file = path / ".compressify_test"
                    temp_file.touch()
                    temp_file.unlink()
                except (OSError, PermissionError):
                    return False, f"No write permission in directory: {path}"
        
        return True, None
    
    except Exception as e:
        return False, f"Error checking permissions: {e}"


def estimate_compression_ratio(file_path: Path, quality_level: QualityLevel) -> float:
    """
    Estimate compression ratio based on file type and quality level.
    
    Args:
        file_path: Input file path
        quality_level: Quality level for compression
        
    Returns:
        Estimated compression ratio (0.1 = 90% reduction, 0.5 = 50% reduction)
    """
    ext = file_path.suffix.lower()
    
    # Base compression ratios by file type and quality
    compression_ratios = {
        "video": {
            QualityLevel.LOW: 0.3,
            QualityLevel.MEDIUM: 0.5,
            QualityLevel.HIGH: 0.7,
        },
        "image": {
            QualityLevel.LOW: 0.2,
            QualityLevel.MEDIUM: 0.4,
            QualityLevel.HIGH: 0.6,
        }
    }
    
    if ext in VIDEO_EXTENSIONS:
        return compression_ratios["video"].get(quality_level, 0.5)
    elif ext in IMAGE_EXTENSIONS:
        return compression_ratios["image"].get(quality_level, 0.4)
    
    return 0.5  # Default ratio
