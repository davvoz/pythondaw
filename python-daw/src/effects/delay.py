from .base import BaseEffect
import math


class Delay(BaseEffect):
    """
    Professional-grade delay effect with:
    - Accurate delay time in milliseconds
    - Circular buffer for proper delay implementation
    - Low-pass and high-pass filtering
    - Stereo/ping-pong support
    - Clean feedback path
    """
    
    def __init__(self, sample_rate=44100):
        super().__init__()
        self.sample_rate = sample_rate
        self.parameters = {
            "delay_time_ms": 300.0,  # Delay time in milliseconds (1-2000ms)
            "feedback": 0.4,          # Feedback amount (0-0.95)
            "mix": 0.5,               # Dry/wet mix (0-1)
            "low_cut": 200.0,         # High-pass filter frequency (Hz)
            "high_cut": 8000.0,       # Low-pass filter frequency (Hz)
            "ping_pong": 0.0,         # Ping-pong effect (0=off, 1=full)
            "sync": False,            # Tempo sync (not implemented yet)
        }
        
        # Circular buffer for delay (max 2 seconds)
        max_delay_samples = int(2.0 * sample_rate)
        self.buffer_left = [0.0] * max_delay_samples
        self.buffer_right = [0.0] * max_delay_samples
        self.write_pos = 0
        
        # Filter states for smoothing
        self.lp_state_left = 0.0
        self.lp_state_right = 0.0
        self.hp_state_left = 0.0
        self.hp_state_right = 0.0
        
    def set_sample_rate(self, sample_rate):
        """Update sample rate and resize buffers if needed"""
        if sample_rate != self.sample_rate:
            self.sample_rate = sample_rate
            max_delay_samples = int(2.0 * sample_rate)
            self.buffer_left = [0.0] * max_delay_samples
            self.buffer_right = [0.0] * max_delay_samples
            self.write_pos = 0
            
    def _calculate_filter_coefficients(self):
        """Calculate one-pole filter coefficients"""
        # Low-pass filter coefficient
        high_cut = self.parameters.get("high_cut", 8000.0)
        lp_freq = min(high_cut, self.sample_rate * 0.49)
        lp_coeff = 1.0 - math.exp(-2.0 * math.pi * lp_freq / self.sample_rate)
        
        # High-pass filter coefficient
        low_cut = self.parameters.get("low_cut", 200.0)
        hp_freq = max(low_cut, 20.0)
        hp_coeff = math.exp(-2.0 * math.pi * hp_freq / self.sample_rate)
        
        return lp_coeff, hp_coeff
        
    def _apply_filters(self, sample, lp_state, hp_state, lp_coeff, hp_coeff):
        """Apply cascaded high-pass and low-pass filters"""
        # Low-pass filter (smooth high frequencies)
        lp_out = lp_state + lp_coeff * (sample - lp_state)
        
        # High-pass filter (remove low frequencies)
        hp_out = hp_coeff * (hp_state + lp_out - sample)
        
        return lp_out, hp_out, lp_out, hp_out
        
    def apply(self, audio_data):
        """
        Apply professional delay effect to audio data.
        Supports both mono and stereo processing.
        """
        if not isinstance(audio_data, list) or not audio_data:
            return audio_data
            
        # Get parameters
        delay_time_ms = self.parameters.get("delay_time_ms", 300.0)
        feedback = max(0.0, min(0.95, self.parameters.get("feedback", 0.4)))
        mix = max(0.0, min(1.0, self.parameters.get("mix", 0.5)))
        ping_pong = max(0.0, min(1.0, self.parameters.get("ping_pong", 0.0)))
        
        # Calculate delay in samples
        delay_samples = int((delay_time_ms / 1000.0) * self.sample_rate)
        delay_samples = max(1, min(delay_samples, len(self.buffer_left) - 1))
        
        # Get filter coefficients
        lp_coeff, hp_coeff = self._calculate_filter_coefficients()
        
        # Check if stereo (list of lists) or mono
        is_stereo = isinstance(audio_data[0], (list, tuple)) if audio_data else False
        
        if is_stereo:
            return self._apply_stereo(audio_data, delay_samples, feedback, mix, 
                                     ping_pong, lp_coeff, hp_coeff)
        else:
            return self._apply_mono(audio_data, delay_samples, feedback, mix, 
                                   lp_coeff, hp_coeff)
    
    def _apply_mono(self, audio_data, delay_samples, feedback, mix, lp_coeff, hp_coeff):
        """Apply delay to mono audio"""
        out = []
        
        for sample in audio_data:
            # Read from delay buffer
            read_pos = (self.write_pos - delay_samples) % len(self.buffer_left)
            delayed = self.buffer_left[read_pos]
            
            # Apply filters to delayed signal
            filtered, _, new_lp, new_hp = self._apply_filters(
                delayed, self.lp_state_left, self.hp_state_left, lp_coeff, hp_coeff
            )
            self.lp_state_left = new_lp
            self.hp_state_left = new_hp
            
            # Write to buffer (input + filtered feedback)
            self.buffer_left[self.write_pos] = sample + (filtered * feedback)
            
            # Mix dry and wet
            output = (1.0 - mix) * sample + mix * filtered
            out.append(output)
            
            # Advance write position
            self.write_pos = (self.write_pos + 1) % len(self.buffer_left)
            
        return out
    
    def _apply_stereo(self, audio_data, delay_samples, feedback, mix, 
                     ping_pong, lp_coeff, hp_coeff):
        """Apply delay to stereo audio with optional ping-pong"""
        out = []
        
        for left, right in audio_data:
            # Read from delay buffers
            read_pos = (self.write_pos - delay_samples) % len(self.buffer_left)
            delayed_left = self.buffer_left[read_pos]
            delayed_right = self.buffer_right[read_pos]
            
            # Apply filters to delayed signals
            filtered_left, _, new_lp_l, new_hp_l = self._apply_filters(
                delayed_left, self.lp_state_left, self.hp_state_left, lp_coeff, hp_coeff
            )
            filtered_right, _, new_lp_r, new_hp_r = self._apply_filters(
                delayed_right, self.lp_state_right, self.hp_state_right, lp_coeff, hp_coeff
            )
            
            self.lp_state_left = new_lp_l
            self.hp_state_left = new_hp_l
            self.lp_state_right = new_lp_r
            self.hp_state_right = new_hp_r
            
            # Ping-pong: cross-feed the delayed signals
            if ping_pong > 0.0:
                cross_left = filtered_left * (1.0 - ping_pong) + filtered_right * ping_pong
                cross_right = filtered_right * (1.0 - ping_pong) + filtered_left * ping_pong
                filtered_left = cross_left
                filtered_right = cross_right
            
            # Write to buffers (input + filtered feedback)
            self.buffer_left[self.write_pos] = left + (filtered_left * feedback)
            self.buffer_right[self.write_pos] = right + (filtered_right * feedback)
            
            # Mix dry and wet
            out_left = (1.0 - mix) * left + mix * filtered_left
            out_right = (1.0 - mix) * right + mix * filtered_right
            out.append([out_left, out_right])
            
            # Advance write position
            self.write_pos = (self.write_pos + 1) % len(self.buffer_left)
            
        return out
    
    def reset(self):
        """Clear delay buffers (useful when stopping playback)"""
        self.buffer_left = [0.0] * len(self.buffer_left)
        self.buffer_right = [0.0] * len(self.buffer_right)
        self.write_pos = 0
        self.lp_state_left = 0.0
        self.lp_state_right = 0.0
        self.hp_state_left = 0.0
        self.hp_state_right = 0.0