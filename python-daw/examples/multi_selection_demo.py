"""Example demonstrating multi-selection and copy/paste features."""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.project import Project
from src.core.timeline import Timeline
from src.audio.clip import AudioClip
from src.audio.mixer import Mixer
from src.audio.engine import AudioEngine
from src.audio.player import TimelinePlayer
from src.ui.window import MainWindow
import numpy as np


def generate_tone(frequency: float, duration: float, sample_rate: int = 44100):
    """Generate a simple tone for demonstration."""
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    wave = 0.3 * np.sin(2 * np.pi * frequency * t)
    return wave.astype(float).tolist()


def main():
    """Demonstrate multi-selection and copy/paste features."""
    
    # Create project components
    project = Project("Multi-Selection Demo")
    timeline = Timeline()
    mixer = Mixer()
    engine = AudioEngine()
    engine.initialize()
    player = TimelinePlayer(timeline, mixer, engine)
    
    # Add tracks
    mixer.add_track("Melody", color="#3b82f6")
    mixer.add_track("Bass", color="#10b981")
    mixer.add_track("Drums", color="#f59e0b")
    
    print("=== Multi-Selection and Copy/Paste Demo ===\n")
    
    # Create sample clips with different tones
    print("📝 Creating sample clips...")
    
    # Melody clips (higher frequency)
    melody1 = AudioClip(
        "Melody 1",
        generate_tone(440, 1.0),  # A4
        44100,
        1.0,
        duration=1.0,
        color="#3b82f6"
    )
    melody1.fade_in = 0.1
    melody1.fade_out = 0.1
    
    melody2 = AudioClip(
        "Melody 2",
        generate_tone(554.37, 1.0),  # C#5
        44100,
        2.5,
        duration=1.0,
        color="#3b82f6"
    )
    melody2.fade_in = 0.05
    melody2.fade_out = 0.05
    melody2.pitch_semitones = 2.0
    
    # Bass clip (lower frequency)
    bass = AudioClip(
        "Bass",
        generate_tone(110, 2.0),  # A2
        44100,
        1.5,
        duration=2.0,
        color="#10b981"
    )
    bass.volume = 0.8
    
    # Drum pattern (simple noise burst)
    drum_sound = (np.random.random(22050) * 0.2 - 0.1).tolist()
    drums = AudioClip(
        "Drums",
        drum_sound,
        44100,
        2.0,
        duration=0.5,
        color="#f59e0b"
    )
    drums.fade_out = 0.05
    
    # Add clips to timeline
    timeline.add_clip(0, melody1)
    timeline.add_clip(0, melody2)
    timeline.add_clip(1, bass)
    timeline.add_clip(2, drums)
    
    print(f"✓ Created {timeline.get_total_clips_count()} clips")
    print(f"  - Track 0 (Melody): {len(timeline.get_clips_for_track(0))} clips")
    print(f"  - Track 1 (Bass): {len(timeline.get_clips_for_track(1))} clips")
    print(f"  - Track 2 (Drums): {len(timeline.get_clips_for_track(2))} clips")
    
    # Set up loop region
    loop_start = 0.0
    loop_end = 4.0
    player.set_loop(True, loop_start, loop_end)
    print(f"\n🔁 Loop region set: {loop_start}s - {loop_end}s")
    
    # Create and show main window
    print("\n🎨 Opening GUI window...")
    print("\n" + "="*60)
    print("KEYBOARD SHORTCUTS:")
    print("="*60)
    print("Selection:")
    print("  • Click           - Select single clip")
    print("  • Ctrl+Click      - Toggle clip selection (multi-select)")
    print()
    print("Clipboard Operations:")
    print("  • Ctrl+C          - Copy selected clips")
    print("  • Ctrl+V          - Paste clips at cursor position")
    print("  • Click Timeline  - Set paste position (green cursor)")
    print("  • Right-Click     - Paste menu at click position")
    print("  • Ctrl+Shift+C    - Copy all clips in loop region")
    print("  • Ctrl+Shift+V    - Paste clips at loop end")
    print()
    print("Editing:")
    print("  • Delete          - Delete selected clips")
    print("  • Ctrl+D          - Duplicate loop region")
    print("  • Right-Click     - Context menu")
    print()
    print("Playback:")
    print("  • Space           - Play/Stop")
    print("  • Shift+Drag      - Set loop region")
    print()
    print("View:")
    print("  • +/-             - Zoom in/out")
    print("  • 0               - Reset zoom")
    print("="*60)
    print()
    print("DEMO INSTRUCTIONS:")
    print("="*60)
    print("1. Try multi-selecting clips with Ctrl+Click")
    print("2. Copy them with Ctrl+C (green cursor appears)")
    print("3. Click anywhere on timeline to set paste position")
    print("4. Press Ctrl+V to paste at the green cursor")
    print("5. Try right-click on empty timeline for paste menu")
    print("6. Try Ctrl+Shift+C to copy the loop region")
    print("7. Then Ctrl+Shift+V to paste at loop end")
    print("8. Right-click on clips to see context menu")
    print("="*60)
    print()
    
    window = MainWindow(
        project=project,
        mixer=mixer,
        transport=player,
        timeline=timeline,
        player=player
    )
    
    window.show()
    window.run()


if __name__ == '__main__':
    main()
