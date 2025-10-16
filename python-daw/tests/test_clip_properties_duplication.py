"""Tests for clip properties duplication (trim, fades, pitch)."""

import unittest
from src.audio.clip import AudioClip
from src.core.timeline import Timeline
from src.ui.window import MainWindow
from src.audio.mixer import Mixer
from src.core.project import Project
from unittest.mock import Mock


class TestClipPropertiesDuplication(unittest.TestCase):
    """Test that clip editing properties are preserved during duplication."""

    def setUp(self):
        """Set up test fixtures."""
        self.project = Project("Test Project")
        self.mixer = Mixer()
        self.timeline = Timeline()
        self.transport = Mock()
        self.player = Mock()
        
        # Mock player methods
        self.player.is_playing = Mock(return_value=False)
        self.player.get_loop = Mock(return_value=(True, 0.0, 2.0))
        self.player.set_loop = Mock()
        self.player.get_current_time = Mock(return_value=0.0)
        self.player._current_time = 0.0
        self.player._last_peak_L = 0.0
        self.player._last_peak_R = 0.0

    def test_clone_clip_copies_all_properties(self):
        """Test that _clone_clip copies all editing properties."""
        window = MainWindow(
            project=self.project,
            mixer=self.mixer,
            transport=self.transport,
            timeline=self.timeline,
            player=self.player
        )
        
        # Create source clip with custom properties
        source_clip = AudioClip(
            "Test Clip",
            [0.1] * 44100,
            44100,
            start_time=1.0,
            duration=2.0,
            color="#ff0000",
            file_path="/test/audio.wav"
        )
        
        # Set editing properties
        source_clip.start_offset = 0.5
        source_clip.end_offset = 0.3
        source_clip.fade_in = 0.2
        source_clip.fade_in_shape = "exp"
        source_clip.fade_out = 0.4
        source_clip.fade_out_shape = "log"
        source_clip.pitch_semitones = 2.5
        
        # Clone the clip
        cloned_clip = window._clone_clip(source_clip, new_start_time=5.0)
        
        # Verify basic properties
        self.assertEqual(cloned_clip.name, "Test Clip")
        self.assertEqual(cloned_clip.start_time, 5.0)
        self.assertEqual(cloned_clip.duration, 2.0)
        self.assertEqual(cloned_clip.color, "#ff0000")
        self.assertEqual(cloned_clip.file_path, "/test/audio.wav")
        self.assertEqual(cloned_clip.sample_rate, 44100)
        self.assertEqual(len(cloned_clip.buffer), 44100)
        
        # Verify editing properties are copied
        self.assertEqual(cloned_clip.start_offset, 0.5)
        self.assertEqual(cloned_clip.end_offset, 0.3)
        self.assertEqual(cloned_clip.fade_in, 0.2)
        self.assertEqual(cloned_clip.fade_in_shape, "exp")
        self.assertEqual(cloned_clip.fade_out, 0.4)
        self.assertEqual(cloned_clip.fade_out_shape, "log")
        self.assertEqual(cloned_clip.pitch_semitones, 2.5)

    def test_clone_clip_with_custom_name(self):
        """Test that _clone_clip accepts custom name."""
        window = MainWindow(
            project=self.project,
            mixer=self.mixer,
            transport=self.transport,
            timeline=self.timeline,
            player=self.player
        )
        
        source_clip = AudioClip("Original", [0.1] * 100, 44100, 0.0)
        cloned_clip = window._clone_clip(source_clip, 5.0, name="Copy")
        
        self.assertEqual(cloned_clip.name, "Copy")

    def test_clone_clip_handles_missing_properties(self):
        """Test that _clone_clip handles clips without new properties gracefully."""
        window = MainWindow(
            project=self.project,
            mixer=self.mixer,
            transport=self.transport,
            timeline=self.timeline,
            player=self.player
        )
        
        # Create a basic clip (simulating old clips without editing properties)
        source_clip = AudioClip("Basic", [0.1] * 100, 44100, 0.0)
        
        # Remove properties to simulate old clip
        if hasattr(source_clip, 'start_offset'):
            delattr(source_clip, 'start_offset')
        if hasattr(source_clip, 'fade_in'):
            delattr(source_clip, 'fade_in')
        if hasattr(source_clip, 'pitch_semitones'):
            delattr(source_clip, 'pitch_semitones')
        
        # Clone should still work with defaults
        cloned_clip = window._clone_clip(source_clip, 5.0)
        
        self.assertEqual(cloned_clip.start_offset, 0.0)
        self.assertEqual(cloned_clip.end_offset, 0.0)
        self.assertEqual(cloned_clip.fade_in, 0.0)
        self.assertEqual(cloned_clip.fade_in_shape, 'linear')
        self.assertEqual(cloned_clip.fade_out, 0.0)
        self.assertEqual(cloned_clip.fade_out_shape, 'linear')
        self.assertEqual(cloned_clip.pitch_semitones, 0.0)

    def test_duplicate_loop_preserves_properties(self):
        """Test that duplicating loop region preserves all clip properties."""
        # Add track to mixer
        self.mixer.add_track("Track 1")
        
        # Create clip with editing properties inside loop region
        clip = AudioClip("Loop Clip", [0.1] * 44100, 44100, 0.5, duration=1.0)
        clip.start_offset = 0.1
        clip.end_offset = 0.2
        clip.fade_in = 0.15
        clip.fade_in_shape = "s-curve"
        clip.fade_out = 0.25
        clip.fade_out_shape = "exp"
        clip.pitch_semitones = -3.0
        
        self.timeline.add_clip(0, clip)
        
        # Create window and duplicate loop
        window = MainWindow(
            project=self.project,
            mixer=self.mixer,
            transport=self.transport,
            timeline=self.timeline,
            player=self.player
        )
        
        # Duplicate loop (loop is 0.0-2.0, clip is at 0.5)
        window._duplicate_loop()
        
        # Get all clips
        all_clips = list(self.timeline.all_placements())
        self.assertEqual(len(all_clips), 2)
        
        # Find the duplicated clip (should be at 2.5 = loop_end + offset)
        duplicated_clip = None
        for track_idx, c in all_clips:
            if c.start_time > 2.0:
                duplicated_clip = c
                break
        
        self.assertIsNotNone(duplicated_clip)
        self.assertAlmostEqual(duplicated_clip.start_time, 2.5, places=5)
        
        # Verify all properties are preserved
        self.assertEqual(duplicated_clip.start_offset, 0.1)
        self.assertEqual(duplicated_clip.end_offset, 0.2)
        self.assertEqual(duplicated_clip.fade_in, 0.15)
        self.assertEqual(duplicated_clip.fade_in_shape, "s-curve")
        self.assertEqual(duplicated_clip.fade_out, 0.25)
        self.assertEqual(duplicated_clip.fade_out_shape, "exp")
        self.assertEqual(duplicated_clip.pitch_semitones, -3.0)


if __name__ == "__main__":
    unittest.main()
