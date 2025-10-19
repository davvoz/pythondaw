"""Resize controller for clip resizing operations."""

from typing import Optional, Dict, Any, Callable


class ResizeController:
    """Handles clip resizing logic."""
    
    def __init__(self, geometry, snap_service):
        """Initialize resize controller.
        
        Args:
            geometry: TimelineGeometry instance
            snap_service: SnapService instance
        """
        self.geometry = geometry
        self.snap_service = snap_service
        self.resize_data: Optional[Dict[str, Any]] = None
        self.resize_handle_size: int = 12  # Detection zone size in pixels
        self.on_invalidate: Optional[Callable] = None
    
    def check_resize_edge(self, mouse_x: float, clip, track_idx: int) -> Optional[str]:
        """Check if mouse is over a resize edge.
        
        Args:
            mouse_x: Mouse x coordinate
            clip: Clip object
            track_idx: Track index
            
        Returns:
            "left" for left edge, "right" for right edge, None otherwise
        """
        x0, _, x1, _ = self.geometry.clip_bounds(clip, track_idx)
        
        # Check left edge (higher priority)
        if abs(mouse_x - x0) <= self.resize_handle_size:
            return "left"
        
        # Check right edge
        if abs(mouse_x - x1) <= self.resize_handle_size:
            return "right"
        
        return None
    
    def start_resize(self, clip, track_idx: int, edge: str):
        """Start resizing a clip.
        
        Args:
            clip: Clip object to resize
            track_idx: Track index
            edge: Which edge to resize ("left" or "right")
        """
        self.resize_data = {
            'clip': clip,
            'track': track_idx,
            'edge': edge,
            'original_start': clip.start_time,
            'original_end': clip.end_time
        }
    
    def update_resize(self, mouse_x: float) -> bool:
        """Update resize position.
        
        Args:
            mouse_x: Current mouse x coordinate
            
        Returns:
            True if resize was updated, False otherwise
        """
        if self.resize_data is None:
            return False
        
        clip = self.resize_data['clip']
        new_time = self.geometry.x_to_time(mouse_x)
        new_time = max(0, new_time)
        new_time = self.snap_service.snap_time(new_time)
        
        if self.resize_data['edge'] == "left":
            # Resize from left - change start_time
            if new_time < clip.end_time:
                # Calculate new duration based on fixed end_time
                old_end = clip.end_time
                clip.start_time = new_time
                new_duration = old_end - new_time
                clip.duration = new_duration
                
                # Update start_offset if clip has it
                if hasattr(clip, 'start_offset'):
                    time_delta = new_time - self.resize_data['original_start']
                    clip.start_offset = max(0, clip.start_offset - time_delta)
        else:
            # Resize from right - change duration (end_time is computed)
            if new_time > clip.start_time:
                new_duration = new_time - clip.start_time
                clip.duration = new_duration
        
        if self.on_invalidate:
            self.on_invalidate()
        
        return True
    
    def end_resize(self):
        """End resizing."""
        result = self.resize_data
        self.resize_data = None
        return result
    
    def is_resizing(self) -> bool:
        """Check if currently resizing.
        
        Returns:
            True if resizing, False otherwise
        """
        return self.resize_data is not None
    
    def get_resize_data(self) -> Optional[Dict[str, Any]]:
        """Get current resize data.
        
        Returns:
            Resize data dictionary or None
        """
        return self.resize_data
