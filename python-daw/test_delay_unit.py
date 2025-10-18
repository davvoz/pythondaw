"""
Simple unit test for the professional delay effect.
Tests the delay in isolation without the full playback system.
"""
import sys
from pathlib import Path
import math

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from effects.delay import Delay

print("=" * 70)
print("DELAY UNIT TEST")
print("=" * 70)

# Test 1: Basic mono processing
print("\n1. Testing basic mono audio processing...")
delay = Delay(sample_rate=44100)
delay.set_parameters({
    "delay_time_ms": 100.0,
    "feedback": 0.5,
    "mix": 0.5,
})

# Create a simple impulse
audio = [0.0] * 44100
audio[1000] = 1.0  # Single impulse

print(f"   Input: {len(audio)} samples, impulse at sample 1000")
output = delay.apply(audio)
print(f"   Output: {len(output)} samples")

# Check if delay worked - look for delayed impulses
delay_samples = int(0.1 * 44100)  # 100ms
threshold = 0.1
found_delayed = False
for i in range(1000 + delay_samples - 100, 1000 + delay_samples + 100):
    if i < len(output) and abs(output[i]) > threshold:
        found_delayed = True
        print(f"   ✓ Found delayed signal at sample {i} (expected ~{1000 + delay_samples})")
        break

if not found_delayed:
    print(f"   ✗ No delayed signal found near expected position")

# Test 2: Parameter updates
print("\n2. Testing parameter updates...")
delay.set_parameters({
    "delay_time_ms": 200.0,
    "feedback": 0.3,
})
print(f"   ✓ Parameters updated: {delay.parameters}")

# Test 3: Stereo processing
print("\n3. Testing stereo audio processing...")
delay_stereo = Delay(sample_rate=44100)
delay_stereo.set_parameters({
    "delay_time_ms": 150.0,
    "feedback": 0.4,
    "mix": 0.6,
    "ping_pong": 0.5,
})

# Create stereo impulse
stereo_audio = [[0.0, 0.0] for _ in range(44100)]
stereo_audio[1000] = [1.0, 0.5]

print(f"   Input: {len(stereo_audio)} stereo samples")
try:
    stereo_output = delay_stereo.apply(stereo_audio)
    print(f"   Output: {len(stereo_output)} stereo samples")
    print(f"   ✓ Stereo processing successful")
except Exception as e:
    print(f"   ✗ Error in stereo processing: {e}")
    import traceback
    traceback.print_exc()

# Test 4: Filter parameters
print("\n4. Testing filter parameters...")
delay_filtered = Delay(sample_rate=44100)
delay_filtered.set_parameters({
    "delay_time_ms": 200.0,
    "feedback": 0.5,
    "mix": 0.7,
    "low_cut": 300.0,
    "high_cut": 5000.0,
})
print(f"   Low cut: {delay_filtered.parameters['low_cut']} Hz")
print(f"   High cut: {delay_filtered.parameters['high_cut']} Hz")

audio2 = [0.0] * 22050
audio2[500] = 1.0
try:
    filtered_output = delay_filtered.apply(audio2)
    print(f"   ✓ Filtered delay processing successful")
except Exception as e:
    print(f"   ✗ Error in filtered processing: {e}")
    import traceback
    traceback.print_exc()

# Test 5: Reset function
print("\n5. Testing reset function...")
delay.reset()
print(f"   ✓ Delay buffers reset")
print(f"   Buffer left size: {len(delay.buffer_left)}")
print(f"   Write position: {delay.write_pos}")

print("\n" + "=" * 70)
print("DELAY UNIT TEST COMPLETE")
print("=" * 70)
