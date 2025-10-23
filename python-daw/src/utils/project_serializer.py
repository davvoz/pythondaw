"""
Project serialization and deserialization utilities.

Handles saving/loading complete DAW projects including:
- Project metadata (BPM, time signature, etc.)
- Tracks and their properties
- Audio clips with samples
- Effects chains
- MIDI sequences
- Timeline placements
"""

import json
import os
import shutil
import base64
from typing import Dict, Any, Optional, List
from pathlib import Path
import wave
import sys


def _import_project():
    """Helper to import Project class."""
    try:
        from ..core.project import Project
        return Project
    except (ImportError, ValueError):
        # Fallback for when run as script
        import sys
        from pathlib import Path
        src_path = Path(__file__).parent.parent
        if str(src_path) not in sys.path:
            sys.path.insert(0, str(src_path))
        from core.project import Project
        return Project


def _import_track():
    """Helper to import Track class."""
    try:
        from ..core.track import Track
        return Track
    except (ImportError, ValueError):
        from core.track import Track
        return Track


def _import_audioclip():
    """Helper to import AudioClip class."""
    try:
        from ..audio.clip import AudioClip
        return AudioClip
    except (ImportError, ValueError):
        from audio.clip import AudioClip
        return AudioClip


class ProjectSerializer:
    """Handles serialization and deserialization of DAW projects."""
    
    VERSION = "1.0.0"
    
    def __init__(self):
        self.project_dir: Optional[Path] = None
        self.audio_dir: Optional[Path] = None
        
    def save_project(self, project, file_path: str, embed_audio: bool = False) -> None:
        """
        Save a complete project to disk.
        
        Args:
            project: Project instance to save
            file_path: Path to the .daw project file
            embed_audio: If True, embed audio data in JSON. If False, copy files to project folder.
        """
        file_path = Path(file_path)
        
        # Create project directory structure
        self.project_dir = file_path.parent / f"{file_path.stem}_data"
        self.audio_dir = self.project_dir / "audio"
        
        # Create directories
        self.project_dir.mkdir(parents=True, exist_ok=True)
        if not embed_audio:
            self.audio_dir.mkdir(exist_ok=True)
        
        # Serialize project data
        project_data = {
            "version": self.VERSION,
            "project": self._serialize_project(project, embed_audio),
        }
        
        # Save JSON
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(project_data, f, indent=2)
        
        print(f"Project saved to: {file_path}")
        if not embed_audio and self.audio_dir.exists():
            print(f"Audio files saved to: {self.audio_dir}")
    
    def load_project(self, file_path: str):
        """
        Load a complete project from disk.
        
        Args:
            file_path: Path to the .daw project file
            
        Returns:
            Reconstructed Project instance
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"Project file not found: {file_path}")
        
        # Set up paths
        self.project_dir = file_path.parent / f"{file_path.stem}_data"
        self.audio_dir = self.project_dir / "audio"
        
        # Load JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            project_data = json.load(f)
        
        # Check version
        version = project_data.get("version", "0.0.0")
        if version != self.VERSION:
            print(f"Warning: Project version {version} differs from current {self.VERSION}")
        
        # Deserialize project
        project = self._deserialize_project(project_data["project"])
        
        print(f"Project loaded from: {file_path}")
        return project
    
    def _serialize_project(self, project, embed_audio: bool) -> Dict[str, Any]:
        """Serialize Project instance to dictionary."""
        return {
            "name": project.name,
            "bpm": project.bpm,
            "time_signature": [project.time_signature_num, project.time_signature_den],
            "tracks": [self._serialize_track(track, i, embed_audio) 
                      for i, track in enumerate(project.tracks)],
        }
    
    def _serialize_track(self, track, track_index: int, embed_audio: bool) -> Dict[str, Any]:
        """Serialize Track instance to dictionary."""
        # Effects chain (optional)
        effects_conf = []
        try:
            fx_chain = getattr(track, 'effects', None)
            if fx_chain and hasattr(fx_chain, 'to_config'):
                effects_conf = fx_chain.to_config()
        except Exception:
            effects_conf = []
        
        # Determine track type from clips (if any MIDI clip, it's a MIDI track)
        track_type = "audio"
        try:
            from ..midi.clip import MidiClip
            for clip in track.audio_files:
                if isinstance(clip, MidiClip):
                    track_type = "midi"
                    break
        except Exception:
            pass

        return {
            "index": track_index,
            "name": getattr(track, 'name', f"Track {track_index + 1}"),
            "volume": track.volume,
            "type": track_type,
            "effects": effects_conf,
            "clips": [self._serialize_clip(clip, track_index, i, embed_audio) 
                     for i, clip in enumerate(track.audio_files)],
            # Include synthesizer settings for MIDI tracks if present
            "synth": None if track_type != 'midi' else self._serialize_synth(getattr(track, 'instrument', None)),
        }
    
    def _serialize_clip(self, clip, track_index: int, clip_index: int, 
                       embed_audio: bool) -> Dict[str, Any]:
        """Serialize a clip (AudioClip or MidiClip) to dictionary."""
        # Detect MIDI clip
        is_midi = False
        try:
            from ..midi.clip import MidiClip  # type: ignore
            is_midi = isinstance(clip, MidiClip)
        except Exception:
            is_midi = False

        clip_data = {
            "name": clip.name,
            "start_time": clip.start_time,
            "duration": clip.duration,
            "sample_rate": getattr(clip, 'sample_rate', 44100),
            "color": clip.color,
            "selected": clip.selected,
            "type": "midi" if is_midi else "audio",
        }
        if not is_midi:
            # AudioClip specific props
            clip_data.update({
                "start_offset": getattr(clip, 'start_offset', 0.0),
                "end_offset": getattr(clip, 'end_offset', 0.0),
                "fade_in": getattr(clip, 'fade_in', 0.0),
                "fade_in_shape": getattr(clip, 'fade_in_shape', 'linear'),
                "fade_out": getattr(clip, 'fade_out', 0.0),
                "fade_out_shape": getattr(clip, 'fade_out_shape', 'linear'),
                "pitch_semitones": getattr(clip, 'pitch_semitones', 0.0),
                "volume": getattr(clip, 'volume', 1.0),
            })
            # Handle audio data
            if embed_audio:
                # Embed audio data directly in JSON (base64 encoded)
                clip_data["audio_embedded"] = True
                clip_data["audio_data"] = self._encode_audio_buffer(clip.buffer)
            else:
                # Save audio to separate file
                audio_filename = f"track{track_index}_clip{clip_index}_{clip.name}.wav"
                audio_path = self.audio_dir / audio_filename
                
                self._save_audio_file(
                    audio_path,
                    clip.buffer,
                    clip.sample_rate
                )
                
                clip_data["audio_embedded"] = False
                clip_data["audio_file"] = audio_filename
                clip_data["original_file_path"] = clip.file_path
        else:
            # MIDI clip specific props
            try:
                notes = getattr(clip, 'notes', []) or []
                clip_data["notes"] = [
                    {"pitch": int(n.pitch), "start": float(n.start), "duration": float(n.duration), "velocity": int(getattr(n, 'velocity', 100))}
                    for n in notes
                ]
            except Exception:
                clip_data["notes"] = []
        
        return clip_data

    def _serialize_synth(self, instrument) -> Optional[Dict[str, Any]]:
        """Serialize Synthesizer parameters, if available."""
        if instrument is None:
            return None
        try:
            from ..instruments.synthesizer import Synthesizer
        except Exception:
            Synthesizer = None
        if Synthesizer is None or not isinstance(instrument, Synthesizer):
            return None
        try:
            return {
                "oscillator_type": getattr(instrument, 'oscillator_type', 'sine'),
                "volume": getattr(instrument, 'volume', 1.0),
                "attack": getattr(instrument, 'attack', 0.005),
                "decay": getattr(instrument, 'decay', 0.05),
                "sustain": getattr(instrument, 'sustain', 0.7),
                "release": getattr(instrument, 'release', 0.1),
            }
        except Exception:
            return None
    
    def _deserialize_project(self, data: Dict[str, Any]):
        """Deserialize dictionary to Project instance."""
        Project = _import_project()
        
        project = Project(
            name=data["name"],
            bpm=data["bpm"],
            time_signature=tuple(data["time_signature"])
        )
        
        # Load tracks
        for track_data in data["tracks"]:
            track = self._deserialize_track(track_data)
            project.create_track(track)
        
        return project
    
    def _deserialize_track(self, data: Dict[str, Any]):
        """Deserialize dictionary to Track instance."""
        Track = _import_track()
        
        track = Track(name=data.get("name"))
        track.volume = data["volume"]
        track.type = data.get("type", "audio")  # Load track type
        
        # Create instrument for MIDI tracks
        if track.type == "midi":
            try:
                from ..instruments.synthesizer import Synthesizer
                track.instrument = Synthesizer()
            except Exception:
                track.instrument = None
            # Restore synth parameters if present
            try:
                synth_conf = data.get("synth")
                if synth_conf and track.instrument is not None:
                    inst = track.instrument
                    inst.oscillator_type = synth_conf.get("oscillator_type", getattr(inst, 'oscillator_type', 'sine'))
                    inst.volume = float(synth_conf.get("volume", getattr(inst, 'volume', 1.0)))
                    inst.attack = float(synth_conf.get("attack", getattr(inst, 'attack', 0.005)))
                    inst.decay = float(synth_conf.get("decay", getattr(inst, 'decay', 0.05)))
                    inst.sustain = float(synth_conf.get("sustain", getattr(inst, 'sustain', 0.7)))
                    inst.release = float(synth_conf.get("release", getattr(inst, 'release', 0.1)))
            except Exception:
                pass
        
        # Restore effects chain if present
        try:
            effects_conf = data.get("effects")
            if effects_conf:
                # simple registry: map known effect types
                try:
                    from ..effects.reverb import Reverb
                    from ..effects.delay import Delay
                    from ..effects.compressor import Compressor
                    from ..effects.equalizer import Equalizer
                except ImportError:
                    # Fallback for running from examples
                    from effects.reverb import Reverb
                    from effects.delay import Delay
                    from effects.compressor import Compressor
                    from effects.equalizer import Equalizer
                
                registry = {
                    'Reverb': Reverb,
                    'Delay': Delay,
                    'Compressor': Compressor,
                    'Equalizer': Equalizer,
                    'Equalizer (Simple Gain)': Equalizer,
                }
                fx_chain = getattr(track, 'effects', None)
                if fx_chain and hasattr(fx_chain, 'from_config'):
                    fx_chain.from_config(effects_conf, registry=registry)
        except Exception as e:
            import traceback
            print(f"Warning: Failed to restore effects: {e}")
            traceback.print_exc()
        
        # Load clips
        for clip_data in data["clips"]:
            clip = self._deserialize_clip(clip_data)
            track.add_audio(clip)
        
        return track
    
    def _deserialize_clip(self, data: Dict[str, Any]):
        """Deserialize dictionary to a clip instance (AudioClip or MidiClip)."""
        clip_type = data.get("type", "audio")
        if clip_type == 'midi':
            try:
                from ..midi.clip import MidiClip
                from ..midi.note import MidiNote
            except Exception:
                MidiClip = None
                MidiNote = None
            if MidiClip is None:
                # Fallback to empty AudioClip of silence if MIDI not available
                AudioClip = _import_audioclip()
                clip = AudioClip(
                    name=data["name"], buffer=[0.0] * int(0.5 * data.get("sample_rate", 44100)),
                    sample_rate=data.get("sample_rate", 44100), start_time=data["start_time"],
                    duration=data.get("duration", 0.5), color=data.get("color")
                )
                clip.selected = data.get("selected", False)
                return clip
            # Rebuild notes
            notes = []
            for nd in data.get("notes", []):
                try:
                    notes.append(MidiNote(int(nd.get("pitch", 60)), float(nd.get("start", 0.0)), float(nd.get("duration", 0.25)), int(nd.get("velocity", 100))))
                except Exception:
                    continue
            
            # For existing clips with notes: ignore saved duration, calculate from notes
            # For empty clips: keep saved duration if present
            # This ensures clips with notes always match their content exactly
            loaded_duration = data.get("duration")
            if notes:
                # Has notes: ignore duration, will be calculated from notes
                loaded_duration = None
            
            clip = MidiClip(
                name=data["name"], notes=notes, start_time=data["start_time"],
                duration=loaded_duration, color=data.get("color"),
                instrument=None, sample_rate=data.get("sample_rate", 44100)
            )
            clip.selected = data.get("selected", False)
            return clip

        # Audio clip path
        AudioClip = _import_audioclip()
        # Load audio buffer
        if data.get("audio_embedded", False):
            buffer = self._decode_audio_buffer(data.get("audio_data", ""))
        else:
            audio_path = self.audio_dir / data.get("audio_file", "")
            buffer = self._load_audio_file(audio_path, data.get("sample_rate", 44100))
        clip = AudioClip(
            name=data["name"],
            buffer=buffer,
            sample_rate=data.get("sample_rate", 44100),
            start_time=data["start_time"],
            duration=data.get("duration"),
            color=data.get("color"),
            file_path=data.get("original_file_path")
        )
        clip.selected = data.get("selected", False)
        clip.start_offset = data.get("start_offset", 0.0)
        clip.end_offset = data.get("end_offset", 0.0)
        clip.fade_in = data.get("fade_in", 0.0)
        clip.fade_in_shape = data.get("fade_in_shape", "linear")
        clip.fade_out = data.get("fade_out", 0.0)
        clip.fade_out_shape = data.get("fade_out_shape", "linear")
        clip.pitch_semitones = data.get("pitch_semitones", 0.0)
        clip.volume = data.get("volume", 1.0)
        return clip
    
    def _encode_audio_buffer(self, buffer: List[float]) -> str:
        """Encode audio buffer to base64 string."""
        # Convert to bytes (float32)
        import struct
        byte_data = b''.join(struct.pack('f', sample) for sample in buffer)
        return base64.b64encode(byte_data).decode('ascii')
    
    def _decode_audio_buffer(self, encoded: str) -> List[float]:
        """Decode base64 string to audio buffer."""
        import struct
        byte_data = base64.b64decode(encoded.encode('ascii'))
        num_samples = len(byte_data) // 4
        return [struct.unpack('f', byte_data[i*4:(i+1)*4])[0] 
                for i in range(num_samples)]
    
    def _save_audio_file(self, path: Path, buffer: List[float], sample_rate: int) -> None:
        """Save audio buffer to WAV file."""
        import struct
        
        with wave.open(str(path), 'wb') as wav_file:
            # Set parameters: mono, 16-bit
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)  # 2 bytes = 16-bit
            wav_file.setframerate(sample_rate)
            
            # Convert float [-1, 1] to int16
            int16_max = 32767
            int16_data = [max(-int16_max, min(int16_max, int(sample * int16_max))) 
                         for sample in buffer]
            
            # Pack to bytes
            byte_data = b''.join(struct.pack('<h', sample) for sample in int16_data)
            wav_file.writeframes(byte_data)
    
    def _load_audio_file(self, path: Path, expected_sample_rate: int) -> List[float]:
        """Load audio buffer from WAV file."""
        import struct
        
        if not path.exists():
            print(f"Warning: Audio file not found: {path}")
            return [0.0] * expected_sample_rate  # Return 1 second of silence
        
        with wave.open(str(path), 'rb') as wav_file:
            sample_rate = wav_file.getframerate()
            n_channels = wav_file.getnchannels()
            sample_width = wav_file.getsampwidth()
            n_frames = wav_file.getnframes()
            
            # Read raw bytes
            byte_data = wav_file.readframes(n_frames)
            
            # Convert based on sample width
            if sample_width == 2:  # 16-bit
                int16_max = 32767.0
                num_samples = len(byte_data) // 2
                samples = [struct.unpack('<h', byte_data[i*2:(i+1)*2])[0] / int16_max 
                          for i in range(num_samples)]
            elif sample_width == 4:  # 32-bit float
                num_samples = len(byte_data) // 4
                samples = [struct.unpack('<f', byte_data[i*4:(i+1)*4])[0] 
                          for i in range(num_samples)]
            else:
                raise ValueError(f"Unsupported sample width: {sample_width}")
            
            # If stereo, mix to mono
            if n_channels == 2:
                samples = [(samples[i] + samples[i+1]) / 2.0 
                          for i in range(0, len(samples), 2)]
            
            return samples


def save_project(project, file_path: str, embed_audio: bool = False) -> None:
    """
    Convenience function to save a project.
    
    Args:
        project: Project instance to save
        file_path: Path to save the project file (.daw)
        embed_audio: If True, embed audio in JSON. If False, save to separate files.
    """
    serializer = ProjectSerializer()
    serializer.save_project(project, file_path, embed_audio)


def load_project(file_path: str):
    """
    Convenience function to load a project.
    
    Args:
        file_path: Path to the project file (.daw)
        
    Returns:
        Loaded Project instance
    """
    serializer = ProjectSerializer()
    return serializer.load_project(file_path)
