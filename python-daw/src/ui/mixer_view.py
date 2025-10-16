from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QPushButton

class MixerView(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Mixer View")
        self.layout = QVBoxLayout()
        self.setLayout(self.layout)

        self.track_labels = []
        self.track_sliders = []
        self.track_buttons = []

    def add_track(self, track_name):
        label = QLabel(track_name)
        slider = QSlider()
        button = QPushButton("Mute")

        self.track_labels.append(label)
        self.track_sliders.append(slider)
        self.track_buttons.append(button)

        self.layout.addWidget(label)
        self.layout.addWidget(slider)
        self.layout.addWidget(button)

    def update_view(self):
        pass

    def set_track_volume(self, track_index, volume):
        if 0 <= track_index < len(self.track_sliders):
            self.track_sliders[track_index].setValue(volume)