"""Test script for audio import functionality."""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.utils.audio_io import get_supported_formats, get_audio_info, load_audio_file


def test_supported_formats():
    """Test getting supported formats."""
    print("=" * 60)
    print("SUPPORTED AUDIO FORMATS")
    print("=" * 60)
    
    formats = get_supported_formats()
    
    for desc, pattern in formats:
        print(f"  {desc:30s} {pattern}")
    
    print()


def test_audio_info(file_path: str):
    """Test getting audio file info."""
    print("=" * 60)
    print(f"AUDIO FILE INFO: {os.path.basename(file_path)}")
    print("=" * 60)
    
    try:
        info = get_audio_info(file_path)
        
        for key, value in info.items():
            if key == 'duration':
                mins = int(value // 60)
                secs = value % 60
                print(f"  {key:15s}: {mins}:{secs:05.2f}")
            elif key == 'size':
                mb = value / (1024 * 1024)
                print(f"  {key:15s}: {mb:.2f} MB")
            else:
                print(f"  {key:15s}: {value}")
        
        print()
    except Exception as e:
        print(f"  Error: {e}\n")


def test_load_audio(file_path: str):
    """Test loading audio file."""
    print("=" * 60)
    print(f"LOADING AUDIO: {os.path.basename(file_path)}")
    print("=" * 60)
    
    try:
        buffer, sr = load_audio_file(file_path, target_sr=44100)
        
        duration = len(buffer) / sr
        mins = int(duration // 60)
        secs = duration % 60
        
        print(f"  ✓ Loaded successfully")
        print(f"  Sample rate: {sr} Hz")
        print(f"  Samples: {len(buffer):,}")
        print(f"  Duration: {mins}:{secs:05.2f}")
        
        # Check range
        min_val = min(buffer)
        max_val = max(buffer)
        print(f"  Range: [{min_val:.3f}, {max_val:.3f}]")
        
        print()
    except Exception as e:
        print(f"  ✗ Error: {e}\n")


def main():
    """Main test function."""
    print("\n" + "=" * 60)
    print("AUDIO IMPORT FUNCTIONALITY TEST")
    print("=" * 60 + "\n")
    
    # Test supported formats
    test_supported_formats()
    
    # Test with example files (if they exist)
    test_files = [
        "test.wav",
        "test.mp3",
        "test.flac",
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            test_audio_info(test_file)
            test_load_audio(test_file)
    
    print("=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)
    print("\nTo test with your own files:")
    print("  python test_audio_import.py your_file.wav")
    print()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test specific file
        file_path = sys.argv[1]
        if os.path.exists(file_path):
            test_audio_info(file_path)
            test_load_audio(file_path)
        else:
            print(f"File not found: {file_path}")
    else:
        main()
