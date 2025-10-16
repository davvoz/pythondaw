class BaseInstrument:
    def play_note(self, note, velocity):
        raise NotImplementedError("This method should be overridden by subclasses.")

    def stop_note(self, note):
        raise NotImplementedError("This method should be overridden by subclasses.")


class Synthesizer(BaseInstrument):
    def __init__(self):
        self.oscillator_type = 'sine'
        self.volume = 1.0
        self.is_playing = False

    def set_oscillator(self, oscillator_type):
        self.oscillator_type = oscillator_type

    def set_volume(self, volume):
        self.volume = volume

    def play_note(self, note, velocity):
        self.is_playing = True
        # Logic to generate sound based on the oscillator type, note, and velocity
        print(f"Playing note {note} with velocity {velocity} on {self.oscillator_type} oscillator at volume {self.volume}.")

    def stop_note(self, note):
        self.is_playing = False
        # Logic to stop the sound for the given note
        print(f"Stopped note {note}.")