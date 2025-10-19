"""Track controls controller for track control interactions."""

from typing import Optional, Dict, Any, Callable


class TrackControlsController:
    """Handles track control interactions (buttons, sliders)."""
    
    def __init__(self, geometry, left_margin: int):
        """Initialize track controls controller.
        
        Args:
            geometry: TimelineGeometry instance
            left_margin: Width of the controls area
        """
        self.geometry = geometry
        self.left_margin = left_margin
        self.dragging_volume: Optional[Dict[str, Any]] = None
        self.dragging_pan: Optional[Dict[str, Any]] = None
        self.on_invalidate: Optional[Callable] = None
    
    def find_control_at(
        self,
        x: float,
        y: float,
        mixer
    ) -> Optional[Dict[str, Any]]:
        """Find which control is at the given coordinates.
        
        Args:
            x: X coordinate
            y: Y coordinate
            mixer: Mixer object with tracks
            
        Returns:
            Dictionary with control info or None
        """
        if x >= self.left_margin:
            return None  # Not in controls area
        
        track_idx = self.geometry.y_to_track(y)
        if track_idx is None or mixer is None or track_idx >= len(mixer.tracks):
            return None
        
        # Calculate y position within track
        y0, _ = self.geometry.track_to_y(track_idx)
        y_in_track = y - y0
        
        # Button positions (top-right of control area)
        btn_y = 8
        btn_x = self.left_margin - 95
        
        # Check buttons (M/S/FX)
        if btn_y <= y_in_track <= btn_y + 18:
            # Mute button
            if btn_x <= x <= btn_x + 20:
                return {'type': 'button', 'action': 'mute', 'track_idx': track_idx}
            # Solo button
            elif btn_x + 25 <= x <= btn_x + 45:
                return {'type': 'button', 'action': 'solo', 'track_idx': track_idx}
            # FX button
            elif btn_x + 50 <= x <= btn_x + 72:
                return {'type': 'button', 'action': 'fx', 'track_idx': track_idx}
        
        # Volume slider
        vol_y = 35
        vol_x = 40
        vol_width = self.left_margin - 100
        
        if vol_y - 4 <= y_in_track <= vol_y + 4:
            if vol_x <= x <= vol_x + vol_width:
                return {'type': 'volume', 'track_idx': track_idx}
        
        # Pan slider
        pan_y = 55
        if pan_y - 4 <= y_in_track <= pan_y + 4:
            if vol_x <= x <= vol_x + vol_width:
                return {'type': 'pan', 'track_idx': track_idx}
        
        return None
    
    def start_volume_drag(self, track_idx: int, mouse_x: float, mixer):
        """Start volume slider drag.
        
        Args:
            track_idx: Track index
            mouse_x: Mouse x coordinate
            mixer: Mixer object
        """
        if mixer is None or track_idx >= len(mixer.tracks):
            return
        
        self.dragging_volume = {
            'track': track_idx,
            'start_x': mouse_x,
            'start_vol': mixer.tracks[track_idx].get('volume', 1.0)
        }
    
    def update_volume_drag(self, mouse_x: float, mixer) -> bool:
        """Update volume slider position.
        
        Args:
            mouse_x: Current mouse x coordinate
            mixer: Mixer object
            
        Returns:
            True if volume was updated, False otherwise
        """
        if self.dragging_volume is None or mixer is None:
            return False
        
        track_idx = self.dragging_volume['track']
        if track_idx >= len(mixer.tracks):
            return False
        
        # Calculate new volume
        vol_x = 40
        vol_width = self.left_margin - 100
        
        # Clamp x to slider bounds
        x = max(vol_x, min(mouse_x, vol_x + vol_width))
        
        # Calculate volume (0.0 to 1.0)
        volume = (x - vol_x) / vol_width
        volume = max(0.0, min(1.0, volume))
        
        # Update mixer
        mixer.tracks[track_idx]['volume'] = volume
        
        if self.on_invalidate:
            self.on_invalidate()
        
        return True
    
    def end_volume_drag(self):
        """End volume drag."""
        result = self.dragging_volume
        self.dragging_volume = None
        return result
    
    def start_pan_drag(self, track_idx: int, mouse_x: float, mixer):
        """Start pan slider drag.
        
        Args:
            track_idx: Track index
            mouse_x: Mouse x coordinate
            mixer: Mixer object
        """
        if mixer is None or track_idx >= len(mixer.tracks):
            return
        
        self.dragging_pan = {
            'track': track_idx,
            'start_x': mouse_x,
            'start_pan': mixer.tracks[track_idx].get('pan', 0.0)
        }
    
    def update_pan_drag(self, mouse_x: float, mixer) -> bool:
        """Update pan slider position.
        
        Args:
            mouse_x: Current mouse x coordinate
            mixer: Mixer object
            
        Returns:
            True if pan was updated, False otherwise
        """
        if self.dragging_pan is None or mixer is None:
            return False
        
        track_idx = self.dragging_pan['track']
        if track_idx >= len(mixer.tracks):
            return False
        
        # Calculate new pan
        pan_x = 40
        pan_width = self.left_margin - 100
        center_x = pan_x + pan_width // 2
        
        # Clamp x to slider bounds
        x = max(pan_x, min(mouse_x, pan_x + pan_width))
        
        # Calculate pan (-1.0 to 1.0)
        pan = (x - center_x) / (pan_width / 2)
        pan = max(-1.0, min(1.0, pan))
        
        # Snap to center if close
        if abs(pan) < 0.05:
            pan = 0.0
        
        # Update mixer
        mixer.tracks[track_idx]['pan'] = pan
        
        if self.on_invalidate:
            self.on_invalidate()
        
        return True
    
    def end_pan_drag(self):
        """End pan drag."""
        result = self.dragging_pan
        self.dragging_pan = None
        return result
    
    def is_dragging(self) -> bool:
        """Check if currently dragging a control.
        
        Returns:
            True if dragging volume or pan, False otherwise
        """
        return self.dragging_volume is not None or self.dragging_pan is not None
