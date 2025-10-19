"""Timeline rendering components - modular renderers for different timeline elements."""

from typing import Any, Optional


class RulerRenderer:
    """Renders the timeline ruler with time markers."""
    
    def __init__(self, geometry):
        """Initialize ruler renderer.
        
        Args:
            geometry: TimelineGeometry instance
        """
        self.geometry = geometry
    
    def draw(self, canvas, width: int, project=None):
        """Draw the time ruler.
        
        Args:
            canvas: Tkinter canvas to draw on
            width: Width of the ruler in pixels
            project: Project object with get_bar_duration() and get_beat_duration() methods
        """
        if canvas is None:
            return
        
        # Ruler background
        canvas.create_rectangle(
            0, 0, width, self.geometry.ruler_height,
            fill="#1a1a1a", outline=""
        )
        
        if project is not None:
            self._draw_musical_ruler(canvas, width, project)
        else:
            self._draw_time_ruler(canvas, width)
    
    def _draw_musical_ruler(self, canvas, width: int, project):
        """Draw musical ruler with bars and beats."""
        bar_duration = project.get_bar_duration()
        beat_duration = project.get_beat_duration()
        max_time = self.geometry.x_to_time(width)
        
        # Draw bar markers
        bar_num = 0
        while True:
            bar_time = bar_num * bar_duration
            if bar_time > max_time:
                break
            
            x = self.geometry.time_to_x(bar_time)
            
            # Bar line - thick bright blue
            canvas.create_line(
                x, 0, x, self.geometry.ruler_height,
                fill="#3b82f6", width=2
            )
            
            # Bar number
            canvas.create_text(
                x + 4, 8, anchor="nw",
                text=f"{bar_num + 1}",
                fill="#60a5fa", font=("Consolas", 9, "bold")
            )
            
            bar_num += 1
        
        # Draw beat markers
        beat_num = 0
        while True:
            beat_time = beat_num * beat_duration
            if beat_time > max_time:
                break
            
            x = self.geometry.time_to_x(beat_time)
            
            # Skip bar positions (already drawn)
            is_bar = abs(beat_time % bar_duration) < 0.001
            if not is_bar:
                canvas.create_line(
                    x, self.geometry.ruler_height - 8,
                    x, self.geometry.ruler_height,
                    fill="#1e40af", width=1
                )
            
            beat_num += 1
    
    def _draw_time_ruler(self, canvas, width: int):
        """Draw simple time ruler in seconds."""
        max_time = self.geometry.x_to_time(width)
        total_secs = int(max_time) + 1
        
        for sec in range(total_secs):
            x = self.geometry.time_to_x(sec)
            
            # Second marker - thick bright blue
            canvas.create_line(
                x, 0, x, self.geometry.ruler_height,
                fill="#3b82f6", width=2
            )
            
            # Second label
            canvas.create_text(
                x + 4, 8, anchor="nw",
                text=f"{sec:02d}s",
                fill="#60a5fa", font=("Consolas", 8, "bold")
            )
            
            # Quarter second markers
            for q in range(1, 4):
                mx = x + q * (self.geometry.px_per_sec / 4.0)
                canvas.create_line(
                    mx, self.geometry.ruler_height - 6,
                    mx, self.geometry.ruler_height,
                    fill="#60a5fa", width=1
                )


class GridRenderer:
    """Renders the timeline grid."""
    
    def __init__(self, geometry):
        """Initialize grid renderer.
        
        Args:
            geometry: TimelineGeometry instance
        """
        self.geometry = geometry
    
    def draw(self, canvas, width: int, height: int, project=None, grid_division: float = 0.25):
        """Draw the grid.
        
        Args:
            canvas: Tkinter canvas to draw on
            width: Width of the canvas
            height: Height of the canvas
            project: Project object (if None, draws time-based grid)
            grid_division: Grid subdivision (fraction of a bar, e.g., 0.25 = quarter notes)
        """
        if canvas is None:
            return
        
        if project is not None:
            self._draw_musical_grid(canvas, width, height, project, grid_division)
        else:
            self._draw_time_grid(canvas, width, height)
    
    def _draw_musical_grid(self, canvas, width: int, height: int, project, grid_division: float):
        """Draw musical grid with bars, beats and subdivisions."""
        bar_duration = project.get_bar_duration()
        beat_duration = project.get_beat_duration()
        max_time = self.geometry.x_to_time(width)
        
        # PASS 1: Draw bar lines (strongest)
        bar_num = 0
        while True:
            bar_time = bar_num * bar_duration
            if bar_time > max_time:
                break
            
            x = self.geometry.time_to_x(bar_time)
            canvas.create_line(
                x, self.geometry.ruler_height, x, height,
                fill="#3b82f6", width=3
            )
            
            bar_num += 1
        
        # PASS 2: Draw grid subdivision lines
        if grid_division > 0:
            grid_time = bar_duration * grid_division
            t = grid_time
            
            while t < max_time:
                # Skip bar positions
                if abs(t % bar_duration) >= 0.001:
                    x = self.geometry.time_to_x(t)
                    canvas.create_line(
                        x, self.geometry.ruler_height, x, height,
                        fill="#1e40af", width=1, dash=(2, 2)
                    )
                t += grid_time
    
    def _draw_time_grid(self, canvas, width: int, height: int):
        """Draw simple time-based grid (seconds)."""
        max_time = self.geometry.x_to_time(width)
        total_secs = int(max_time) + 1
        
        for sec in range(total_secs):
            x = self.geometry.time_to_x(sec)
            
            # Major gridline
            canvas.create_line(
                x, self.geometry.ruler_height, x, height,
                fill="#3b82f6", width=2
            )
            
            # Minor ticks (quarters)
            for q in range(1, 4):
                mx = x + q * (self.geometry.px_per_sec / 4.0)
                canvas.create_line(
                    mx, self.geometry.ruler_height, mx, height,
                    fill="#60a5fa", width=1, dash=(3, 3)
                )


