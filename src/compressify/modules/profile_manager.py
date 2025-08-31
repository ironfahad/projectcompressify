"""
Profile management for saving, loading, and managing compression profiles.
"""

import json
from pathlib import Path
from typing import Dict, List, Optional

from ..config import CompressionProfile, QUALITY_PROFILES
from ..utils import validate_profile_name


class ProfileManager:
    """Manager for compression profiles."""
    
    def __init__(self, profiles_dir: Optional[Path] = None):
        """
        Initialize ProfileManager.
        
        Args:
            profiles_dir: Custom directory for storing profiles
        """
        if profiles_dir:
            self.profiles_dir = profiles_dir
        else:
            # Default to user's home directory
            self.profiles_dir = Path.home() / ".compressify" / "profiles"
        
        # Ensure profiles directory exists
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
    
    def save_profile(self, profile: CompressionProfile) -> bool:
        """
        Save a compression profile.
        
        Args:
            profile: CompressionProfile to save
            
        Returns:
            True if saved successfully, False otherwise
        """
        try:
            # Validate profile name
            is_valid, error = validate_profile_name(profile.name)
            if not is_valid:
                raise ValueError(f"Invalid profile name: {error}")
            
            # Don't allow overwriting built-in profiles
            if profile.name in QUALITY_PROFILES:
                raise ValueError(f"Cannot overwrite built-in profile: {profile.name}")
            
            # Save to file
            profile_file = self.profiles_dir / f"{profile.name}.json"
            
            # Add timestamps
            import datetime
            now = datetime.datetime.now().isoformat()
            profile_data = profile.dict()
            
            if not profile_data.get("created_at"):
                profile_data["created_at"] = now
            profile_data["updated_at"] = now
            
            with open(profile_file, 'w', encoding='utf-8') as f:
                json.dump(profile_data, f, indent=2, default=str)
            
            return True
        
        except Exception as e:
            print(f"Error saving profile: {e}")
            return False
    
    def load_profile(self, name: str) -> Optional[CompressionProfile]:
        """
        Load a compression profile by name.
        
        Args:
            name: Profile name to load
            
        Returns:
            CompressionProfile if found, None otherwise
        """
        try:
            # Check built-in profiles first
            if name in QUALITY_PROFILES:
                return QUALITY_PROFILES[name].copy(deep=True)
            
            # Check custom profiles
            profile_file = self.profiles_dir / f"{name}.json"
            
            if not profile_file.exists():
                return None
            
            with open(profile_file, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            return CompressionProfile(**profile_data)
        
        except Exception as e:
            print(f"Error loading profile '{name}': {e}")
            return None
    
    def delete_profile(self, name: str) -> bool:
        """
        Delete a custom compression profile.
        
        Args:
            name: Profile name to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            # Don't allow deleting built-in profiles
            if name in QUALITY_PROFILES:
                raise ValueError(f"Cannot delete built-in profile: {name}")
            
            profile_file = self.profiles_dir / f"{name}.json"
            
            if not profile_file.exists():
                return False
            
            profile_file.unlink()
            return True
        
        except Exception as e:
            print(f"Error deleting profile '{name}': {e}")
            return False
    
    def list_custom_profiles(self) -> List[str]:
        """
        List all custom profile names.
        
        Returns:
            List of custom profile names
        """
        try:
            profiles = []
            for profile_file in self.profiles_dir.glob("*.json"):
                profile_name = profile_file.stem
                profiles.append(profile_name)
            
            return sorted(profiles)
        
        except Exception:
            return []
    
    def list_all_profiles(self) -> Dict[str, str]:
        """
        List all available profiles (built-in and custom).
        
        Returns:
            Dictionary mapping profile names to types ("built-in" or "custom")
        """
        profiles = {}
        
        # Built-in profiles
        for name in QUALITY_PROFILES.keys():
            profiles[name] = "built-in"
        
        # Custom profiles
        for name in self.list_custom_profiles():
            profiles[name] = "custom"
        
        return profiles
    
    def export_profile(self, name: str, output_path: Path) -> bool:
        """
        Export a profile to a specific file.
        
        Args:
            name: Profile name to export
            output_path: Output file path
            
        Returns:
            True if exported successfully, False otherwise
        """
        try:
            profile = self.load_profile(name)
            if not profile:
                return False
            
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(profile.dict(), f, indent=2, default=str)
            
            return True
        
        except Exception as e:
            print(f"Error exporting profile '{name}': {e}")
            return False
    
    def import_profile(self, file_path: Path, new_name: Optional[str] = None) -> Optional[str]:
        """
        Import a profile from a file.
        
        Args:
            file_path: Path to profile file
            new_name: Optional new name for the profile
            
        Returns:
            Profile name if imported successfully, None otherwise
        """
        try:
            if not file_path.exists():
                raise FileNotFoundError(f"Profile file not found: {file_path}")
            
            with open(file_path, 'r', encoding='utf-8') as f:
                profile_data = json.load(f)
            
            profile = CompressionProfile(**profile_data)
            
            # Use new name if provided
            if new_name:
                # Validate new name
                is_valid, error = validate_profile_name(new_name)
                if not is_valid:
                    raise ValueError(f"Invalid profile name: {error}")
                profile.name = new_name
            
            # Check if profile already exists
            if self.load_profile(profile.name):
                raise ValueError(f"Profile '{profile.name}' already exists")
            
            # Save the imported profile
            if self.save_profile(profile):
                return profile.name
            
            return None
        
        except Exception as e:
            print(f"Error importing profile from '{file_path}': {e}")
            return None
    
    def duplicate_profile(self, source_name: str, new_name: str) -> bool:
        """
        Duplicate an existing profile with a new name.
        
        Args:
            source_name: Name of profile to duplicate
            new_name: Name for the new profile
            
        Returns:
            True if duplicated successfully, False otherwise
        """
        try:
            # Load source profile
            source_profile = self.load_profile(source_name)
            if not source_profile:
                raise ValueError(f"Source profile '{source_name}' not found")
            
            # Validate new name
            is_valid, error = validate_profile_name(new_name)
            if not is_valid:
                raise ValueError(f"Invalid profile name: {error}")
            
            # Check if new name already exists
            if self.load_profile(new_name):
                raise ValueError(f"Profile '{new_name}' already exists")
            
            # Create new profile
            new_profile = source_profile.copy(deep=True)
            new_profile.name = new_name
            new_profile.description = f"Copy of {source_name}"
            
            # Clear timestamps to mark as new
            new_profile.created_at = None
            new_profile.updated_at = None
            
            return self.save_profile(new_profile)
        
        except Exception as e:
            print(f"Error duplicating profile '{source_name}': {e}")
            return False
    
    def validate_profile(self, profile: CompressionProfile) -> tuple[bool, List[str]]:
        """
        Validate a compression profile.
        
        Args:
            profile: Profile to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        try:
            # Validate name
            is_valid, error = validate_profile_name(profile.name)
            if not is_valid:
                errors.append(f"Profile name: {error}")
            
            # Validate video settings
            if profile.video_settings:
                if profile.video_settings.quality_mode == "advanced":
                    if profile.video_settings.crf_value is None:
                        errors.append("CRF value required in advanced quality mode")
                    elif not (0 <= profile.video_settings.crf_value <= 51):
                        errors.append("CRF value must be between 0 and 51")
            
            # Validate image settings
            if profile.image_settings:
                if not (1 <= profile.image_settings.quality <= 100):
                    errors.append("Image quality must be between 1 and 100")
                
                if profile.image_settings.width and profile.image_settings.width <= 0:
                    errors.append("Image width must be positive")
                
                if profile.image_settings.height and profile.image_settings.height <= 0:
                    errors.append("Image height must be positive")
            
            # Validate processing settings
            if profile.processing_settings:
                import os
                max_cores = os.cpu_count() or 1
                if not (1 <= profile.processing_settings.cpu_cores <= max_cores):
                    errors.append(f"CPU cores must be between 1 and {max_cores}")
            
            return len(errors) == 0, errors
        
        except Exception as e:
            errors.append(f"Validation error: {e}")
            return False, errors
    
    def get_profile_info(self, name: str) -> Optional[Dict]:
        """
        Get detailed information about a profile.
        
        Args:
            name: Profile name
            
        Returns:
            Dictionary with profile information or None if not found
        """
        profile = self.load_profile(name)
        if not profile:
            return None
        
        info = {
            "name": profile.name,
            "description": profile.description,
            "file_types": profile.file_types.value,
            "created_at": profile.created_at,
            "updated_at": profile.updated_at,
            "type": "built-in" if name in QUALITY_PROFILES else "custom",
        }
        
        # Add settings summary
        if profile.file_types in ("videos", "both"):
            info["video_format"] = profile.video_settings.format.value
            info["video_resolution"] = profile.video_settings.resolution.value
            info["video_quality"] = (
                profile.video_settings.quality_level.value 
                if profile.video_settings.quality_level 
                else f"CRF {profile.video_settings.crf_value}"
            )
        
        if profile.file_types in ("images", "both"):
            info["image_format"] = profile.image_settings.format.value
            info["image_quality"] = profile.image_settings.quality
        
        info["cpu_cores"] = profile.processing_settings.cpu_cores
        
        return info
