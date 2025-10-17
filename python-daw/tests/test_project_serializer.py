"""
Tests for project serialization (save/load functionality).
"""

import pytest
import os
import json
import tempfile
import shutil
from pathlib import Path

import sys
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from src.core.project import Project
from src.core.track import Track
from src.audio.clip import AudioClip
from src.utils.project_serializer import ProjectSerializer, save_project, load_project


class TestProjectSerializer:
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test files."""
        temp = tempfile.mkdtemp()
        yield temp
        # Cleanup
        if os.path.exists(temp):
            shutil.rmtree(temp)
    
    @pytest.fixture
    def sample_project(self):
        """Create a sample project for testing."""
        project = Project(name="Test Project", bpm=140.0, time_signature=(4, 4))
        
        # Track 1 with 2 clips
        track1 = Track()
        track1.set_volume(0.8)
        
        clip1 = AudioClip(
            name="Clip 1",
            buffer=[0.1, 0.2, 0.3, 0.4] * 1000,  # Small buffer
            sample_rate=44100,
            start_time=0.0,
            color="#FF0000"
        )
        clip1.fade_in = 0.1
        clip1.volume = 0.9
        
        clip2 = AudioClip(
            name="Clip 2",
            buffer=[0.5, 0.6, 0.7, 0.8] * 500,
            sample_rate=44100,
            start_time=2.0,
            color="#00FF00"
        )
        clip2.pitch_semitones = 2.0
        
        track1.add_audio(clip1)
        track1.add_audio(clip2)
        
        # Track 2 with 1 clip
        track2 = Track()
        track2.set_volume(0.6)
        
        clip3 = AudioClip(
            name="Clip 3",
            buffer=[0.9, 1.0, 0.8, 0.7] * 750,
            sample_rate=48000,
            start_time=1.0,
        )
        clip3.start_offset = 0.5
        clip3.end_offset = 0.2
        
        track2.add_audio(clip3)
        
        project.create_track(track1)
        project.create_track(track2)
        
        return project
    
    def test_save_project_with_separate_files(self, temp_dir, sample_project):
        """Test saving project with separate audio files."""
        save_path = os.path.join(temp_dir, "test.daw")
        
        save_project(sample_project, save_path, embed_audio=False)
        
        # Check that project file exists
        assert os.path.exists(save_path)
        
        # Check that audio directory exists
        audio_dir = Path(save_path).parent / "test_data" / "audio"
        assert audio_dir.exists()
        
        # Check that audio files were created
        audio_files = list(audio_dir.glob("*.wav"))
        assert len(audio_files) == 3  # 3 clips total
    
    def test_save_project_with_embedded_audio(self, temp_dir, sample_project):
        """Test saving project with embedded audio."""
        save_path = os.path.join(temp_dir, "test_embedded.daw")
        
        save_project(sample_project, save_path, embed_audio=True)
        
        # Check that project file exists
        assert os.path.exists(save_path)
        
        # Check that no audio directory was created
        audio_dir = Path(save_path).parent / "test_embedded_data" / "audio"
        assert not audio_dir.exists()
        
        # Check that JSON contains embedded audio
        with open(save_path, 'r') as f:
            data = json.load(f)
        
        clips = data["project"]["tracks"][0]["clips"]
        assert clips[0]["audio_embedded"] is True
        assert "audio_data" in clips[0]
    
    def test_load_project_with_separate_files(self, temp_dir, sample_project):
        """Test loading project with separate audio files."""
        save_path = os.path.join(temp_dir, "test.daw")
        
        # Save
        save_project(sample_project, save_path, embed_audio=False)
        
        # Load
        loaded = load_project(save_path)
        
        # Verify project properties
        assert loaded.name == sample_project.name
        assert loaded.bpm == sample_project.bpm
        assert loaded.time_signature_num == sample_project.time_signature_num
        assert loaded.time_signature_den == sample_project.time_signature_den
        
        # Verify tracks
        assert len(loaded.tracks) == len(sample_project.tracks)
        assert loaded.tracks[0].volume == sample_project.tracks[0].volume
        assert loaded.tracks[1].volume == sample_project.tracks[1].volume
        
        # Verify clips
        assert len(loaded.tracks[0].audio_files) == 2
        assert len(loaded.tracks[1].audio_files) == 1
        
        clip1 = loaded.tracks[0].audio_files[0]
        assert clip1.name == "Clip 1"
        assert clip1.start_time == 0.0
        assert clip1.color == "#FF0000"
        assert clip1.fade_in == 0.1
        assert clip1.volume == 0.9
        assert len(clip1.buffer) > 0
    
    def test_load_project_with_embedded_audio(self, temp_dir, sample_project):
        """Test loading project with embedded audio."""
        save_path = os.path.join(temp_dir, "test_embedded.daw")
        
        # Save
        save_project(sample_project, save_path, embed_audio=True)
        
        # Load
        loaded = load_project(save_path)
        
        # Verify
        assert loaded.name == sample_project.name
        assert len(loaded.tracks) == 2
        assert len(loaded.tracks[0].audio_files) == 2
        
        # Check that audio buffers were restored
        clip1 = loaded.tracks[0].audio_files[0]
        assert len(clip1.buffer) == len(sample_project.tracks[0].audio_files[0].buffer)
    
    def test_clip_properties_preserved(self, temp_dir, sample_project):
        """Test that all clip properties are preserved during save/load."""
        save_path = os.path.join(temp_dir, "test.daw")
        
        # Save and load
        save_project(sample_project, save_path, embed_audio=False)
        loaded = load_project(save_path)
        
        # Get original and loaded clip
        orig_clip = sample_project.tracks[0].audio_files[1]
        loaded_clip = loaded.tracks[0].audio_files[1]
        
        # Verify all properties
        assert loaded_clip.name == orig_clip.name
        assert loaded_clip.start_time == orig_clip.start_time
        assert loaded_clip.sample_rate == orig_clip.sample_rate
        assert loaded_clip.color == orig_clip.color
        assert loaded_clip.pitch_semitones == orig_clip.pitch_semitones
        assert loaded_clip.fade_in == orig_clip.fade_in
        assert loaded_clip.fade_out == orig_clip.fade_out
        assert loaded_clip.volume == orig_clip.volume
    
    def test_trim_properties_preserved(self, temp_dir, sample_project):
        """Test that trim/offset properties are preserved."""
        save_path = os.path.join(temp_dir, "test.daw")
        
        # Save and load
        save_project(sample_project, save_path, embed_audio=False)
        loaded = load_project(save_path)
        
        # Get clip with offsets
        orig_clip = sample_project.tracks[1].audio_files[0]
        loaded_clip = loaded.tracks[1].audio_files[0]
        
        assert loaded_clip.start_offset == orig_clip.start_offset
        assert loaded_clip.end_offset == orig_clip.end_offset
    
    def test_save_empty_project(self, temp_dir):
        """Test saving an empty project."""
        project = Project(name="Empty", bpm=120.0)
        save_path = os.path.join(temp_dir, "empty.daw")
        
        save_project(project, save_path)
        loaded = load_project(save_path)
        
        assert loaded.name == "Empty"
        assert loaded.bpm == 120.0
        assert len(loaded.tracks) == 0
    
    def test_save_project_with_no_clips(self, temp_dir):
        """Test saving project with tracks but no clips."""
        project = Project(name="No Clips", bpm=130.0)
        track = Track()
        project.create_track(track)
        
        save_path = os.path.join(temp_dir, "noclips.daw")
        save_project(project, save_path)
        loaded = load_project(save_path)
        
        assert len(loaded.tracks) == 1
        assert len(loaded.tracks[0].audio_files) == 0
    
    def test_load_nonexistent_file(self):
        """Test loading a file that doesn't exist."""
        with pytest.raises(FileNotFoundError):
            load_project("nonexistent.daw")
    
    def test_serializer_version(self, temp_dir, sample_project):
        """Test that version is saved in the project file."""
        save_path = os.path.join(temp_dir, "test.daw")
        
        save_project(sample_project, save_path)
        
        with open(save_path, 'r') as f:
            data = json.load(f)
        
        assert "version" in data
        assert data["version"] == ProjectSerializer.VERSION


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
