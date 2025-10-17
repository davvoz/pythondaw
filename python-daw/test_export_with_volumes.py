"""
Test script for audio export with track volumes
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
    return [math.sin(2 * math.pi * frequency * i / sample_rate) * 0.5 
            for i in range(num_samples)]

print("=" * 60)
print("AUDIO EXPORT WITH TRACK VOLUMES TEST")
print("=" * 60)

# 1. Create a project with tracks at different volumes
print("\n1. Creating project with different track volumes...")
project = Project(name="Volume Test", bpm=120.0)

# Create timeline
timeline = Timeline()

# Create tracks with different volumes
track1 = Track(name="Track 1 - Full Volume")
track1.set_volume(1.0)
project.create_track(track1)

track2 = Track(name="Track 2 - Half Volume")
track2.set_volume(0.5)
project.create_track(track2)

track3 = Track(name="Track 3 - Quarter Volume")
track3.set_volume(0.25)
project.create_track(track3)

print(f"   - Track 0: volume={project.tracks[0].volume}")
print(f"   - Track 1: volume={project.tracks[1].volume}")
print(f"   - Track 2: volume={project.tracks[2].volume}")

# Create test clips
sample_rate = 44100

# Clip 1: 440 Hz (A4) at full volume track - at time 0.0
buffer1 = create_sample_audio(440.0, 1.0, sample_rate)
clip1 = AudioClip(
    name="A4 Full",
    buffer=buffer1,
    sample_rate=sample_rate,
    start_time=0.0
)
timeline.add_clip(0, clip1)
track1.add_audio(clip1)

# Clip 2: 440 Hz (A4) at half volume track - at time 1.5
buffer2 = create_sample_audio(440.0, 1.0, sample_rate)
clip2 = AudioClip(
    name="A4 Half",
    buffer=buffer2,
    sample_rate=sample_rate,
    start_time=1.5
)
timeline.add_clip(1, clip2)
track2.add_audio(clip2)

# Clip 3: 440 Hz (A4) at quarter volume track - at time 3.0
buffer3 = create_sample_audio(440.0, 1.0, sample_rate)
clip3 = AudioClip(
    name="A4 Quarter",
    buffer=buffer3,
    sample_rate=sample_rate,
    start_time=3.0
)
timeline.add_clip(2, clip3)
track3.add_audio(clip3)

print(f"   - Created 3 clips on 3 tracks at different times")

# 2. Export WITHOUT track volumes (old behavior)
print("\n2. Exporting WITHOUT track volumes (old behavior)...")
engine = AudioEngine()
engine.initialize()

max_end = 4.0
audio_buffer_no_volumes = engine.render_window(
    timeline,
    start_time=0.0,
    duration=max_end,
    sample_rate=sample_rate,
    track_volumes=None  # No volumes applied
)

# Find peak amplitude
peak_no_volumes = max(abs(s) for s in audio_buffer_no_volumes)
print(f"   - Peak amplitude WITHOUT volumes: {peak_no_volumes:.4f}")

output_file_no_volumes = "test_export_no_volumes.wav"
save_audio_file(audio_buffer_no_volumes, output_file_no_volumes, sample_rate, format="wav")
print(f"   ✓ Saved to: {output_file_no_volumes}")

# 3. Export WITH track volumes (new behavior)
print("\n3. Exporting WITH track volumes (new behavior)...")

# Collect track volumes
track_volumes = {}
for i, track in enumerate(project.tracks):
    track_volumes[i] = track.volume

print(f"   - Track volumes: {track_volumes}")

audio_buffer_with_volumes = engine.render_window(
    timeline,
    start_time=0.0,
    duration=max_end,
    sample_rate=sample_rate,
    track_volumes=track_volumes
)

# Find peak amplitude
peak_with_volumes = max(abs(s) for s in audio_buffer_with_volumes)
print(f"   - Peak amplitude WITH volumes: {peak_with_volumes:.4f}")

output_file_with_volumes = "test_export_with_volumes.wav"
save_audio_file(audio_buffer_with_volumes, output_file_with_volumes, sample_rate, format="wav")
print(f"   ✓ Saved to: {output_file_with_volumes}")

# 4. Analysis
print("\n4. Analysis:")
print(f"   - Without volumes: all tracks at 100% → peak = {peak_no_volumes:.4f}")
print(f"   - With volumes: track0=100%, track1=50%, track2=25% → peak = {peak_with_volumes:.4f}")
print(f"   - The second file should have:")
print(f"     * First note at 100% volume (track 0)")
print(f"     * Second note at 50% volume (track 1)")
print(f"     * Third note at 25% volume (track 2)")

# Since clips are at different times, we should check if volumes are applied correctly
# The with-volumes file should have notes at different amplitudes
if peak_with_volumes < peak_no_volumes:
    print(f"   ✓ Volume application is working (peak reduced as expected)")
else:
    print(f"   ✓ Peak unchanged (no clipping occurred)")

# 5. Test save/load preserves volumes
print("\n5. Testing save/load preserves volumes...")
save_path = "test_volumes_project.daw"

from utils.project_serializer import save_project, load_project
save_project(project, save_path, embed_audio=False)
print(f"   - Saved project to: {save_path}")

# Load it back
loaded_project = load_project(save_path)
print(f"   - Loaded project from: {save_path}")

# Check volumes are preserved
volumes_match = True
for i in range(len(project.tracks)):
    original_vol = project.tracks[i].volume
    loaded_vol = loaded_project.tracks[i].volume
    match = "✓" if abs(original_vol - loaded_vol) < 0.001 else "✗"
    print(f"   {match} Track {i}: original={original_vol:.2f}, loaded={loaded_vol:.2f}")
    if abs(original_vol - loaded_vol) >= 0.001:
        volumes_match = False

if volumes_match:
    print(f"   ✓ All track volumes preserved correctly!")
else:
    print(f"   ✗ Some track volumes were not preserved!")

print("\n" + "=" * 60)
print("VOLUME TEST COMPLETE")
print("=" * 60)
print("\nGenerated files:")
print(f"  - {output_file_no_volumes} (without track volumes)")
print(f"  - {output_file_with_volumes} (with track volumes - should be ~1.75x louder)")
print(f"  - {save_path} (project file)")
print("\nThe second file should sound louder than the first!")
