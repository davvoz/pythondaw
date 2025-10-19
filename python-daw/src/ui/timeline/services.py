"""Timeline services - snap, clipboard, and other utilities."""

from typing import List, Tuple, Dict, Any, Optional


class SnapService:
    """Handles snap-to-grid functionality."""
    
    def __init__(self, project=None):
        """Initialize snap service.
        
        Args:
            project: Project object with snap_to_grid method
        """
        self.project = project
        self.enabled = False
        self.grid_division = 0.25  # Default: quarter notes
    
    def set_enabled(self, enabled: bool):
        """Enable or disable snapping."""
        self.enabled = enabled
    
    def set_grid_division(self, division: float):
        """Set grid division.
        
        Args:
            division: Grid division in fraction of a bar (e.g., 0.25 = quarter notes)
        """
        self.grid_division = division
    
    def snap_time(self, time: float) -> float:
        """Snap time to grid if enabled.
        
        Args:
            time: Time in seconds
            
        Returns:
            Snapped time or original time if snap is disabled
        """
        if not self.enabled or self.project is None:
            return time
        
        try:
            return self.project.snap_to_grid(time, self.grid_division)
        except Exception:
            return time


class ClipboardService:
    """Handles clip copy/paste operations."""
    
    def __init__(self):
        """Initialize clipboard service."""
        self.clipboard: List[Dict[str, Any]] = []
        self.paste_position: float = 0.0
        self.paste_cursor_visible: bool = False
    
    def copy_clips(self, selected_clips: List[Tuple[int, Any]], current_time: float = 0.0) -> int:
        """Copy selected clips to clipboard.
        
        Args:
            selected_clips: List of (track_index, clip_object) tuples
            current_time: Current playback time to set as initial paste position
            
        Returns:
            Number of clips copied
        """
        if not selected_clips:
            return 0
        
        # Store clip data in clipboard
        self.clipboard = []
        
        for track_idx, clip in selected_clips:
            clip_data = {
                'track_idx': track_idx,
                'name': clip.name,
                'buffer': clip.buffer,
                'sample_rate': clip.sample_rate,
                'start_time': clip.start_time,
                'duration': clip.duration,
                'color': clip.color,
                'file_path': getattr(clip, 'file_path', None),
                # Editing properties
                'start_offset': getattr(clip, 'start_offset', 0.0),
                'end_offset': getattr(clip, 'end_offset', 0.0),
                'fade_in': getattr(clip, 'fade_in', 0.0),
                'fade_in_shape': getattr(clip, 'fade_in_shape', 'linear'),
                'fade_out': getattr(clip, 'fade_out', 0.0),
                'fade_out_shape': getattr(clip, 'fade_out_shape', 'linear'),
                'pitch_semitones': getattr(clip, 'pitch_semitones', 0.0),
                'volume': getattr(clip, 'volume', 1.0),
            }
            self.clipboard.append(clip_data)
        
        # Show paste cursor at current playback position
        self.paste_position = current_time
        self.paste_cursor_visible = True
        
        return len(self.clipboard)
    
    def has_clips(self) -> bool:
        """Check if clipboard has clips.
        
        Returns:
            True if clipboard is not empty
        """
        return len(self.clipboard) > 0
    
    def set_paste_position(self, position: float, visible: bool = True):
        """Set paste cursor position.
        
        Args:
            position: Time position in seconds
            visible: Whether to show paste cursor
        """
        self.paste_position = position
        self.paste_cursor_visible = visible
    
    def paste_clips(self, at_time: Optional[float], timeline) -> List[Tuple[int, Any]]:
        """Paste clips from clipboard.
        
        Args:
            at_time: Time to paste at (None = use paste_position)
            timeline: Timeline object with add_clip method
            
        Returns:
            List of (track_index, clip) tuples for pasted clips
        """
        if not self.clipboard:
            return []
        
        from src.audio.clip import AudioClip
        
        # Determine paste position
        if at_time is None:
            at_time = self.paste_position
        
        # Find earliest clip to calculate offset
        min_start = min(clip_data['start_time'] for clip_data in self.clipboard)
        time_offset = at_time - min_start
        
        pasted_clips = []
        
        for clip_data in self.clipboard:
            # Create new clip with offset time
            new_start_time = clip_data['start_time'] + time_offset
            
            new_clip = AudioClip(
                clip_data['name'] + " (paste)",
                clip_data['buffer'],
                clip_data['sample_rate'],
                new_start_time,
                duration=clip_data['duration'],
                color=clip_data['color'],
                file_path=clip_data['file_path'],
            )
            
            # Restore editing properties
            new_clip.start_offset = clip_data['start_offset']
            new_clip.end_offset = clip_data['end_offset']
            new_clip.fade_in = clip_data['fade_in']
            new_clip.fade_in_shape = clip_data['fade_in_shape']
            new_clip.fade_out = clip_data['fade_out']
            new_clip.fade_out_shape = clip_data['fade_out_shape']
            new_clip.pitch_semitones = clip_data['pitch_semitones']
            new_clip.volume = clip_data['volume']
            
            # Add to timeline
            track_idx = clip_data['track_idx']
            if timeline:
                timeline.add_clip(track_idx, new_clip)
                pasted_clips.append((track_idx, new_clip))
        
        # Hide paste cursor after pasting
        self.paste_cursor_visible = False
        
        return pasted_clips
    
    def clear(self):
        """Clear clipboard."""
        self.clipboard = []
        self.paste_cursor_visible = False
    
    def draw_paste_cursor(self, canvas, geometry, height: int):
        """Draw paste position cursor.
        
        Args:
            canvas: Tkinter canvas to draw on
            geometry: TimelineGeometry instance
            height: Height of the canvas
        """
        if not self.paste_cursor_visible or not self.clipboard or canvas is None:
            return
        
        paste_x = geometry.time_to_x(self.paste_position)
        
        # Paste cursor line (dashed, green)
        canvas.create_line(
            paste_x, geometry.ruler_height, paste_x, height,
            fill="#10b981", width=2, dash=(5, 3), tags="paste_cursor"
        )
        
        # Paste cursor indicator (triangle pointing down)
        canvas.create_polygon(
            paste_x - 8, geometry.ruler_height,
            paste_x + 8, geometry.ruler_height,
            paste_x, geometry.ruler_height + 12,
            fill="#10b981", outline="#065f46", width=2, tags="paste_cursor"
        )
        
        # Time label
        time_str = f"{self.paste_position:.2f}s"
        canvas.create_text(
            paste_x, geometry.ruler_height + 22,
            text=time_str,
            fill="#10b981",
            font=("Segoe UI", 8, "bold"),
            tags="paste_cursor"
        )
