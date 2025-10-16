"""Tests for the refactored window UI components."""

import unittest
from unittest.mock import Mock, MagicMock
from src.ui.window import MainWindow
from src.core.project import Project
from src.audio.mixer import Mixer
from src.core.timeline import Timeline


class TestWindowRefactoring(unittest.TestCase):
    """Test the refactored window components."""

    def setUp(self):
        """Set up test fixtures."""
        self.project = Project("Test Project")
        self.mixer = Mixer()
        self.timeline = Timeline()
        self.transport = Mock()
        self.player = Mock()
        
        # Mock player methods
        self.player.is_playing = Mock(return_value=False)
        self.player.get_loop = Mock(return_value=(False, 0.0, 10.0))
        self.player.set_loop = Mock()
        self.player.get_current_time = Mock(return_value=0.0)
        self.player._current_time = 0.0
        self.player._last_peak_L = 0.0
        self.player._last_peak_R = 0.0

    def test_window_initialization(self):
        """Test window can be initialized with all components."""
        window = MainWindow(
            project=self.project,
            mixer=self.mixer,
            transport=self.transport,
            timeline=self.timeline,
            player=self.player
        )
        
        self.assertEqual(window.project, self.project)
        self.assertEqual(window.mixer, self.mixer)
        self.assertEqual(window.transport, self.transport)
        self.assertEqual(window.timeline, self.timeline)
        self.assertEqual(window.player, self.player)
        self.assertFalse(window.is_open)

    def test_window_console_mode(self):
        """Test window falls back to console mode when tkinter unavailable."""
        window = MainWindow(
            project=self.project,
            mixer=self.mixer,
            transport=self.transport,
            timeline=self.timeline,
            player=self.player
        )
        
        # This should not raise an error even if tk is None
        window.show()
        
        # In console mode or GUI mode, window should be marked as open
        self.assertTrue(window.is_open)
        
        window.close()
        self.assertFalse(window.is_open)

    def test_window_components_creation(self):
        """Test that window components are properly initialized."""
        window = MainWindow(
            project=self.project,
            mixer=self.mixer,
            transport=self.transport,
            timeline=self.timeline,
            player=self.player
        )
        
        # Components should be None before show
        self.assertIsNone(window._timeline_canvas)
        self.assertIsNone(window._track_controls)
        self.assertIsNone(window._menu_manager)
        self.assertIsNone(window._toolbar_manager)

    def test_mixer_track_management(self):
        """Test track can be added through mixer."""
        self.mixer.add_track("Track 1", volume=0.8, pan=0.0)
        self.assertEqual(len(self.mixer.tracks), 1)
        self.assertEqual(self.mixer.tracks[0]["name"], "Track 1")
        self.assertEqual(self.mixer.tracks[0]["volume"], 0.8)

    def test_timeline_clip_management(self):
        """Test clips can be added to timeline."""
        from src.audio.clip import AudioClip
        
        clip = AudioClip("test_clip", [0.1] * 100, 44100, start_time=0.0)
        self.timeline.add_clip(0, clip)
        
        placements = list(self.timeline.all_placements())
        self.assertEqual(len(placements), 1)
        self.assertEqual(placements[0][0], 0)  # track index
        self.assertEqual(placements[0][1].name, "test_clip")

    def test_backward_compatibility_properties(self):
        """Test legacy properties still work for backward compatibility."""
        window = MainWindow(
            project=self.project,
            mixer=self.mixer,
            transport=self.transport,
            timeline=self.timeline,
            player=self.player
        )
        
        # These should not raise errors even if components not initialized
        track_tree = window._track_tree
        volume_var = window._volume_var
        loop_var = window._loop_var
        bpm_var = window._bpm_var
        
        # They should be None when components not initialized
        self.assertIsNone(track_tree)
        self.assertIsNone(volume_var)
        self.assertIsNone(loop_var)
        self.assertIsNone(bpm_var)


if __name__ == "__main__":
    unittest.main()
