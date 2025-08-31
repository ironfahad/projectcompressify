"""
Interactive mode implementation using Questionary for user prompts.
"""

from pathlib import Path
from typing import Optional

import questionary
from rich.console import Console
from rich.panel import Panel

from ..config import (
    CompressionProfile,
    FileType,
    ImageFormat,
    ImageSettings,
    JobSettings,
    ProcessingSettings,
    QualityLevel,
    VideoFormat,
    VideoResolution,
    VideoSettings,
    QUALITY_PROFILES
)
from ..utils import (
    get_supported_files,
    validate_cpu_cores,
    validate_crf_value,
    validate_profile_name
)


class InteractiveMode:
    """Interactive mode for configuring compression jobs."""
    
    def __init__(self, console: Console):
        self.console = console
    
    def run(self, input_path: Path) -> JobSettings:
        """
        Run interactive mode to configure compression job.
        
        Args:
            input_path: Input file or directory path
            
        Returns:
            Configured JobSettings
        """
        self.console.print(Panel(
            "🎥 Welcome to Compressify Interactive Mode!\n"
            "Let's configure your compression settings step by step.",
            title="Interactive Configuration",
            border_style="blue"
        ))
        
        # Analyze input files
        files = get_supported_files(input_path)
        self._show_file_analysis(files)
        
        # Choose configuration method
        config_method = questionary.select(
            "How would you like to configure compression?",
            choices=[
                "Use a predefined profile",
                "Create custom settings",
                "Quick setup (recommended)"
            ]
        ).ask()
        
        if config_method == "Use a predefined profile":
            return self._configure_with_profile(input_path, files)
        elif config_method == "Create custom settings":
            return self._configure_custom_settings(input_path, files)
        else:  # Quick setup
            return self._configure_quick_setup(input_path, files)
    
    def create_profile(self, name: str) -> Optional[CompressionProfile]:
        """
        Create a new compression profile interactively.
        
        Args:
            name: Profile name
            
        Returns:
            Created CompressionProfile or None if cancelled
        """
        self.console.print(Panel(
            f"Creating new profile: {name}",
            title="Profile Creation",
            border_style="green"
        ))
        
        # Basic profile info
        description = questionary.text(
            "Profile description (optional):",
            default=""
        ).ask()
        
        # File types to process
        file_types = questionary.select(
            "What types of files should this profile handle?",
            choices=[
                questionary.Choice("Both videos and images", FileType.BOTH),
                questionary.Choice("Videos only", FileType.VIDEOS),
                questionary.Choice("Images only", FileType.IMAGES)
            ]
        ).ask()
        
        # Configure settings based on file types
        video_settings = None
        image_settings = None
        
        if file_types in (FileType.BOTH, FileType.VIDEOS):
            video_settings = self._configure_video_settings()
        
        if file_types in (FileType.BOTH, FileType.IMAGES):
            image_settings = self._configure_image_settings()
        
        # Processing settings
        processing_settings = self._configure_processing_settings()
        
        return CompressionProfile(
            name=name,
            description=description if description else None,
            file_types=file_types,
            video_settings=video_settings or VideoSettings(),
            image_settings=image_settings or ImageSettings(),
            processing_settings=processing_settings
        )
    
    def _show_file_analysis(self, files: dict):
        """Show analysis of input files."""
        total_videos = len(files["videos"])
        total_images = len(files["images"])
        
        analysis_text = f"📁 Found {total_videos} video(s) and {total_images} image(s)"
        
        if total_videos > 0:
            video_size = sum(f.stat().st_size for f in files["videos"]) / (1024 * 1024)
            analysis_text += f"\n🎥 Videos: {video_size:.1f} MB"
        
        if total_images > 0:
            image_size = sum(f.stat().st_size for f in files["images"]) / (1024 * 1024)
            analysis_text += f"\n🖼️  Images: {image_size:.1f} MB"
        
        self.console.print(Panel(analysis_text, title="File Analysis", border_style="cyan"))
    
    def _configure_with_profile(self, input_path: Path, files: dict) -> JobSettings:
        """Configure job using existing profile."""
        # Show available profiles
        profile_choices = []
        for name, profile in QUALITY_PROFILES.items():
            profile_choices.append(questionary.Choice(
                f"{profile.name} - {profile.description}",
                value=name
            ))
        
        selected_profile = questionary.select(
            "Choose a compression profile:",
            choices=profile_choices
        ).ask()
        
        profile = QUALITY_PROFILES[selected_profile].copy(deep=True)
        
        # Ask for any overrides
        if questionary.confirm("Would you like to modify any settings?").ask():
            profile = self._modify_profile_settings(profile)
        
        return JobSettings(
            input_path=input_path,
            profile=profile,
            file_types=profile.file_types
        )
    
    def _configure_custom_settings(self, input_path: Path, files: dict) -> JobSettings:
        """Configure job with custom settings."""
        # Determine file types to process
        has_videos = len(files["videos"]) > 0
        has_images = len(files["images"]) > 0
        
        if has_videos and has_images:
            file_types = questionary.select(
                "Which file types would you like to process?",
                choices=[
                    questionary.Choice("Both videos and images", FileType.BOTH),
                    questionary.Choice("Videos only", FileType.VIDEOS),
                    questionary.Choice("Images only", FileType.IMAGES)
                ]
            ).ask()
        elif has_videos:
            file_types = FileType.VIDEOS
        else:
            file_types = FileType.IMAGES
        
        # Configure settings
        video_settings = None
        image_settings = None
        
        if file_types in (FileType.BOTH, FileType.VIDEOS):
            video_settings = self._configure_video_settings()
        
        if file_types in (FileType.BOTH, FileType.IMAGES):
            image_settings = self._configure_image_settings()
        
        processing_settings = self._configure_processing_settings()
        
        # Create profile
        profile = CompressionProfile(
            name="Custom Settings",
            description="Custom settings for this job",
            file_types=file_types,
            video_settings=video_settings or VideoSettings(),
            image_settings=image_settings or ImageSettings(),
            processing_settings=processing_settings
        )
        
        return JobSettings(
            input_path=input_path,
            profile=profile,
            file_types=file_types
        )
    
    def _configure_quick_setup(self, input_path: Path, files: dict) -> JobSettings:
        """Configure job with quick setup."""
        # Simple quality selection
        quality = questionary.select(
            "Choose overall quality level:",
            choices=[
                questionary.Choice("High Quality (larger files, better quality)", QualityLevel.HIGH),
                questionary.Choice("Medium Quality (balanced)", QualityLevel.MEDIUM),
                questionary.Choice("Low Quality (smaller files, lower quality)", QualityLevel.LOW)
            ]
        ).ask()
        
        # Determine file types
        has_videos = len(files["videos"]) > 0
        has_images = len(files["images"]) > 0
        
        if has_videos and has_images:
            file_types = FileType.BOTH
        elif has_videos:
            file_types = FileType.VIDEOS
        else:
            file_types = FileType.IMAGES
        
        # Create quick profile
        profile = self._create_quick_profile(quality, file_types)
        
        return JobSettings(
            input_path=input_path,
            profile=profile,
            file_types=file_types
        )
    
    def _configure_video_settings(self) -> VideoSettings:
        """Configure video compression settings."""
        self.console.print("\n🎥 Video Settings", style="bold blue")
        
        # Output format
        format_choice = questionary.select(
            "Output video format:",
            choices=[
                questionary.Choice("MP4 (recommended)", VideoFormat.MP4),
                questionary.Choice("WebM", VideoFormat.WEBM),
                questionary.Choice("AVI", VideoFormat.AVI),
                questionary.Choice("MKV", VideoFormat.MKV),
                questionary.Choice("MOV", VideoFormat.MOV)
            ]
        ).ask()
        
        # Resolution
        resolution = questionary.select(
            "Target resolution:",
            choices=[
                questionary.Choice("Keep original", VideoResolution.ORIGINAL),
                questionary.Choice("1080p (Full HD)", VideoResolution.FHD_1080P),
                questionary.Choice("720p (HD)", VideoResolution.HD_720P),
                questionary.Choice("480p (SD)", VideoResolution.SD_480P),
                questionary.Choice("4K (Ultra HD)", VideoResolution.UHD_4K),
                questionary.Choice("1440p (QHD)", VideoResolution.QHD_1440P)
            ]
        ).ask()
        
        # Quality mode
        quality_mode = questionary.select(
            "Quality control mode:",
            choices=[
                questionary.Choice("Simple (Low/Medium/High)", "simple"),
                questionary.Choice("Advanced (CRF value)", "advanced")
            ]
        ).ask()
        
        quality_level = None
        crf_value = None
        
        if quality_mode == "simple":
            quality_level = questionary.select(
                "Quality level:",
                choices=[
                    questionary.Choice("High (best quality)", QualityLevel.HIGH),
                    questionary.Choice("Medium (balanced)", QualityLevel.MEDIUM),
                    questionary.Choice("Low (smaller files)", QualityLevel.LOW)
                ]
            ).ask()
        else:
            crf_value = questionary.text(
                "CRF value (0-51, lower = better quality):",
                default="23",
                validate=lambda x: validate_crf_value(int(x)) if x.isdigit() else "Must be a number 0-51"
            ).ask()
            crf_value = int(crf_value)
        
        return VideoSettings(
            format=format_choice,
            resolution=resolution,
            quality_mode=quality_mode,
            quality_level=quality_level,
            crf_value=crf_value
        )
    
    def _configure_image_settings(self) -> ImageSettings:
        """Configure image compression settings."""
        self.console.print("\n🖼️  Image Settings", style="bold green")
        
        # Output format
        format_choice = questionary.select(
            "Output image format:",
            choices=[
                questionary.Choice("WebP (modern, best compression)", ImageFormat.WEBP),
                questionary.Choice("JPEG (widely supported)", ImageFormat.JPEG),
                questionary.Choice("PNG (lossless)", ImageFormat.PNG),
                questionary.Choice("GIF (animations)", ImageFormat.GIF)
            ]
        ).ask()
        
        # Quality
        quality = questionary.text(
            "Quality (1-100, higher = better):",
            default="85",
            validate=lambda x: "Quality must be 1-100" if not (x.isdigit() and 1 <= int(x) <= 100) else True
        ).ask()
        
        # Custom dimensions
        resize = questionary.confirm("Resize images?").ask()
        width = height = None
        
        if resize:
            width = questionary.text(
                "Target width (pixels, 0 to keep aspect ratio):",
                default="0",
                validate=lambda x: "Must be a number" if not x.isdigit() else True
            ).ask()
            width = int(width) if int(width) > 0 else None
            
            height = questionary.text(
                "Target height (pixels, 0 to keep aspect ratio):",
                default="0",
                validate=lambda x: "Must be a number" if not x.isdigit() else True
            ).ask()
            height = int(height) if int(height) > 0 else None
        
        # Advanced options
        quantization = questionary.confirm(
            "Apply color quantization for smaller files?",
            default=True
        ).ask()
        
        return ImageSettings(
            format=format_choice,
            width=width,
            height=height,
            quality=int(quality),
            apply_quantization=quantization
        )
    
    def _configure_processing_settings(self) -> ProcessingSettings:
        """Configure processing and performance settings."""
        self.console.print("\n⚙️  Processing Settings", style="bold yellow")
        
        # CPU cores
        import os
        max_cores = os.cpu_count() or 1
        
        cpu_cores = questionary.text(
            f"Number of CPU cores to use (1-{max_cores}):",
            default="1",
            validate=lambda x: "Invalid core count" if not (x.isdigit() and validate_cpu_cores(int(x))) else True
        ).ask()
        
        # Processing options
        priority_images = questionary.confirm(
            "Process images before videos?",
            default=True
        ).ask()
        
        resume_jobs = questionary.confirm(
            "Resume interrupted jobs?",
            default=True
        ).ask()
        
        delete_source = questionary.confirm(
            "Delete source files after compression? (⚠️  Use with caution!)",
            default=False
        ).ask()
        
        return ProcessingSettings(
            cpu_cores=int(cpu_cores),
            priority_images_first=priority_images,
            resume_jobs=resume_jobs,
            delete_source_files=delete_source
        )
    
    def _modify_profile_settings(self, profile: CompressionProfile) -> CompressionProfile:
        """Allow user to modify existing profile settings."""
        modifications = questionary.checkbox(
            "What would you like to modify?",
            choices=[
                "Video settings",
                "Image settings", 
                "Processing settings"
            ]
        ).ask()
        
        if "Video settings" in modifications:
            profile.video_settings = self._configure_video_settings()
        
        if "Image settings" in modifications:
            profile.image_settings = self._configure_image_settings()
        
        if "Processing settings" in modifications:
            profile.processing_settings = self._configure_processing_settings()
        
        return profile
    
    def _create_quick_profile(self, quality: QualityLevel, file_types: FileType) -> CompressionProfile:
        """Create a quick profile based on quality level."""
        # Quality mappings
        quality_map = {
            QualityLevel.HIGH: {"crf": 18, "image_quality": 90},
            QualityLevel.MEDIUM: {"crf": 23, "image_quality": 80},
            QualityLevel.LOW: {"crf": 28, "image_quality": 65}
        }
        
        settings = quality_map[quality]
        
        return CompressionProfile(
            name=f"Quick {quality.value.title()} Quality",
            description=f"Quick setup for {quality.value} quality compression",
            file_types=file_types,
            video_settings=VideoSettings(
                format=VideoFormat.MP4,
                resolution=VideoResolution.ORIGINAL,
                quality_mode="advanced",
                crf_value=settings["crf"]
            ),
            image_settings=ImageSettings(
                format=ImageFormat.WEBP,
                quality=settings["image_quality"],
                apply_quantization=True
            ),
            processing_settings=ProcessingSettings(
                cpu_cores=1,
                priority_images_first=True,
                resume_jobs=True,
                delete_source_files=False
            )
        )