class TrackRenderer:
    """Renders track backgrounds."""
    
    def __init__(self, geometry):
        """Initialize track renderer.
        
        Args:
            geometry: TimelineGeometry instance
        """
        self.geometry = geometry
    
    def draw(self, canvas, width: int, track_count: int, selected_track_idx: Optional[int] = None):
        """Draw track backgrounds.
        
        Args:
            canvas: Tkinter canvas to draw on
            width: Width of the canvas
            track_count: Number of tracks
            selected_track_idx: Index of selected track (for highlighting)
        """
        if canvas is None:
            return
        
        for i in range(track_count):
            y0, y1 = self.geometry.track_to_y(i)
            
            # Alternating background with selection highlight
            if selected_track_idx == i:
                bg_color = "#1a2332"  # Highlight selected track
            else:
                bg_color = "#0d0d0d" if i % 2 == 0 else "#151515"
            
            canvas.create_rectangle(
                0, y0, width, y1,
                fill=bg_color, outline=""
            )


class ClipRenderer:
    """Renders clips on the timeline."""
    
    def __init__(self, geometry):
        """Initialize clip renderer.
        
        Args:
            geometry: TimelineGeometry instance
        """
        self.geometry = geometry
    
    def draw_clip(
        self,
        canvas,
        clip,
        track_idx: int,
        is_selected: bool = False,
        track_color: str = "#3b82f6"
    ) -> int:
        """Draw a single clip.
        
        Args:
            canvas: Tkinter canvas to draw on
            clip: Clip object with start_time, end_time, name attributes
            track_idx: Track index
            is_selected: Whether clip is selected
            track_color: Color for the clip
            
        Returns:
            Canvas item ID of the clip rectangle
        """
        x0, y0, x1, y1 = self.geometry.clip_bounds(clip, track_idx)
        
        # Colors
        clip_color = track_color
        clip_border = self._lighten_color(track_color)
        
        # Selection highlight
        border_width = 3 if is_selected else 2
        if is_selected:
            clip_border = "#ffffff"
        
        # Clip rectangle with padding
        clip_id = canvas.create_rectangle(
            x0, y0 + 8, x1, y1 - 8,
            fill=clip_color, outline=clip_border, width=border_width
        )
        
        # Draw waveform
        self._draw_waveform(canvas, clip, x0, x1, y0, y1)
        
        # Clip name
        clip_name = getattr(clip, 'name', 'clip')
        canvas.create_text(
            x0 + 6, y0 + 14, anchor="nw",
            text=clip_name,
            fill="#ffffff", font=("Segoe UI", 9, "bold")
        )
        
        # Draw resize handles if selected
        if is_selected:
            self._draw_resize_handles(canvas, x0, x1, y0, y1)
        
        return clip_id
    
    def _draw_waveform(self, canvas, clip, x0: float, x1: float, y0: float, y1: float):
        """Draw waveform visualization in clip."""
        try:
            clip_width = x1 - x0
            if clip_width > 20:
                # Simple waveform visualization
                num_bars = min(int(clip_width / 3), 100)
                bar_width = clip_width / num_bars
                
                for i in range(num_bars):
                    # Vary height for visual effect
                    bar_height = (i % 7 + 1) * 3
                    bar_x = x0 + i * bar_width
                    center_y = (y0 + y1) / 2
                    
                    canvas.create_rectangle(
                        bar_x, center_y - bar_height,
                        bar_x + bar_width - 1, center_y + bar_height,
                        fill="#60a5fa", outline=""
                    )
        except Exception:
            pass
    
    def _draw_resize_handles(self, canvas, x0: float, x1: float, y0: float, y1: float):
        """Draw resize handles on clip edges."""
        handle_color = "#ffffff"
        handle_width = 3
        
        # Left handle (vertical line)
        canvas.create_line(
            x0, y0 + 8, x0, y1 - 8,
            fill=handle_color, width=handle_width, tags="resize_handle"
        )
        
        # Right handle (vertical line)
        canvas.create_line(
            x1, y0 + 8, x1, y1 - 8,
            fill=handle_color, width=handle_width, tags="resize_handle"
        )
        
        # Visual indicators (arrows)
        handle_mid_y = (y0 + y1) / 2
        
        # Left arrow
        canvas.create_polygon(
            x0 + 1, handle_mid_y,
            x0 + 8, handle_mid_y - 4,
            x0 + 8, handle_mid_y + 4,
            fill=handle_color, outline="", tags="resize_handle"
        )
        
        # Right arrow
        canvas.create_polygon(
            x1 - 1, handle_mid_y,
            x1 - 8, handle_mid_y - 4,
            x1 - 8, handle_mid_y + 4,
            fill=handle_color, outline="", tags="resize_handle"
        )
    
    @staticmethod
    def _lighten_color(hex_color: str, factor: float = 1.3) -> str:
        """Lighten a hex color."""
        try:
            hex_color = hex_color.lstrip('#')
            r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return "#60a5fa"


