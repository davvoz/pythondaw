"""
Test real-time effects playback.

This demonstrates that effects NOW work during real-time playback,
not just during export!
"""
import sys
from pathlib import Path
import math
import time

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from core.project import Project
from core.track import Track
from core.timeline import Timeline
from audio.clip import AudioClip
from audio.player import TimelinePlayer
from audio.mixer import Mixer
from effects.reverb import Reverb
from effects.delay import Delay

print("=" * 70)
print("REAL-TIME EFFECTS PLAYBACK TEST")
print("=" * 70)

# Check if sounddevice is available
try:
    import sounddevice as sd
    import numpy as np
    print("\n✓ sounddevice and numpy available - real-time playback enabled")
except ImportError:
    print("\n✗ sounddevice or numpy not available - playback will be silent")
    print("  Install with: pip install sounddevice numpy")
    sys.exit(0)

# Create a simple tone
def make_tone(freq, duration, sr=44100):
    return [0.3 * math.sin(2 * math.pi * freq * i / sr) 
            for i in range(int(duration * sr))]

# Setup
print("\n1. Creating project with 5-second tone...")
project = Project(name="RT Effects Test")
timeline = Timeline()
mixer = Mixer()
mixer.add_track("Test Track", volume=1.0)

track = Track(name="Test Track")
tone = make_tone(440, 5.0)  # 5 seconds
clip = AudioClip("Tone", tone, 44100, start_time=0.0)
track.add_audio(clip)
timeline.add_clip(0, clip)
project.create_track(track)

# Create player WITH project reference (for effects)
player = TimelinePlayer(timeline, sample_rate=44100, mixer=mixer, project=project)

print("\n2. Playing WITHOUT effects for 3 seconds...")
print("   (You should hear a plain 440Hz tone)")
player.start(start_time=0.0)
time.sleep(3)
player.stop()
time.sleep(0.5)

# Add effects
print("\n3. Adding REVERB effect (70% wet)...")
reverb = Reverb()
reverb.set_parameters({
    "room_size": 0.8,
    "wet_level": 0.7,
    "dry_level": 0.3
})
track.add_effect(reverb, name="Room Reverb", wet=0.7)

print("   Effect chain:")
for i, slot in enumerate(track.effects.slots):
    print(f"     {i+1}. {slot.name} (wet: {slot.wet*100:.0f}%)")

print("\n4. Playing WITH REVERB for 3 seconds...")
print("   (You should now hear the reverb tail!)")
player.start(start_time=0.0)
time.sleep(3)
player.stop()
time.sleep(0.5)

# Add delay too
print("\n5. Adding DELAY effect (60% wet)...")
delay = Delay()
delay.set_parameters({
    "delay_time": 0.25,
    "feedback": 0.6,
    "mix": 0.6
})
track.add_effect(delay, name="Delay", wet=0.6)

print("   Updated effect chain:")
for i, slot in enumerate(track.effects.slots):
    print(f"     {i+1}. {slot.name} (wet: {slot.wet*100:.0f}%)")

print("\n6. Playing WITH REVERB + DELAY for 3 seconds...")
print("   (You should hear both reverb AND echo repeats!)")
player.start(start_time=0.0)
time.sleep(3)
player.stop()

print("\n" + "=" * 70)
print("✓ Real-time effects playback test complete!")
print("\nIf you heard:")
print("  1. Plain tone")
print("  2. Tone with reverb tail")
print("  3. Tone with reverb + echo")
print("\n...then effects are working in REAL-TIME! 🎉")
print("=" * 70)
