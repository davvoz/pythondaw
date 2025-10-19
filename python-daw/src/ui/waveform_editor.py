"""Professional Waveform Editor Widget for AudioClip editing."""

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover
    tk = None
    ttk = None

from typing import Optional, Callable, Tuple
import math


class WaveformEditor(tk.Canvas):
    """Interactive waveform display with visual trim/fade controls.
    
    Features:
    - Visual waveform display with peaks
    - Draggable trim handles (start/end offset)
    - Draggable fade handles (fade in/out)
    - Zoom and pan controls
    - Real-time visual feedback
    """
    
    def __init__(self, parent, clip, on_change: Optional[Callable] = None, **kwargs):
        """Initialize the waveform editor.
        
        Args:
            parent: Parent widget
            clip: AudioClip instance to edit
            on_change: Callback when clip parameters change
            **kwargs: Additional canvas options
        """
        # Default styling
        kwargs.setdefault('bg', '#0f0f0f')
        kwargs.setdefault('highlightthickness', 0)
        kwargs.setdefault('height', 200)
        
        super().__init__(parent, **kwargs)
        
        self.clip = clip
        self.on_change = on_change
        
        # Visual state
        self.peaks = []
        self.zoom = 1.0
        self.scroll_offset = 0.0
        
        # Interaction state
        self.dragging = None  # None | 'start' | 'end' | 'fade_in' | 'fade_out' | 'waveform'
        self.drag_start_x = 0
        self.drag_start_value = 0
        
        # Colors
        self.waveform_color = '#3b82f6'
        self.waveform_fill = '#1e3a8a'
        self.trim_color = '#ef4444'
        self.fade_color = '#10b981'
        self.handle_color = '#f59e0b'
        self.grid_color = '#262626'
        self.text_color = '#9ca3af'
        
        # Bind events
        self.bind('<Configure>', self._on_resize)
        self.bind('<Button-1>', self._on_click)
        self.bind('<B1-Motion>', self._on_drag)
        self.bind('<ButtonRelease-1>', self._on_release)
        self.bind('<MouseWheel>', self._on_scroll)
        self.bind('<Motion>', self._on_motion)
        
        # Initial draw
        self.after(50, self._update_peaks)
    
    def _update_peaks(self):
        """Update peaks from clip buffer."""
        if self.clip and hasattr(self.clip, 'get_peaks'):
            width = self.winfo_width()
            if width > 0:
                num_points = int(width * self.zoom)
                self.peaks = self.clip.get_peaks(max(100, num_points))
        else:
            self.peaks = []
        self.redraw()
    
    def redraw(self):
        """Redraw the entire waveform display."""
        self.delete('all')
        
        width = self.winfo_width()
        height = self.winfo_height()
        
        if width <= 0 or height <= 0:
            return
        
        # Draw grid lines
        self._draw_grid(width, height)
        
        # Draw waveform
        self._draw_waveform(width, height)
        
        # Draw trim regions (darkened areas)
        self._draw_trim_regions(width, height)
        
        # Draw fade indicators
        self._draw_fade_regions(width, height)
        
        # Draw handles
        self._draw_handles(width, height)
        
        # Draw time markers
        self._draw_time_markers(width, height)
    
    def _draw_grid(self, width: int, height: int):
        """Draw background grid."""
        mid_y = height / 2
        
        # Center line
        self.create_line(0, mid_y, width, mid_y, fill=self.grid_color, width=1)
        
        # Horizontal lines at ±0.5 amplitude
        quarter = height / 4
        self.create_line(0, quarter, width, quarter, fill=self.grid_color, width=1, dash=(2, 4))
        self.create_line(0, height - quarter, width, height - quarter, fill=self.grid_color, width=1, dash=(2, 4))
    
    def _draw_waveform(self, width: int, height: int):
        """Draw the audio waveform."""
        if not self.peaks:
            return
        
        mid_y = height / 2
        amplitude_scale = (height / 2) * 0.9  # Leave 10% margin
        
        num_peaks = len(self.peaks)
        if num_peaks == 0:
            return
        
        # Calculate visible range based on zoom and scroll
        visible_start = int(self.scroll_offset * num_peaks)
        visible_end = int(min(visible_start + num_peaks / self.zoom, num_peaks))
        
        if visible_end <= visible_start:
            return
        
        visible_peaks = self.peaks[visible_start:visible_end]
        pixels_per_peak = width / len(visible_peaks)
        
        # Draw filled polygon for waveform
        points = []
        
        # Top half (max values)
        for i, (min_val, max_val) in enumerate(visible_peaks):
            x = i * pixels_per_peak
            y = mid_y - (max_val * amplitude_scale)
            points.append((x, y))
        
        # Bottom half (min values, reversed)
        for i in range(len(visible_peaks) - 1, -1, -1):
            min_val, max_val = visible_peaks[i]
            x = i * pixels_per_peak
            y = mid_y - (min_val * amplitude_scale)
            points.append((x, y))
        
        if len(points) > 2:
            self.create_polygon(points, fill=self.waveform_fill, outline=self.waveform_color, width=1, tags='waveform')
    
    def _draw_trim_regions(self, width: int, height: int):
        """Draw darkened regions for trimmed areas."""
        if not self.clip:
            return
        
        total_duration = self._get_total_duration()
        if total_duration <= 0:
            return
        
        # Start trim region
        start_trim_width = (self.clip.start_offset / total_duration) * width
        if start_trim_width > 0:
            self.create_rectangle(
                0, 0, start_trim_width, height,
                fill='#000000', stipple='gray50', outline=self.trim_color, width=2, tags='trim_start'
            )
            self.create_text(
                start_trim_width / 2, height - 10,
                text='TRIMMED', fill=self.trim_color, font=('Segoe UI', 8, 'bold'), tags='trim_start_text'
            )
        
        # End trim region
        end_trim_start = width * (1 - (self.clip.end_offset / total_duration))
        end_trim_width = width - end_trim_start
        if end_trim_width > 0:
            self.create_rectangle(
                end_trim_start, 0, width, height,
                fill='#000000', stipple='gray50', outline=self.trim_color, width=2, tags='trim_end'
            )
            self.create_text(
                end_trim_start + end_trim_width / 2, height - 10,
                text='TRIMMED', fill=self.trim_color, font=('Segoe UI', 8, 'bold'), tags='trim_end_text'
            )
    
    def _draw_fade_regions(self, width: int, height: int):
        """Draw fade in/out indicator regions."""
        if not self.clip:
            return
        
        duration = self.clip.length_seconds
        if duration <= 0:
            return
        
        # Fade in
        if self.clip.fade_in > 0:
            fade_in_width = (self.clip.fade_in / duration) * width
            fade_in_width = min(fade_in_width, width / 2)
            
            # Draw gradient-like effect with multiple rectangles
            steps = 10
            for i in range(steps):
                alpha = int(255 * (i / steps))
                x1 = (i / steps) * fade_in_width
                x2 = ((i + 1) / steps) * fade_in_width
                opacity = f'#{alpha:02x}{"ff00" if self.dragging == "fade_in" else "bb00"}'
                self.create_rectangle(
                    x1, 0, x2, height,
                    fill='', outline=self.fade_color, width=0, tags='fade_in'
                )
            
            # Fade in line
            self.create_line(
                0, height, fade_in_width, 0,
                fill=self.fade_color, width=2, dash=(4, 2), tags='fade_in_line'
            )
            
            self.create_text(
                fade_in_width / 2, 15,
                text=f'Fade In\n{self.clip.fade_in:.2f}s', fill=self.fade_color,
                font=('Segoe UI', 8, 'bold'), tags='fade_in_text'
            )
        
        # Fade out
        if self.clip.fade_out > 0:
            fade_out_width = (self.clip.fade_out / duration) * width
            fade_out_width = min(fade_out_width, width / 2)
            fade_out_start = width - fade_out_width
            
            # Fade out line
            self.create_line(
                fade_out_start, 0, width, height,
                fill=self.fade_color, width=2, dash=(4, 2), tags='fade_out_line'
            )
            
            self.create_text(
                fade_out_start + fade_out_width / 2, 15,
                text=f'Fade Out\n{self.clip.fade_out:.2f}s', fill=self.fade_color,
                font=('Segoe UI', 8, 'bold'), tags='fade_out_text'
            )
    
    def _draw_handles(self, width: int, height: int):
        """Draw interactive handles for trim and fade controls."""
        if not self.clip:
            return
        
        total_duration = self._get_total_duration()
        duration = self.clip.length_seconds
        
        if total_duration <= 0:
            return
        
        handle_width = 8
        handle_height = height
        
        # Start trim handle
        start_x = (self.clip.start_offset / total_duration) * width
        self._draw_handle(start_x, 0, handle_width, handle_height, 'start', 'S')
        
        # End trim handle
        end_x = width * (1 - (self.clip.end_offset / total_duration))
        self._draw_handle(end_x, 0, handle_width, handle_height, 'end', 'E')
        
        # Fade in handle (only if fade_in > 0 or being dragged)
        if self.clip.fade_in > 0 or self.dragging == 'fade_in':
            fade_in_x = start_x + (self.clip.fade_in / duration) * (end_x - start_x)
            self._draw_handle(fade_in_x, 0, handle_width, handle_height, 'fade_in', 'FI', self.fade_color)
        
        # Fade out handle
        if self.clip.fade_out > 0 or self.dragging == 'fade_out':
            fade_out_x = end_x - (self.clip.fade_out / duration) * (end_x - start_x)
            self._draw_handle(fade_out_x, 0, handle_width, handle_height, 'fade_out', 'FO', self.fade_color)
    
    def _draw_handle(self, x: float, y: float, width: int, height: int, tag: str, label: str, color: Optional[str] = None):
        """Draw a single draggable handle."""
        color = color or self.handle_color
        
        # Handle rectangle
        self.create_rectangle(
            x - width / 2, y, x + width / 2, height,
            fill=color, outline='white', width=1, tags=(tag, 'handle')
        )
        
        # Label
        self.create_text(
            x, height / 2,
            text=label, fill='white', font=('Segoe UI', 7, 'bold'), tags=(tag, 'handle_label')
        )
    
    def _draw_time_markers(self, width: int, height: int):
        """Draw time scale markers."""
        duration = self._get_total_duration()
        if duration <= 0:
            return
        
        # Draw time markers every second or appropriate interval
        interval = self._get_time_interval(duration)
        num_markers = int(duration / interval) + 1
        
        for i in range(num_markers):
            time = i * interval
            x = (time / duration) * width
            
            # Tick mark
            self.create_line(x, height - 20, x, height, fill=self.text_color, width=1, tags='time_marker')
            
            # Time label
            self.create_text(
                x, height - 10,
                text=f'{time:.1f}s', fill=self.text_color, font=('Segoe UI', 7), tags='time_label'
            )
    
    def _get_time_interval(self, duration: float) -> float:
        """Calculate appropriate time interval for markers."""
        if duration <= 2:
            return 0.5
        elif duration <= 10:
            return 1.0
        elif duration <= 30:
            return 5.0
        else:
            return 10.0
    
    def _get_total_duration(self) -> float:
        """Get total duration including trimmed parts."""
        if not self.clip or self.clip.sample_rate <= 0:
            return 0.0
        return len(self.clip.buffer) / float(self.clip.sample_rate)
    
    def _on_resize(self, event):
        """Handle canvas resize."""
        self._update_peaks()
    
    def _on_click(self, event):
        """Handle mouse click to start dragging."""
        width = self.winfo_width()
        total_duration = self._get_total_duration()
        
        if total_duration <= 0:
            return
        
        # Check if clicking on a handle
        handle_tolerance = 10
        
        # Check trim handles
        start_x = (self.clip.start_offset / total_duration) * width
        end_x = width * (1 - (self.clip.end_offset / total_duration))
        
        if abs(event.x - start_x) < handle_tolerance:
            self.dragging = 'start'
            self.drag_start_x = event.x
            self.drag_start_value = self.clip.start_offset
            self.config(cursor='sb_h_double_arrow')
            return
        
        if abs(event.x - end_x) < handle_tolerance:
            self.dragging = 'end'
            self.drag_start_x = event.x
            self.drag_start_value = self.clip.end_offset
            self.config(cursor='sb_h_double_arrow')
            return
        
        # Check fade handles
        duration = self.clip.length_seconds
        if duration > 0:
            fade_in_x = start_x + (self.clip.fade_in / duration) * (end_x - start_x)
            fade_out_x = end_x - (self.clip.fade_out / duration) * (end_x - start_x)
            
            if abs(event.x - fade_in_x) < handle_tolerance and self.clip.fade_in > 0:
                self.dragging = 'fade_in'
                self.drag_start_x = event.x
                self.drag_start_value = self.clip.fade_in
                self.config(cursor='sb_h_double_arrow')
                return
            
            if abs(event.x - fade_out_x) < handle_tolerance and self.clip.fade_out > 0:
                self.dragging = 'fade_out'
                self.drag_start_x = event.x
                self.drag_start_value = self.clip.fade_out
                self.config(cursor='sb_h_double_arrow')
                return
    
    def _on_drag(self, event):
        """Handle dragging of handles."""
        if not self.dragging:
            return
        
        width = self.winfo_width()
        total_duration = self._get_total_duration()
        
        if total_duration <= 0:
            return
        
        dx_pixels = event.x - self.drag_start_x
        dx_seconds = (dx_pixels / width) * total_duration
        
        if self.dragging == 'start':
            new_offset = max(0.0, min(self.drag_start_value + dx_seconds, total_duration - self.clip.end_offset - 0.1))
            self.clip.start_offset = new_offset
        
        elif self.dragging == 'end':
            new_offset = max(0.0, min(self.drag_start_value - dx_seconds, total_duration - self.clip.start_offset - 0.1))
            self.clip.end_offset = new_offset
        
        elif self.dragging == 'fade_in':
            duration = self.clip.length_seconds
            new_fade = max(0.0, min(self.drag_start_value + dx_seconds, duration / 2))
            self.clip.fade_in = new_fade
        
        elif self.dragging == 'fade_out':
            duration = self.clip.length_seconds
            new_fade = max(0.0, min(self.drag_start_value - dx_seconds, duration / 2))
            self.clip.fade_out = new_fade
        
        self.redraw()
        
        if self.on_change:
            self.on_change()
    
    def _on_release(self, event):
        """Handle mouse release."""
        if self.dragging:
            self.dragging = None
            self.config(cursor='')
            if self.on_change:
                self.on_change()
    
    def _on_scroll(self, event):
        """Handle mouse wheel for zoom."""
        # Ctrl+Scroll for zoom
        if event.state & 0x0004:  # Ctrl key
            zoom_factor = 1.1 if event.delta > 0 else 0.9
            self.zoom = max(0.5, min(self.zoom * zoom_factor, 10.0))
            self._update_peaks()
    
    def _on_motion(self, event):
        """Handle mouse motion for cursor changes."""
        if self.dragging:
            return
        
        width = self.winfo_width()
        total_duration = self._get_total_duration()
        
        if total_duration <= 0:
            return
        
        handle_tolerance = 10
        
        # Check if hovering over handles
        start_x = (self.clip.start_offset / total_duration) * width
        end_x = width * (1 - (self.clip.end_offset / total_duration))
        
        duration = self.clip.length_seconds
        fade_in_x = start_x + (self.clip.fade_in / duration) * (end_x - start_x) if duration > 0 else 0
        fade_out_x = end_x - (self.clip.fade_out / duration) * (end_x - start_x) if duration > 0 else 0
        
        if (abs(event.x - start_x) < handle_tolerance or 
            abs(event.x - end_x) < handle_tolerance or
            (abs(event.x - fade_in_x) < handle_tolerance and self.clip.fade_in > 0) or
            (abs(event.x - fade_out_x) < handle_tolerance and self.clip.fade_out > 0)):
            self.config(cursor='sb_h_double_arrow')
        else:
            self.config(cursor='')
