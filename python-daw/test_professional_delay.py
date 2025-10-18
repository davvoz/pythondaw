"""
Test Professional Delay Effect

Demonstrates the new professional-grade delay with:
- Accurate millisecond timing
- Low-pass and high-pass filtering
- Ping-pong stereo effect
- Clean feedback path
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
from effects.delay import Delay

print("=" * 70)
print("PROFESSIONAL DELAY EFFECT DEMONSTRATION")
print("=" * 70)

# Check if sounddevice is available
try:
    import sounddevice as sd
    import numpy as np
    print("\n✓ sounddevice and numpy available")
except ImportError:
    print("\n✗ sounddevice or numpy not available")
    print("  Install with: pip install sounddevice numpy")
    sys.exit(0)

# Create test signals
def make_tone(freq, duration, sr=44100):
    """Generate a sine wave"""
    return [0.3 * math.sin(2 * math.pi * freq * i / sr) 
            for i in range(int(duration * sr))]

def make_impulse(duration, sr=44100):
    """Generate a short click for testing delay"""
    samples = int(duration * sr)
    result = [0.0] * samples
    # Add a few impulses
    for i in [sr // 4, sr // 2, 3 * sr // 4]:
        if i < len(result):
            result[i] = 0.5
    return result

# Setup
print("\n1. Creating project with test signals...")
project = Project(name="Pro Delay Test")
timeline = Timeline()
mixer = Mixer()
mixer.add_track("Delay Test", volume=1.0)

track = Track(name="Delay Test")

# Use impulses for clear delay demonstration
print("   Using impulse clicks for clear delay timing demonstration")
audio = make_impulse(4.0, 44100)
clip = AudioClip("Impulses", audio, 44100, start_time=0.0)
track.add_audio(clip)
timeline.add_clip(0, clip)
project.create_track(track)

player = TimelinePlayer(timeline, sample_rate=44100, mixer=mixer, project=project)

# Test 1: Short delay
print("\n" + "=" * 70)
print("TEST 1: SHORT DELAY (150ms)")
print("=" * 70)
delay1 = Delay(sample_rate=44100)
delay1.set_parameters({
    "delay_time_ms": 150.0,
    "feedback": 0.4,
    "mix": 0.7,
    "low_cut": 200.0,
    "high_cut": 8000.0,
    "ping_pong": 0.0
})
track.effects.clear()
track.add_effect(delay1, name="Short Delay", wet=0.7)
print("   Delay Time: 150ms")
print("   Feedback: 40%")
print("   Mix: 70%")
print("\n   Playing...")
player.start(start_time=0.0)
time.sleep(3)
player.stop()
time.sleep(0.5)

# Test 2: Medium delay with more feedback
print("\n" + "=" * 70)
print("TEST 2: MEDIUM DELAY (300ms) with Higher Feedback")
print("=" * 70)
delay2 = Delay(sample_rate=44100)
delay2.set_parameters({
    "delay_time_ms": 300.0,
    "feedback": 0.6,
    "mix": 0.7,
    "low_cut": 200.0,
    "high_cut": 8000.0,
    "ping_pong": 0.0
})
track.effects.clear()
track.add_effect(delay2, name="Medium Delay", wet=0.7)
print("   Delay Time: 300ms")
print("   Feedback: 60% (more repeats)")
print("   Mix: 70%")
print("\n   Playing...")
player.start(start_time=0.0)
time.sleep(4)
player.stop()
time.sleep(0.5)

# Test 3: Long delay
print("\n" + "=" * 70)
print("TEST 3: LONG DELAY (600ms)")
print("=" * 70)
delay3 = Delay(sample_rate=44100)
delay3.set_parameters({
    "delay_time_ms": 600.0,
    "feedback": 0.5,
    "mix": 0.7,
    "low_cut": 200.0,
    "high_cut": 8000.0,
    "ping_pong": 0.0
})
track.effects.clear()
track.add_effect(delay3, name="Long Delay", wet=0.7)
print("   Delay Time: 600ms")
print("   Feedback: 50%")
print("   Mix: 70%")
print("\n   Playing...")
player.start(start_time=0.0)
time.sleep(4)
player.stop()
time.sleep(0.5)

# Test 4: Filtered delay
print("\n" + "=" * 70)
print("TEST 4: FILTERED DELAY (Dark, Warm Sound)")
print("=" * 70)
delay4 = Delay(sample_rate=44100)
delay4.set_parameters({
    "delay_time_ms": 250.0,
    "feedback": 0.6,
    "mix": 0.7,
    "low_cut": 400.0,    # Cut more lows
    "high_cut": 3000.0,  # Cut more highs - darker sound
    "ping_pong": 0.0
})
track.effects.clear()
track.add_effect(delay4, name="Filtered Delay", wet=0.7)
print("   Delay Time: 250ms")
print("   Feedback: 60%")
print("   Low Cut: 400Hz (removes rumble)")
print("   High Cut: 3000Hz (warm, dark repeats)")
print("\n   Playing... (notice the darker, warmer repeats)")
player.start(start_time=0.0)
time.sleep(4)
player.stop()
time.sleep(0.5)

# Test 5: For stereo test, use a tone instead
print("\n" + "=" * 70)
print("TEST 5: PING-PONG DELAY (Stereo Bouncing)")
print("=" * 70)
print("   Recreating track with stereo tone...")

# Create a new track with tone for stereo demo
track2 = Track(name="Stereo Test")
tone = make_tone(440, 4.0, 44100)
# Convert to fake stereo (same signal both channels)
stereo_tone = [[s, s] for s in tone]
clip2 = AudioClip("Stereo Tone", stereo_tone, 44100, start_time=0.0)
track2.add_audio(clip2)

timeline.clips.clear()
timeline.add_clip(0, clip2)
project.tracks = [track2]

mixer.tracks = {}
mixer.add_track("Stereo Test", volume=1.0)

delay5 = Delay(sample_rate=44100)
delay5.set_parameters({
    "delay_time_ms": 200.0,
    "feedback": 0.5,
    "mix": 0.7,
    "low_cut": 200.0,
    "high_cut": 8000.0,
    "ping_pong": 1.0  # Full ping-pong!
})
track2.add_effect(delay5, name="Ping-Pong Delay", wet=0.7)

print("   Delay Time: 200ms")
print("   Feedback: 50%")
print("   Ping-Pong: 100% (bounces between left/right)")
print("\n   Playing... (use headphones to hear stereo effect!)")
player2 = TimelinePlayer(timeline, sample_rate=44100, mixer=mixer, project=project)
player2.start(start_time=0.0)
time.sleep(4)
player2.stop()

print("\n" + "=" * 70)
print("✓ Professional Delay Demonstration Complete!")
print("=" * 70)
print("\nThe new delay features:")
print("  ✓ Accurate millisecond timing")
print("  ✓ Clean, musical feedback")
print("  ✓ Low-cut filter (removes rumble)")
print("  ✓ High-cut filter (warm, vintage tone)")
print("  ✓ Ping-pong stereo effect")
print("  ✓ Professional sound quality")
print("\nThis is now a studio-grade delay! 🎛️")
print("=" * 70)
