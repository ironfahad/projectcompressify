"""
Compressify - Cross-platform CLI tool for efficient batch compression of video and image files.

A powerful, Docker-containerized solution for compressing media files with both
interactive and non-interactive modes, supporting job resumption and parallel processing.
"""

__version__ = "1.0.0"
__author__ = "Project Compressify Team"
__description__ = "Cross-platform CLI tool for efficient batch compression of video and image files"

from .config import CompressionProfile, ImageSettings, VideoSettings
from .main import app
from .modules import CompressionEngine, InteractiveMode, ProfileManager

__all__ = [
    "app",
    "CompressionEngine", 
    "CompressionProfile",
    "ImageSettings",
    "InteractiveMode",
    "ProfileManager",
    "VideoSettings",
]