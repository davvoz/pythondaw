"""Timeline geometry calculations and coordinate conversions."""

from typing import Optional, Tuple


class TimelineGeometry:
    """Handles all coordinate conversions and dimension calculations for the timeline."""
    
    def __init__(
        self,
        px_per_sec: int = 200,
        track_height: int = 80,
        ruler_height: int = 32,
        left_margin: int = 280
    ):
        """Initialize timeline geometry.
        
        Args:
            px_per_sec: Pixels per second for horizontal scale
            track_height: Height of each track in pixels
            ruler_height: Height of the ruler area in pixels
            left_margin: Width of the left controls area in pixels
        """
        self.px_per_sec = px_per_sec
        self.track_height = track_height
        self.ruler_height = ruler_height
        self.left_margin = left_margin
    
    # Coordinate conversions
    
    def time_to_x(self, time: float) -> float:
        """Convert time in seconds to canvas x coordinate.
        
        Args:
            time: Time in seconds
            
        Returns:
            X coordinate in pixels (without left margin offset)
        """
        return time * self.px_per_sec
    
    def x_to_time(self, x: float) -> float:
        """Convert canvas x coordinate to time in seconds.
        
        Args:
            x: X coordinate in pixels (without left margin offset)
            
        Returns:
            Time in seconds
        """
        return x / self.px_per_sec
    
    def track_to_y(self, track_idx: int) -> Tuple[float, float]:
        """Convert track index to canvas y coordinates (top, bottom).
        
        Args:
            track_idx: Zero-based track index
            
        Returns:
            Tuple of (y_top, y_bottom) in pixels
        """
        y0 = self.ruler_height + track_idx * self.track_height
        y1 = y0 + self.track_height
        return y0, y1
    
    def y_to_track(self, y: float) -> Optional[int]:
        """Convert canvas y coordinate to track index.
        
        Args:
            y: Y coordinate in pixels
            
        Returns:
            Track index or None if y is in ruler area or invalid
        """
        if y <= self.ruler_height:
            return None
        track_idx = int((y - self.ruler_height) / self.track_height)
        return track_idx if track_idx >= 0 else None
    
    def clip_bounds(self, clip, track_idx: int) -> Tuple[float, float, float, float]:
        """Get canvas bounds (x0, y0, x1, y1) for a clip.
        
        Args:
            clip: Clip object with start_time and end_time attributes
            track_idx: Track index where clip is placed
            
        Returns:
            Tuple of (x0, y0, x1, y1) in pixels
        """
        y0, y1 = self.track_to_y(track_idx)
        x0 = self.time_to_x(clip.start_time)
        x1 = self.time_to_x(clip.end_time)
        return x0, y0, x1, y1
    
    # Dimension calculations
    
    def compute_width(self, timeline=None, min_width: int = 800) -> int:
        """Calculate timeline width based on content.
        
        Args:
            timeline: Timeline object with all_placements() method
            min_width: Minimum width in pixels
            
        Returns:
            Width in pixels
        """
        max_end = 5.0  # Default 5 seconds
        
        if timeline is not None:
            try:
                for _, clip in timeline.all_placements():
                    max_end = max(max_end, clip.end_time)
            except Exception:
                pass
        
        width = int(max_end * self.px_per_sec + 40)
        return max(width, min_width)
    
    def compute_height(self, track_count: int) -> int:
        """Calculate timeline height based on track count.
        
        Args:
            track_count: Number of tracks
            
        Returns:
            Height in pixels
        """
        track_count = max(1, track_count)
        return self.ruler_height + (self.track_height * track_count)
    
    # Zoom operations
    
    def zoom(self, factor: float) -> float:
        """Apply zoom factor to timeline.
        
        Args:
            factor: Zoom multiplier (>1 = zoom in, <1 = zoom out)
            
        Returns:
            New zoom level (1.0 = default)
        """
        self.px_per_sec = max(40, min(800, int(self.px_per_sec * factor)))
        return self.px_per_sec / 200.0
    
    def zoom_reset(self):
        """Reset zoom to default."""
        self.px_per_sec = 200
