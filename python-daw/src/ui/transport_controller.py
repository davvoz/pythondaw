"""
Transport Controller - Manages playback, loop, and BPM controls.
Extracted from MainWindow for better separation of concerns.
"""


class TransportController:
    """Handles transport operations (play, stop, loop, BPM) for the DAW."""
    
    def __init__(self, transport=None, player=None, project=None, timeline=None):
        """Initialize transport controller.
        
        Args:
            transport: Transport object for playback control
            player: Audio player object
            project: Project object for BPM/timing info
            timeline: Timeline object for clip management
        """
        self.transport = transport
        self.player = player
        self.project = project
        self.timeline = timeline
        
        # Callbacks for UI updates
        self.on_status_change = None  # Callback(status_text)
        self.on_timeline_redraw = None  # Callback()
        self.on_time_update_start = None  # Callback()
        self.on_meter_update_start = None  # Callback()
        self.on_time_update_stop = None  # Callback()
        
        # References to UI components
        self._toolbar_manager = None
        self._timeline_canvas = None
    
    def set_toolbar_manager(self, toolbar_manager):
        """Set reference to toolbar manager."""
        self._toolbar_manager = toolbar_manager
    
    def set_timeline_canvas(self, timeline_canvas):
        """Set reference to timeline canvas."""
        self._timeline_canvas = timeline_canvas
    
    def play(self):
        """Handle play button."""
        # Protection: check if already playing before starting
        if self.player is not None and hasattr(self.player, "is_playing"):
            if self.player.is_playing():
                print("TransportController: Already playing, ignoring play request.")
                return
        
        if self.transport is not None:
            try:
                self.transport.play()
                if self.on_status_change:
                    self.on_status_change("▶ Playing")
            except Exception as e:
                print(f"Play error: {e}")
        
        if self.player is not None and hasattr(self.player, "is_playing"):
            if self.on_time_update_start:
                self.on_time_update_start()
            if self.on_meter_update_start:
                self.on_meter_update_start()
    
    def stop(self):
        """Handle stop button."""
        if self.transport is not None:
            try:
                self.transport.stop()
                if self.on_status_change:
                    self.on_status_change("■ Stopped")
            except Exception as e:
                print(f"Stop error: {e}")
        
        if self.on_time_update_stop:
            self.on_time_update_stop()
    
    def toggle_loop(self):
        """Toggle loop on/off."""
        if self.player is None or self._toolbar_manager is None:
            return
        
        enabled = self._toolbar_manager.get_loop_enabled()
        loop_info = self.player.get_loop()
        
        # Se il loop viene attivato ma i punti sono invalidi, imposta valori di default
        if enabled and loop_info[1] >= loop_info[2]:
            # Imposta loop da posizione corrente a 4 secondi dopo
            current = self.player.get_current_time()
            self.player.set_loop(True, current, current + 4.0)
            loop_start, loop_end = current, current + 4.0
        else:
            self.player.set_loop(enabled, loop_info[1], loop_info[2])
            loop_start, loop_end = loop_info[1], loop_info[2]
        
        # Aggiorna UI
        if self.on_timeline_redraw:
            self.on_timeline_redraw()
        
        # Feedback visivo migliorato
        if enabled:
            status = f"🔁 Loop ON [{loop_start:.2f}s - {loop_end:.2f}s]"
        else:
            status = "Loop OFF"
        
        if self.on_status_change:
            self.on_status_change(status)
        print(status)
    
    def set_loop_start(self):
        """Set loop start to current playback position."""
        if self.player is None:
            return
        
        # Usa la posizione corrente del playback
        current_time = self.player.get_current_time()
        if self._timeline_canvas:
            current_time = self._timeline_canvas.snap_time(current_time)
        
        # Ottieni il loop attuale
        loop_info = self.player.get_loop()
        loop_enabled, loop_start, loop_end = loop_info
        
        # Se il loop non è configurato o ha valori invalidi, crea uno nuovo
        if not loop_enabled or loop_start >= loop_end:
            # Crea un loop di 4 secondi dalla posizione corrente
            new_start = current_time
            new_end = current_time + 4.0
        else:
            # Modifica solo il punto di inizio, mantieni la fine
            new_start = current_time
            new_end = loop_end
            
            # Se il nuovo inizio è dopo la fine, sposta la fine
            if new_start >= new_end:
                new_end = new_start + 0.5
        
        self.player.set_loop(True, new_start, new_end)
        
        # Aggiorna checkbox
        if self._toolbar_manager:
            self._toolbar_manager.set_loop_enabled(True)
        
        if self.on_timeline_redraw:
            self.on_timeline_redraw()
        
        status = f"🔁 Loop start set: {new_start:.3f}s (end: {new_end:.3f}s)"
        if self.on_status_change:
            self.on_status_change(status)
        print(status)
    
    def set_loop_end(self):
        """Set loop end to current playback position."""
        if self.player is None:
            return
        
        current_time = self.player.get_current_time()
        if self._timeline_canvas:
            current_time = self._timeline_canvas.snap_time(current_time)
        
        loop_info = self.player.get_loop()
        loop_start = loop_info[1]
        
        # Assicura che end sia sempre dopo start
        if current_time <= loop_start:
            loop_start = max(0, current_time - 1.0)
        
        self.player.set_loop(True, loop_start, current_time)
        
        # Aggiorna checkbox se necessario
        if self._toolbar_manager:
            self._toolbar_manager.set_loop_enabled(True)
        
        if self.on_timeline_redraw:
            self.on_timeline_redraw()
        
        status = f"🔁 Loop end: {loop_start:.3f}s → {current_time:.3f}s"
        if self.on_status_change:
            self.on_status_change(status)
        print(status)
    
    def change_bpm(self, new_bpm):
        """Update project BPM and adjust loop points and clip positions.
        
        Args:
            new_bpm: New BPM value
        """
        if self.project is None:
            return
        
        try:
            old_bpm = self.project.bpm
            
            if abs(old_bpm - new_bpm) < 0.01:
                return
            
            # Store loop points in musical time
            loop_enabled = False
            loop_start_bars = 0.0
            loop_end_bars = 0.0
            
            if self.player is not None:
                try:
                    loop_enabled, loop_start_sec, loop_end_sec = self.player.get_loop()
                    loop_start_bars = self.project.seconds_to_bars(loop_start_sec)
                    loop_end_bars = self.project.seconds_to_bars(loop_end_sec)
                except Exception:
                    pass
            
            # Convert all clip positions to musical time (bars) before changing BPM
            clip_positions = []  # (track_idx, clip, start_bars, duration_bars)
            if self.timeline is not None:
                try:
                    for track_idx, clip in self.timeline.all_placements():
                        start_bars = self.project.seconds_to_bars(clip.start_time)
                        duration_bars = self.project.seconds_to_bars(clip.length_seconds)
                        clip_positions.append((track_idx, clip, start_bars, duration_bars))
                except Exception as e:
                    print(f"Error storing clip positions: {e}")
            
            # Update BPM
            self.project.bpm = float(new_bpm)
            
            # Convert clip positions back to seconds with new BPM
            clips_adjusted = 0
            for track_idx, clip, start_bars, duration_bars in clip_positions:
                try:
                    new_start_time = self.project.bars_to_seconds(start_bars)
                    new_duration = self.project.bars_to_seconds(duration_bars)
                    
                    # Update clip timing
                    clip.start_time = new_start_time
                    # Only update duration if it was explicitly set (not derived from buffer)
                    if clip.duration is not None:
                        clip.duration = new_duration
                    
                    clips_adjusted += 1
                except Exception as e:
                    print(f"Error adjusting clip {clip.name}: {e}")
            
            # Convert loop points back
            if self.player is not None and loop_enabled:
                try:
                    new_loop_start = self.project.bars_to_seconds(loop_start_bars)
                    new_loop_end = self.project.bars_to_seconds(loop_end_bars)
                    self.player.set_loop(loop_enabled, new_loop_start, new_loop_end)
                    print(f"🔁 Loop adjusted: {loop_start_sec:.3f}s → {new_loop_start:.3f}s, {loop_end_sec:.3f}s → {new_loop_end:.3f}s")
                except Exception as e:
                    print(f"Loop adjustment error: {e}")
            
            if self.on_timeline_redraw:
                self.on_timeline_redraw()
            
            print(f"♪ BPM changed: {old_bpm:.1f} → {new_bpm}")
            if clips_adjusted > 0:
                print(f"✓ {clips_adjusted} clip(s) adjusted to maintain musical grid alignment")
        except Exception as e:
            print(f"BPM change error: {e}")
