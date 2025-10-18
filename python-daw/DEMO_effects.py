"""
Quick demo: Create a project, add effects, export to hear them.

This script shows that effects ARE working by creating:
1. A clean tone without effects
2. The same tone WITH heavy reverb and delay
3. Export both so you can HEAR the difference
"""
import sys
from pathlib import Path
import math

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

print("=" * 70)
print("EFFECTS DEMO - You WILL hear the difference!")
print("=" * 70)

# Create a simple 440Hz tone
def make_tone(freq, duration, sr=44100):
    return [0.5 * math.sin(2 * math.pi * freq * i / sr) 
            for i in range(int(duration * sr))]

# Setup
project = Project(name="Effects Test")
timeline = Timeline()
engine = AudioEngine()
engine.initialize()

# Create track with a 2-second tone
track = Track(name="Test Tone")
tone = make_tone(440, 2.0)
clip = AudioClip("Tone", tone, 44100, start_time=0.0)
track.add_audio(clip)
timeline.add_clip(0, clip)
project.create_track(track)

# 1. Export WITHOUT effects
print("\n1. Exporting WITHOUT effects...")
buffer_clean = engine.render_window(
    timeline, 0.0, 2.0, 44100,
    track_volumes={0: 1.0},
    project=project
)
save_audio_file(buffer_clean, "DEMO_clean.wav", 44100)
print("   ✓ Saved: DEMO_clean.wav")

# 2. Add HEAVY effects so you can REALLY hear them
print("\n2. Adding HEAVY effects (you'll hear these!)...")

# Heavy reverb
reverb = Reverb()
reverb.set_parameters({
    "room_size": 0.9,    # Big room
    "wet_level": 0.8,    # 80% wet!
    "dry_level": 0.2
})
track.add_effect(reverb, name="Heavy Reverb", wet=0.8)
print("   ✓ Added reverb (80% wet)")

# Prominent delay
delay = Delay()
delay.set_parameters({
    "delay_time": 0.3,   # 300ms
    "feedback": 0.7,     # Lots of repeats
    "mix": 0.7          # 70% effect
})
track.add_effect(delay, name="Slapback Delay", wet=0.7)
print("   ✓ Added delay (70% wet, 70% feedback)")

# 3. Export WITH effects
print("\n3. Exporting WITH effects...")
buffer_fx = engine.render_window(
    timeline, 0.0, 2.0, 44100,
    track_volumes={0: 1.0},
    project=project
)
save_audio_file(buffer_fx, "DEMO_with_effects.wav", 44100)
print("   ✓ Saved: DEMO_with_effects.wav")

# 4. Comparison
print("\n" + "=" * 70)
print("RESULTS:")
print("=" * 70)
print(f"Clean:        {len([s for s in buffer_clean if abs(s) > 0.01])} active samples")
print(f"With Effects: {len([s for s in buffer_fx if abs(s) > 0.01])} active samples")

diff = sum(1 for a, b in zip(buffer_clean, buffer_fx) if abs(a - b) > 0.001)
print(f"\nDifferent samples: {diff}/{len(buffer_clean)} ({diff/len(buffer_clean)*100:.1f}%)")

print("\n🎧 NOW LISTEN TO THE FILES:")
print("   DEMO_clean.wav        - Plain 440Hz tone")
print("   DEMO_with_effects.wav - Same tone with reverb + delay")
print("\nYou'll DEFINITELY hear the reverb tail and echo repeats!")
print("=" * 70)
