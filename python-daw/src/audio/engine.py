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
                     mixer=None,
                     project=None) -> List[float]:
        """Render a mono buffer for [start_time, start_time+duration).

        Combina i clip sovrapposti sommandoli e clampando in [-1, 1].
        Applica i volumi delle tracce se forniti.
        Applica gli effetti per-traccia DOPO il mix dei clip della traccia ma PRIMA del volume finale.
        
        Args:
            timeline: Timeline object con i clip
            start_time: Tempo di inizio in secondi
            duration: Durata in secondi
            sample_rate: Sample rate in Hz
            track_volumes: Dictionary opzionale {track_index: volume} con i volumi delle tracce (0.0-1.0)
            solo_tracks: List opzionale di track indices da renderizzare in solo (ignora altre tracce)
            mixer: Mixer opzionale per controllare mute/solo state
            project: Project opzionale per applicare effetti per-traccia
        """
        if duration <= 0:
            return []
        total_samples = int(duration * sample_rate)
        output = [0.0] * total_samples
        end_time = start_time + duration
        
        # Raggruppa clip per traccia
        track_clips: Dict[int, list] = {}
        for track_index, clip in timeline.get_clips_for_range(start_time, end_time):
            # Se solo_tracks è specificato, salta le tracce che non sono in lista
            if solo_tracks is not None and track_index not in solo_tracks:
                continue
            
            # Check mute/solo state from mixer
            if mixer is not None and hasattr(mixer, 'should_play_track'):
                if not mixer.should_play_track(track_index):
                    continue  # Skip muted/non-soloed tracks
            
            if track_index not in track_clips:
                track_clips[track_index] = []
            track_clips[track_index].append(clip)

        # Determina le tracce da processare (per tenere vive le code FX):
        tracks_to_process = set(track_clips.keys())
        if project is not None and hasattr(project, 'tracks'):
            try:
                for idx in range(len(project.tracks)):
                    # onora mute/solo se mixer presente
                    if mixer is not None and hasattr(mixer, 'should_play_track'):
                        if not mixer.should_play_track(idx):
                            continue
                    if solo_tracks is not None and idx not in solo_tracks:
                        continue
                    tracks_to_process.add(idx)
            except Exception:
                pass
        
        # Renderizza ogni traccia separatamente, applica effetti, poi mixa
        for track_index in sorted(tracks_to_process):
            clips = track_clips.get(track_index, [])
            # Crea buffer vuoto per questa traccia
            track_buffer = [0.0] * total_samples
            
            # Renderizza tutti i clip della traccia nel buffer
            for clip in clips:
                overlap_start = max(start_time, clip.start_time)
                overlap_end = min(end_time, clip.end_time)
                if overlap_end <= overlap_start:
                    continue
                
                # Posizione nel buffer di output
                out_start_idx = int((overlap_start - start_time) * sample_rate)
                
                # Campioni nel buffer del clip (local time)
                clip_local_start = overlap_start - clip.start_time
                clip_local_end = overlap_end - clip.start_time
                clip_samples = clip.slice_samples(clip_local_start, clip_local_end)
                
                # Ottieni il volume del clip
                clip_volume = getattr(clip, 'volume', 1.0)
                
                # Mix clips della stessa traccia (somma e clamp)
                for i, s in enumerate(clip_samples):
                    idx = out_start_idx + i
                    if 0 <= idx < total_samples:
                        sample_with_clip_volume = float(s) * clip_volume
                        mixed = track_buffer[idx] + sample_with_clip_volume
                        # Clamp al livello traccia
                        if mixed > 1.0:
                            mixed = 1.0
                        elif mixed < -1.0:
                            mixed = -1.0
                        track_buffer[idx] = mixed
            
            # Applica effetti per-traccia (se presenti)
            if project is not None and hasattr(project, 'tracks'):
                try:
                    if 0 <= int(track_index) < len(project.tracks):
                        tr = project.tracks[int(track_index)]
                        fx_chain = getattr(tr, 'effects', None)
                        if fx_chain and getattr(fx_chain, 'slots', None):
                            # Aggiorna il sample rate sugli effetti, se supportato
                            try:
                                for slot in fx_chain.slots:
                                    fx = getattr(slot, 'effect', None)
                                    if fx is not None and hasattr(fx, 'set_sample_rate'):
                                        fx.set_sample_rate(sample_rate)
                            except Exception:
                                pass
                            track_buffer = fx_chain.process(track_buffer)
                except Exception as e:
                    # Fail-safe: ignore any effect processing errors
                    print(f"Warning: Failed to apply effects on track {track_index}: {e}")
            
            # Applica volume della traccia
            track_volume = 1.0
            if track_volumes is not None and track_index in track_volumes:
                track_volume = float(track_volumes[track_index])
            
            # Mixa nel buffer finale
            for i in range(total_samples):
                sample_with_track_volume = track_buffer[i] * track_volume
                mixed = output[i] + sample_with_track_volume
                # Clamp al master
                if mixed > 1.0:
                    mixed = 1.0
                elif mixed < -1.0:
                    mixed = -1.0
                output[i] = mixed
        
        return output