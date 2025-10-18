from typing import List, Optional, Dict


class AudioEngine:
    def __init__(self):
        self.is_initialized = False

    def initialize(self):
        # Initialize audio system (placeholder)
        self.is_initialized = True

    def start_playback(self):
        if not self.is_initialized:
            raise RuntimeError("AudioEngine not initialized.")
        # Start audio playback (placeholder)

    def stop_playback(self):
        if not self.is_initialized:
            raise RuntimeError("AudioEngine not initialized.")
        # Stop audio playback (placeholder)

    # Offline rendering for a time window
    def render_window(self, timeline, start_time: float, duration: float, sample_rate: int, 
                     track_volumes: Optional[Dict[int, float]] = None,
                     solo_tracks: Optional[List[int]] = None,
                     mixer=None) -> List[float]:
        """Render a mono buffer for [start_time, start_time+duration).

        Combina i clip sovrapposti sommandoli e clampando in [-1, 1].
        Applica i volumi delle tracce se forniti.
        
        Args:
            timeline: Timeline object con i clip
            start_time: Tempo di inizio in secondi
            duration: Durata in secondi
            sample_rate: Sample rate in Hz
            track_volumes: Dictionary opzionale {track_index: volume} con i volumi delle tracce (0.0-1.0)
            solo_tracks: List opzionale di track indices da renderizzare in solo (ignora altre tracce)
            mixer: Mixer opzionale per controllare mute/solo state
        """
        if duration <= 0:
            return []
        total_samples = int(duration * sample_rate)
        output = [0.0] * total_samples
        end_time = start_time + duration
        for track_index, clip in timeline.get_clips_for_range(start_time, end_time):
            # Se solo_tracks è specificato, salta le tracce che non sono in lista
            if solo_tracks is not None and track_index not in solo_tracks:
                continue
            
            # Check mute/solo state from mixer
            if mixer is not None and hasattr(mixer, 'should_play_track'):
                if not mixer.should_play_track(track_index):
                    continue  # Skip muted/non-soloed tracks
                
            # determina gli intervalli di sovrapposizione
            overlap_start = max(start_time, clip.start_time)
            overlap_end = min(end_time, clip.end_time)
            if overlap_end <= overlap_start:
                continue
            # campioni nel buffer di output
            out_start_idx = int((overlap_start - start_time) * sample_rate)
            out_end_idx = int((overlap_end - start_time) * sample_rate)
            # campioni nel buffer del clip (local time)
            clip_local_start = overlap_start - clip.start_time
            clip_local_end = overlap_end - clip.start_time
            clip_samples = clip.slice_samples(clip_local_start, clip_local_end)
            
            # Ottieni il volume della traccia (default 1.0 se non specificato)
            track_volume = 1.0
            if track_volumes is not None and track_index in track_volumes:
                track_volume = float(track_volumes[track_index])
            
            # Ottieni il volume del clip
            clip_volume = getattr(clip, 'volume', 1.0)
            
            # Volume combinato (traccia * clip)
            combined_volume = track_volume * clip_volume
            
            # mix semplice (somma e clamp) con applicazione del volume
            for i, s in enumerate(clip_samples):
                idx = out_start_idx + i
                if 0 <= idx < total_samples:
                    # Applica il volume combinato
                    sample_with_volume = float(s) * combined_volume
                    mixed = output[idx] + sample_with_volume
                    if mixed > 1.0:
                        mixed = 1.0
                    elif mixed < -1.0:
                        mixed = -1.0
                    output[idx] = mixed
        return output