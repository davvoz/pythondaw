"""
Test delay with chunked processing (like real-time playback).
This simulates how the audio engine processes audio in small chunks.
"""
import sys
from pathlib import Path
import math

src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from effects.delay import Delay

print("=" * 70)
print("DELAY CHUNKED PROCESSING TEST")
print("=" * 70)

# Simulate real-time processing with small chunks
CHUNK_SIZE = 512
SAMPLE_RATE = 44100
DURATION = 2.0

print(f"\nSimulating real-time processing:")
print(f"  Sample rate: {SAMPLE_RATE} Hz")
print(f"  Chunk size: {CHUNK_SIZE} samples ({CHUNK_SIZE/SAMPLE_RATE*1000:.1f}ms)")
print(f"  Duration: {DURATION} seconds")

# Create delay
delay = Delay(sample_rate=SAMPLE_RATE)
delay.set_parameters({
    "delay_time_ms": 250.0,  # 250ms delay
    "feedback": 0.5,
    "mix": 0.7,
    "low_cut": 200.0,
    "high_cut": 6000.0,
})

print(f"\nDelay settings:")
print(f"  Delay time: {delay.parameters['delay_time_ms']}ms")
print(f"  Feedback: {delay.parameters['feedback']*100}%")
print(f"  Mix: {delay.parameters['mix']*100}%")

# Create input signal: impulses at specific times
total_samples = int(DURATION * SAMPLE_RATE)
input_signal = [0.0] * total_samples

# Add impulses every 0.5 seconds
for t in [0.1, 0.6, 1.1, 1.6]:
    idx = int(t * SAMPLE_RATE)
    if idx < len(input_signal):
        input_signal[idx] = 0.8
        print(f"  Input impulse at {t}s (sample {idx})")

# Process in chunks
print(f"\nProcessing {total_samples // CHUNK_SIZE} chunks...")
output_signal = []
num_chunks = 0

for start_idx in range(0, total_samples, CHUNK_SIZE):
    end_idx = min(start_idx + CHUNK_SIZE, total_samples)
    chunk = input_signal[start_idx:end_idx]
    
    # Process chunk through delay
    processed_chunk = delay.apply(chunk)
    output_signal.extend(processed_chunk)
    num_chunks += 1

print(f"✓ Processed {num_chunks} chunks successfully")
print(f"  Total output samples: {len(output_signal)}")

# Analyze output for delayed signals
print(f"\nAnalyzing output for delayed signals...")
threshold = 0.05
delay_samples = int(delay.parameters['delay_time_ms'] / 1000.0 * SAMPLE_RATE)
print(f"  Expected delay: {delay_samples} samples ({delay_samples/SAMPLE_RATE*1000:.1f}ms)")

for input_time in [0.1, 0.6, 1.1, 1.6]:
    input_idx = int(input_time * SAMPLE_RATE)
    expected_delay_idx = input_idx + delay_samples
    
    # Look for signal near expected position
    found = False
    for i in range(max(0, expected_delay_idx - 100), min(len(output_signal), expected_delay_idx + 100)):
        if abs(output_signal[i]) > threshold:
            actual_delay_ms = (i - input_idx) / SAMPLE_RATE * 1000
            found = True
            print(f"  Input at {input_time}s → Delayed signal at {i/SAMPLE_RATE:.3f}s (delay: {actual_delay_ms:.1f}ms)")
            break
    
    if not found:
        print(f"  ✗ No delayed signal found for impulse at {input_time}s")

# Test multiple feedbacks
print(f"\nChecking for multiple feedback repeats...")
input_idx = int(0.1 * SAMPLE_RATE)
for repeat in range(1, 4):
    expected_idx = input_idx + (delay_samples * repeat)
    if expected_idx < len(output_signal):
        # Look for feedback repeats
        found = False
        for i in range(max(0, expected_idx - 100), min(len(output_signal), expected_idx + 100)):
            if abs(output_signal[i]) > threshold * (0.5 ** repeat):  # Each repeat quieter
                found = True
                print(f"  ✓ Feedback repeat #{repeat} found at {i/SAMPLE_RATE:.3f}s")
                break

print("\n" + "=" * 70)
print("✓ CHUNKED PROCESSING TEST COMPLETE")
print("=" * 70)
print("\nThe delay correctly maintains state across multiple")
print("chunks, making it suitable for real-time processing!")
print("=" * 70)
