"""Drag controller for clip dragging operations."""

from typing import Optional, Dict, Any, Callable


class DragController:
    """Handles clip dragging logic."""
    
    def __init__(self, geometry, snap_service):
        """Initialize drag controller.
        
        Args:
            geometry: TimelineGeometry instance
            snap_service: SnapService instance
        """
        self.geometry = geometry
        self.snap_service = snap_service
        self.drag_data: Optional[Dict[str, Any]] = None
        self.on_invalidate: Optional[Callable] = None
    
    def start_drag(self, clip, track_idx: int, mouse_x: float):
        """Start dragging a clip.
        
        Args:
            clip: Clip object to drag
            track_idx: Current track index
            mouse_x: Mouse x coordinate
        """
        self.drag_data = {
            'clip': clip,
            'track': track_idx,
            'start_x': mouse_x,
            'start_time': clip.start_time
        }
    
    def update_drag(self, mouse_x: float, mouse_y: float, mixer) -> bool:
        """Update drag position.
        
        Args:
            mouse_x: Current mouse x coordinate
            mouse_y: Current mouse y coordinate
            mixer: Mixer object with tracks
            
        Returns:
            True if drag was updated, False otherwise
        """
        if self.drag_data is None:
            return False
        
        clip = self.drag_data['clip']
        delta_x = mouse_x - self.drag_data['start_x']
        delta_time = self.geometry.x_to_time(delta_x)
        
        new_start = self.drag_data['start_time'] + delta_time
        new_start = max(0, new_start)
        new_start = self.snap_service.snap_time(new_start)
        
        clip.start_time = new_start
        
        # Check track change
        track_idx = self.geometry.y_to_track(mouse_y)
        if track_idx is not None and mixer is not None:
            track_idx = max(0, min(track_idx, len(mixer.tracks) - 1))
            
            if track_idx != self.drag_data['track']:
                # Move clip to different track
                old_track = self.drag_data['track']
                self.drag_data['track'] = track_idx
                # Caller should handle timeline.move_clip(old_track, track_idx, clip)
        
        if self.on_invalidate:
            self.on_invalidate()
        
        return True
    
    def end_drag(self):
        """End dragging."""
        result = self.drag_data
        self.drag_data = None
        return result
    
    def is_dragging(self) -> bool:
        """Check if currently dragging.
        
        Returns:
            True if dragging, False otherwise
        """
        return self.drag_data is not None
    
    def get_drag_data(self) -> Optional[Dict[str, Any]]:
        """Get current drag data.
        
        Returns:
            Drag data dictionary or None
        """
        return self.drag_data
