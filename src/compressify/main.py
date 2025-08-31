"""
Main CLI application entry point for Compressify.

This module provides both interactive and non-interactive modes for the CLI,
using Typer for argument parsing and Rich for beautiful output.
"""

import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import (
    CompressionProfile, 
    ImageFormat,
    VideoFormat,
    QualityLevel,
    ImageSettings,
    VideoSettings
)
from .modules import CompressionEngine, InteractiveMode, ProfileManager
from .utils import validate_input_path, setup_logger

# Initialize console and logger
console = Console()
logger = setup_logger()

# Create the main Typer app
app = typer.Typer(
    name="compressify",
    help="🎬 Cross-platform CLI tool for efficient batch compression of video and image files",
    epilog="Built with ❤️ using Python, FFmpeg, and Docker",
    rich_markup_mode="rich",
    no_args_is_help=True,
)

# Initialize global components
compression_engine = CompressionEngine(console)
profile_manager = ProfileManager(console)


@app.command()
def compress(
    input_paths: List[Path] = typer.Argument(
        ...,
        help="Input file or directory paths",
        exists=True,
    ),
    output_dir: Path = typer.Option(
        Path("./compressed"),
        "--output", "-o",
        help="Output directory"
    ),
    profile: str = typer.Option(
        "medium",
        "--profile", "-p",
        help="Compression profile name"
    ),
    recursive: bool = typer.Option(
        False,
        "--recursive", "-r",
        help="Process directories recursively"
    ),
    overwrite: bool = typer.Option(
        False,
        "--overwrite",
        help="Overwrite existing output files"
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Preview what would be compressed without actually doing it"
    ),
    workers: Optional[int] = typer.Option(
        None,
        "--workers", "-w",
        help="Number of parallel workers (default: auto)"
    )
):
    """
    Compress video and image files using specified settings.
    
    Examples:
        compressify compress video.mp4 image.jpg
        compressify compress ./media/ -o ./output/ -r --profile high
        compressify compress *.mp4 --dry-run
    """
    # Validate input paths
    for input_path in input_paths:
        if not validate_input_path(input_path):
            console.print(f"[red]Error: Invalid input path: {input_path}[/red]")
            raise typer.Exit(1)
    
    # Load compression profile
    try:
        compression_profile = profile_manager.load_profile(profile)
    except Exception as e:
        console.print(f"[red]Error loading profile '{profile}': {e}[/red]")
        raise typer.Exit(1)
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Show header
    console.print(Panel(
        f"[bold blue]Compressify Compression[/bold blue]\n"
        f"Profile: {compression_profile.name}\n"
        f"Output: {output_dir}\n"
        f"Mode: {'Dry Run' if dry_run else 'Compression'}",
        border_style="blue"
    ))
    
    # Execute compression
    try:
        result = compression_engine.compress_files(
            input_paths=input_paths,
            output_dir=output_dir,
            profile=compression_profile,
            recursive=recursive,
            overwrite=overwrite,
            dry_run=dry_run
        )
        
        if result["success"]:
            if dry_run:
                console.print("\n[green]✓ Dry run completed successfully[/green]")
            else:
                console.print("\n[green]✓ Compression completed successfully[/green]")
        else:
            console.print(f"\n[red]✗ Compression failed: {result.get('error', 'Unknown error')}[/red]")
            raise typer.Exit(1)
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        raise typer.Exit(1)


@app.command()
def interactive():
    """
    Start interactive mode for guided compression setup.
    
    This mode provides step-by-step prompts to help you configure
    compression settings without remembering command-line arguments.
    """
    console.print(Panel(
        "[bold green]Interactive Compression Mode[/bold green]\n"
        "Follow the prompts to configure your compression settings.",
        border_style="green"
    ))
    
    try:
        interactive_mode = InteractiveMode(console, profile_manager)
        result = interactive_mode.run()
        
        if result:
            console.print("\n[green]✓ Interactive compression completed[/green]")
        else:
            console.print("\n[yellow]Interactive mode cancelled[/yellow]")
    
    except KeyboardInterrupt:
        console.print("\n[yellow]Interactive mode cancelled[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error in interactive mode: {e}[/red]")
        raise typer.Exit(1)


