class Sequencer:
    def __init__(self):
        self.sequences = []

    def add_sequence(self, sequence):
        self.sequences.append(sequence)

    def play_sequence(self):
        for sequence in self.sequences:
            # Logic to play the sequence
            pass

    def remove_sequence(self, sequence):
        if sequence in self.sequences:
            self.sequences.remove(sequence)