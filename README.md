# Digital Audio Workstation (DAW)

This project is a scalable and object-oriented Digital Audio Workstation (DAW) built in Python. It provides a comprehensive framework for audio production, including features for managing projects, tracks, audio processing, effects, MIDI handling, and a user interface.

## Features

- **Project Management**: Create, save, and manage audio projects with multiple tracks.
- **💾 Project Save/Load**: Save complete projects with audio samples and restore everything
- **Track Handling**: Add and remove audio tracks, adjust volume, and manage audio data.
- **🎵 Multi-Format Audio Import**: Load WAV, MP3, FLAC, OGG, AAC, M4A files with automatic conversion
- **Audio Browser**: Browse and preview audio files before importing
- **Recent Files**: Quick access to recently imported audio files
- **🔁 Loop Duplication**: Duplicate entire loop regions with a single keystroke (Ctrl+D)
- **📋 Multi-Selection & Copy/Paste**: Select multiple clips, copy and paste with full property preservation
- **✂️ Advanced Clipboard**: Copy/paste individual clips or entire loop regions
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
from src.core.project import Project
from src.core.track import Track
from src.audio.clip import AudioClip
from src.utils.audio_io import load_audio_file

# Create a new project
project = Project(name="My Song", bpm=128.0, time_signature=(4, 4))

# Load and add audio
buffer, sr = load_audio_file("kick.wav")
clip = AudioClip("Kick", buffer, sr, start_time=0.0)

track = Track()
track.add_audio(clip)
project.create_track(track)

# Save the project (with separate audio files)
project.save_project("my_song.daw", embed_audio=False)

# Load the project later
loaded_project = Project.load_project("my_song.daw")
print(f"Loaded: {loaded_project.name} with {len(loaded_project.tracks)} tracks")
```

For more examples, see the `examples/` directory.

## Documentation

- **[Project Save/Load Guide](docs/PROJECT_SAVE_LOAD.md)** - Complete guide for saving and loading projects
- **[Audio Import Guide](docs/AUDIO_IMPORT.md)** - Complete guide for importing audio files
- **[Audio Import Summary](docs/AUDIO_IMPORT_SUMMARY.md)** - Technical details of the import system
- **[Duplicate Loop](docs/DUPLICATE_LOOP.md)** - Guide for duplicating loop regions
- **[Multi-Selection & Copy/Paste](docs/MULTI_SELECTION.md)** - Guide for multi-selection and clipboard operations
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

### 🎨 Professional Clip Inspector (Latest)
- **Interactive waveform display** with real-time visualization
- **Visual editing with draggable handles** for trim and fade controls
- **User-friendly interface** for professional audio editing
- **Zoom and pan** support for detailed waveform inspection
- **Real-time preview** of all modifications
- **Professional color-coded UI** with clear visual feedback
- **Multiple fade shapes** (Linear, Exponential, Logarithmic, S-Curve)

See [CLIP_INSPECTOR_GUIDE.md](python-daw/CLIP_INSPECTOR_GUIDE.md) for complete documentation.

### 💾 Project Save/Load System
- **Save complete projects** including all audio samples
- **Two modes**: Separate files (recommended) or embedded audio
- **Full property preservation**: All clip properties, fades, effects, etc.
- **Smart file management**: Organized project structure with audio folder
- **Format**: JSON + WAV files for maximum compatibility
- **Easy backup**: Simple file-based project management

## Per-track Effects Chain

Tracks now include an optional, extensible effects chain that applies **during both playback AND export**.

### How to Use

**In the UI:**
1. Click the **FX** button (purple) next to any track in the sidebar
2. In the Effects Chain dialog:
   - **➕ Add Effect** - Choose from Reverb, Delay, Compressor, or EQ
   - **Select** an effect to adjust its **Wet/Dry** mix (0-100%)
   - **Bypass** checkbox to temporarily disable an effect
   - **▲/▼** buttons to reorder effects in the chain
   - **🗑 Remove** to delete selected effect
3. Effects are applied **automatically** during:
   - ▶️ **Real-time playback** (you hear them immediately!)
   - 💾 **Export** (single track or master mix)

**Programmatically:**

```python
from src.core.project import Project
from src.core.track import Track
from src.effects.reverb import Reverb
from src.effects.delay import Delay

project = Project()
track = Track("Lead")
project.create_track(track)

# Add reverb (30% wet)
track.add_effect(Reverb(), wet=0.3)

# Add delay with custom settings
slap = Delay()
slap.set_parameters({"delay_time": 0.25, "feedback": 0.4, "mix": 0.6})
track.add_effect(slap, name="Slap Delay", wet=0.5)

# Bypass an effect
track.effects.slots[0].bypass = True

# Reorder effects (move index 1 to position 0)
track.move_effect(1, 0)

# Effects apply automatically during playback AND export
# Just pass project=project to TimelinePlayer and render_window()
```

### Technical Details

- Each effect must implement `apply(audio_data: List[float]) -> List[float]` (see `src/effects/base.py`)
- Effects are processed **before** track volume and mixing
- **Real-time playback**: Effects are applied in the audio callback (per-track buffering)
- **Export/Rendering**: Same per-track logic in `AudioEngine.render_window()`
- Projects save/load the complete effects configuration (type, wet, bypass, parameters)
- Available effects: **Reverb**, **Delay**, **Compressor**, **Equalizer**
- Easily extensible - add new effects by subclassing `BaseEffect`

See `examples/effects_chain_example.py` for a complete demonstration.


See [docs/PROJECT_SAVE_LOAD.md](docs/PROJECT_SAVE_LOAD.md) for complete documentation.

### 📋 Multi-Selection and Copy/Paste
- **Multi-select clips** with **Ctrl+Click**
- **Copy/paste clips** with **Ctrl+C / Ctrl+V**
- **Copy/paste loop regions** with **Ctrl+Shift+C / Ctrl+Shift+V**
- **Delete multiple clips** with **Delete** key
- Context menu support for multi-selection
- Full property preservation (fades, pitch, volume, trim, etc.)
- Maintains relative timing when pasting multiple clips

See [docs/MULTI_SELECTION.md](docs/MULTI_SELECTION.md) for details.

### 🔁 Loop Duplication Feature
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