@app.command("profiles")
def manage_profiles():
    """Manage compression profiles."""
    
    # Create profiles sub-app
    profiles_app = typer.Typer(help="Manage compression profiles")
    
    @profiles_app.command("list")
    def list_profiles():
        """List all available profiles."""
        console.print("\n[bold cyan]Available Profiles:[/bold cyan]")
        
        # Built-in profiles
        built_in = profile_manager.list_builtin_profiles()
        if built_in:
            console.print("\n[bold blue]Built-in Profiles:[/bold blue]")
            for profile_name in built_in:
                profile = profile_manager.load_profile(profile_name)
                console.print(f"  • {profile_name}: {profile.description}")
        
        # Custom profiles
        custom = profile_manager.list_custom_profiles()
        if custom:
            console.print("\n[bold green]Custom Profiles:[/bold green]")
            for profile_name in custom:
                profile = profile_manager.load_profile(profile_name)
                console.print(f"  • {profile_name}: {profile.description}")
        
        if not built_in and not custom:
            console.print("[yellow]No profiles found[/yellow]")
    
    @profiles_app.command("show")
    def show_profile(
        name: str = typer.Argument(..., help="Profile name to show")
    ):
        """Show detailed profile settings."""
        try:
            profile = profile_manager.load_profile(name)
            
            table = Table(title=f"Profile: {profile.name}")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="magenta")
            
            # Basic info
            table.add_row("Name", profile.name)
            table.add_row("Description", profile.description)
            
            # Video settings
            table.add_row("Video Format", profile.video_settings.format.value)
            table.add_row("Video Quality", str(profile.video_settings.quality_level))
            table.add_row("Video Codec", profile.video_settings.codec)
            
            # Image settings  
            table.add_row("Image Format", profile.image_settings.format.value)
            table.add_row("Image Quality", str(profile.image_settings.quality_level))
            
            console.print(table)
        
        except Exception as e:
            console.print(f"[red]Error loading profile '{name}': {e}[/red]")
            raise typer.Exit(1)
    
    # Execute the profiles sub-command
    profiles_app()


@app.command()
def info():
    """Show system information and supported formats."""
    
    # System info table
    table = Table(title="System Information")
    table.add_column("Component", style="cyan")
    table.add_column("Status", style="magenta")
    
    # Check FFmpeg
    ffmpeg_available = compression_engine.video_compressor.is_ffmpeg_available()
    table.add_row(
        "FFmpeg", 
        "[green]Available[/green]" if ffmpeg_available else "[red]Not Found[/red]"
    )
    
    # Check supported formats
    table.add_row("Video Formats", ", ".join([fmt.value for fmt in VideoFormat]))
    table.add_row("Image Formats", ", ".join([fmt.value for fmt in ImageFormat]))
    
    console.print(table)
    
    # Show version info
    from . import __version__
    console.print(f"\n[bold blue]Compressify v{__version__}[/bold blue]")
    console.print("Built with Python, FFmpeg, and Rich")


@app.callback()
def main(
    version: bool = typer.Option(
        False, "--version", "-v", help="Show version and exit"
    )
):
    """
    Compressify - Cross-platform CLI tool for video and image compression.
    
    Efficiently compress video and image files with customizable settings,
    parallel processing, and both interactive and batch modes.
    """
    if version:
        from . import __version__
        console.print(f"Compressify v{__version__}")
        raise typer.Exit()


def cli():
    """Entry point for the CLI application."""
    try:
        app()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"\n[red]Unexpected error: {e}[/red]")
        sys.exit(1)
    finally:
        # Clean shutdown
        compression_engine.shutdown()


if __name__ == "__main__":
    cli()