class CursorRenderer:
    """Renders the playback cursor."""
    
    def __init__(self, geometry):
        """Initialize cursor renderer.
        
        Args:
            geometry: TimelineGeometry instance
        """
        self.geometry = geometry
    
    def draw(self, canvas, height: int, current_time: float = 0.0) -> int:
        """Draw the playback cursor.
        
        Args:
            canvas: Tkinter canvas to draw on
            height: Height of the canvas
            current_time: Current playback time in seconds
            
        Returns:
            Canvas item ID of the cursor line
        """
        if canvas is None:
            return None
        
        cursor_x = self.geometry.time_to_x(current_time)
        
        # Cursor line
        cursor_id = canvas.create_line(
            cursor_x, 0, cursor_x, height,
            fill="#ef4444", width=3
        )
        
        # Cursor head (triangle)
        canvas.create_polygon(
            cursor_x - 6, 0,
            cursor_x + 6, 0,
            cursor_x, 10,
            fill="#ef4444", outline=""
        )
        
        return cursor_id
    
    def update(self, canvas, cursor_id: Optional[int], height: int, current_time: float):
        """Update cursor position.
        
        Args:
            canvas: Tkinter canvas
            cursor_id: Canvas item ID of cursor line
            height: Height of the canvas
            current_time: Current playback time in seconds
        """
        if canvas is None or cursor_id is None:
            return
        
        x = self.geometry.time_to_x(current_time)
        
        try:
            canvas.coords(cursor_id, x, 0, x, height)
        except Exception:
            pass


class LoopRenderer:
    """Renders loop region markers."""
    
    def __init__(self, geometry):
        """Initialize loop renderer.
        
        Args:
            geometry: TimelineGeometry instance
        """
        self.geometry = geometry
    
    def draw(
        self,
        canvas,
        ruler_canvas,
        height: int,
        loop_start: float,
        loop_end: float
    ):
        """Draw loop region markers.
        
        Args:
            canvas: Main timeline canvas
            ruler_canvas: Ruler canvas for markers
            height: Height of the main canvas
            loop_start: Loop start time in seconds
            loop_end: Loop end time in seconds
        """
        if canvas is None:
            return
        
        loop_x_start = self.geometry.time_to_x(loop_start)
        loop_x_end = self.geometry.time_to_x(loop_end)
        
        # Loop region highlight on main canvas
        canvas.create_rectangle(
            loop_x_start, 0,
            loop_x_end, height,
            fill="#10b981", stipple="gray25", outline=""
        )
        
        # Draw loop markers on ruler canvas
        if ruler_canvas is not None:
            self._draw_loop_marker(ruler_canvas, loop_x_start, "[", is_end=False)
            self._draw_loop_marker(ruler_canvas, loop_x_end, "]", is_end=True)
    
    def _draw_loop_marker(self, canvas, x: float, label: str, is_end: bool = False):
        """Draw a single loop marker."""
        # Marker line (vertical line in ruler area)
        canvas.create_line(
            x, 0, x, self.geometry.ruler_height,
            fill="#10b981", width=3, tags=f"loop_marker_{label.lower()}"
        )
        
        # Marker flag (handle at bottom of ruler)
        marker_y = self.geometry.ruler_height - 2
        
        if is_end:
            # End marker - triangle pointing left
            canvas.create_polygon(
                x, marker_y,
                x - 10, marker_y - 8,
                x - 10, marker_y,
                fill="#10b981", outline="#065f46", width=2,
                tags=f"loop_marker_{label.lower()}"
            )
            canvas.create_text(
                x - 5, marker_y - 4, text=label,
                fill="#ffffff", font=("Segoe UI", 9, "bold"),
                tags=f"loop_marker_{label.lower()}"
            )
        else:
            # Start marker - triangle pointing right
            canvas.create_polygon(
                x, marker_y,
                x + 10, marker_y - 8,
                x + 10, marker_y,
                fill="#10b981", outline="#065f46", width=2,
                tags=f"loop_marker_{label.lower()}"
            )
            canvas.create_text(
                x + 5, marker_y - 4, text=label,
                fill="#ffffff", font=("Segoe UI", 9, "bold"),
                tags=f"loop_marker_{label.lower()}"
            )
