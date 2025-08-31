"""
Video compression module using ffmpeg-python.
"""

import subprocess
from pathlib import Path
from typing import Dict, Optional, Tuple

import ffmpeg
from rich.console import Console

from ..config import VideoFormat, VideoResolution, VideoSettings, QUALITY_PRESETS
from ..utils import format_file_size, parse_resolution


class VideoCompressor:
    """Video compression using FFmpeg."""
    
    def __init__(self, console: Console):
        self.console = console
    
    def compress_video(
        self,
        input_path: Path,
        output_path: Path,
        settings: VideoSettings
    ) -> Dict[str, any]:
        """
        Compress a single video file.
        
        Args:
            input_path: Input video file path
            output_path: Output video file path
            settings: Video compression settings
            
        Returns:
            Dictionary with compression results
        """
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Get input video info
            input_info = self._get_video_info(input_path)
            
            # Build ffmpeg stream
            stream = self._build_ffmpeg_stream(input_path, output_path, settings, input_info)
            
            # Get file sizes before compression
            original_size = input_path.stat().st_size
            
            # Run compression
            self._run_ffmpeg_stream(stream)
            
            # Get compressed file size
            compressed_size = output_path.stat().st_size if output_path.exists() else 0
            
            # Calculate savings
            savings = self._calculate_savings(original_size, compressed_size)
            
            return {
                "success": True,
                "input_path": input_path,
                "output_path": output_path,
                "original_size": original_size,
                "compressed_size": compressed_size,
                "savings": savings,
                "input_info": input_info
            }
        
        except Exception as e:
            return {
                "success": False,
                "input_path": input_path,
                "error": str(e)
            }
    
    def _get_video_info(self, video_path: Path) -> Dict:
        """Get video file information using ffprobe."""
        try:
            probe = ffmpeg.probe(str(video_path))
            video_stream = next(
                (stream for stream in probe['streams'] if stream['codec_type'] == 'video'), 
                None
            )
            
            if not video_stream:
                raise ValueError("No video stream found")
            
            info = {
                "width": int(video_stream.get('width', 0)),
                "height": int(video_stream.get('height', 0)),
                "duration": float(probe['format'].get('duration', 0)),
                "bitrate": int(probe['format'].get('bit_rate', 0)),
                "codec": video_stream.get('codec_name', 'unknown'),
                "fps": self._parse_fps(video_stream.get('r_frame_rate', '0/1')),
                "pixel_format": video_stream.get('pix_fmt', 'unknown')
            }
            
            return info
        
        except Exception as e:
            # Return minimal info if probe fails
            return {
                "width": 0,
                "height": 0,
                "duration": 0,
                "bitrate": 0,
                "codec": "unknown",
                "fps": 0,
                "pixel_format": "unknown",
                "probe_error": str(e)
            }
    
    def _build_ffmpeg_stream(
        self,
        input_path: Path,
        output_path: Path,
        settings: VideoSettings,
        input_info: Dict
    ) -> ffmpeg.nodes.OutputStream:
        """Build ffmpeg stream with compression settings."""
        
        # Input stream
        input_stream = ffmpeg.input(str(input_path))
        
        # Video processing chain
        video = input_stream.video
        
        # Apply resolution scaling if needed
        if settings.resolution != VideoResolution.ORIGINAL:
            video = self._apply_resolution_scaling(video, settings.resolution, input_info)
        
        # Audio processing (copy or re-encode)
        audio = input_stream.audio
        
        # Build output with compression settings
        output_kwargs = self._build_output_kwargs(settings)
        
        # Create output stream
        output_stream = ffmpeg.output(
            video,
            audio,
            str(output_path),
            **output_kwargs
        )
        
        return output_stream
    
    def _apply_resolution_scaling(
        self,
        video_stream,
        target_resolution: VideoResolution,
        input_info: Dict
    ):
        """Apply resolution scaling with aspect ratio preservation."""
        
        if target_resolution == VideoResolution.ORIGINAL:
            return video_stream
        
        # Parse target resolution
        target_width, target_height = parse_resolution(target_resolution.value)
        input_width = input_info.get('width', 0)
        input_height = input_info.get('height', 0)
        
        if input_width == 0 or input_height == 0:
            # Can't scale without input dimensions
            return video_stream
        
        # Calculate scaling with aspect ratio preservation
        input_aspect = input_width / input_height
        target_aspect = target_width / target_height
        
        if input_aspect > target_aspect:
            # Input is wider - fit to width, add letterboxing
            scale_width = target_width
            scale_height = int(target_width / input_aspect)
            
            if scale_height % 2 != 0:
                scale_height -= 1  # Ensure even height
            
            # Scale and pad
            video_stream = video_stream.filter('scale', scale_width, scale_height)
            
            if scale_height < target_height:
                pad_height = target_height - scale_height
                pad_top = pad_height // 2
                video_stream = video_stream.filter(
                    'pad',
                    target_width,
                    target_height,
                    0,
                    pad_top,
                    color='black'
                )
        else:
            # Input is taller - fit to height, add pillarboxing
            scale_height = target_height
            scale_width = int(target_height * input_aspect)
            
            if scale_width % 2 != 0:
                scale_width -= 1  # Ensure even width
            
            # Scale and pad
            video_stream = video_stream.filter('scale', scale_width, scale_height)
            
            if scale_width < target_width:
                pad_width = target_width - scale_width
                pad_left = pad_width // 2
                video_stream = video_stream.filter(
                    'pad',
                    target_width,
                    target_height,
                    pad_left,
                    0,
                    color='black'
                )
        
        return video_stream
    
    def _build_output_kwargs(self, settings: VideoSettings) -> Dict:
        """Build ffmpeg output arguments."""
        kwargs = {
            'vcodec': settings.codec,
            'acodec': settings.audio_codec,
            'pix_fmt': 'yuv420p',  # Ensure compatibility
        }
        
        # Quality settings
        if settings.quality_mode == "simple" and settings.quality_level:
            # Use preset values
            preset_values = QUALITY_PRESETS.get(settings.quality_level, {})
            kwargs['crf'] = preset_values.get('crf', 23)
            kwargs['preset'] = preset_values.get('preset', 'medium')
        
        elif settings.quality_mode == "advanced" and settings.crf_value is not None:
            # Use custom CRF value
            kwargs['crf'] = settings.crf_value
            kwargs['preset'] = 'medium'  # Default preset
        
        # Bitrate override
        if settings.bitrate:
            kwargs['video_bitrate'] = settings.bitrate
            # Remove CRF when using bitrate
            kwargs.pop('crf', None)
        
        # Format-specific settings
        if settings.format == VideoFormat.MP4:
            kwargs['movflags'] = 'faststart'  # Enable streaming
        
        elif settings.format == VideoFormat.WEBM:
            kwargs['vcodec'] = 'libvpx-vp9'
            kwargs['acodec'] = 'libopus'
            # Remove incompatible options
            kwargs.pop('preset', None)
        
        return kwargs
    
    def _run_ffmpeg_stream(self, stream: ffmpeg.nodes.OutputStream):
        """Run ffmpeg stream with error handling."""
        try:
            # Run with overwrite and quiet mode
            ffmpeg.run(
                stream,
                overwrite_output=True,
                quiet=True,
                capture_stdout=True,
                capture_stderr=True
            )
        
        except ffmpeg.Error as e:
            error_message = "FFmpeg execution failed"
            
            if e.stderr:
                stderr_text = e.stderr.decode('utf-8', errors='ignore')
                # Extract meaningful error from stderr
                lines = stderr_text.split('\n')
                for line in lines:
                    if 'error' in line.lower() or 'invalid' in line.lower():
                        error_message = line.strip()
                        break
                else:
                    # Use last non-empty line if no specific error found
                    for line in reversed(lines):
                        if line.strip():
                            error_message = line.strip()
                            break
            
            raise RuntimeError(error_message)
    
    def _parse_fps(self, fps_string: str) -> float:
        """Parse frame rate from ffprobe output."""
        try:
            if '/' in fps_string:
                num, den = fps_string.split('/')
                return float(num) / float(den) if float(den) != 0 else 0
            else:
                return float(fps_string)
        except (ValueError, ZeroDivisionError):
            return 0
    
    def _calculate_savings(self, original_size: int, compressed_size: int) -> Dict:
        """Calculate compression savings."""
        if original_size == 0:
            return {
                "bytes": 0,
                "percentage": 0.0,
                "human_readable": "0 B"
            }
        
        saved_bytes = original_size - compressed_size
        saved_percentage = (saved_bytes / original_size) * 100
        
        return {
            "bytes": saved_bytes,
            "percentage": saved_percentage,
            "human_readable": format_file_size(saved_bytes)
        }
    
    def estimate_output_size(
        self,
        input_path: Path,
        settings: VideoSettings
    ) -> Optional[int]:
        """
        Estimate output file size.
        
        Args:
            input_path: Input video file
            settings: Compression settings
            
        Returns:
            Estimated size in bytes or None if estimation fails
        """
        try:
            input_info = self._get_video_info(input_path)
            original_size = input_path.stat().st_size
            
            # Simple estimation based on quality settings
            if settings.quality_mode == "simple" and settings.quality_level:
                compression_ratios = {
                    "low": 0.3,
                    "medium": 0.5,
                    "high": 0.7
                }
                ratio = compression_ratios.get(settings.quality_level.value, 0.5)
            
            elif settings.crf_value is not None:
                # CRF-based estimation
                if settings.crf_value <= 18:
                    ratio = 0.8  # High quality
                elif settings.crf_value <= 23:
                    ratio = 0.6  # Medium quality
                elif settings.crf_value <= 28:
                    ratio = 0.4  # Lower quality
                else:
                    ratio = 0.3  # Low quality
            
            else:
                ratio = 0.5  # Default
            
            # Adjust for resolution changes
            if settings.resolution != VideoResolution.ORIGINAL:
                target_width, target_height = parse_resolution(settings.resolution.value)
                input_width = input_info.get('width', 1920)
                input_height = input_info.get('height', 1080)
                
                resolution_ratio = (target_width * target_height) / (input_width * input_height)
                ratio *= resolution_ratio
            
            return int(original_size * ratio)
        
        except Exception:
            return None
    
    def is_ffmpeg_available(self) -> bool:
        """Check if FFmpeg is available."""
        try:
            result = subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def get_supported_codecs(self) -> Dict[str, list]:
        """Get list of supported video and audio codecs."""
        try:
            # Get encoders
            result = subprocess.run(
                ['ffmpeg', '-encoders'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode != 0:
                return {"video": [], "audio": []}
            
            lines = result.stdout.split('\n')
            video_codecs = []
            audio_codecs = []
            
            for line in lines:
                if line.startswith(' V'):  # Video encoder
                    parts = line.split()
                    if len(parts) >= 2:
                        codec_name = parts[1]
                        video_codecs.append(codec_name)
                elif line.startswith(' A'):  # Audio encoder
                    parts = line.split()
                    if len(parts) >= 2:
                        codec_name = parts[1]
                        audio_codecs.append(codec_name)
            
            return {
                "video": sorted(video_codecs),
                "audio": sorted(audio_codecs)
            }
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return {"video": [], "audio": []}
