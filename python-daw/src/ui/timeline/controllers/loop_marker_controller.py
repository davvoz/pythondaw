"""Loop marker controller for loop region dragging."""

from typing import Optional, Callable


class LoopMarkerController:
    """Handles loop marker dragging logic."""
    
    def __init__(self, geometry, snap_service):
        """Initialize loop marker controller.
        
        Args:
            geometry: TimelineGeometry instance
            snap_service: SnapService instance
        """
        self.geometry = geometry
        self.snap_service = snap_service
        self.dragging_loop_marker: Optional[str] = None  # "start" or "end"
        self.marker_click_threshold: int = 15  # Detection zone in pixels
        self.on_invalidate: Optional[Callable] = None
    
    def check_loop_marker_hit(
        self,
        mouse_x: float,
        mouse_y: float,
        player
    ) -> Optional[str]:
        """Check if mouse is over a loop marker.
        
        Args:
            mouse_x: Mouse x coordinate
            mouse_y: Mouse y coordinate
            player: Player object with get_loop method
            
        Returns:
            "start" for start marker, "end" for end marker, None otherwise
        """
        if player is None:
            return None
        
        # Only check in ruler area
        if mouse_y > self.geometry.ruler_height + 30:
            return None
        
        try:
            loop_enabled, loop_start, loop_end = player.get_loop()
            if not loop_enabled:
                return None
            
            loop_x_start = self.geometry.time_to_x(loop_start)
            loop_x_end = self.geometry.time_to_x(loop_end)
            
            # Check start marker (higher priority)
            if abs(mouse_x - loop_x_start) <= self.marker_click_threshold:
                return "start"
            
            # Check end marker
            if abs(mouse_x - loop_x_end) <= self.marker_click_threshold:
                return "end"
        except Exception:
            pass
        
        return None
    
    def start_drag(self, marker: str):
        """Start dragging a loop marker.
        
        Args:
            marker: Which marker to drag ("start" or "end")
        """
        self.dragging_loop_marker = marker
    
    def update_drag(self, mouse_x: float, player) -> bool:
        """Update loop marker position.
        
        Args:
            mouse_x: Current mouse x coordinate
            player: Player object with set_loop method
            
        Returns:
            True if marker was updated, False otherwise
        """
        if self.dragging_loop_marker is None or player is None:
            return False
        
        new_time = self.geometry.x_to_time(mouse_x)
        new_time = max(0, new_time)
        new_time = self.snap_service.snap_time(new_time)
        
        try:
            loop_enabled, loop_start, loop_end = player.get_loop()
            
            if self.dragging_loop_marker == "start":
                # Ensure start is before end
                if new_time < loop_end:
                    player.set_loop(True, new_time, loop_end)
            else:  # "end"
                # Ensure end is after start
                if new_time > loop_start:
                    player.set_loop(True, loop_start, new_time)
            
            if self.on_invalidate:
                self.on_invalidate()
            
            return True
        except Exception:
            return False
    
    def end_drag(self):
        """End dragging loop marker."""
        marker = self.dragging_loop_marker
        self.dragging_loop_marker = None
        return marker
    
    def is_dragging(self) -> bool:
        """Check if currently dragging a loop marker.
        
        Returns:
            True if dragging, False otherwise
        """
        return self.dragging_loop_marker is not None
    
    def get_dragging_marker(self) -> Optional[str]:
        """Get which marker is being dragged.
        
        Returns:
            "start", "end", or None
        """
        return self.dragging_loop_marker
