"""
Example demonstrating project save/load functionality.

Shows how to:
1. Create a project with tracks and clips
2. Save the project (with audio files)
3. Load the project back
4. Verify that everything is restored correctly
"""

import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from core.project import Project
from core.track import Track
from audio.clip import AudioClip
from utils.project_serializer import save_project, load_project
import math


def create_sample_audio(frequency: float, duration: float, sample_rate: int = 44100):
    """Generate a sine wave for testing."""
    num_samples = int(duration * sample_rate)
    return [math.sin(2 * math.pi * frequency * i / sample_rate) 
            for i in range(num_samples)]


def main():
    print("=" * 60)
    print("Project Save/Load Example")
    print("=" * 60)
    
    # Create a new project
    print("\n1. Creating new project...")
    project = Project(name="My Demo Song", bpm=128.0, time_signature=(4, 4))
    
    # Create tracks
    track1 = Track()
    track1.set_volume(0.8)
    
    track2 = Track()
    track2.set_volume(0.6)
    
    # Create audio clips with sine waves
    print("2. Creating audio clips...")
    
    # Clip 1: 440 Hz (A4) for 2 seconds
    buffer1 = create_sample_audio(440.0, 2.0)
    clip1 = AudioClip(
        name="A4 Note",
        buffer=buffer1,
        sample_rate=44100,
        start_time=0.0,
        color="#FF6B6B"
    )
    clip1.fade_in = 0.1
    clip1.fade_out = 0.2
    clip1.volume = 0.9
    
    # Clip 2: 523.25 Hz (C5) for 1.5 seconds
    buffer2 = create_sample_audio(523.25, 1.5)
    clip2 = AudioClip(
        name="C5 Note",
        buffer=buffer2,
        sample_rate=44100,
        start_time=2.5,
        color="#4ECDC4"
    )
    clip2.pitch_semitones = -2.0
    
    # Clip 3: 329.63 Hz (E4) for 3 seconds
    buffer3 = create_sample_audio(329.63, 3.0)
    clip3 = AudioClip(
        name="E4 Note",
        buffer=buffer3,
        sample_rate=44100,
        start_time=1.0,
        color="#95E1D3"
    )
    clip3.start_offset = 0.5
    clip3.end_offset = 0.3
    
    # Add clips to tracks
    track1.add_audio(clip1)
    track1.add_audio(clip2)
    track2.add_audio(clip3)
    
    # Add tracks to project
    project.create_track(track1)
    project.create_track(track2)
    
    print(f"   - Project: {project.name}")
    print(f"   - BPM: {project.bpm}")
    print(f"   - Time Signature: {project.time_signature_num}/{project.time_signature_den}")
    print(f"   - Tracks: {len(project.tracks)}")
    print(f"   - Track 1 clips: {len(track1.audio_files)}")
    print(f"   - Track 2 clips: {len(track2.audio_files)}")
    
    # Save the project
    print("\n3. Saving project...")
    save_path = "test_project.daw"
    
    # Option 1: Save with separate audio files (recommended for large projects)
    print("   a) Saving with separate audio files...")
    save_project(project, save_path, embed_audio=False)
    
    # Option 2: Save with embedded audio (convenient for small projects)
    save_path_embedded = "test_project_embedded.daw"
    print("   b) Saving with embedded audio...")
    save_project(project, save_path_embedded, embed_audio=True)
    
    # Load the project back
    print("\n4. Loading project...")
    loaded_project = load_project(save_path)
    
    # Verify the loaded project
    print("\n5. Verifying loaded project...")
    print(f"   - Project name: {loaded_project.name}")
    print(f"   - BPM: {loaded_project.bpm}")
    print(f"   - Time Signature: {loaded_project.time_signature_num}/{loaded_project.time_signature_den}")
    print(f"   - Number of tracks: {len(loaded_project.tracks)}")
    
    for i, track in enumerate(loaded_project.tracks):
        print(f"\n   Track {i+1}:")
        print(f"     - Volume: {track.volume}")
        print(f"     - Number of clips: {len(track.audio_files)}")
        
        for j, clip in enumerate(track.audio_files):
            print(f"     Clip {j+1}:")
            print(f"       - Name: {clip.name}")
            print(f"       - Start time: {clip.start_time}s")
            print(f"       - Duration: {clip.length_seconds:.2f}s")
            print(f"       - Sample rate: {clip.sample_rate} Hz")
            print(f"       - Buffer size: {len(clip.buffer)} samples")
            print(f"       - Color: {clip.color}")
            print(f"       - Volume: {clip.volume}")
            print(f"       - Fade in: {clip.fade_in}s")
            print(f"       - Fade out: {clip.fade_out}s")
            print(f"       - Pitch shift: {clip.pitch_semitones} semitones")
    
    # Test loading embedded version
    print("\n6. Loading embedded version...")
    loaded_embedded = load_project(save_path_embedded)
    print(f"   - Successfully loaded embedded project: {loaded_embedded.name}")
    print(f"   - Tracks: {len(loaded_embedded.tracks)}")
    
    print("\n" + "=" * 60)
    print("Project save/load test completed successfully!")
    print("=" * 60)
    print(f"\nFiles created:")
    print(f"  - {save_path}")
    print(f"  - {save_path.replace('.daw', '_data/')} (audio folder)")
    print(f"  - {save_path_embedded}")
    print("\nYou can now load these projects in your DAW!")


if __name__ == "__main__":
    main()
