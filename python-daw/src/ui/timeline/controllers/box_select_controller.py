"""Box selection controller for rectangular clip selection."""

from typing import Optional, Tuple, Callable, List, Any


class BoxSelectController:
    """Handles box selection (rectangular selection) logic."""
    
    def __init__(self, geometry):
        """Initialize box select controller.
        
        Args:
            geometry: TimelineGeometry instance
        """
        self.geometry = geometry
        self.box_selection_start: Optional[Tuple[float, float]] = None
        self.box_selection_rect: Optional[int] = None  # Canvas item ID
        self.on_invalidate: Optional[Callable] = None
    
    def start_selection(self, mouse_x: float, mouse_y: float):
        """Start box selection.
        
        Args:
            mouse_x: Mouse x coordinate
            mouse_y: Mouse y coordinate
        """
        self.box_selection_start = (mouse_x, mouse_y)
        self.box_selection_rect = None
    
    def update_selection(self, canvas, mouse_x: float, mouse_y: float):
        """Update box selection visual.
        
        Args:
            canvas: Tkinter canvas to draw on
            mouse_x: Current mouse x coordinate
            mouse_y: Current mouse y coordinate
        """
        if self.box_selection_start is None or canvas is None:
            return
        
        start_x, start_y = self.box_selection_start
        
        # Calculate rectangle bounds
        x1 = min(start_x, mouse_x)
        y1 = min(start_y, mouse_y)
        x2 = max(start_x, mouse_x)
        y2 = max(start_y, mouse_y)
        
        # Delete previous selection rectangle
        if self.box_selection_rect is not None:
            try:
                canvas.delete(self.box_selection_rect)
            except Exception:
                pass
        
        # Draw selection rectangle
        self.box_selection_rect = canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="#60a5fa", width=2, dash=(4, 4),
            fill="#3b82f6", stipple="gray25",
            tags="box_selection"
        )
        
        print(f"📦 Drawing box: ({x1:.0f},{y1:.0f}) → ({x2:.0f},{y2:.0f})")
    
    def complete_selection(
        self,
        canvas,
        timeline,
        current_mouse_x: float,
        current_mouse_y: float
    ) -> List[Tuple[int, Any]]:
        """Complete box selection and return selected clips.
        
        Args:
            canvas: Tkinter canvas
            timeline: Timeline object with all_placements method
            current_mouse_x: Current mouse x coordinate
            current_mouse_y: Current mouse y coordinate
            
        Returns:
            List of (track_index, clip) tuples for clips within the box
        """
        if self.box_selection_start is None:
            return []
        
        start_x, start_y = self.box_selection_start
        
        # Calculate selection bounds
        x1 = min(start_x, current_mouse_x)
        y1 = min(start_y, current_mouse_y)
        x2 = max(start_x, current_mouse_x)
        y2 = max(start_y, current_mouse_y)
        
        selected_clips = []
        
        # Find clips within selection box
        if timeline is not None:
            try:
                for track_idx, clip in timeline.all_placements():
                    clip_x0, clip_y0, clip_x1, clip_y1 = self.geometry.clip_bounds(clip, track_idx)
                    
                    # Check if clip intersects with selection box
                    if (clip_x0 < x2 and clip_x1 > x1 and
                        clip_y0 < y2 and clip_y1 > y1):
                        selected_clips.append((track_idx, clip))
            except Exception:
                pass
        
        # Clear selection visual
        if canvas and self.box_selection_rect is not None:
            try:
                canvas.delete(self.box_selection_rect)
            except Exception:
                pass
        
        self.box_selection_start = None
        self.box_selection_rect = None
        
        return selected_clips
    
    def cancel_selection(self, canvas):
        """Cancel box selection.
        
        Args:
            canvas: Tkinter canvas
        """
        if canvas and self.box_selection_rect is not None:
            try:
                canvas.delete(self.box_selection_rect)
            except Exception:
                pass
        
        self.box_selection_start = None
        self.box_selection_rect = None
    
    def is_selecting(self) -> bool:
        """Check if currently selecting.
        
        Returns:
            True if box selection is active, False otherwise
        """
        return self.box_selection_start is not None
