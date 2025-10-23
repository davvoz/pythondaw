"""
Advanced Professional Synthesizer with comprehensive features.
"""

import math
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
        
    def _midi_to_freq(self, midi_note: int) -> float:
        """Convert MIDI note to frequency in Hz."""
        return 440.0 * (2.0 ** ((midi_note - 69) / 12.0))
    
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
        """Render MIDI notes to audio samples."""
        n_samples = int(round((end_sec - start_sec) * sample_rate))
        if n_samples <= 0:
            return []
        
        out = [0.0] * n_samples
        
        # Sort notes by start time for glide
        sorted_notes = sorted(notes, key=lambda n: n.start)
        
        for note_idx, note in enumerate(sorted_notes):
            base_freq = self._midi_to_freq(int(note.pitch))
            vel_amp = max(0.0, min(1.0, note.velocity / 127.0))
            
            # Sample range for this note
            n0 = max(0, int(round((note.start - start_sec) * sample_rate)))
            n1 = min(n_samples, int(round((note.end - start_sec) * sample_rate)))
            
            if n1 <= n0:
                continue
            
            note_samples = []
            
            # Generate samples for this note
            for i in range(n0, n1):
                time = (start_sec + i / sample_rate) - note.start
                
                # LFO modulation
                lfo_value = self._generate_lfo(start_sec + i / sample_rate)
                
                # Amplitude envelope
                amp_env = self._compute_envelope(time, note.duration,
                                                self.attack, self.decay, 
                                                self.sustain, self.release)
                
                # Filter envelope
                filter_env = self._compute_envelope(time, note.duration,
                                                   self.filter_attack, self.filter_decay,
                                                   self.filter_sustain, self.filter_release)
                
                # Apply glide
                if self.glide_enabled and note_idx > 0:
                    prev_note = sorted_notes[note_idx - 1]
                    if time < self.glide_time and note.start < prev_note.end + 0.01:
                        prev_freq = self._midi_to_freq(int(prev_note.pitch))
                        current_freq = self._apply_glide(base_freq, time)
                    else:
                        current_freq = base_freq
                else:
                    current_freq = base_freq
                
                # Generate unison voices
                unison_sample = 0.0
                num_voices = self.unison_voices if self.unison_enabled else 1
                
                for voice in range(num_voices):
                    # Detune for unison
                    if num_voices > 1:
                        detune_offset = ((voice - (num_voices - 1) / 2.0) / 
                                       ((num_voices - 1) / 2.0)) * self.unison_detune
                        voice_freq = current_freq * (2.0 ** (detune_offset / 1200.0))
                    else:
                        voice_freq = current_freq
                    
                    # OSCILLATOR 1
                    osc1_freq = self._apply_pitch_modulation(voice_freq, self.osc1_octave, 
                                                            self.osc1_semitone, self.osc1_detune)
                    
                    # Apply LFO to pitch if enabled
                    if self.lfo_enabled and self.lfo_target == 'pitch':
                        osc1_freq *= (1.0 + lfo_value * 0.1)  # ±10% pitch modulation
                    
                    phase1 = (osc1_freq * (i - n0) / sample_rate) % 1.0
                    
                    # Apply LFO to PWM if enabled
                    pwm1 = self.osc1_pwm
                    if self.lfo_enabled and self.lfo_target == 'pwm':
                        pwm1 = max(0.1, min(0.9, pwm1 + lfo_value * 0.3))
                    
                    osc1_sample = self._generate_oscillator(self.osc1_type, phase1, pwm1) * self.osc1_level
                    
                    # OSCILLATOR 2
                    osc2_freq = self._apply_pitch_modulation(voice_freq, self.osc2_octave,
                                                            self.osc2_semitone, self.osc2_detune)
                    
                    if self.lfo_enabled and self.lfo_target == 'pitch':
                        osc2_freq *= (1.0 + lfo_value * 0.1)
                    
                    phase2 = (osc2_freq * (i - n0) / sample_rate) % 1.0
                    
                    pwm2 = self.osc2_pwm
                    if self.lfo_enabled and self.lfo_target == 'pwm':
                        pwm2 = max(0.1, min(0.9, pwm2 + lfo_value * 0.3))
                    
                    osc2_sample = self._generate_oscillator(self.osc2_type, phase2, pwm2) * self.osc2_level
                    
                    # SUB OSCILLATOR
                    sub_sample = 0.0
                    if self.sub_enabled:
                        sub_freq = voice_freq * (2.0 ** self.sub_octave)
                        phase_sub = (sub_freq * (i - n0) / sample_rate) % 1.0
                        sub_sample = math.sin(2 * math.pi * phase_sub) * self.sub_level
                    
                    # Mix oscillators
                    mixed = (osc1_sample * (1.0 - self.osc_mix) + 
                            osc2_sample * self.osc_mix + sub_sample)
                    
                    unison_sample += mixed / num_voices
                
                # Apply LFO to amplitude if enabled
                final_amp = amp_env
                if self.lfo_enabled and self.lfo_target == 'amplitude':
                    final_amp *= (1.0 + lfo_value * 0.5)
                
                sample = unison_sample * final_amp * vel_amp * self.volume * 0.3
                note_samples.append(sample)
            
            # Apply filter with envelope modulation
            if self.filter_enabled and len(note_samples) > 0:
                # Modulate cutoff with filter envelope
                modulated_cutoff = self.filter_cutoff
                if self.filter_envelope_amount != 0.0:
                    # Calculate average envelope for this segment (simplified)
                    avg_filter_env = 0.5  # Could be improved with per-sample envelope
                    modulated_cutoff *= (1.0 + self.filter_envelope_amount * avg_filter_env)
                
                # Apply LFO to filter if enabled
                if self.lfo_enabled and self.lfo_target == 'filter':
                    modulated_cutoff *= (1.0 + lfo_value * 0.5)
                
                note_samples = self._apply_filter(note_samples, modulated_cutoff, 
                                                 self.filter_resonance, self.filter_type, 
                                                 sample_rate)
            
            # Add to output
            for i, sample in enumerate(note_samples):
                if n0 + i < len(out):
                    out[n0 + i] += sample
        
        # Soft clipping
        for i in range(len(out)):
            v = out[i]
            if v > 1.0:
                v = 1.0
            elif v < -1.0:
                v = -1.0
            out[i] = v
        
        return out
    
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
