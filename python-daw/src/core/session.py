class Session:
    def __init__(self):
        self._is_playing = False

    def start_session(self):
        self._is_playing = True
        # Additional logic for starting the session

    def stop_session(self):
        self._is_playing = False
        # Additional logic for stopping the session

    def is_playing(self):
        return self._is_playing