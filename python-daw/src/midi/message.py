class MidiMessage:
    def __init__(self, message_type, channel, note, velocity):
        self.message_type = message_type
        self.channel = channel
        self.note = note
        self.velocity = velocity

    def create_message(self):
        return [self.message_type | self.channel, self.note, self.velocity]

    @staticmethod
    def parse_message(message):
        message_type = message[0] & 0xF0
        channel = message[0] & 0x0F
        note = message[1]
        velocity = message[2]
        return MidiMessage(message_type, channel, note, velocity)