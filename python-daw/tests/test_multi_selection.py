"""Unit tests for multi-selection and copy/paste functionality."""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.timeline import Timeline
from src.audio.clip import AudioClip
from src.audio.mixer import Mixer
from src.audio.player import TimelinePlayer
from src.ui.timeline_canvas import TimelineCanvas
from unittest.mock import Mock


class TestMultiSelection(unittest.TestCase):
    """Test cases for multi-selection and copy/paste features."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.timeline = Timeline()
        self.mixer = Mixer()
        self.player = Mock()
        
        # Mock player methods
        self.player.is_playing = Mock(return_value=False)
        self.player.get_loop = Mock(return_value=(True, 0.0, 4.0))
        self.player.set_loop = Mock()
        self.player.get_current_time = Mock(return_value=0.0)
        self.player._current_time = 0.0
        
        # Add tracks
        self.mixer.add_track("Track 1")
        self.mixer.add_track("Track 2")
        
        # Create timeline canvas (without GUI)
        self.canvas = TimelineCanvas(
            parent=None,
            project=None,
            mixer=self.mixer,
            timeline=self.timeline,
            player=self.player
        )
    
    def test_multi_selection(self):
        """Test selecting multiple clips."""
        # Create clips
        clip1 = AudioClip("Clip 1", [0.1] * 44100, 44100, 1.0, duration=1.0)
        clip2 = AudioClip("Clip 2", [0.1] * 44100, 44100, 2.0, duration=1.0)
        clip3 = AudioClip("Clip 3", [0.1] * 44100, 44100, 3.0, duration=1.0)
        
        self.timeline.add_clip(0, clip1)
        self.timeline.add_clip(0, clip2)
        self.timeline.add_clip(1, clip3)
        
        # Select first clip
        self.canvas.select_clip(0, clip1)
        self.assertEqual(len(self.canvas.selected_clips), 1)
        self.assertEqual(self.canvas.selected_clips[0], (0, clip1))
        
        # Toggle second clip (add to selection)
        self.canvas.toggle_clip_selection(0, clip2)
        self.assertEqual(len(self.canvas.selected_clips), 2)
        self.assertIn((0, clip1), self.canvas.selected_clips)
        self.assertIn((0, clip2), self.canvas.selected_clips)
        
        # Toggle third clip
        self.canvas.toggle_clip_selection(1, clip3)
        self.assertEqual(len(self.canvas.selected_clips), 3)
        
        # Toggle second clip again (deselect)
        self.canvas.toggle_clip_selection(0, clip2)
        self.assertEqual(len(self.canvas.selected_clips), 2)
        self.assertNotIn((0, clip2), self.canvas.selected_clips)
    
    def test_copy_paste_single_clip(self):
        """Test copying and pasting a single clip."""
        # Create clip
        clip = AudioClip("Test Clip", [0.1] * 44100, 44100, 1.0, duration=1.0)
        clip.fade_in = 0.1
        clip.fade_out = 0.2
        clip.pitch_semitones = 2.0
        
        self.timeline.add_clip(0, clip)
        
        # Select and copy
        self.canvas.select_clip(0, clip)
        result = self.canvas.copy_selected_clips()
        self.assertTrue(result)
        self.assertEqual(len(self.canvas.clipboard), 1)
        
        # Paste at time 5.0
        pasted = self.canvas.paste_clips(at_time=5.0)
        self.assertEqual(len(pasted), 1)
        
        track_idx, pasted_clip = pasted[0]
        self.assertEqual(track_idx, 0)
        self.assertEqual(pasted_clip.start_time, 5.0)
        self.assertEqual(pasted_clip.fade_in, 0.1)
        self.assertEqual(pasted_clip.fade_out, 0.2)
        self.assertEqual(pasted_clip.pitch_semitones, 2.0)
        self.assertIn("(paste)", pasted_clip.name)
    
    def test_copy_paste_multiple_clips(self):
        """Test copying and pasting multiple clips."""
        # Create clips
        clip1 = AudioClip("Clip 1", [0.1] * 44100, 44100, 1.0, duration=1.0)
        clip2 = AudioClip("Clip 2", [0.1] * 44100, 44100, 2.5, duration=1.0)
        clip3 = AudioClip("Clip 3", [0.1] * 44100, 44100, 1.5, duration=0.5)
        
        self.timeline.add_clip(0, clip1)
        self.timeline.add_clip(0, clip2)
        self.timeline.add_clip(1, clip3)
        
        # Select all clips
        self.canvas.selected_clips = [(0, clip1), (0, clip2), (1, clip3)]
        
        # Copy
        result = self.canvas.copy_selected_clips()
        self.assertTrue(result)
        self.assertEqual(len(self.canvas.clipboard), 3)
        
        # Paste at time 10.0
        pasted = self.canvas.paste_clips(at_time=10.0)
        self.assertEqual(len(pasted), 3)
        
        # Check relative timing is preserved
        # Original earliest clip was at 1.0, so offset is 9.0 (10.0 - 1.0)
        times = [clip.start_time for _, clip in pasted]
        self.assertIn(10.0, times)  # clip1: 1.0 + 9.0
        self.assertIn(11.5, times)  # clip2: 2.5 + 9.0
        self.assertIn(10.5, times)  # clip3: 1.5 + 9.0
    
    def test_copy_paste_preserves_properties(self):
        """Test that copy/paste preserves all clip properties."""
        # Create clip with all properties
        clip = AudioClip("Test", [0.1] * 44100, 44100, 2.0, duration=1.5)
        clip.start_offset = 0.1
        clip.end_offset = 0.2
        clip.fade_in = 0.15
        clip.fade_in_shape = "exp"
        clip.fade_out = 0.25
        clip.fade_out_shape = "log"
        clip.pitch_semitones = -3.5
        clip.volume = 0.8
        clip.color = "#ff0000"
        clip.file_path = "/test/path.wav"
        
        self.timeline.add_clip(0, clip)
        
        # Copy and paste
        self.canvas.select_clip(0, clip)
        self.canvas.copy_selected_clips()
        pasted = self.canvas.paste_clips(at_time=5.0)
        
        _, pasted_clip = pasted[0]
        
        # Verify all properties
        self.assertEqual(pasted_clip.duration, 1.5)
        self.assertEqual(pasted_clip.start_offset, 0.1)
        self.assertEqual(pasted_clip.end_offset, 0.2)
        self.assertEqual(pasted_clip.fade_in, 0.15)
        self.assertEqual(pasted_clip.fade_in_shape, "exp")
        self.assertEqual(pasted_clip.fade_out, 0.25)
        self.assertEqual(pasted_clip.fade_out_shape, "log")
        self.assertEqual(pasted_clip.pitch_semitones, -3.5)
        self.assertEqual(pasted_clip.volume, 0.8)
        self.assertEqual(pasted_clip.color, "#ff0000")
        self.assertEqual(pasted_clip.file_path, "/test/path.wav")
    
    def test_clear_selection(self):
        """Test clearing selection."""
        # Create and select clips
        clip1 = AudioClip("Clip 1", [0.1] * 44100, 44100, 1.0)
        clip2 = AudioClip("Clip 2", [0.1] * 44100, 44100, 2.0)
        
        self.timeline.add_clip(0, clip1)
        self.timeline.add_clip(0, clip2)
        
        self.canvas.selected_clips = [(0, clip1), (0, clip2)]
        self.canvas.selected_clip = (0, clip1)
        
        # Clear selection
        self.canvas.clear_selection()
        
        self.assertEqual(len(self.canvas.selected_clips), 0)
        self.assertIsNone(self.canvas.selected_clip)
    
    def test_paste_empty_clipboard(self):
        """Test pasting when clipboard is empty."""
        pasted = self.canvas.paste_clips()
        self.assertEqual(len(pasted), 0)
    
    def test_copy_with_no_selection(self):
        """Test copying with no clips selected."""
        result = self.canvas.copy_selected_clips()
        self.assertFalse(result)
        self.assertEqual(len(self.canvas.clipboard), 0)
    
    def test_paste_position_cursor(self):
        """Test paste position cursor functionality."""
        # Create and copy clip
        clip = AudioClip("Test", [0.1] * 44100, 44100, 1.0, duration=1.0)
        self.timeline.add_clip(0, clip)
        
        self.canvas.select_clip(0, clip)
        self.canvas.copy_selected_clips()
        
        # Verify paste cursor is visible after copy
        self.assertTrue(self.canvas.paste_cursor_visible)
        
        # Set custom paste position
        self.canvas.paste_position = 7.5
        self.canvas.paste_cursor_visible = True
        
        # Paste should use paste_position
        pasted = self.canvas.paste_clips()
        self.assertEqual(len(pasted), 1)
        
        _, pasted_clip = pasted[0]
        self.assertEqual(pasted_clip.start_time, 7.5)
        
        # Paste cursor should be hidden after pasting
        self.assertFalse(self.canvas.paste_cursor_visible)
    
    def test_paste_position_priority(self):
        """Test paste position priority (at_time > paste_position > current_time)."""
        clip = AudioClip("Test", [0.1] * 44100, 44100, 1.0, duration=1.0)
        self.timeline.add_clip(0, clip)
        
        self.canvas.select_clip(0, clip)
        self.canvas.copy_selected_clips()
        
        # Set paste position
        self.canvas.paste_position = 5.0
        self.canvas.paste_cursor_visible = True
        
        # Set player time
        self.player._current_time = 3.0
        
        # 1. Without at_time, should use paste_position (5.0)
        pasted = self.canvas.paste_clips()
        _, clip1 = pasted[0]
        self.assertEqual(clip1.start_time, 5.0)
        
        # Copy again
        self.canvas.copy_selected_clips()
        
        # 2. With explicit at_time, should override paste_position
        pasted = self.canvas.paste_clips(at_time=10.0)
        _, clip2 = pasted[0]
        self.assertEqual(clip2.start_time, 10.0)
        
        # Copy again and hide paste cursor
        self.canvas.copy_selected_clips()
        self.canvas.paste_cursor_visible = False
        
        # 3. Without paste_position visible, should use current_time (3.0)
        pasted = self.canvas.paste_clips()
        _, clip3 = pasted[0]
        self.assertEqual(clip3.start_time, 3.0)


if __name__ == '__main__':
    unittest.main()
