"""
Example demonstrating per-track effects chain usage.

Shows how to:
1. Add effects to a track programmatically
2. Configure effect parameters
3. Control wet/dry mix and bypass
4. Reorder effects in the chain
5. Save/load projects with effects
"""

import sys
from pathlib import Path
import math

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.project import Project
from core.track import Track
from audio.clip import AudioClip
from effects.reverb import Reverb
from effects.delay import Delay
from effects.compressor import Compressor
from effects.equalizer import Equalizer
from utils.project_serializer import save_project, load_project


def create_test_audio(frequency: float, duration: float, sample_rate: int = 44100):
    """Generate a sine wave for testing."""
    num_samples = int(duration * sample_rate)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        sample = 0.5 * math.sin(2.0 * math.pi * frequency * t)
        samples.append(sample)
    return samples


def main():
    print("=" * 60)
    print("EFFECTS CHAIN EXAMPLE")
    print("=" * 60)
    
    # 1. Create a project with tracks
    print("\n1. Creating project with tracks...")
    project = Project(name="Effects Demo", bpm=128.0)
    
    # Track 1: Lead with reverb and delay
    track1 = Track(name="Lead Synth")
    track1.set_volume(0.8)
    
    # Add some audio
    lead_audio = create_test_audio(440.0, 2.0)
    clip1 = AudioClip("Lead", lead_audio, 44100, start_time=0.0)
    track1.add_audio(clip1)
    
    # Add effects to track 1
    print("\n2. Adding effects to Lead Synth track...")
    
    # Add reverb (30% wet)
    reverb = Reverb()
    reverb.set_parameters({
        "room_size": 0.7,
        "damping": 0.5,
        "wet_level": 0.3,
        "dry_level": 0.7
    })
    idx1 = track1.add_effect(reverb, name="Room Reverb", wet=0.3)
    print(f"   Added Reverb at slot {idx1}")
    
    # Add delay (50% wet)
    delay = Delay()
    delay.set_parameters({
        "delay_time": 0.25,
        "feedback": 0.4,
        "mix": 0.6
    })
    idx2 = track1.add_effect(delay, name="Slap Delay", wet=0.5)
    print(f"   Added Delay at slot {idx2}")
    
    # Track 2: Bass with compressor and EQ
    track2 = Track(name="Bass")
    track2.set_volume(0.7)
    
    bass_audio = create_test_audio(110.0, 2.0)
    clip2 = AudioClip("Bass", bass_audio, 44100, start_time=0.5)
    track2.add_audio(clip2)
    
    print("\n3. Adding effects to Bass track...")
    
    # Add compressor
    comp = Compressor()
    comp.set_parameters({
        "threshold": -15.0,
        "ratio": 4.0,
        "attack": 0.01,
        "release": 0.1,
        "makeup_gain": 2.0
    })
    idx3 = track2.add_effect(comp, name="Bass Compressor", wet=1.0)
    print(f"   Added Compressor at slot {idx3}")
    
    # Add EQ boost
    eq = Equalizer()
    eq.set_parameters({
        "frequency": 100.0,
        "gain": 3.0,
        "q": 1.0
    })
    idx4 = track2.add_effect(eq, name="Low Boost", wet=0.8)
    print(f"   Added EQ at slot {idx4}")
    
    # Add tracks to project
    project.create_track(track1)
    project.create_track(track2)
    
    # 4. Inspect effects chain
    print("\n4. Effects chain summary:")
    for i, track in enumerate(project.tracks):
        print(f"\n   Track {i + 1}: {track.name}")
        if hasattr(track, 'effects') and track.effects:
            for j, slot in enumerate(track.effects.slots):
                bypass_str = " [BYPASSED]" if slot.bypass else ""
                print(f"      {j + 1}. {slot.name} (wet: {slot.wet * 100:.0f}%){bypass_str}")
        else:
            print("      (no effects)")
    
    # 5. Demonstrate bypass and wet control
    print("\n5. Modifying effects...")
    
    # Bypass the delay on track 1
    track1.effects.slots[1].bypass = True
    print("   Bypassed Slap Delay on Lead Synth")
    
    # Reduce reverb wet mix
    track1.effects.slots[0].wet = 0.15
    print("   Reduced Room Reverb wet to 15%")
    
    # 6. Reorder effects (swap compressor and EQ on bass)
    print("\n6. Reordering effects on Bass...")
    print("   Original order: Compressor -> EQ")
    track2.move_effect(0, 1)  # Move compressor after EQ
    print("   New order: EQ -> Compressor")
    
    # 7. Save project with effects
    print("\n7. Saving project with effects...")
    save_path = "effects_demo.daw"
    save_project(project, save_path, embed_audio=False)
    print(f"   Saved to {save_path}")
    
    # 8. Load and verify
    print("\n8. Loading project and verifying effects...")
    loaded = load_project(save_path)
    
    print(f"   Loaded project: {loaded.name}")
    print(f"   Tracks: {len(loaded.tracks)}")
    
    for i, track in enumerate(loaded.tracks):
        print(f"\n   Track {i + 1}: {track.name}")
        if hasattr(track, 'effects') and track.effects:
            for j, slot in enumerate(track.effects.slots):
                bypass_str = " [BYPASSED]" if slot.bypass else ""
                print(f"      {j + 1}. {slot.name} (wet: {slot.wet * 100:.0f}%){bypass_str}")
                
                # Check parameters were restored
                if hasattr(slot.effect, 'parameters'):
                    print(f"         Parameters: {slot.effect.parameters}")
    
    # 9. Export audio with effects applied
    print("\n9. Effects are applied automatically during export!")
    print("   Use File > Export Audio in the UI, or:")
    print("   from audio.engine import AudioEngine")
    print("   engine = AudioEngine()")
    print("   engine.initialize()")
    print("   buffer = engine.render_window(")
    print("       timeline, 0.0, duration, 44100,")
    print("       track_volumes={0: 0.8, 1: 0.7},")
    print("       project=project  # Pass project to apply effects")
    print("   )")
    
    print("\n" + "=" * 60)
    print("✓ Effects chain example complete!")
    print("=" * 60)


if __name__ == "__main__":
    main()
