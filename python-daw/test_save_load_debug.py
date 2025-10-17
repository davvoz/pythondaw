"""
Debug script to test save/load functionality
"""
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from core.project import Project
from core.track import Track
from audio.clip import AudioClip
from utils.project_serializer import save_project, load_project
import math

def create_sample_audio(frequency: float, duration: float, sample_rate: int = 44100):
    """Generate a sine wave for testing."""
    num_samples = int(duration * sample_rate)
    return [math.sin(2 * math.pi * frequency * i / sample_rate) 
            for i in range(num_samples)]

print("=" * 60)
print("DEBUG: Save/Load Test")
print("=" * 60)

# 1. Create a project
print("\n1. Creating project...")
project = Project(name="Test Project", bpm=128.0, time_signature=(4, 4))

# 2. Create tracks
print("2. Creating tracks...")
track1 = Track(name="Bass Track")
track1.set_volume(0.8)

track2 = Track(name="Lead Track")
track2.set_volume(0.6)

# 3. Create clips
print("3. Creating clips...")
buffer1 = create_sample_audio(440.0, 2.0)  # A4 for 2 seconds
clip1 = AudioClip(
    name="Bass Clip",
    buffer=buffer1,
    sample_rate=44100,
    start_time=0.0,
    color="#FF6B6B"
)
clip1.volume = 0.9

buffer2 = create_sample_audio(523.25, 1.5)  # C5 for 1.5 seconds
clip2 = AudioClip(
    name="Lead Clip",
    buffer=buffer2,
    sample_rate=44100,
    start_time=2.0,
    color="#4ECDC4"
)

# 4. Add clips to tracks
print("4. Adding clips to tracks...")
track1.add_audio(clip1)
track2.add_audio(clip2)

print(f"   Track1 has {len(track1.audio_files)} clips")
print(f"   Track2 has {len(track2.audio_files)} clips")

# 5. Add tracks to project
print("5. Adding tracks to project...")
project.create_track(track1)
project.create_track(track2)

print(f"   Project has {len(project.tracks)} tracks")
for i, track in enumerate(project.tracks):
    print(f"   Track {i}: '{track.name}' with {len(track.audio_files)} clips")

# 6. Save project
print("\n6. Saving project...")
save_path = "test_debug.daw"
save_project(project, save_path, embed_audio=False)

# 7. Check saved file
print("\n7. Checking saved file...")
import json
with open(save_path, 'r') as f:
    saved_data = json.load(f)

print(f"   Project name: {saved_data['project']['name']}")
print(f"   Number of tracks: {len(saved_data['project']['tracks'])}")
for i, track_data in enumerate(saved_data['project']['tracks']):
    print(f"   Track {i}: '{track_data['name']}' with {len(track_data['clips'])} clips")
    for j, clip_data in enumerate(track_data['clips']):
        print(f"      Clip {j}: '{clip_data['name']}' at {clip_data['start_time']}s")

# 8. Load project back
print("\n8. Loading project...")
loaded_project = load_project(save_path)

print(f"   Loaded project name: {loaded_project.name}")
print(f"   Loaded project has {len(loaded_project.tracks)} tracks")
for i, track in enumerate(loaded_project.tracks):
    print(f"   Track {i}: '{track.name}' with {len(track.audio_files)} clips, volume={track.volume}")
    for j, clip in enumerate(track.audio_files):
        print(f"      Clip {j}: '{clip.name}' at {clip.start_time}s, buffer={len(clip.buffer)} samples")

# 9. Verification
print("\n9. Verification...")
success = True

if len(loaded_project.tracks) != 2:
    print("   ❌ FAIL: Expected 2 tracks, got", len(loaded_project.tracks))
    success = False
else:
    print("   ✓ PASS: Track count correct")

if len(loaded_project.tracks[0].audio_files) != 1:
    print(f"   ❌ FAIL: Track 0 should have 1 clip, got {len(loaded_project.tracks[0].audio_files)}")
    success = False
else:
    print("   ✓ PASS: Track 0 clip count correct")

if len(loaded_project.tracks[1].audio_files) != 1:
    print(f"   ❌ FAIL: Track 1 should have 1 clip, got {len(loaded_project.tracks[1].audio_files)}")
    success = False
else:
    print("   ✓ PASS: Track 1 clip count correct")

if loaded_project.tracks[0].audio_files:
    clip = loaded_project.tracks[0].audio_files[0]
    if len(clip.buffer) == 0:
        print(f"   ❌ FAIL: Clip buffer is empty")
        success = False
    else:
        print(f"   ✓ PASS: Clip buffer loaded ({len(clip.buffer)} samples)")

print("\n" + "=" * 60)
if success:
    print("✓ ALL TESTS PASSED")
else:
    print("❌ SOME TESTS FAILED")
print("=" * 60)
