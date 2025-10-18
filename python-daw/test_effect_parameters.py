"""Test effect parameter editing functionality."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.core.track import Track
from src.effects.reverb import Reverb
from src.effects.delay import Delay
from src.effects.compressor import Compressor
from src.effects.equalizer import Equalizer


def test_parameter_defaults():
    """Test that effects have default parameters."""
    print("\n=== Testing Effect Parameter Defaults ===\n")
    
    # Reverb
    reverb = Reverb()
    print(f"Reverb parameters: {reverb.parameters}")
    assert hasattr(reverb, 'parameters')
    assert 'room_size' in reverb.parameters
    assert 'damping' in reverb.parameters
    assert 'wet_level' in reverb.parameters
    assert 'dry_level' in reverb.parameters
    print("✓ Reverb has all expected parameters")
    
    # Delay
    delay = Delay()
    print(f"\nDelay parameters: {delay.parameters}")
    assert 'delay_time' in delay.parameters
    assert 'feedback' in delay.parameters
    assert 'mix' in delay.parameters
    print("✓ Delay has all expected parameters")
    
    # Compressor
    compressor = Compressor()
    print(f"\nCompressor parameters: {compressor.parameters}")
    assert 'threshold' in compressor.parameters
    assert 'ratio' in compressor.parameters
    assert 'attack' in compressor.parameters
    assert 'release' in compressor.parameters
    assert 'makeup_gain' in compressor.parameters
    print("✓ Compressor has all expected parameters")
    
    # Equalizer
    eq = Equalizer()
    print(f"\nEqualizer parameters: {eq.parameters}")
    assert 'frequency' in eq.parameters
    assert 'gain' in eq.parameters
    assert 'q' in eq.parameters
    print("✓ Equalizer has all expected parameters")


def test_parameter_modification():
    """Test modifying effect parameters."""
    print("\n\n=== Testing Parameter Modification ===\n")
    
    track = Track("Test Track")
    
    # Add reverb with default parameters
    reverb = Reverb()
    track.add_effect(reverb, name="My Reverb", wet=0.7)
    
    print(f"Initial reverb parameters: {reverb.parameters}")
    
    # Modify parameters
    reverb.parameters['room_size'] = 0.8
    reverb.parameters['damping'] = 0.3
    reverb.parameters['wet_level'] = 0.9
    
    print(f"Modified reverb parameters: {reverb.parameters}")
    assert reverb.parameters['room_size'] == 0.8
    assert reverb.parameters['damping'] == 0.3
    assert reverb.parameters['wet_level'] == 0.9
    print("✓ Parameters modified successfully")
    
    # Test that modifications persist in track
    slot = track.effects.slots[0]
    assert slot.effect.parameters['room_size'] == 0.8
    print("✓ Parameter modifications persist in track")


def test_parameter_types():
    """Test that parameters have correct types."""
    print("\n\n=== Testing Parameter Types ===\n")
    
    # Test numeric parameters
    delay = Delay()
    assert isinstance(delay.parameters['delay_time'], (int, float))
    assert isinstance(delay.parameters['feedback'], (int, float))
    assert isinstance(delay.parameters['mix'], (int, float))
    print("✓ Delay parameters are numeric")
    
    compressor = Compressor()
    assert isinstance(compressor.parameters['threshold'], (int, float))
    assert isinstance(compressor.parameters['ratio'], (int, float))
    assert isinstance(compressor.parameters['attack'], (int, float))
    assert isinstance(compressor.parameters['release'], (int, float))
    assert isinstance(compressor.parameters['makeup_gain'], (int, float))
    print("✓ Compressor parameters are numeric")


def test_parameter_ranges():
    """Test that parameter values are within reasonable ranges."""
    print("\n\n=== Testing Parameter Ranges ===\n")
    
    reverb = Reverb()
    assert 0.0 <= reverb.parameters['room_size'] <= 1.0
    assert 0.0 <= reverb.parameters['damping'] <= 1.0
    print("✓ Reverb parameters in range [0, 1]")
    
    delay = Delay()
    assert delay.parameters['delay_time'] >= 0.0
    assert 0.0 <= delay.parameters['feedback'] <= 1.0
    assert 0.0 <= delay.parameters['mix'] <= 1.0
    print("✓ Delay parameters in valid ranges")
    
    compressor = Compressor()
    assert compressor.parameters['threshold'] <= 0.0  # dB (negative)
    assert compressor.parameters['ratio'] >= 1.0  # ratio >= 1:1
    assert compressor.parameters['attack'] > 0.0  # positive time
    assert compressor.parameters['release'] > 0.0  # positive time
    print("✓ Compressor parameters in valid ranges")


def test_parameter_serialization():
    """Test that parameters are preserved during serialization."""
    print("\n\n=== Testing Parameter Serialization ===\n")
    
    track = Track("Test Track")
    
    # Add effect with custom parameters
    delay = Delay()
    delay.parameters['delay_time'] = 0.5
    delay.parameters['feedback'] = 0.6
    delay.parameters['mix'] = 0.8
    track.add_effect(delay, name="Custom Delay", wet=0.7)
    
    # Serialize
    config = track.effects.to_config()
    print(f"Serialized config: {config}")
    
    # Verify parameters are in config
    assert len(config) == 1
    slot_config = config[0]
    assert 'params' in slot_config
    assert slot_config['params']['delay_time'] == 0.5
    assert slot_config['params']['feedback'] == 0.6
    assert slot_config['params']['mix'] == 0.8
    print("✓ Parameters correctly serialized")
    
    # Deserialize
    new_track = Track("New Track")
    from src.effects.chain import EffectChain
    
    # Build registry
    from src.effects.delay import Delay as DelayClass
    registry = {'Delay': DelayClass}
    
    new_track.effects.from_config(config, registry=registry)
    
    # Verify parameters restored
    restored_slot = new_track.effects.slots[0]
    assert restored_slot.effect.parameters['delay_time'] == 0.5
    assert restored_slot.effect.parameters['feedback'] == 0.6
    assert restored_slot.effect.parameters['mix'] == 0.8
    print("✓ Parameters correctly deserialized")


def test_parameter_effect_on_audio():
    """Test that parameter changes affect audio output."""
    print("\n\n=== Testing Parameter Effect on Audio ===\n")
    
    # Create test audio (simple sine-like pattern)
    test_audio = [0.1, 0.3, 0.5, 0.3, 0.1, -0.1, -0.3, -0.5, -0.3, -0.1] * 10
    
    # Test with EQ (simple gain effect)
    eq1 = Equalizer()
    eq1.parameters['gain'] = 0.0  # 0 dB = no change
    output1 = eq1.apply(test_audio[:])
    
    eq2 = Equalizer()
    eq2.parameters['gain'] = 6.0  # +6 dB = ~2x louder
    output2 = eq2.apply(test_audio[:])
    
    # Output2 should be louder than output1
    avg1 = sum(abs(x) for x in output1) / len(output1)
    avg2 = sum(abs(x) for x in output2) / len(output2)
    
    print(f"Average amplitude with 0dB gain: {avg1:.4f}")
    print(f"Average amplitude with +6dB gain: {avg2:.4f}")
    print(f"Ratio: {avg2/avg1:.2f}x")
    
    assert avg2 > avg1, "Higher gain should produce louder output"
    print("✓ Parameter changes affect audio output")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Effect Parameter Editing")
    print("=" * 60)
    
    try:
        test_parameter_defaults()
        test_parameter_modification()
        test_parameter_types()
        test_parameter_ranges()
        test_parameter_serialization()
        test_parameter_effect_on_audio()
        
        print("\n" + "=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
        print("\nParameter editing is working correctly:")
        print("  • All effects have configurable parameters")
        print("  • Parameters can be modified programmatically")
        print("  • Parameters are serialized/deserialized correctly")
        print("  • Parameter changes affect audio output")
        print("\nNow test the UI:")
        print("  1. Run: python src\\main.py")
        print("  2. Click FX button on a track")
        print("  3. Add an effect (Reverb, Delay, Compressor, or EQ)")
        print("  4. Click ⚙ Edit button")
        print("  5. Adjust parameters with sliders")
        print("  6. Hear the changes during playback!")
        
    except AssertionError as e:
        print(f"\n❌ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
