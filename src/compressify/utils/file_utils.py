"""
Utility functions for file operations and validation.
"""

from pathlib import Path
from typing import Dict, List

from ..config import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS


def get_supported_files(input_path: Path) -> Dict[str, List[Path]]:
    """
    Get all supported video and image files from input path.
    
    Args:
        input_path: Path to file or directory
        
    Returns:
        Dictionary with 'videos' and 'images' keys containing file lists
    """
    files = {"videos": [], "images": []}
    
    if input_path.is_file():
        # Single file
        if input_path.suffix.lower() in VIDEO_EXTENSIONS:
            files["videos"].append(input_path)
        elif input_path.suffix.lower() in IMAGE_EXTENSIONS:
            files["images"].append(input_path)
    else:
        # Directory - recursively find all supported files
        for file_path in input_path.rglob("*"):
            if file_path.is_file():
                ext = file_path.suffix.lower()
                if ext in VIDEO_EXTENSIONS:
                    files["videos"].append(file_path)
                elif ext in IMAGE_EXTENSIONS:
                    files["images"].append(file_path)
    
    return files


def validate_path(path: Path) -> bool:
    """
    Validate if path exists and is readable.
    
    Args:
        path: Path to validate
        
    Returns:
        True if path is valid, False otherwise
    """
    try:
        return path.exists() and (path.is_file() or path.is_dir())
    except (OSError, PermissionError):
        return False


def ensure_directory(path: Path) -> bool:
    """
    Ensure directory exists, create if it doesn't.
    
    Args:
        path: Directory path to ensure
        
    Returns:
        True if directory exists or was created successfully
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except (OSError, PermissionError):
        return False


def get_output_filename(input_file: Path, output_dir: Path, new_extension: str = None) -> Path:
    """
    Generate output filename for compressed file.
    
    Args:
        input_file: Original file path
        output_dir: Output directory
        new_extension: New file extension (optional)
        
    Returns:
        Output file path
    """
    if new_extension:
        # Change extension
        output_name = f"{input_file.stem}.{new_extension.lstrip('.')}"
    else:
        # Keep original extension
        output_name = input_file.name
    
    return output_dir / output_name


def is_already_processed(input_file: Path, output_dir: Path, new_extension: str = None) -> bool:
    """
    Check if file has already been processed (for job resumption).
    
    Args:
        input_file: Original file path
        output_dir: Output directory
        new_extension: New file extension (optional)
        
    Returns:
        True if output file already exists
    """
    output_file = get_output_filename(input_file, output_dir, new_extension)
    return output_file.exists()


def calculate_space_saved(original_size: int, compressed_size: int) -> Dict[str, str]:
    """
    Calculate space savings from compression.
    
    Args:
        original_size: Original file size in bytes
        compressed_size: Compressed file size in bytes
        
    Returns:
        Dictionary with savings information
    """
    if original_size == 0:
        return {"bytes": "0", "percentage": "0%", "mb": "0.0 MB"}
    
    saved_bytes = original_size - compressed_size
    saved_percentage = (saved_bytes / original_size) * 100
    saved_mb = saved_bytes / (1024 * 1024)
    
    return {
        "bytes": str(saved_bytes),
        "percentage": f"{saved_percentage:.1f}%",
        "mb": f"{saved_mb:.1f} MB"
    }


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted size string
    """
    if size_bytes == 0:
        return "0 B"
    
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_bytes)
    
    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1
    
    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.1f} {units[unit_index]}"


def get_relative_path(file_path: Path, base_path: Path) -> Path:
    """
    Get relative path from base path.
    
    Args:
        file_path: Full file path
        base_path: Base directory path
        
    Returns:
        Relative path
    """
    try:
        return file_path.relative_to(base_path)
    except ValueError:
        # If paths are not related, return the filename
        return file_path.name


def safe_filename(filename: str) -> str:
    """
    Create a safe filename by removing/replacing problematic characters.
    
    Args:
        filename: Original filename
        
    Returns:
        Safe filename
    """
    # Remove or replace problematic characters
    invalid_chars = '<>:"/\\|?*'
    safe_name = filename
    
    for char in invalid_chars:
        safe_name = safe_name.replace(char, '_')
    
    # Remove leading/trailing whitespace and dots
    safe_name = safe_name.strip(' .')
    
    # Ensure filename is not empty
    if not safe_name:
        safe_name = "output"
    
    return safe_name
