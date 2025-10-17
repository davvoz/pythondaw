"""
Visual test to verify track volumes are applied correctly
"""
import sys
from pathlib import Path
import math

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from core.timeline import Timeline
from audio.clip import AudioClip
from audio.engine import AudioEngine

def create_sample_audio(amplitude: float, duration: float, sample_rate: int = 44100):
    """Generate a constant amplitude signal for testing."""
    num_samples = int(duration * sample_rate)
    return [amplitude] * num_samples

print("=" * 70)
print("VISUAL TEST: Track Volume Application")
print("=" * 70)

# Setup
sample_rate = 44100
timeline = Timeline()

# Create 3 clips with CONSTANT amplitude of 1.0 on different tracks
# Track 0: volume 1.0
# Track 1: volume 0.5
# Track 2: volume 0.25

buffer = create_sample_audio(1.0, 0.5, sample_rate)  # 0.5 seconds at amplitude 1.0

clip1 = AudioClip("Track0_Clip", buffer, sample_rate, start_time=0.0)
timeline.add_clip(0, clip1)

clip2 = AudioClip("Track1_Clip", buffer, sample_rate, start_time=0.6)
timeline.add_clip(1, clip2)

clip3 = AudioClip("Track2_Clip", buffer, sample_rate, start_time=1.2)
timeline.add_clip(2, clip3)

print("\n📋 Test Setup:")
print("   - 3 clips, each with constant amplitude = 1.0")
print("   - Clip 1 on track 0 (0.0-0.5s)")
print("   - Clip 2 on track 1 (0.6-1.1s)")
print("   - Clip 3 on track 2 (1.2-1.7s)")

# Test 1: Without volumes
print("\n🔍 Test 1: Render WITHOUT track volumes")
engine = AudioEngine()
engine.initialize()

audio_no_vol = engine.render_window(timeline, 0.0, 2.0, sample_rate, track_volumes=None)

# Sample at middle of each clip
sample1_no_vol = audio_no_vol[int(0.25 * sample_rate)]  # Middle of clip 1
sample2_no_vol = audio_no_vol[int(0.85 * sample_rate)]  # Middle of clip 2
sample3_no_vol = audio_no_vol[int(1.45 * sample_rate)]  # Middle of clip 3

print(f"   Sample from clip 1 (track 0): {sample1_no_vol:.4f} (expected: 1.0)")
print(f"   Sample from clip 2 (track 1): {sample2_no_vol:.4f} (expected: 1.0)")
print(f"   Sample from clip 3 (track 2): {sample3_no_vol:.4f} (expected: 1.0)")

# Test 2: With volumes
print("\n🔍 Test 2: Render WITH track volumes")
track_volumes = {0: 1.0, 1: 0.5, 2: 0.25}
print(f"   Track volumes: {track_volumes}")

audio_with_vol = engine.render_window(timeline, 0.0, 2.0, sample_rate, track_volumes=track_volumes)

# Sample at middle of each clip
sample1_with_vol = audio_with_vol[int(0.25 * sample_rate)]  # Middle of clip 1
sample2_with_vol = audio_with_vol[int(0.85 * sample_rate)]  # Middle of clip 2
sample3_with_vol = audio_with_vol[int(1.45 * sample_rate)]  # Middle of clip 3

print(f"   Sample from clip 1 (track 0, vol=1.0):  {sample1_with_vol:.4f} (expected: 1.0)")
print(f"   Sample from clip 2 (track 1, vol=0.5):  {sample2_with_vol:.4f} (expected: 0.5)")
print(f"   Sample from clip 3 (track 2, vol=0.25): {sample3_with_vol:.4f} (expected: 0.25)")

# Verification
print("\n✅ Verification:")
tolerance = 0.01

test1_pass = abs(sample1_with_vol - 1.0) < tolerance
test2_pass = abs(sample2_with_vol - 0.5) < tolerance
test3_pass = abs(sample3_with_vol - 0.25) < tolerance

print(f"   {'✓' if test1_pass else '✗'} Track 0 volume (1.0):  {sample1_with_vol:.4f}")
print(f"   {'✓' if test2_pass else '✗'} Track 1 volume (0.5):  {sample2_with_vol:.4f}")
print(f"   {'✓' if test3_pass else '✗'} Track 2 volume (0.25): {sample3_with_vol:.4f}")

if test1_pass and test2_pass and test3_pass:
    print("\n🎉 SUCCESS! Track volumes are applied correctly!")
else:
    print("\n❌ FAILURE! Track volumes are NOT applied correctly!")

print("\n" + "=" * 70)
