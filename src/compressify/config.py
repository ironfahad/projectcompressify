"""
Configuration models and settings for Compressify.

This module defines all configuration structures using Pydantic models
for type safety and validation.
"""

from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Union

from pydantic import BaseModel, Field, validator


class VideoFormat(str, Enum):
    """Supported video output formats."""
    MP4 = "mp4"
    AVI = "avi"
    MKV = "mkv"
    WEBM = "webm"
    MOV = "mov"


class ImageFormat(str, Enum):
    """Supported image output formats."""
    JPEG = "jpeg"
    PNG = "png"
    WEBP = "webp"
    AVIF = "avif"
    TIFF = "tiff"
    BMP = "bmp"


class VideoResolution(str, Enum):
    """Standard video resolutions."""
    ORIGINAL = "original"
    UHD_4K = "3840x2160"
    QHD_1440P = "2560x1440"
    FHD_1080P = "1920x1080"
    HD_720P = "1280x720"
    SD_480P = "854x480"
    SD_360P = "640x360"


class QualityLevel(str, Enum):
    """Simple quality levels for non-technical users."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class VideoSettings(BaseModel):
    """Video compression settings."""
    format: VideoFormat = VideoFormat.MP4
    resolution: VideoResolution = VideoResolution.ORIGINAL
    quality_mode: str = "simple"  # "simple" or "advanced"
    quality_level: Optional[QualityLevel] = QualityLevel.MEDIUM
    crf_value: Optional[int] = Field(None, ge=0, le=51)
    bitrate: Optional[str] = None  # e.g., "2M", "500k"
    codec: str = "libx264"
    audio_codec: str = "aac"
    preset: str = "medium"

    @validator("crf_value")
    def validate_crf(cls, v, values):
        if values.get("quality_mode") == "advanced" and v is None:
            raise ValueError("CRF value required in advanced mode")
        return v


class ImageSettings(BaseModel):
    """Image compression settings."""
    format: ImageFormat = ImageFormat.JPEG
    width: Optional[int] = Field(None, gt=0)
    height: Optional[int] = Field(None, gt=0)
    quality_mode: str = "simple"  # "simple" or "advanced"
    quality_level: Optional[QualityLevel] = QualityLevel.MEDIUM
    quality_value: Optional[int] = Field(None, ge=1, le=100)
    preserve_aspect_ratio: bool = True
    lossless: bool = False

    @validator("quality_value")
    def validate_quality(cls, v, values):
        if values.get("quality_mode") == "advanced" and v is None:
            raise ValueError("Quality value required in advanced mode")
        return v


class ProcessingSettings(BaseModel):
    """Processing and performance settings."""
    max_workers: Optional[int] = Field(None, ge=1)
    overwrite_existing: bool = False
    preserve_metadata: bool = True
    create_backup: bool = False


class CompressionProfile(BaseModel):
    """Complete compression profile configuration."""
    name: str
    description: str = ""
    video_settings: VideoSettings = VideoSettings()
    image_settings: ImageSettings = ImageSettings()
    processing_settings: ProcessingSettings = ProcessingSettings()
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

    class Config:
        json_encoders = {
            Path: str
        }


# File extension mappings
VIDEO_EXTENSIONS = {
    ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", 
    ".m4v", ".3gp", ".ogv", ".ts", ".mts", ".m2ts"
}

IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".tiff", 
    ".tif", ".avif", ".raw", ".cr2", ".nef", ".arw"
}

# Quality presets for different use cases
QUALITY_PRESETS = {
    QualityLevel.LOW: {
        "crf": 28, 
        "preset": "fast", 
        "image_quality": 60,
        "description": "Fast compression with smaller files"
    },
    QualityLevel.MEDIUM: {
        "crf": 23, 
        "preset": "medium", 
        "image_quality": 85,
        "description": "Balanced quality and file size"
    },
    QualityLevel.HIGH: {
        "crf": 18, 
        "preset": "slow", 
        "image_quality": 95,
        "description": "High quality with larger files"
    }
}

# Built-in compression profiles
BUILTIN_PROFILES = {
    "low": CompressionProfile(
        name="low",
        description="Fast compression with smaller files, optimized for web sharing",
        video_settings=VideoSettings(
            format=VideoFormat.MP4,
            quality_level=QualityLevel.LOW,
            codec="libx264",
            preset="fast"
        ),
        image_settings=ImageSettings(
            format=ImageFormat.JPEG,
            quality_level=QualityLevel.LOW
        )
    ),
    "medium": CompressionProfile(
        name="medium",
        description="Balanced quality and file size for general use",
        video_settings=VideoSettings(
            format=VideoFormat.MP4,
            quality_level=QualityLevel.MEDIUM,
            codec="libx264",
            preset="medium"
        ),
        image_settings=ImageSettings(
            format=ImageFormat.JPEG,
            quality_level=QualityLevel.MEDIUM
        )
    ),
    "high": CompressionProfile(
        name="high",
        description="High quality compression for professional use",
        video_settings=VideoSettings(
            format=VideoFormat.MP4,
            quality_level=QualityLevel.HIGH,
            codec="libx264",
            preset="slow"
        ),
        image_settings=ImageSettings(
            format=ImageFormat.JPEG,
            quality_level=QualityLevel.HIGH
        )
    ),
    "web_optimized": CompressionProfile(
        name="web_optimized",
        description="Optimized for web delivery with modern formats",
        video_settings=VideoSettings(
            format=VideoFormat.WEBM,
            quality_level=QualityLevel.MEDIUM,
            codec="libvpx-vp9",
            resolution=VideoResolution.FHD_1080P
        ),
        image_settings=ImageSettings(
            format=ImageFormat.WEBP,
            quality_level=QualityLevel.MEDIUM
        )
    )
}