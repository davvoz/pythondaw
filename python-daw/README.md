# Digital Audio Workstation (DAW)

This project is a scalable and object-oriented Digital Audio Workstation (DAW) built in Python. It provides a comprehensive framework for audio production, including features for managing projects, tracks, audio processing, effects, MIDI handling, and a user interface.

## Features

- **Project Management**: Create, save, and manage audio projects with multiple tracks.
- **Track Handling**: Add and remove audio tracks, adjust volume, and manage audio data.
- **🎵 Multi-Format Audio Import**: Load WAV, MP3, FLAC, OGG, AAC, M4A files with automatic conversion
- **Audio Browser**: Browse and preview audio files before importing
- **Recent Files**: Quick access to recently imported audio files
- **🔁 Loop Duplication**: Duplicate entire loop regions with a single keystroke (Ctrl+D)
- **Audio Processing**: Apply various audio effects such as reverb, delay, compression, and equalization.
- **MIDI Support**: Handle MIDI messages and sequences for instrument control.
- **User Interface**: A simple and intuitive UI for managing playback and mixing.

## Project Structure

```
python-daw
├── src
│   ├── main.py
│   ├── core
│   ├── audio
│   ├── effects
│   ├── instruments
│   ├── midi
│   ├── ui
│   └── utils
├── tests
├── requirements.txt
├── setup.py
└── README.md
```

## Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   ```

2. Navigate to the project directory:
   ```bash
   cd python-daw
   ```

3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. **Optional**: Install audio format support:
   ```bash
   # For WAV, FLAC, OGG support (recommended)
   pip install soundfile
   
   # For MP3, AAC, M4A support
   pip install pydub
   
   # Install both for maximum format support
   pip install soundfile pydub
   ```

   **Note**: For MP3 support, you'll also need `ffmpeg` installed on your system:
   - **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/)
   - **Linux**: `sudo apt install ffmpeg`
   - **macOS**: `brew install ffmpeg`

## Usage

### Starting the Application

To start the DAW, run:
```bash
python src/main.py
```

### Importing Audio Files

The DAW supports multiple methods to import your audio files:

#### Method 1: Quick Import
1. Select a track in the sidebar
2. Go to **File → Import Audio** (or press `Ctrl+I`)
3. Choose your audio file
4. The file will be loaded onto the selected track

#### Method 2: Audio Browser
1. Go to **File → Browse Audio Files** (or press `Ctrl+B`)
2. Navigate to your audio folder
3. Preview file information
4. Double-click or press "Import" to load

#### Method 3: Recent Files
1. Go to **File → Recent Files**
2. Select a recently imported file
3. File will be loaded automatically

### Supported Audio Formats

- **WAV** (.wav) - Uncompressed, high quality
- **FLAC** (.flac) - Lossless compression
- **OGG** (.ogg) - Open source format
- **MP3** (.mp3) - Universal format
- **AAC** (.aac) - High quality compression
- **M4A** (.m4a) - Apple audio format

### Example Code

```python
from src.utils.audio_io import load_audio_file, get_audio_info

# Get file information
info = get_audio_info("my_sound.wav")
print(f"Duration: {info['duration']:.2f}s")
print(f"Sample rate: {info['sample_rate']}Hz")

# Load audio file
buffer, sample_rate = load_audio_file("my_sound.wav", target_sr=44100)
print(f"Loaded {len(buffer)} samples")
```

For more examples, see the `examples/` directory.

## Documentation

- **[Audio Import Guide](docs/AUDIO_IMPORT.md)** - Complete guide for importing audio files
- **[Audio Import Summary](docs/AUDIO_IMPORT_SUMMARY.md)** - Technical details of the import system
- **[Duplicate Loop](docs/DUPLICATE_LOOP.md)** - Guide for duplicating loop regions
- **[Examples](examples/)** - Code examples and tutorials

## Testing

Run the audio import test:
```bash
cd tests
python test_audio_import.py

# Test with a specific file
python test_audio_import.py your_file.wav
```

Run all unit tests:
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

## Recent Updates

### 🔁 Loop Duplication Feature (Latest)
- Duplicate entire loop regions with **Ctrl+D**
- Preserves relative timing and clip positioning
- Available via Edit menu or keyboard shortcut
- Perfect for building arrangements and creating patterns

See [docs/DUPLICATE_LOOP.md](docs/DUPLICATE_LOOP.md) for details.

### ✨ Audio Import System
- Multi-format support (WAV, MP3, FLAC, OGG, AAC, M4A)
- Audio file browser with preview
- Recent files tracking
- Smart audio conversion (mono, resampling, normalization)
- Comprehensive error handling

For detailed information, see [docs/AUDIO_IMPORT.md](docs/AUDIO_IMPORT.md)