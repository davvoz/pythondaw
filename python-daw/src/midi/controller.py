class MidiController:
    def __init__(self):
        self.connected_devices = []

    def connect(self, device):
        self.connected_devices.append(device)
        print(f"Connected to {device}")

    def send_message(self, message):
        for device in self.connected_devices:
            device.send(message)
            print(f"Sent message: {message} to {device}")