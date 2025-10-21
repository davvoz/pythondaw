class BaseInstrument:
    def play_note(self, note, velocity):
        raise NotImplementedError("This method should be overridden by subclasses.")

    def stop_note(self, note):
        raise NotImplementedError("This method should be overridden by subclasses.")


class Synthesizer(BaseInstrument):
    """Very simple mono synth with basic waveforms and ADSR, offline rendering API.

    Exposes render_notes(notes, start_sec, end_sec, sample_rate) -> List[float]
    so that MidiClip can ask for audio for a window.
    """

    def __init__(self):
        self.oscillator_type = 'sine'  # 'sine' | 'square' | 'saw' | 'triangle'
        self.volume = 1.0
        # ADSR in seconds (very basic)
        self.attack = 0.005
        self.decay = 0.05
        self.sustain = 0.7
        self.release = 0.1

    def set_oscillator(self, oscillator_type):
        self.oscillator_type = oscillator_type

    def set_volume(self, volume):
        self.volume = float(volume)

    def set_adsr(self, attack: float, decay: float, sustain: float, release: float):
        self.attack = max(0.0, float(attack))
        self.decay = max(0.0, float(decay))
        self.sustain = max(0.0, min(1.0, float(sustain)))
        self.release = max(0.0, float(release))

    # Realtime stubs for compatibility
    def play_note(self, note, velocity):
        pass

    def stop_note(self, note):
        pass

    # Offline rendering for a set of MidiNote in a window
    def render_notes(self, notes, start_sec, end_sec, sample_rate):
        import math
        n_samples = int(round((end_sec - start_sec) * sample_rate))
        if n_samples <= 0:
            return []
        out = [0.0] * n_samples

        def midi_to_freq(m: int) -> float:
            return 440.0 * (2.0 ** ((m - 69) / 12.0))

        def osc(phase: float):
            # phase in [0,1)
            p = phase - math.floor(phase)
            t = self.oscillator_type
            if t == 'square':
                return 1.0 if p < 0.5 else -1.0
            if t == 'saw':
                return 2.0 * p - 1.0
            if t == 'triangle':
                return 4.0 * abs(p - 0.5) - 1.0
            # sine default
            return math.sin(2 * math.pi * p)

        # Precompute samples timeline for index->time
        for note in notes:
            f = midi_to_freq(int(note.pitch))
            vel_amp = max(0.0, min(1.0, note.velocity / 127.0))
            amp = vel_amp * (self.volume * 0.3)  # conservative gain
            # overlap sample indices for this note relative to window
            n0 = max(0, int(round((note.start - start_sec) * sample_rate)))
            n1 = min(n_samples, int(round((note.end - start_sec) * sample_rate)))
            if n1 <= n0:
                continue
            # phase increment
            inc = f / float(sample_rate)
            # start phase continuous by time from note.start (not critical here)
            start_phase = (note.start * f) % 1.0
            for i in range(n0, n1):
                t = (start_sec + i / sample_rate) - note.start
                # ADSR envelope
                env = 1.0
                if t < self.attack:
                    env = (t / self.attack) if self.attack > 0 else 1.0
                elif t < self.attack + self.decay:
                    dpos = (t - self.attack) / max(1e-9, self.decay)
                    env = 1.0 + (self.sustain - 1.0) * dpos
                elif t <= note.duration:
                    env = self.sustain
                else:
                    # release after nominal duration
                    rpos = (t - note.duration) / max(1e-9, self.release)
                    env = max(0.0, self.sustain * (1.0 - rpos))

                phase = start_phase + inc * (i - n0)
                s = osc(phase) * amp * env
                out[i] += s

        # clamp
        for i in range(n_samples):
            v = out[i]
            if v > 1.0:
                v = 1.0
            elif v < -1.0:
                v = -1.0
            out[i] = v
        return out