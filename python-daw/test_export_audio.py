"""
Test script for audio export functionality
"""
import sys
from pathlib import Path
import math

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from core.project import Project
from core.track import Track
from core.timeline import Timeline
from audio.clip import AudioClip
from audio.engine import AudioEngine
from utils.audio_io import save_audio_file

def create_sample_audio(frequency: float, duration: float, sample_rate: int = 44100):
    """Generate a sine wave for testing."""
    num_samples = int(duration * sample_rate)
    return [math.sin(2 * math.pi * frequency * i / sample_rate) * 0.3 
            for i in range(num_samples)]

print("=" * 60)
print("AUDIO EXPORT TEST")
print("=" * 60)

# 1. Create a project with some clips
print("\n1. Creating project with audio clips...")
project = Project(name="Export Test", bpm=120.0)

# Create timeline
timeline = Timeline()

# Create some test clips
sample_rate = 44100

# Clip 1: 440 Hz (A4) for 2 seconds at position 0
buffer1 = create_sample_audio(440.0, 2.0, sample_rate)
clip1 = AudioClip(
    name="A4 Note",
    buffer=buffer1,
    sample_rate=sample_rate,
    start_time=0.0
)
timeline.add_clip(0, clip1)

# Clip 2: 523.25 Hz (C5) for 1.5 seconds at position 1.5
buffer2 = create_sample_audio(523.25, 1.5, sample_rate)
clip2 = AudioClip(
    name="C5 Note",
    buffer=buffer2,
    sample_rate=sample_rate,
    start_time=1.5
)
timeline.add_clip(0, clip2)

# Clip 3: 329.63 Hz (E4) for 1 second at position 3.5
buffer3 = create_sample_audio(329.63, 1.0, sample_rate)
clip3 = AudioClip(
    name="E4 Note",
    buffer=buffer3,
    sample_rate=sample_rate,
    start_time=3.5
)
timeline.add_clip(1, clip3)

print(f"   - Created 3 clips")
print(f"   - Clip 1: A4 (440 Hz) at 0.0s, duration 2.0s")
print(f"   - Clip 2: C5 (523 Hz) at 1.5s, duration 1.5s")
print(f"   - Clip 3: E4 (330 Hz) at 3.5s, duration 1.0s")

# 2. Export full song
print("\n2. Exporting full song...")
engine = AudioEngine()
engine.initialize()

# Find the extent of all clips
max_end = 0.0
for track_idx, clip in timeline.all_placements():
    if hasattr(clip, 'end_time'):
        max_end = max(max_end, clip.end_time)

print(f"   - Timeline duration: 0.0s to {max_end:.2f}s")

# Render the audio
audio_buffer = engine.render_window(
    timeline,
    start_time=0.0,
    duration=max_end,
    sample_rate=sample_rate
)

print(f"   - Rendered {len(audio_buffer):,} samples")
print(f"   - Duration: {len(audio_buffer) / sample_rate:.2f}s")

# Save to file
output_file = "test_export_full.wav"
save_audio_file(audio_buffer, output_file, sample_rate, format="wav")
print(f"   ✓ Saved to: {output_file}")

import os
file_size = os.path.getsize(output_file) / 1024
print(f"   - File size: {file_size:.1f} KB")

# 3. Export loop region (e.g., from 1.0s to 3.0s)
print("\n3. Exporting loop region (1.0s to 3.0s)...")
loop_start = 1.0
loop_end = 3.0
loop_duration = loop_end - loop_start

audio_buffer_loop = engine.render_window(
    timeline,
    start_time=loop_start,
    duration=loop_duration,
    sample_rate=sample_rate
)

print(f"   - Rendered {len(audio_buffer_loop):,} samples")
print(f"   - Duration: {len(audio_buffer_loop) / sample_rate:.2f}s")

# Save to file
output_file_loop = "test_export_loop.wav"
save_audio_file(audio_buffer_loop, output_file_loop, sample_rate, format="wav")
print(f"   ✓ Saved to: {output_file_loop}")

file_size_loop = os.path.getsize(output_file_loop) / 1024
print(f"   - File size: {file_size_loop:.1f} KB")

print("\n" + "=" * 60)
print("EXPORT TEST COMPLETE")
print("=" * 60)
print("\nGenerated files:")
print(f"  - {output_file} (full song)")
print(f"  - {output_file_loop} (loop region)")
print("\nYou can play these files with any audio player to verify the export.")
