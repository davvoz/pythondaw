"""Example: Editing effect parameters programmatically and via UI."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.core.project import Project
from src.core.track import Track
from src.effects.reverb import Reverb
from src.effects.delay import Delay
from src.effects.compressor import Compressor
from src.effects.equalizer import Equalizer


def example_programmatic_parameters():
    """Example: Modifying effect parameters programmatically."""
    print("\n" + "="*60)
    print("Example 1: Programmatic Parameter Editing")
    print("="*60)
    
    project = Project()
    track = Track("Vocal")
    project.create_track(track)
    
    # Add a compressor with custom parameters
    compressor = Compressor()
    print(f"\n1. Default compressor parameters:")
    for param, value in compressor.parameters.items():
        print(f"   {param}: {value}")
    
    # Customize the compressor for vocals
    compressor.parameters['threshold'] = -18.0  # dBFS
    compressor.parameters['ratio'] = 3.0
    compressor.parameters['attack'] = 0.005  # 5ms
    compressor.parameters['release'] = 0.05  # 50ms
    compressor.parameters['makeup_gain'] = 3.0  # dB
    
    track.add_effect(compressor, name="Vocal Compressor", wet=1.0)
    
    print(f"\n2. Customized compressor parameters:")
    for param, value in compressor.parameters.items():
        print(f"   {param}: {value}")
    
    # Add a reverb with custom room characteristics
    reverb = Reverb()
    reverb.parameters['room_size'] = 0.7  # Large room
    reverb.parameters['damping'] = 0.3  # Bright
    reverb.parameters['wet_level'] = 0.4
    reverb.parameters['dry_level'] = 0.6
    
    track.add_effect(reverb, name="Room Reverb", wet=0.5)
    
    print(f"\n3. Custom reverb parameters:")
    for param, value in reverb.parameters.items():
        print(f"   {param}: {value}")
    
    # The parameters are automatically saved/loaded with the project
    print("\n4. Effect chain summary:")
    for i, slot in enumerate(track.effects.slots):
        print(f"   Slot {i}: {slot.name} (wet: {slot.wet*100:.0f}%, bypass: {slot.bypass})")
        print(f"           Parameters: {slot.effect.parameters}")


def example_effect_presets():
    """Example: Creating effect presets with different parameter sets."""
    print("\n\n" + "="*60)
    print("Example 2: Creating Effect Presets")
    print("="*60)
    
    # Reverb presets
    print("\n1. Reverb Presets:")
    
    # Small room
    small_room = Reverb()
    small_room.parameters['room_size'] = 0.3
    small_room.parameters['damping'] = 0.6
    print(f"   Small Room: {small_room.parameters}")
    
    # Large hall
    large_hall = Reverb()
    large_hall.parameters['room_size'] = 0.9
    large_hall.parameters['damping'] = 0.3
    print(f"   Large Hall: {large_hall.parameters}")
    
    # Delay presets
    print("\n2. Delay Presets:")
    
    # Slap delay
    slap = Delay()
    slap.parameters['delay_time'] = 0.1  # 100ms
    slap.parameters['feedback'] = 0.2
    slap.parameters['mix'] = 0.3
    print(f"   Slap Delay: {slap.parameters}")
    
    # Long echo
    echo = Delay()
    echo.parameters['delay_time'] = 0.5  # 500ms
    echo.parameters['feedback'] = 0.6
    echo.parameters['mix'] = 0.4
    print(f"   Long Echo: {echo.parameters}")
    
    # Compressor presets
    print("\n3. Compressor Presets:")
    
    # Gentle compression
    gentle = Compressor()
    gentle.parameters['threshold'] = -15.0
    gentle.parameters['ratio'] = 2.0
    gentle.parameters['attack'] = 0.01
    gentle.parameters['release'] = 0.1
    print(f"   Gentle: {gentle.parameters}")
    
    # Heavy limiting
    limiter = Compressor()
    limiter.parameters['threshold'] = -6.0
    limiter.parameters['ratio'] = 10.0
    limiter.parameters['attack'] = 0.001
    limiter.parameters['release'] = 0.05
    print(f"   Limiter: {limiter.parameters}")


def example_parameter_automation():
    """Example: Demonstrating parameter changes over time (conceptual)."""
    print("\n\n" + "="*60)
    print("Example 3: Parameter Changes During Processing")
    print("="*60)
    
    track = Track("Lead")
    
    # Create delay with initial parameters
    delay = Delay()
    delay.parameters['delay_time'] = 0.25
    delay.parameters['feedback'] = 0.3
    delay.parameters['mix'] = 0.5
    track.add_effect(delay, name="Tempo Delay", wet=0.8)
    
    print("\n1. Initial delay parameters:")
    print(f"   {delay.parameters}")
    
    # Simulate parameter change during playback
    # (In real usage, you could modify these in real-time)
    print("\n2. Adjusting delay time for different tempo...")
    delay.parameters['delay_time'] = 0.375  # Dotted eighth note
    print(f"   Updated: {delay.parameters}")
    
    # Simulate increasing feedback for dramatic effect
    print("\n3. Increasing feedback for build-up...")
    delay.parameters['feedback'] = 0.7
    print(f"   Updated: {delay.parameters}")
    
    print("\n   💡 In the UI, these changes happen in real-time!")
    print("      Adjust sliders and hear immediate results!")


def example_parameter_ranges():
    """Example: Understanding parameter ranges and meanings."""
    print("\n\n" + "="*60)
    print("Example 4: Parameter Ranges and Meanings")
    print("="*60)
    
    print("\nREVERB Parameters:")
    print("  • room_size (0.0 - 1.0): Size of reverb space")
    print("    - 0.0 = Tiny booth, 0.5 = Room, 1.0 = Cathedral")
    print("  • damping (0.0 - 1.0): High frequency absorption")
    print("    - 0.0 = Bright/metallic, 1.0 = Dark/muted")
    print("  • wet_level (0.0 - 1.0): Amount of reverb signal")
    print("  • dry_level (0.0 - 1.0): Amount of original signal")
    
    print("\nDELAY Parameters:")
    print("  • delay_time (0.0 - 2.0 seconds): Time between echoes")
    print("    - Sync to tempo: 1/4 = 0.5s @ 120bpm")
    print("  • feedback (0.0 - 1.0): Amount fed back for repeats")
    print("    - 0.0 = Single echo, 0.5 = Medium decay, 0.9 = Long tail")
    print("  • mix (0.0 - 1.0): Wet/dry balance")
    
    print("\nCOMPRESSOR Parameters:")
    print("  • threshold (-60.0 - 0.0 dBFS): Level to start compressing")
    print("    - Common: -20dB for vocals, -10dB for limiting")
    print("  • ratio (1.0 - 20.0): Amount of compression")
    print("    - 2:1 = Gentle, 4:1 = Medium, 10:1 = Limiting")
    print("  • attack (0.001 - 1.0 seconds): How fast compression starts")
    print("    - Fast (1ms) = Catch peaks, Slow (50ms) = Preserve punch")
    print("  • release (0.01 - 1.0 seconds): How fast compression stops")
    print("  • makeup_gain (-24.0 - 24.0 dB): Compensate for level loss")
    
    print("\nEQUALIZER Parameters:")
    print("  • frequency (20.0 - 20000.0 Hz): Target frequency")
    print("  • gain (-24.0 - 24.0 dB): Boost or cut amount")
    print("  • q (0.1 - 10.0): Bandwidth of affected frequencies")
    print("    - Low Q = Wide, High Q = Narrow/surgical")


if __name__ == "__main__":
    print("="*60)
    print("Effect Parameter Editing Examples")
    print("="*60)
    print("\nThese examples show how to work with effect parameters")
    print("both programmatically and through the UI.")
    
    example_programmatic_parameters()
    example_effect_presets()
    example_parameter_automation()
    example_parameter_ranges()
    
    print("\n\n" + "="*60)
    print("Try it in the UI!")
    print("="*60)
    print("\n1. Run the DAW: python src\\main.py")
    print("2. Load or create a project with audio")
    print("3. Click the FX button (purple) on any track")
    print("4. Add an effect (Reverb, Delay, Compressor, or EQ)")
    print("5. Click ⚙ Edit to open the parameter editor")
    print("6. Adjust sliders and hear changes in real-time!")
    print("7. Use 🔄 Reset to restore default values")
    print("8. Close and save - parameters are preserved!")
    print("\n" + "="*60)
