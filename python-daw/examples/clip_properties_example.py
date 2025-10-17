"""Example demonstrating the improved Clip Inspector with real-time updates.

This example shows:
1. Creating an audio clip
2. Opening the Clip Inspector dialog
3. Real-time parameter adjustments with sliders
4. Volume control
5. All changes apply immediately without clicking Apply button
"""

from src.audio.clip import AudioClip
from src.ui.clip_inspector import show_clip_inspector
import tkinter as tk
from tkinter import ttk
import math


def generate_test_audio(duration_sec=2.0, sample_rate=44100, frequency=440.0):
    """Generate a simple sine wave for testing."""
    num_samples = int(duration_sec * sample_rate)
    samples = []
    for i in range(num_samples):
        t = i / sample_rate
        sample = 0.3 * math.sin(2.0 * math.pi * frequency * t)
        samples.append(sample)
    return samples


def main():
    """Run the clip inspector example."""
    # Create main window
    root = tk.Tk()
    root.title("Clip Inspector Example")
    root.geometry("400x200")
    root.configure(bg="#1e1e1e")
    
    # Generate test audio
    print("Generating test audio...")
    buffer = generate_test_audio(duration_sec=2.0)
    
    # Create audio clip
    clip = AudioClip(
        name="Test Audio",
        buffer=buffer,
        sample_rate=44100,
        start_time=0.0,
        duration=2.0
    )
    
    # Set some initial properties
    clip.volume = 1.0
    clip.pitch_semitones = 0.0
    clip.fade_in = 0.1
    clip.fade_out = 0.1
    
    def on_property_change(updated_clip):
        """Callback when clip properties change."""
        print(f"\nClip properties updated:")
        print(f"  Volume: {updated_clip.volume:.2f}")
        print(f"  Pitch: {updated_clip.pitch_semitones:.1f} semitones")
        print(f"  Start offset: {updated_clip.start_offset:.3f} s")
        print(f"  End offset: {updated_clip.end_offset:.3f} s")
        print(f"  Fade in: {updated_clip.fade_in:.3f} s ({updated_clip.fade_in_shape})")
        print(f"  Fade out: {updated_clip.fade_out:.3f} s ({updated_clip.fade_out_shape})")
    
    def open_inspector():
        """Open the clip inspector dialog."""
        show_clip_inspector(root, clip, on_apply=on_property_change)
    
    # Create UI
    frame = ttk.Frame(root, padding=20)
    frame.pack(expand=True)
    
    info_text = """Clip Inspector Features:

• Real-time updates - no Apply button needed!
• Volume control (0.0 to 2.0)
• Pitch shift (-12 to +12 semitones)
• Trim controls (start/end offset)
• Fade in/out with shape selection
• Intuitive sliders instead of text fields
"""
    
    label = tk.Label(
        frame,
        text=info_text,
        bg="#1e1e1e",
        fg="#f5f5f5",
        font=("Segoe UI", 10),
        justify="left"
    )
    label.pack(pady=10)
    
    btn = ttk.Button(
        frame,
        text="Open Clip Inspector",
        command=open_inspector
    )
    btn.pack(pady=10)
    
    print("\nClick 'Open Clip Inspector' to test the new interface!")
    print("All changes apply immediately as you move the sliders.\n")
    
    root.mainloop()


if __name__ == "__main__":
    main()
