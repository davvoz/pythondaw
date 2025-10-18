"""
Test script to verify that effects are actually applied during rendering.
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
from effects.reverb import Reverb
from effects.delay import Delay
from utils.audio_io import save_audio_file


def create_test_tone(frequency: float, duration: float, sample_rate: int = 44100):
    """Generate a simple sine wave."""
    num_samples = int(duration * sample_rate)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        sample = 0.3 * math.sin(2.0 * math.pi * frequency * t)
        samples.append(sample)
    return samples


def analyze_audio(buffer, name=""):
    """Print basic audio statistics."""
    if not buffer:
        print(f"  {name}: Empty buffer")
        return
    
    min_val = min(buffer)
    max_val = max(buffer)
    avg_val = sum(abs(s) for s in buffer) / len(buffer)
    
    print(f"  {name}:")
    print(f"    Length: {len(buffer)} samples")
    print(f"    Min: {min_val:.4f}, Max: {max_val:.4f}")
    print(f"    Avg Amplitude: {avg_val:.4f}")


print("=" * 60)
print("EFFECTS RENDERING TEST")
print("=" * 60)

# 1. Create project with timeline
print("\n1. Creating project...")
project = Project(name="FX Test", bpm=120.0)
timeline = Timeline()

# 2. Create track with audio
print("\n2. Creating track with test tone...")
track = Track(name="Test Track")
track.set_volume(1.0)

# Add a 1-second 440Hz tone
tone = create_test_tone(440.0, 1.0, 44100)
clip = AudioClip("Tone", tone, 44100, start_time=0.0)
track.add_audio(clip)
timeline.add_clip(0, clip)

project.create_track(track)

# 3. Render WITHOUT effects
print("\n3. Rendering WITHOUT effects...")
engine = AudioEngine()
engine.initialize()

buffer_no_fx = engine.render_window(
    timeline,
    start_time=0.0,
    duration=1.0,
    sample_rate=44100,
    track_volumes={0: 1.0},
    project=project  # Pass project but no effects yet
)

analyze_audio(buffer_no_fx, "No Effects")

# 4. Add reverb effect
print("\n4. Adding Reverb effect (wet=0.5)...")
reverb = Reverb()
reverb.set_parameters({
    "room_size": 0.8,
    "damping": 0.5,
    "wet_level": 0.5,
    "dry_level": 0.5
})
idx = track.add_effect(reverb, name="Test Reverb", wet=0.5)
print(f"   Added effect at slot {idx}")
print(f"   Track effects: {track.effects}")
print(f"   Slots: {track.effects.slots if track.effects else 'None'}")

# 5. Render WITH effects
print("\n5. Rendering WITH effects...")
buffer_with_fx = engine.render_window(
    timeline,
    start_time=0.0,
    duration=1.0,
    sample_rate=44100,
    track_volumes={0: 1.0},
    project=project  # Now effects should apply
)

analyze_audio(buffer_with_fx, "With Reverb")

# 6. Compare
print("\n6. Comparison:")
if buffer_no_fx == buffer_with_fx:
    print("   ❌ ERROR: Buffers are IDENTICAL - effects NOT applied!")
else:
    print("   ✓ Buffers are DIFFERENT - effects ARE applied!")
    
    # Calculate difference
    diff_count = sum(1 for a, b in zip(buffer_no_fx, buffer_with_fx) if abs(a - b) > 0.0001)
    print(f"   Different samples: {diff_count}/{len(buffer_no_fx)} ({diff_count/len(buffer_no_fx)*100:.1f}%)")

# 7. Save both for comparison
print("\n7. Saving audio files...")
save_audio_file(buffer_no_fx, "test_no_fx.wav", 44100)
save_audio_file(buffer_with_fx, "test_with_fx.wav", 44100)
print("   Saved: test_no_fx.wav, test_with_fx.wav")

# 8. Test with delay
print("\n8. Adding Delay effect on top of reverb...")
delay = Delay()
delay.set_parameters({
    "delay_time": 0.3,
    "feedback": 0.5,
    "mix": 0.5
})
track.add_effect(delay, name="Test Delay", wet=0.6)

buffer_with_both = engine.render_window(
    timeline,
    start_time=0.0,
    duration=1.0,
    sample_rate=44100,
    track_volumes={0: 1.0},
    project=project
)

analyze_audio(buffer_with_both, "With Reverb + Delay")
save_audio_file(buffer_with_both, "test_with_both_fx.wav", 44100)

print("\n" + "=" * 60)
print("✓ Effects rendering test complete!")
print("=" * 60)
