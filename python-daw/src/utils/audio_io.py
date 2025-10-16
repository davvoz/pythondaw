"""Audio I/O utilities for loading and saving audio files."""

import os
from typing import Tuple, List, Optional

try:
    import soundfile as sf
    import numpy as np
    SOUNDFILE_AVAILABLE = True
except ImportError:
    SOUNDFILE_AVAILABLE = False
    sf = None
    np = None

try:
    from pydub import AudioSegment
    PYDUB_AVAILABLE = True
except ImportError:
    PYDUB_AVAILABLE = False
    AudioSegment = None


def get_supported_formats() -> List[Tuple[str, str]]:
    """Return list of supported audio formats as (description, extension) tuples."""
    formats = []
    
    if SOUNDFILE_AVAILABLE:
        formats.extend([
            ("WAV files", "*.wav"),
            ("FLAC files", "*.flac"),
            ("OGG files", "*.ogg"),
        ])
    
    if PYDUB_AVAILABLE:
        formats.extend([
            ("MP3 files", "*.mp3"),
            ("AAC files", "*.aac"),
            ("M4A files", "*.m4a"),
        ])
    
    if not formats:
        # Fallback to basic WAV only
        formats.append(("WAV files", "*.wav"))
    
    formats.append(("All audio files", "*.wav;*.mp3;*.flac;*.ogg;*.aac;*.m4a"))
    formats.append(("All files", "*.*"))
    
    return formats


def load_audio_file(file_path: str, target_sr: Optional[int] = None) -> Tuple[List[float], int]:
    """Load audio file and return (mono_buffer, sample_rate).
    
    Args:
        file_path: Path to audio file
        target_sr: Target sample rate (None = keep original)
        
    Returns:
        Tuple of (mono buffer as list, sample_rate as int)
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ImportError: If required libraries not available
        ValueError: If file format not supported
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    ext = os.path.splitext(file_path)[1].lower()
    
    # Try soundfile first (better for WAV, FLAC, OGG)
    if SOUNDFILE_AVAILABLE and ext in ['.wav', '.flac', '.ogg']:
        try:
            data, sr = sf.read(file_path)
            
            # Convert to mono if stereo
            if len(data.shape) > 1:
                data = np.mean(data, axis=1)
            
            # Resample if needed
            if target_sr is not None and target_sr != sr:
                data = _resample_numpy(data, sr, target_sr)
                sr = target_sr
            
            # Convert to list and ensure float range [-1, 1]
            buffer = data.tolist()
            return buffer, int(sr)
        except Exception as e:
            raise ValueError(f"Failed to load {file_path} with soundfile: {str(e)}")
    
    # Try pydub for other formats (MP3, AAC, M4A)
    if PYDUB_AVAILABLE:
        try:
            audio = AudioSegment.from_file(file_path)
            
            # Convert to mono
            if audio.channels > 1:
                audio = audio.set_channels(1)
            
            # Resample if needed
            sr = audio.frame_rate
            if target_sr is not None and target_sr != sr:
                audio = audio.set_frame_rate(target_sr)
                sr = target_sr
            
            # Convert to normalized float samples
            samples = np.array(audio.get_array_of_samples())
            
            # Normalize based on bit depth
            if audio.sample_width == 1:  # 8-bit
                samples = samples.astype(np.float32) / 128.0 - 1.0
            elif audio.sample_width == 2:  # 16-bit
                samples = samples.astype(np.float32) / 32768.0
            elif audio.sample_width == 4:  # 32-bit
                samples = samples.astype(np.float32) / 2147483648.0
            else:
                samples = samples.astype(np.float32)
            
            buffer = samples.tolist()
            return buffer, int(sr)
        except Exception as e:
            raise ValueError(f"Failed to load {file_path} with pydub: {str(e)}")
    
    # No libraries available
    raise ImportError(
        "No audio library available. Install soundfile or pydub:\n"
        "pip install soundfile\n"
        "or\n"
        "pip install pydub"
    )


def _resample_numpy(data, orig_sr: int, target_sr: int):
    """Simple resampling using numpy (linear interpolation)."""
    if not SOUNDFILE_AVAILABLE or np is None:
        return data
    
    orig_len = len(data)
    target_len = int(orig_len * target_sr / orig_sr)
    
    # Linear interpolation
    orig_indices = np.linspace(0, orig_len - 1, orig_len)
    target_indices = np.linspace(0, orig_len - 1, target_len)
    
    resampled = np.interp(target_indices, orig_indices, data)
    return resampled


def save_audio_file(buffer: List[float], file_path: str, sample_rate: int = 44100, format: str = "wav"):
    """Save audio buffer to file.
    
    Args:
        buffer: Mono audio buffer (list of floats in [-1, 1])
        file_path: Output file path
        sample_rate: Sample rate in Hz
        format: Output format ('wav', 'flac', 'ogg', 'mp3')
    """
    if SOUNDFILE_AVAILABLE and format in ['wav', 'flac', 'ogg']:
        data = np.array(buffer, dtype=np.float32)
        sf.write(file_path, data, sample_rate, format=format)
        return
    
    if PYDUB_AVAILABLE:
        # Convert float buffer to 16-bit int
        samples = np.array(buffer, dtype=np.float32)
        samples = (samples * 32767).astype(np.int16)
        
        audio = AudioSegment(
            samples.tobytes(),
            frame_rate=sample_rate,
            sample_width=2,  # 16-bit
            channels=1
        )
        
        audio.export(file_path, format=format)
        return
    
    raise ImportError("No audio library available for saving files.")


def get_audio_info(file_path: str) -> dict:
    """Get information about an audio file without loading it.
    
    Returns:
        Dictionary with keys: duration, sample_rate, channels, format
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"The file {file_path} does not exist.")
    
    if SOUNDFILE_AVAILABLE:
        try:
            info = sf.info(file_path)
            return {
                'duration': info.duration,
                'sample_rate': info.samplerate,
                'channels': info.channels,
                'format': info.format,
                'subtype': info.subtype,
            }
        except Exception:
            pass
    
    if PYDUB_AVAILABLE:
        try:
            audio = AudioSegment.from_file(file_path)
            return {
                'duration': len(audio) / 1000.0,  # ms to seconds
                'sample_rate': audio.frame_rate,
                'channels': audio.channels,
                'format': os.path.splitext(file_path)[1][1:].upper(),
            }
        except Exception:
            pass
    
    # Fallback: just file size
    return {
        'size': os.path.getsize(file_path),
        'format': os.path.splitext(file_path)[1][1:].upper(),
    }