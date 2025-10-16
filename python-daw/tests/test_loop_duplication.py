"""Unit tests for loop duplication functionality."""

import unittest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from src.core.timeline import Timeline
from src.audio.clip import AudioClip
from src.audio.mixer import Mixer
from src.audio.player import TimelinePlayer


class TestLoopDuplication(unittest.TestCase):
    """Test cases for loop duplication feature."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.timeline = Timeline()
        self.mixer = Mixer()
        
        # Add tracks
        self.mixer.add_track("Track 1")
        self.mixer.add_track("Track 2")
        
        # Create test player
        self.player = TimelinePlayer(self.timeline, mixer=self.mixer)
    
    def test_duplicate_empty_loop(self):
        """Test duplicating a loop with no clips."""
        # Set loop points
        self.player.set_loop(True, 0.0, 4.0)
        
        # Get clips in loop (should be empty)
        clips_in_loop = list(self.timeline.get_clips_for_range(0.0, 4.0))
        
        self.assertEqual(len(clips_in_loop), 0, "Loop should be empty")
    
    def test_duplicate_single_clip(self):
        """Test duplicating a loop with a single clip."""
        # Create a clip
        clip = AudioClip(
            name="Test Clip",
            buffer=[0.0] * 44100,  # 1 second at 44100Hz
            sample_rate=44100,
            start_time=1.0,
            duration=1.0
        )
        self.timeline.add_clip(0, clip)
        
        # Set loop points
        loop_start = 0.0
        loop_end = 4.0
        self.player.set_loop(True, loop_start, loop_end)
        
        # Duplicate loop
        clips_in_loop = list(self.timeline.get_clips_for_range(loop_start, loop_end))
        self.assertEqual(len(clips_in_loop), 1, "Should have 1 clip in loop")
        
        # Simulate duplication
        for track_idx, original_clip in clips_in_loop:
            offset = original_clip.start_time - loop_start
            new_start = loop_end + offset
            
            new_clip = AudioClip(
                original_clip.name,
                original_clip.buffer,
                original_clip.sample_rate,
                new_start,
                duration=original_clip.duration
            )
            self.timeline.add_clip(track_idx, new_clip)
        
        # Verify
        all_clips = self.timeline.get_clips_for_track(0)
        self.assertEqual(len(all_clips), 2, "Should have 2 clips after duplication")
        
        # Check positions
        self.assertEqual(all_clips[0].start_time, 1.0, "Original clip at 1.0s")
        self.assertEqual(all_clips[1].start_time, 5.0, "Duplicated clip at 5.0s (4.0 + 1.0)")
    
    def test_duplicate_multiple_clips(self):
        """Test duplicating a loop with multiple clips on different tracks."""
        # Create clips
        clip1 = AudioClip("Clip 1", [0.0] * 44100, 44100, 0.5, 1.0)
        clip2 = AudioClip("Clip 2", [0.0] * 88200, 44100, 1.5, 2.0)
        clip3 = AudioClip("Clip 3", [0.0] * 44100, 44100, 2.0, 1.0)
        
        self.timeline.add_clip(0, clip1)
        self.timeline.add_clip(1, clip2)
        self.timeline.add_clip(0, clip3)
        
        # Set loop points
        loop_start = 0.0
        loop_end = 4.0
        self.player.set_loop(True, loop_start, loop_end)
        
        # Get clips in loop
        clips_in_loop = list(self.timeline.get_clips_for_range(loop_start, loop_end))
        self.assertEqual(len(clips_in_loop), 3, "Should have 3 clips in loop")
        
        # Duplicate
        for track_idx, original_clip in clips_in_loop:
            offset = original_clip.start_time - loop_start
            new_start = loop_end + offset
            
            new_clip = AudioClip(
                original_clip.name,
                original_clip.buffer,
                original_clip.sample_rate,
                new_start,
                duration=original_clip.duration
            )
            self.timeline.add_clip(track_idx, new_clip)
        
        # Verify track 0 has 4 clips (2 original + 2 duplicated)
        track0_clips = self.timeline.get_clips_for_track(0)
        self.assertEqual(len(track0_clips), 4, "Track 0 should have 4 clips")
        
        # Verify track 1 has 2 clips (1 original + 1 duplicated)
        track1_clips = self.timeline.get_clips_for_track(1)
        self.assertEqual(len(track1_clips), 2, "Track 1 should have 2 clips")
    
    def test_duplicate_preserves_timing(self):
        """Test that duplication preserves relative timing."""
        # Create clips with specific timing
        clip1 = AudioClip("Early", [0.0] * 22050, 44100, 0.25, 0.5)
        clip2 = AudioClip("Late", [0.0] * 22050, 44100, 3.5, 0.5)
        
        self.timeline.add_clip(0, clip1)
        self.timeline.add_clip(0, clip2)
        
        # Set loop
        loop_start = 0.0
        loop_end = 4.0
        loop_duration = loop_end - loop_start
        
        # Duplicate
        clips_in_loop = list(self.timeline.get_clips_for_range(loop_start, loop_end))
        
        for track_idx, original_clip in clips_in_loop:
            offset = original_clip.start_time - loop_start
            new_start = loop_end + offset
            
            new_clip = AudioClip(
                original_clip.name,
                original_clip.buffer,
                original_clip.sample_rate,
                new_start,
                duration=original_clip.duration
            )
            self.timeline.add_clip(track_idx, new_clip)
        
        # Get all clips
        all_clips = self.timeline.get_clips_for_track(0)
        self.assertEqual(len(all_clips), 4, "Should have 4 clips")
        
        # Verify timing
        self.assertAlmostEqual(all_clips[0].start_time, 0.25, places=2)
        self.assertAlmostEqual(all_clips[1].start_time, 3.5, places=2)
        self.assertAlmostEqual(all_clips[2].start_time, 4.25, places=2)  # 4.0 + 0.25
        self.assertAlmostEqual(all_clips[3].start_time, 7.5, places=2)   # 4.0 + 3.5
    
    def test_partial_overlap(self):
        """Test clips that partially overlap with loop region."""
        # Clip that starts before loop but ends inside
        clip1 = AudioClip("Before", [0.0] * 88200, 44100, -1.0, 2.0)  # -1.0 to 1.0
        
        # Clip that starts inside loop but ends after
        clip2 = AudioClip("After", [0.0] * 88200, 44100, 3.0, 2.0)    # 3.0 to 5.0
        
        # Clip fully inside
        clip3 = AudioClip("Inside", [0.0] * 44100, 44100, 1.5, 1.0)   # 1.5 to 2.5
        
        self.timeline.add_clip(0, clip1)
        self.timeline.add_clip(0, clip2)
        self.timeline.add_clip(0, clip3)
        
        # Set loop
        loop_start = 0.0
        loop_end = 4.0
        
        # Get clips in loop (should include all three due to overlap)
        clips_in_loop = list(self.timeline.get_clips_for_range(loop_start, loop_end))
        self.assertEqual(len(clips_in_loop), 3, "All clips overlap with loop")


if __name__ == '__main__':
    unittest.main()
