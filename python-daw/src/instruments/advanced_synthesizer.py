"""
Advanced Professional Synthesizer with comprehensive features.
OPTIMIZED WITH NUMPY for real-time performance.
"""

import math
import numpy as np
from typing import List
from .base import BaseInstrument


class AdvancedSynthesizer(BaseInstrument):
    """
    Professional synthesizer with advanced features:
    - Dual oscillators with mixing
    - Filters (Low-pass, High-pass, Band-pass) with resonance
    - Glide/Portamento
    - Unison with detune
    - LFO modulation
    - Sub-oscillator
    - PWM (Pulse Width Modulation)
    - Polyphonic support
    """

    def __init__(self):
        # OSCILLATOR 1
        self.osc1_type = 'saw'  # 'sine', 'square', 'saw', 'triangle', 'noise'
        self.osc1_octave = 0  # -2 to +2
        self.osc1_semitone = 0  # -12 to +12
        self.osc1_detune = 0.0  # cents -100 to +100
        self.osc1_level = 1.0  # 0.0 to 1.0
        self.osc1_pwm = 0.5  # 0.0 to 1.0 (for square wave)
        
        # OSCILLATOR 2
        self.osc2_type = 'square'
        self.osc2_octave = 0
        self.osc2_semitone = 0
        self.osc2_detune = 0.0
        self.osc2_level = 0.5
        self.osc2_pwm = 0.5
        
        # SUB OSCILLATOR
        self.sub_enabled = False
        self.sub_level = 0.3
        self.sub_octave = -1  # usually one octave below
        
        # MIXER
        self.osc_mix = 0.5  # 0.0 = osc1, 1.0 = osc2
        
        # UNISON
        self.unison_enabled = False
        self.unison_voices = 3  # 1 to 7
        self.unison_detune = 10.0  # cents
        self.unison_spread = 0.5  # stereo spread 0.0 to 1.0
        
        # FILTER
        self.filter_enabled = True
        self.filter_type = 'lowpass'  # 'lowpass', 'highpass', 'bandpass'
        self.filter_cutoff = 8000.0  # Hz
        self.filter_resonance = 0.7  # Q factor (0.5 to 10.0)
        self.filter_envelope_amount = 0.0  # -1.0 to 1.0
        
        # FILTER ENVELOPE
        self.filter_attack = 0.01
        self.filter_decay = 0.1
        self.filter_sustain = 0.5
        self.filter_release = 0.2
        
        # AMPLITUDE ENVELOPE (ADSR)
        self.attack = 0.01
        self.decay = 0.1
        self.sustain = 0.7
        self.release = 0.2
        
        # GLIDE/PORTAMENTO
        self.glide_enabled = False
        self.glide_time = 0.1  # seconds
        
        # LFO
        self.lfo_enabled = False
        self.lfo_rate = 5.0  # Hz
        self.lfo_type = 'sine'  # 'sine', 'square', 'saw', 'triangle'
        self.lfo_amount = 0.2  # 0.0 to 1.0
        self.lfo_target = 'pitch'  # 'pitch', 'filter', 'amplitude', 'pwm'
        
        # MASTER
        self.volume = 0.8
        
        # Internal state for glide
        self._last_freq = None
        self._current_freq = None
        
        # PERFORMANCE: Pre-calculated wavetables
        self._wavetable_size = 2048
        self._wavetables = self._build_wavetables()
        
    def _midi_to_freq(self, midi_note: int) -> float:
        """Convert MIDI note to frequency in Hz."""
        return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))
    
    def _build_wavetables(self) -> dict:
        """Pre-calculate wavetables for all waveform types (PERFORMANCE OPTIMIZATION)."""
        size = self._wavetable_size
        x = np.linspace(0, 1, size, endpoint=False)
        
        wavetables = {}
        wavetables['sine'] = np.sin(2 * np.pi * x)
        wavetables['square'] = np.where(x < 0.5, 1.0, -1.0)
        wavetables['saw'] = 2.0 * x - 1.0
        wavetables['triangle'] = np.where(x < 0.5, 4.0 * x - 1.0, -4.0 * x + 3.0)
        
        return wavetables
    
    def _read_wavetable(self, wave_type: str, phase: np.ndarray, pwm: float = 0.5) -> np.ndarray:
        """Read from wavetable with linear interpolation (VECTORIZED)."""
        if wave_type == 'noise':
            return np.random.uniform(-1.0, 1.0, len(phase))
        
        # PWM for square wave
        if wave_type == 'square' and pwm != 0.5:
            return np.where(phase < pwm, 1.0, -1.0)
        
        if wave_type not in self._wavetables:
            wave_type = 'sine'
        
        table = self._wavetables[wave_type]
        # Phase is 0-1, scale to table index
        indices = phase * len(table)
        idx_floor = np.floor(indices).astype(int) % len(table)
        idx_ceil = (idx_floor + 1) % len(table)
        frac = indices - np.floor(indices)
        
        # Linear interpolation
        return table[idx_floor] * (1 - frac) + table[idx_ceil] * frac
    
    def _apply_pitch_modulation(self, base_freq: float, octave: int, semitone: int, detune: float) -> float:
        """Apply octave, semitone and detune modulation to frequency."""
        freq = base_freq * (2.0 ** octave)
        freq = freq * (2.0 ** (semitone / 12.0))
        freq = freq * (2.0 ** (detune / 1200.0))  # cents to ratio
        return freq
    
    def _generate_oscillator(self, osc_type: str, phase: float, pwm: float = 0.5) -> float:
        """Generate oscillator waveform sample."""
        p = phase - math.floor(phase)
        
        if osc_type == 'sine':
            return math.sin(2 * math.pi * p)
        elif osc_type == 'square':
            return 1.0 if p < pwm else -1.0
        elif osc_type == 'saw':
            return 2.0 * p - 1.0
        elif osc_type == 'triangle':
            return 4.0 * abs(p - 0.5) - 1.0
        elif osc_type == 'noise':
            import random
            return random.uniform(-1.0, 1.0)
        else:
            return math.sin(2 * math.pi * p)
    
    def _apply_filter(self, samples: List[float], cutoff: float, resonance: float, 
                      filter_type: str, sample_rate: float) -> List[float]:
        """Apply digital filter to samples."""
        if not self.filter_enabled or len(samples) == 0:
            return samples
        
        # Simple state-variable filter implementation
        # This is a basic implementation; for production use scipy.signal filters
        
        cutoff = max(20.0, min(cutoff, sample_rate * 0.49))
        freq = 2.0 * math.sin(math.pi * cutoff / sample_rate)
        q = max(0.5, min(resonance, 10.0))
        damp = min(2.0 * (1.0 - 0.15 * freq * freq), 2.0 / q)
        
        low = 0.0
        high = 0.0
        band = 0.0
        notch = 0.0
        
        filtered = []
        
        for sample in samples:
            # State variable filter
            low = low + freq * band
            high = sample - low - damp * band
            band = freq * high + band
            notch = high + low
            
            # Select output based on filter type
            if filter_type == 'lowpass':
                filtered.append(low)
            elif filter_type == 'highpass':
                filtered.append(high)
            elif filter_type == 'bandpass':
                filtered.append(band)
            else:
                filtered.append(low)
        
        return filtered
    
    def _generate_lfo(self, time: float) -> float:
        """Generate LFO modulation value."""
        if not self.lfo_enabled:
            return 0.0
        
        phase = (time * self.lfo_rate) % 1.0
        
        if self.lfo_type == 'sine':
            return math.sin(2 * math.pi * phase) * self.lfo_amount
        elif self.lfo_type == 'square':
            return (1.0 if phase < 0.5 else -1.0) * self.lfo_amount
        elif self.lfo_type == 'saw':
            return (2.0 * phase - 1.0) * self.lfo_amount
        elif self.lfo_type == 'triangle':
            return (4.0 * abs(phase - 0.5) - 1.0) * self.lfo_amount
        else:
            return 0.0
    
    def _compute_envelope_vectorized(self, time_array: np.ndarray, duration: float,
                                    attack: float, decay: float, 
                                    sustain: float, release: float) -> np.ndarray:
        """Compute ADSR envelope for time array (VECTORIZED - FAST)."""
        env = np.ones_like(time_array, dtype=np.float32)
        
        # Attack phase
        attack_mask = time_array < attack
        if attack > 0:
            env[attack_mask] = time_array[attack_mask] / attack
        
        # Decay phase
        decay_end = attack + decay
        decay_mask = (time_array >= attack) & (time_array < decay_end)
        if decay > 0:
            env[decay_mask] = 1.0 - (1.0 - sustain) * (time_array[decay_mask] - attack) / decay
        
        # Sustain phase
        sustain_mask = (time_array >= decay_end) & (time_array < duration)
        env[sustain_mask] = sustain
        
        # Release phase
        release_mask = time_array >= duration
        if release > 0:
            release_time = time_array[release_mask] - duration
            env[release_mask] = sustain * np.exp(-5.0 * release_time / release)
        else:
            env[release_mask] = 0.0
        
        return env
    
    def _compute_envelope(self, time: float, duration: float, 
                         attack: float, decay: float, sustain: float, release: float) -> float:
        """Compute ADSR envelope value at given time."""
        if time < 0:
            return 0.0
        
        if time < attack:
            # Attack phase
            return (time / attack) if attack > 0 else 1.0
        elif time < attack + decay:
            # Decay phase
            decay_pos = (time - attack) / max(1e-9, decay)
            return 1.0 + (sustain - 1.0) * decay_pos
        elif time < duration:
            # Sustain phase
            return sustain
        else:
            # Release phase
            release_pos = (time - duration) / max(1e-9, release)
            return max(0.0, sustain * (1.0 - release_pos))
    
    def _apply_glide(self, target_freq: float, time: float) -> float:
        """Apply glide/portamento to frequency."""
        if not self.glide_enabled or self._last_freq is None:
            self._last_freq = target_freq
            return target_freq
        
        if time >= self.glide_time:
            self._last_freq = target_freq
            return target_freq
        
        # Exponential glide
        t = time / max(1e-9, self.glide_time)
        freq = self._last_freq * ((target_freq / self._last_freq) ** t)
        return freq
    
    def render_notes(self, notes, start_sec, end_sec, sample_rate):
        """Render MIDI notes to audio samples - OPTIMIZED WITH NUMPY."""
        n_samples = int(round((end_sec - start_sec) * sample_rate))
        if n_samples <= 0:
            return []
        
        # Use NumPy array for output (FAST)
        out = np.zeros(n_samples, dtype=np.float32)
        
        # Limit unison voices for performance
        max_unison = min(3, self.unison_voices) if self.unison_enabled else 1
        
        for note in notes:
            base_freq = self._midi_to_freq(int(note.pitch))
            vel_amp = np.clip(note.velocity / 127.0, 0.0, 1.0)
            
            # Sample range for this note
            n0 = max(0, int(round((note.start - start_sec) * sample_rate)))
            n1 = min(n_samples, int(round((note.end - start_sec) * sample_rate)))
            
            if n1 <= n0:
                continue
            
            note_len = n1 - n0
            
            # TIME ARRAY (vectorized instead of loop)
            time_array = np.arange(note_len, dtype=np.float32) / sample_rate
            time_from_note_start = time_array + ((start_sec + n0/sample_rate) - note.start)
            
            # AMPLITUDE ENVELOPE (vectorized)
            amp_env = self._compute_envelope_vectorized(
                time_from_note_start, note.duration,
                self.attack, self.decay, self.sustain, self.release
            )
            
            # LFO (vectorized if enabled)
            lfo_mod = np.zeros(note_len, dtype=np.float32)
            if self.lfo_enabled:
                lfo_phase = ((start_sec + (n0 + time_array) / sample_rate) * self.lfo_rate) % 1.0
                if self.lfo_type == 'sine':
                    lfo_mod = np.sin(2 * np.pi * lfo_phase) * self.lfo_amount
                elif self.lfo_type == 'square':
                    lfo_mod = np.where(lfo_phase < 0.5, 1.0, -1.0) * self.lfo_amount
                elif self.lfo_type == 'saw':
                    lfo_mod = (2.0 * lfo_phase - 1.0) * self.lfo_amount
                elif self.lfo_type == 'triangle':
                    lfo_mod = (4.0 * np.abs(lfo_phase - 0.5) - 1.0) * self.lfo_amount
            
            # Mix from all unison voices
            mixed = np.zeros(note_len, dtype=np.float32)
            
            for voice_idx in range(max_unison):
                # Detune for unison
                voice_freq = base_freq
                if max_unison > 1:
                    detune_offset = ((voice_idx - (max_unison - 1) / 2.0) / 
                                   ((max_unison - 1) / 2.0)) * self.unison_detune
                    voice_freq = base_freq * (2.0 ** (detune_offset / 1200.0))
                
                # OSCILLATOR 1 (vectorized)
                osc1_freq = self._apply_pitch_modulation(
                    voice_freq, self.osc1_octave, self.osc1_semitone, self.osc1_detune
                )
                
                if self.lfo_enabled and self.lfo_target == 'pitch':
                    osc1_freq = osc1_freq * (1.0 + lfo_mod * 0.1)
                    phase1 = np.cumsum(osc1_freq * np.ones(note_len) / sample_rate) % 1.0
                else:
                    phase1 = (osc1_freq * time_array) % 1.0
                
                osc1_samples = self._read_wavetable(self.osc1_type, phase1, self.osc1_pwm) * self.osc1_level
                
                # OSCILLATOR 2 (only if level > 0)
                osc2_samples = np.zeros(note_len, dtype=np.float32)
                if self.osc2_level > 0.01:
                    osc2_freq = self._apply_pitch_modulation(
                        voice_freq, self.osc2_octave, self.osc2_semitone, self.osc2_detune
                    )
                    
                    if self.lfo_enabled and self.lfo_target == 'pitch':
                        osc2_freq = osc2_freq * (1.0 + lfo_mod * 0.1)
                        phase2 = np.cumsum(osc2_freq * np.ones(note_len) / sample_rate) % 1.0
                    else:
                        phase2 = (osc2_freq * time_array) % 1.0
                    
                    osc2_samples = self._read_wavetable(self.osc2_type, phase2, self.osc2_pwm) * self.osc2_level
                
                # SUB OSCILLATOR (only if enabled)
                sub_samples = np.zeros(note_len, dtype=np.float32)
                if self.sub_enabled and self.sub_level > 0.01:
                    sub_freq = voice_freq * (2.0 ** self.sub_octave)
                    phase_sub = (sub_freq * time_array) % 1.0
                    sub_samples = np.sin(2 * np.pi * phase_sub) * self.sub_level
                
                # Mix oscillators
                voice_mixed = (osc1_samples * (1.0 - self.osc_mix) + 
                             osc2_samples * self.osc_mix + sub_samples)
                
                mixed += voice_mixed / max_unison
            
            # Apply LFO to amplitude if enabled
            if self.lfo_enabled and self.lfo_target == 'amplitude':
                amp_env = amp_env * (1.0 + lfo_mod * 0.5)
            
            # Apply envelope and volume
            note_samples = mixed * amp_env * vel_amp * self.volume * 0.3
            
            # FILTER (simplified for performance - skip if cutoff very high)
            if self.filter_enabled and self.filter_cutoff < 18000:
                note_samples = self._apply_filter_fast(note_samples, sample_rate)
            
            # Add to output buffer
            out[n0:n1] += note_samples[:n1-n0]
        
        # Soft clipping (better than hard clip)
        out = np.tanh(out * 0.7)
        
        return out.tolist()
    
    def _apply_filter_fast(self, samples: np.ndarray, sample_rate: float) -> np.ndarray:
        """Fast state-variable filter using NumPy."""
        if len(samples) == 0:
            return samples
        
        cutoff = np.clip(self.filter_cutoff, 20.0, sample_rate * 0.49)
        freq = 2.0 * np.sin(np.pi * cutoff / sample_rate)
        q = np.clip(self.filter_resonance, 0.5, 10.0)
        damp = min(2.0 * (1.0 - 0.15 * freq * freq), 2.0 / q)
        
        # State variables
        low = 0.0
        band = 0.0
        
        filtered = np.empty_like(samples)
        
        # Process sample by sample (IIR filter requires this)
        for i in range(len(samples)):
            low = low + freq * band
            high = samples[i] - low - damp * band
            band = freq * high + band
            
            if self.filter_type == 'lowpass':
                filtered[i] = low
            elif self.filter_type == 'highpass':
                filtered[i] = high
            elif self.filter_type == 'bandpass':
                filtered[i] = band
            else:
                filtered[i] = low
        
        return filtered
    
    # Compatibility methods
    def play_note(self, note, velocity):
        pass
    
    def stop_note(self, note):
        pass
    
    def set_oscillator(self, oscillator_type):
        """Legacy compatibility."""
        self.osc1_type = oscillator_type
    
    def set_volume(self, volume):
        self.volume = float(volume)
    
    def set_adsr(self, attack: float, decay: float, sustain: float, release: float):
        self.attack = max(0.0, float(attack))
        self.decay = max(0.0, float(decay))
        self.sustain = max(0.0, min(1.0, float(sustain)))
        self.release = max(0.0, float(release))
