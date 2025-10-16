class BaseInstrument:
    def play_note(self, note, velocity):
        raise NotImplementedError("This method should be overridden by subclasses.")

    def stop_note(self, note):
        raise NotImplementedError("This method should be overridden by subclasses.")