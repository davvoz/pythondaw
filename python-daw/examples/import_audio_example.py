"""
Example: How to Import Audio Files in Python DAW

This example demonstrates the new audio import capabilities.
"""

from src.core.project import Project
from src.core.timeline import Timeline
from src.audio.mixer import Mixer
from src.audio.player import TimelinePlayer
from src.utils.audio_io import load_audio_file, get_audio_info
from src.audio.clip import AudioClip

# Initialize DAW components
project = Project("My Audio Project")
timeline = Timeline()
mixer = Mixer()

# Add some tracks
mixer.add_track("Drums", volume=0.8, pan=0.0, color="#ef4444")
mixer.add_track("Bass", volume=0.7, pan=-0.3, color="#3b82f6")
mixer.add_track("Guitar", volume=0.6, pan=0.3, color="#10b981")

print("=" * 60)
print("AUDIO IMPORT EXAMPLE")
print("=" * 60)
print()

# Example 1: Get info about a file before loading
print("1. Getting file information:")
print("-" * 60)

example_file = "your_audio_file.wav"  # Replace with your file

try:
    info = get_audio_info(example_file)
    print(f"File: {example_file}")
    print(f"Duration: {info.get('duration', 0):.2f} seconds")
    print(f"Sample Rate: {info.get('sample_rate', 0)} Hz")
    print(f"Channels: {info.get('channels', 0)}")
    print(f"Format: {info.get('format', 'Unknown')}")
except FileNotFoundError:
    print(f"File not found: {example_file}")
    print("Replace 'your_audio_file.wav' with an actual audio file path")
except Exception as e:
    print(f"Error: {e}")

print()

# Example 2: Load audio file
print("2. Loading audio file:")
print("-" * 60)

try:
    # Load with automatic conversion to 44100 Hz
    buffer, sample_rate = load_audio_file(example_file, target_sr=44100)
    
    print(f"✓ Loaded successfully")
    print(f"Samples: {len(buffer):,}")
    print(f"Sample Rate: {sample_rate} Hz")
    print(f"Duration: {len(buffer)/sample_rate:.2f} seconds")
    
    # Example 3: Create clip and add to timeline
    print()
    print("3. Adding to timeline:")
    print("-" * 60)
    
    clip = AudioClip(
        name="My Audio Clip",
        buffer=buffer,
        sample_rate=sample_rate,
        start_time=0.0,  # Start at beginning
        file_path=example_file
    )
    
    # Add to track 0 (Drums)
    timeline.add_clip(0, clip)
    
    print(f"✓ Clip added to track 0 (Drums)")
    print(f"Clip name: {clip.name}")
    print(f"Start time: {clip.start_time}s")
    print(f"End time: {clip.end_time:.2f}s")
    print(f"Duration: {clip.length_seconds:.2f}s")
    
except FileNotFoundError:
    print(f"File not found: {example_file}")
except Exception as e:
    print(f"Error: {e}")

print()

# Example 4: Load multiple files
print("4. Loading multiple files:")
print("-" * 60)

audio_files = [
    "kick.wav",
    "snare.wav",
    "hihat.wav",
]

for i, filename in enumerate(audio_files):
    try:
        buffer, sr = load_audio_file(filename, target_sr=44100)
        
        clip = AudioClip(
            name=filename.replace(".wav", ""),
            buffer=buffer,
            sample_rate=sr,
            start_time=i * 1.0,  # Offset each by 1 second
            file_path=filename
        )
        
        timeline.add_clip(0, clip)
        print(f"✓ Loaded {filename} ({len(buffer):,} samples)")
        
    except FileNotFoundError:
        print(f"⚠ File not found: {filename}")
    except Exception as e:
        print(f"✗ Error loading {filename}: {e}")

print()

# Example 5: Check timeline contents
print("5. Timeline summary:")
print("-" * 60)

total_clips = len(list(timeline.all_placements()))
print(f"Total clips in timeline: {total_clips}")

for track_idx in range(len(mixer.tracks)):
    clips = timeline.get_clips_for_track(track_idx)
    track_name = mixer.tracks[track_idx]['name']
    print(f"  Track {track_idx} ({track_name}): {len(clips)} clips")

print()
print("=" * 60)
print("Example complete!")
print()
print("To use in the GUI:")
print("  1. Run: python src/main.py")
print("  2. Select a track")
print("  3. File → Import Audio (Ctrl+I)")
print("  4. Choose your audio file")
print("=" * 60)
