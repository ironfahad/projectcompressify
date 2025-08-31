# Project Compressify 🗜️

A powerful, user-friendly command-line tool for compressing videos and images with advanced features and beautiful output.

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## ✨ Features

### 🎥 Video Compression
- **Advanced codec support**: H.264, H.265 (HEVC), VP9, AV1
- **Flexible quality control**: CRF and bitrate-based compression
- **Resolution scaling**: Automatic and custom resolution options
- **Format conversion**: Support for MP4, AVI, MKV, WebM, MOV

### 🖼️ Image Compression
- **Multi-format support**: JPEG, PNG, WebP, AVIF
- **Quality optimization**: Intelligent quality settings
- **Batch processing**: Handle entire directories efficiently
- **Format conversion**: Convert between image formats

### 🚀 Advanced Features
- **Interactive Mode**: User-friendly wizard for beginners
- **Profile Management**: Save and reuse compression settings
- **Job Management**: Pause, resume, and track compression jobs
- **Progress Tracking**: Real-time progress with beautiful output
- **Docker Support**: Containerized deployment
- **Cross-platform**: Works on Windows, macOS, and Linux

## 📦 Installation

### Option 1: Using pip (Recommended)
```bash
pip install compressify
```

### Option 2: From Source
```bash
git clone https://github.com/ironfahad/projectcompressify.git
cd projectcompressify
pip install -e .
```

### Option 3: Docker
```bash
docker run -v $(pwd):/workspace ironfahad/compressify compress /workspace/input /workspace/output
```

## 🚀 Quick Start

### Basic Usage
```bash
# Compress a single video
compressify compress input.mp4 output/

# Compress all videos in a directory
compressify compress videos/ compressed/

# Interactive mode (recommended for beginners)
compressify interactive
```

### Video Compression Examples
```bash
# High quality compression
compressify compress input.mp4 output/ --profile high-quality

# Fast compression with H.265
compressify compress input.mp4 output/ --codec h265 --crf 28

# Compress to specific resolution
compressify compress input.mp4 output/ --resolution 1920x1080

# Custom bitrate
compressify compress input.mp4 output/ --bitrate 2M
```

### Image Compression Examples
```bash
# Compress images with 80% quality
compressify compress photos/ compressed/ --quality 80

# Convert to WebP format
compressify compress image.jpg output/ --format webp

# Batch process with custom quality
compressify compress images/ output/ --profile web-optimized
```

## 📖 Detailed Usage

### Command Line Interface

#### Compress Command
```bash
compressify compress INPUT OUTPUT [OPTIONS]
```

**Arguments:**
- `INPUT`: Input file or directory
- `OUTPUT`: Output directory

**Options:**
- `--profile`: Use predefined compression profile
- `--codec`: Video codec (h264, h265, vp9, av1)
- `--crf`: Constant Rate Factor (0-51, lower = higher quality)
- `--bitrate`: Target bitrate (e.g., "2M", "500k")
- `--resolution`: Target resolution (e.g., "1920x1080", "720p")
- `--quality`: Image quality (1-100)
- `--format`: Output format
- `--cpu-cores`: Number of CPU cores to use
- `--resume`: Resume interrupted job

#### Interactive Mode
```bash
compressify interactive
```
Launch the interactive wizard that guides you through the compression process.

#### Profile Management
```bash
# List available profiles
compressify profiles list

# Create new profile
compressify profiles create my-profile

# Use custom profile
compressify compress input/ output/ --profile my-profile
```

#### System Information
```bash
compressify info
```
Display system information and available codecs.

### Built-in Profiles

| Profile | Description | Best For |
|---------|-------------|----------|
| `high-quality` | Maximum quality, larger files | Archival, professional use |
| `balanced` | Good quality, reasonable size | General purpose |
| `web-optimized` | Optimized for web delivery | Streaming, web content |
| `mobile-friendly` | Small files, good on mobile | Mobile apps, limited bandwidth |
| `archive` | Lossless compression | Long-term storage |

## 🐳 Docker Usage

### Pull the Image
```bash
docker pull ironfahad/compressify
```

### Basic Usage
```bash
# Mount your files and compress
docker run -v /path/to/files:/workspace ironfahad/compressify compress /workspace/input /workspace/output
```

### Development Mode
```bash
docker-compose up -d
docker-compose exec compressify bash
```

## 🛠️ Development

### Setup Development Environment
```bash
git clone https://github.com/ironfahad/projectcompressify.git
cd projectcompressify
pip install -e ".[dev]"
```

### Run Tests
```bash
pytest tests/
```

### Code Quality
```bash
# Format code
black src/
isort src/

# Lint code
flake8 src/
mypy src/
```

### Build Docker Image
```bash
docker build -t compressify .
```

## 📋 Requirements

### System Requirements
- Python 3.11 or higher
- FFmpeg (for video processing)
- 2GB+ RAM recommended
- Multi-core CPU recommended

### Python Dependencies
- `typer[all]` - CLI framework
- `rich` - Beautiful terminal output
- `pydantic` - Data validation
- `pillow` - Image processing
- `pathlib` - Path handling

### Optional Dependencies
- `docker` - Containerized deployment
- `pytest` - Testing framework
- `black` - Code formatting

## 🎯 Use Cases

### Content Creators
- Compress videos for YouTube, TikTok, Instagram
- Batch process screen recordings
- Optimize images for social media

### Web Developers
- Optimize media assets for websites
- Convert images to modern formats (WebP, AVIF)
- Reduce page load times

### Archival & Storage
- Compress video archives while maintaining quality
- Reduce storage costs
- Prepare files for cloud backup

### Mobile App Development
- Optimize media for mobile apps
- Reduce app bundle sizes
- Improve app performance

## 📊 Performance

### Benchmarks
- **Video**: Up to 70% size reduction with minimal quality loss
- **Images**: Up to 85% size reduction with WebP/AVIF formats
- **Speed**: Multi-threaded processing utilizes all CPU cores
- **Memory**: Efficient processing of large files

### Optimization Tips
1. Use appropriate profiles for your use case
2. Enable hardware acceleration when available
3. Adjust CPU core usage based on your system
4. Use resume functionality for large jobs

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new features
5. Ensure all tests pass
6. Submit a pull request

### Reporting Issues
- Use GitHub Issues for bug reports
- Include system information and error logs
- Provide sample files when possible

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **FFmpeg** - The backbone of video processing
- **Pillow** - Powerful image processing library
- **Rich** - Beautiful terminal interfaces
- **Typer** - Modern CLI framework

## 🔗 Links

- [Documentation](https://github.com/ironfahad/projectcompressify/wiki)
- [Issue Tracker](https://github.com/ironfahad/projectcompressify/issues)
- [Discussions](https://github.com/ironfahad/projectcompressify/discussions)
- [Docker Hub](https://hub.docker.com/r/ironfahad/compressify)

## 📈 Roadmap

### Upcoming Features
- [ ] GUI application
- [ ] Hardware acceleration (GPU support)
- [ ] Cloud processing integration
- [ ] Advanced video filters
- [ ] Subtitle preservation
- [ ] Metadata management
- [ ] Plugin system
- [ ] API server mode

### Version History
- **v1.0.0** - Initial release with core compression features
- **v1.1.0** - Added profile management and interactive mode
- **v1.2.0** - Docker support and performance improvements

---

Made with ❤️ by [Fahad](https://github.com/ironfahad)