"""Timeline canvas management for visual timeline rendering and clip interaction."""

try:
    import tkinter as tk
except Exception:  # pragma: no cover
    tk = None


class TimelineCanvas:
    """Manages the timeline canvas, rendering, and clip interactions."""

    def __init__(self, parent, project=None, mixer=None, timeline=None, player=None):
        self.project = project
        self.mixer = mixer
        self.timeline = timeline
        self.player = player
        
        # Canvas state
        self.canvas = None
        self.scroll = None
        self.cursor_id = None
        
        # Display settings
        self.px_per_sec = 200  # pixels per second
        self.track_height = 60
        self.left_margin = 60
        self.ruler_height = 32
        
        # Clip interaction state
        self.selected_clip = None  # (track_index, clip_object) - for single selection compatibility
        self.selected_clips = []  # [(track_index, clip_object), ...] - for multiple selection
        self.drag_data = None  # {"clip": clip, "track": idx, "start_x": x, "start_time": t}
        self.resize_data = None  # {"clip": clip, "track": idx, "edge": "left"|"right", ...}
        self.clip_canvas_ids = {}  # {canvas_id: (track_idx, clip_obj)}
        
        # Clipboard for copy/paste
        self.clipboard = []  # [(track_index, clip_data), ...]
        
        # Paste cursor position (where to paste clips)
        self.paste_position = 0.0  # Time in seconds where clips will be pasted
        self.paste_cursor_visible = False  # Show visual indicator
        
        # Grid state
        self.snap_enabled = False
        self.grid_division = 0.25  # quarter notes by default
        
        # Loop selection
        self.loop_selection_start = None
        
        # Loop marker dragging
        self.dragging_loop_marker = None  # "start" or "end"
        
        # Box selection (rectangular selection)
        self.box_selection_start = None  # (x, y) start point of box selection
        self.box_selection_rect = None  # Canvas rectangle ID for visual feedback
        
        self._build_canvas(parent)

    def _build_canvas(self, parent):
        """Build the timeline canvas with scrollbars."""
        if parent is None or tk is None:
            return
            
        frame = tk.Frame(parent, bg="#0d0d0d")
        frame.pack(fill="both", expand=True)
        
        self.canvas = tk.Canvas(
            frame,
            bg="#0d0d0d",
            highlightthickness=0,
            borderwidth=0
        )
        
        # Scrollbars
        try:
            from tkinter import ttk
            hscroll = ttk.Scrollbar(frame, orient="horizontal", command=self.canvas.xview)
            vscroll = ttk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
        except Exception:
            hscroll = tk.Scrollbar(frame, orient="horizontal", command=self.canvas.xview)
            vscroll = tk.Scrollbar(frame, orient="vertical", command=self.canvas.yview)
            
        self.canvas.configure(xscrollcommand=hscroll.set, yscrollcommand=vscroll.set)
        
        self.canvas.grid(row=0, column=0, sticky="nsew")
        hscroll.grid(row=1, column=0, sticky="ew")
        vscroll.grid(row=0, column=1, sticky="ns")
        
        frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        
        self.scroll = hscroll
        
        # Mouse bindings
        self._bind_mouse_events()

    def _bind_mouse_events(self):
        """Bind mouse events for clip interaction."""
        if self.canvas is None:
            return
            
        # Mouse wheel for horizontal scroll with Shift
        def on_wheel(event):
            try:
                if event.state & 0x0001:  # Shift pressed
                    delta = (event.delta or -event.num) / 120.0
                    self.canvas.xview_scroll(int(-delta * 3), 'units')
            except Exception:
                pass
                
        self.canvas.bind('<MouseWheel>', on_wheel)
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.canvas.bind('<Button-3>', self.on_right_click)
        self.canvas.bind('<Motion>', self.on_motion)

    def compute_width(self):
        """Calculate timeline width based on content."""
        max_end = 5.0
        try:
            if self.timeline is not None:
                for _, clip in self.timeline.all_placements():
                    if getattr(clip, 'end_time', None) is not None:
                        if clip.end_time > max_end:
                            max_end = clip.end_time
        except Exception:
            pass
        width = int(self.left_margin + max_end * self.px_per_sec + 40)
        return max(width, 800)

    def compute_height(self):
        """Calculate timeline height based on track count."""
        tracks_count = max(1, len(getattr(self.mixer, 'tracks', [])))
        return self.ruler_height + (self.track_height * tracks_count) + 20

    def redraw(self):
        """Redraw the entire timeline."""
        if self.canvas is None:
            return
            
        self.canvas.delete("all")
        
        width = self.compute_width()
        height = self.compute_height()
        
        self.canvas.config(scrollregion=(0, 0, width, height))
        
        self._draw_ruler(width)
        self._draw_grid(width, height)
        self._draw_track_lanes(width)
        self._draw_clips()
        self._draw_loop_markers(height)
        self._draw_cursor(height)

    def _draw_ruler(self, width):
        """Draw the time ruler at the top."""
        if self.canvas is None:
            return
            
        # Ruler background
        self.canvas.create_rectangle(
            0, 0, width, self.ruler_height,
            fill="#1a1a1a", outline=""
        )

    def _draw_grid(self, width, height):
        """Draw the musical grid or time grid."""
        if self.canvas is None:
            return
            
        if self.project is not None:
            self._draw_musical_grid(width, height)
        else:
            self._draw_time_grid(width, height)

    def _draw_musical_grid(self, width, height):
        """Draw musical grid with bars and beats."""
        bar_duration = self.project.get_bar_duration()
        beat_duration = self.project.get_beat_duration()
        
        max_time = width / self.px_per_sec
        
        # First pass: Draw all bar lines explicitly
        bar_num = 0
        while True:
            bar_time = bar_num * bar_duration
            if bar_time > max_time:
                break
            
            x = self.left_margin + bar_time * self.px_per_sec
            
            # Bar line (thick, bright blue)
            self.canvas.create_line(x, self.ruler_height, x, height, fill="#2b6cb0", width=3)
            self.canvas.create_text(
                x + 4, 8, anchor="nw", text=f"{bar_num + 1}",
                fill="#63b3ed", font=("Consolas", 9, "bold")
            )
            bar_num += 1
        
        # Second pass: Draw beat and subdivision lines
        grid_time = bar_duration * self.grid_division
        t = grid_time  # Start from first subdivision (skip t=0 already drawn as bar)
        
        while t < max_time:
            x = self.left_margin + t * self.px_per_sec
            
            # Check if this is close to a bar line (skip if already drawn)
            is_bar_line = abs(t % bar_duration) < 0.001
            if is_bar_line:
                t += grid_time
                continue
            
            # Determine line type with tolerance
            is_beat = abs(t % beat_duration) < 0.001
            is_half_beat = abs(t % (beat_duration / 2)) < 0.001
            is_quarter_beat = abs(t % (beat_duration / 4)) < 0.001
            
            if is_beat:
                self.canvas.create_line(x, self.ruler_height, x, height, fill="#2563eb", width=2)
            elif is_half_beat:
                self.canvas.create_line(x, self.ruler_height, x, height, fill="#3b82f6", width=1)
            elif is_quarter_beat:
                self.canvas.create_line(x, self.ruler_height, x, height, fill="#60a5fa", width=1, dash=(2, 2))
            else:
                self.canvas.create_line(x, self.ruler_height, x, height, fill="#93c5fd", width=1, dash=(1, 3))
            
            t += grid_time

    def _draw_time_grid(self, width, height):
        """Draw simple time-based grid (seconds)."""
        total_secs = int(width / self.px_per_sec) + 1
        
        for sec in range(0, total_secs):
            x = self.left_margin + sec * self.px_per_sec
            
            # Major gridline
            self.canvas.create_line(x, self.ruler_height, x, height, fill="#1f1f1f", width=1)
            
            # Time label
            self.canvas.create_text(
                x + 4, 8, anchor="nw", text=f"{sec:02d}s",
                fill="#888888", font=("Consolas", 8)
            )
            
            # Minor ticks (quarters)
            for q in range(1, 4):
                mx = x + q * (self.px_per_sec / 4.0)
                self.canvas.create_line(mx, self.ruler_height - 8, mx, height, fill="#151515", width=1)

    def _draw_track_lanes(self, width):
        """Draw track lanes with labels."""
        if self.canvas is None or self.mixer is None:
            return
            
        tracks_count = len(self.mixer.tracks)
        
        for i in range(tracks_count):
            y0 = self.ruler_height + i * self.track_height
            y1 = y0 + self.track_height
            
            # Alternating background
            bg_color = "#0d0d0d" if i % 2 == 0 else "#111111"
            self.canvas.create_rectangle(
                self.left_margin, y0, width, y1,
                fill=bg_color, outline=""
            )
            
            # Track separator
            self.canvas.create_line(
                self.left_margin, y1, width, y1,
                fill="#252525", width=1
            )
            
            # Track label
            label = self.mixer.tracks[i].get("name", f"Track {i+1}")
            track_color = self.mixer.tracks[i].get("color", "#3b82f6")
            
            self.canvas.create_rectangle(0, y0, self.left_margin, y1, fill="#1a1a1a", outline="")
            self.canvas.create_rectangle(2, y0 + 4, 6, y1 - 4, fill=track_color, outline="")
            self.canvas.create_text(
                10, y0 + self.track_height // 2, anchor="w",
                text=f"{i+1}. {label}", fill=track_color,
                font=("Segoe UI", 9, "bold")
            )

    def _draw_clips(self):
        """Draw all clips on the timeline."""
        if self.canvas is None or self.timeline is None:
            return
            
        self.clip_canvas_ids = {}
        
        try:
            for ti, clip in self.timeline.all_placements():
                self._draw_clip(ti, clip)
        except Exception:
            pass

    def _draw_clip(self, track_idx, clip):
        """Draw a single clip."""
        y0 = self.ruler_height + track_idx * self.track_height
        y1 = y0 + self.track_height
        x0 = self.left_margin + int(clip.start_time * self.px_per_sec)
        x1 = self.left_margin + int(clip.end_time * self.px_per_sec)
        
        # Get track color
        clip_color = "#3b82f6"
        clip_border = "#60a5fa"
        
        try:
            if self.mixer is not None and track_idx < len(self.mixer.tracks):
                clip_color = self.mixer.tracks[track_idx].get("color", "#3b82f6")
                clip_border = self._lighten_color(clip_color, 1.3)
        except Exception:
            pass
        
        # Check if clip is in multi-selection
        is_selected = any(c == clip for _, c in self.selected_clips)
        
        # Selection highlight
        border_width = 3 if is_selected else 2
        if is_selected:
            clip_border = "#ffffff"
        
        # Clip rectangle
        clip_id = self.canvas.create_rectangle(
            x0, y0 + 8, x1, y1 - 8,
            fill=clip_color, outline=clip_border, width=border_width
        )
        
        self.clip_canvas_ids[clip_id] = (track_idx, clip)
        
        # Draw waveform
        self._draw_waveform(clip, x0, x1, y0, y1)
        
        # Clip name
        clip_name = getattr(clip, 'name', 'clip')
        self.canvas.create_text(
            x0 + 6, y0 + 14, anchor="nw", text=clip_name,
            fill="#ffffff", font=("Segoe UI", 9, "bold")
        )

    def _draw_waveform(self, clip, x0, x1, y0, y1):
        """Draw waveform visualization in clip."""
        try:
            clip_width = x1 - x0
            if clip_width > 20:
                num_points = max(10, int(clip_width / 2))
                peaks = clip.get_peaks(num_points)
                
                wave_y_center = (y0 + y1) / 2
                wave_h = (y1 - y0 - 20) / 2
                
                for i, (min_val, max_val) in enumerate(peaks):
                    px = x0 + (i * clip_width / len(peaks))
                    py_min = wave_y_center - (min_val * wave_h)
                    py_max = wave_y_center - (max_val * wave_h)
                    
                    self.canvas.create_line(
                        px, py_min, px, py_max,
                        fill="#000000", width=1
                    )
        except Exception:
            pass

    def _draw_loop_markers(self, height):
        """Draw loop region markers if loop is enabled."""
        if self.canvas is None or self.player is None:
            return
            
        try:
            loop_enabled, loop_start, loop_end = self.player.get_loop()
            if not loop_enabled:
                return
                
            loop_x_start = self.left_margin + loop_start * self.px_per_sec
            loop_x_end = self.left_margin + loop_end * self.px_per_sec
            
            # Loop region highlight
            self.canvas.create_rectangle(
                loop_x_start, self.ruler_height,
                loop_x_end, height,
                fill="#10b981", stipple="gray25", outline=""
            )
            
            # Loop start marker
            self._draw_loop_marker(loop_x_start, height, "[")
            
            # Loop end marker
            self._draw_loop_marker(loop_x_end, height, "]", is_end=True)
        except Exception:
            pass

    def _draw_loop_marker(self, x, height, label, is_end=False):
        """Draw a single loop marker."""
        # Marker line
        line_id = self.canvas.create_line(
            x, self.ruler_height, x, height,
            fill="#10b981", width=3, tags=f"loop_marker_{label.lower()}"
        )
        
        # Marker flag (handle draggabile)
        if is_end:
            handle_id = self.canvas.create_polygon(
                x, self.ruler_height,
                x - 12, self.ruler_height + 6,
                x, self.ruler_height + 12,
                fill="#10b981", outline="#065f46", width=2,
                tags=f"loop_marker_{label.lower()}"
            )
            text_id = self.canvas.create_text(
                x - 4, self.ruler_height + 6, text=label,
                fill="#ffffff", font=("Segoe UI", 10, "bold"),
                tags=f"loop_marker_{label.lower()}"
            )
        else:
            handle_id = self.canvas.create_polygon(
                x, self.ruler_height,
                x + 12, self.ruler_height + 6,
                x, self.ruler_height + 12,
                fill="#10b981", outline="#065f46", width=2,
                tags=f"loop_marker_{label.lower()}"
            )
            text_id = self.canvas.create_text(
                x + 4, self.ruler_height + 6, text=label,
                fill="#ffffff", font=("Segoe UI", 10, "bold"),
                tags=f"loop_marker_{label.lower()}"
            )
        
        # Aggiungi una zona cliccabile più grande per facilitare il drag
        hitbox_id = self.canvas.create_rectangle(
            x - 15, self.ruler_height, x + 15, self.ruler_height + 30,
            fill="", outline="", tags=f"loop_marker_{label.lower()}"
        )

    def _draw_cursor(self, height):
        """Draw the playback cursor."""
        if self.canvas is None:
            return
            
        cur = 0.0
        try:
            cur = float(getattr(self.player, "_current_time", 0.0))
        except Exception:
            pass
        
        cursor_x = self.left_margin + cur * self.px_per_sec
        
        # Cursor line
        self.cursor_id = self.canvas.create_line(
            cursor_x, 0, cursor_x, height,
            fill="#ef4444", width=3
        )
        
        # Cursor head (triangle)
        self.canvas.create_polygon(
            cursor_x - 6, 0,
            cursor_x + 6, 0,
            cursor_x, 10,
            fill="#ef4444", outline=""
        )
        
        # Draw paste cursor if visible
        if self.paste_cursor_visible and self.clipboard:
            self._draw_paste_cursor(height)

    def _draw_paste_cursor(self, height):
        """Draw the paste position cursor."""
        if self.canvas is None:
            return
        
        paste_x = self.left_margin + self.paste_position * self.px_per_sec
        
        # Paste cursor line (dashed, different color)
        self.canvas.create_line(
            paste_x, self.ruler_height, paste_x, height,
            fill="#10b981", width=2, dash=(5, 3), tags="paste_cursor"
        )
        
        # Paste cursor indicator (triangle pointing down)
        self.canvas.create_polygon(
            paste_x - 8, self.ruler_height,
            paste_x + 8, self.ruler_height,
            paste_x, self.ruler_height + 12,
            fill="#10b981", outline="#065f46", width=2, tags="paste_cursor"
        )
        
        # Time label
        time_str = f"{self.paste_position:.2f}s"
        self.canvas.create_text(
            paste_x, self.ruler_height + 22,
            text=time_str,
            fill="#10b981",
            font=("Segoe UI", 8, "bold"),
            tags="paste_cursor"
        )

    def update_cursor(self, current_time):
        """Update cursor position."""
        if self.canvas is None or self.cursor_id is None:
            return
            
        x = self.left_margin + current_time * self.px_per_sec
        
        try:
            height = self.compute_height()
            self.canvas.coords(self.cursor_id, x, 0, x, height)
            
            # Auto-scroll to keep cursor visible
            vis_left = self.canvas.canvasx(0)
            vis_right = self.canvas.canvasx(self.canvas.winfo_width())
            
            if x < vis_left or x > vis_right:
                self.canvas.xview_moveto(
                    max(0.0, (x - self.left_margin) / max(1, self.compute_width()))
                )
        except Exception:
            pass

    def zoom(self, factor):
        """Zoom timeline by factor."""
        self.px_per_sec = max(40, min(800, int(self.px_per_sec * factor)))
        self.redraw()
        return self.px_per_sec / 200.0  # Return zoom value

    def zoom_reset(self):
        """Reset zoom to default."""
        self.px_per_sec = 200
        self.redraw()

    def set_snap(self, enabled):
        """Enable/disable snap to grid."""
        self.snap_enabled = enabled
        self.redraw()

    def set_grid_division(self, division):
        """Set grid division (1.0 = bar, 0.25 = quarter, etc.)."""
        self.grid_division = division
        self.redraw()

    def snap_time(self, time):
        """Snap time to grid if enabled."""
        if not self.snap_enabled or self.project is None:
            return time
        return self.project.snap_to_grid(time, self.grid_division)

    # Mouse event handlers
    def on_click(self, event):
        """Handle mouse click."""
        if self.canvas is None:
            return
            
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Check if clicking on loop markers
        if self._check_loop_marker_click(x, y):
            return
        
        # Check for loop region selection with Shift
        if event.state & 0x0001:  # Shift key
            time = (x - self.left_margin) / self.px_per_sec
            self.loop_selection_start = max(0, time)
            return
        
        # Check for Ctrl key (multi-selection)
        ctrl_pressed = event.state & 0x0004  # Ctrl key
        
        # Find clicked clip
        clicked_clip = self._find_clip_at(x, y)
        
        if clicked_clip:
            track_idx, clip = clicked_clip
            clip_x0 = self.left_margin + clip.start_time * self.px_per_sec
            clip_x1 = self.left_margin + clip.end_time * self.px_per_sec
            
            # Check for edge resize (only if single clip selected)
            if not ctrl_pressed and abs(x - clip_x0) < 8:
                self.resize_data = {
                    "clip": clip, "track": track_idx,
                    "edge": "left", "orig_start": clip.start_time
                }
                self.select_clip(track_idx, clip)
            elif not ctrl_pressed and abs(x - clip_x1) < 8:
                self.resize_data = {
                    "clip": clip, "track": track_idx,
                    "edge": "right", "orig_end": clip.end_time
                }
                self.select_clip(track_idx, clip)
            else:
                # Multi-selection or single selection
                if ctrl_pressed:
                    self.toggle_clip_selection(track_idx, clip)
                else:
                    # Start drag if not multi-selecting
                    self.drag_data = {
                        "clip": clip, "track": track_idx,
                        "start_x": x, "start_time": clip.start_time
                    }
                    self.select_clip(track_idx, clip)
        else:
            # Clicked on empty area
            if not ctrl_pressed:
                self.clear_selection()
            
            # Start box selection if in track area (not in ruler)
            if y > self.ruler_height:
                self.box_selection_start = (x, y)
                # Don't set paste position during box selection start
            
            # Set paste position if clipboard has content (only if not starting box selection)
            elif self.clipboard:
                time = (x - self.left_margin) / self.px_per_sec
                self.paste_position = max(0, self.snap_time(time))
                self.paste_cursor_visible = True
                self.redraw()
                print(f"📍 Paste position set to {self.paste_position:.2f}s (click here or press Ctrl+V to paste)")
            elif not self.clipboard:
                # Hide paste cursor if clipboard is empty
                self.paste_cursor_visible = False
                self.redraw()

    def on_drag(self, event):
        """Handle mouse drag."""
        if self.canvas is None:
            return
            
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Drag loop marker
        if self.dragging_loop_marker is not None:
            self._handle_loop_marker_drag(x)
            return
        
        # Loop region selection with Shift
        if self.loop_selection_start is not None:
            # Disegna preview del loop durante il drag
            self.canvas.delete("loop_preview")
            
            end_time = (x - self.left_margin) / self.px_per_sec
            end_time = max(0, end_time)
            
            start_time = self.loop_selection_start
            
            # Visualizza l'area che sarà selezionata
            loop_x_start = self.left_margin + min(start_time, end_time) * self.px_per_sec
            loop_x_end = self.left_margin + max(start_time, end_time) * self.px_per_sec
            
            height = self.compute_height()
            self.canvas.create_rectangle(
                loop_x_start, self.ruler_height,
                loop_x_end, height,
                fill="#10b981", stipple="gray25", outline="#10b981",
                width=2, tags="loop_preview"
            )
            return
        
        # Box selection (rectangular clip selection)
        if self.box_selection_start is not None:
            self._handle_box_selection_drag(x, y)
            return
        
        if self.resize_data:
            self._handle_resize(x)
        elif self.drag_data:
            self._handle_drag(x, y)

    def on_release(self, event):
        """Handle mouse release."""
        # Release loop marker drag
        if self.dragging_loop_marker is not None:
            self.dragging_loop_marker = None
            self.canvas.config(cursor="")
            return
        
        # Check loop region selection
        if self.loop_selection_start is not None:
            self.canvas.delete("loop_preview")
            
            x = self.canvas.canvasx(event.x)
            end_time = (x - self.left_margin) / self.px_per_sec
            end_time = max(0, end_time)
            
            start = self.snap_time(min(self.loop_selection_start, end_time))
            end = self.snap_time(max(self.loop_selection_start, end_time))
            
            # Minimo di 0.1 secondi per il loop
            if abs(end - start) > 0.1 and self.player is not None:
                self.player.set_loop(True, start, end)
                self.redraw()
                print(f"🔁 Loop region set: {start:.3f}s - {end:.3f}s")
            else:
                print("⚠ Loop region too small (min 0.1s required)")
            
            self.loop_selection_start = None
            return
        
        # Box selection release
        if self.box_selection_start is not None:
            self._complete_box_selection()
            return
        
        self.drag_data = None
        self.resize_data = None

    def on_motion(self, event):
        """Handle mouse motion for cursor changes."""
        if self.canvas is None or self.drag_data or self.resize_data or self.dragging_loop_marker:
            return
            
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Check if hovering over loop markers
        if self._is_over_loop_marker(x, y):
            self.canvas.config(cursor="sb_h_double_arrow")
            return
        
        clicked_clip = self._find_clip_at(x, y)
        
        if clicked_clip:
            track_idx, clip = clicked_clip
            clip_x0 = self.left_margin + clip.start_time * self.px_per_sec
            clip_x1 = self.left_margin + clip.end_time * self.px_per_sec
            
            if abs(x - clip_x0) < 8 or abs(x - clip_x1) < 8:
                self.canvas.config(cursor="sb_h_double_arrow")
            else:
                self.canvas.config(cursor="hand2")
        else:
            self.canvas.config(cursor="")

    def on_right_click(self, event):
        """Handle right-click context menu."""
        # This will be handled by MainWindow for now
        pass

    def _find_clip_at(self, x, y):
        """Find clip at given canvas coordinates."""
        if self.canvas is None:
            return None
            
        items = self.canvas.find_overlapping(x, y, x, y)
        
        for item in items:
            if item in self.clip_canvas_ids:
                return self.clip_canvas_ids[item]
        
        return None

    def _handle_resize(self, x):
        """Handle clip resize."""
        clip = self.resize_data["clip"]
        new_time = (x - self.left_margin) / self.px_per_sec
        new_time = max(0, new_time)
        new_time = self.snap_time(new_time)
        
        if self.resize_data["edge"] == "left":
            if new_time < clip.end_time - 0.1:
                clip.start_time = new_time
        else:
            if new_time > clip.start_time + 0.1:
                clip.duration = new_time - clip.start_time
        
        self.redraw()

    def _handle_drag(self, x, y):
        """Handle clip drag."""
        clip = self.drag_data["clip"]
        delta_x = x - self.drag_data["start_x"]
        delta_time = delta_x / self.px_per_sec
        new_start = self.drag_data["start_time"] + delta_time
        new_start = max(0, new_start)
        new_start = self.snap_time(new_start)
        
        clip.start_time = new_start
        
        # Check track change
        track_idx = int((y - self.ruler_height) / self.track_height)
        track_idx = max(0, min(track_idx, len(self.mixer.tracks) - 1))
        
        if track_idx != self.drag_data["track"]:
            old_track = self.drag_data["track"]
            self.timeline.remove_clip(old_track, clip)
            self.timeline.add_clip(track_idx, clip)
            self.drag_data["track"] = track_idx
            self.selected_clip = (track_idx, clip)
        
        self.redraw()

    def _handle_box_selection_drag(self, x, y):
        """Handle dragging for box selection."""
        if self.box_selection_start is None:
            return
        
        start_x, start_y = self.box_selection_start
        
        # Calculate rectangle bounds
        x1 = min(start_x, x)
        y1 = min(start_y, y)
        x2 = max(start_x, x)
        y2 = max(start_y, y)
        
        # Delete previous selection rectangle
        if self.box_selection_rect is not None:
            self.canvas.delete(self.box_selection_rect)
        
        # Draw selection rectangle
        self.box_selection_rect = self.canvas.create_rectangle(
            x1, y1, x2, y2,
            outline="#60a5fa", width=2, dash=(4, 4),
            fill="#3b82f6", stipple="gray25",
            tags="box_selection"
        )
    
    def _complete_box_selection(self):
        """Complete box selection and select all clips within the box."""
        if self.box_selection_start is None:
            return
        
        # Get the current mouse position from the box rectangle
        if self.box_selection_rect is not None:
            coords = self.canvas.coords(self.box_selection_rect)
            if len(coords) == 4:
                x1, y1, x2, y2 = coords
                
                # Find all clips that intersect with the selection box
                selected = []
                
                if self.timeline is not None:
                    for track_idx, clip in self.timeline.all_placements():
                        clip_x1 = self.left_margin + clip.start_time * self.px_per_sec
                        clip_x2 = self.left_margin + clip.end_time * self.px_per_sec
                        clip_y1 = self.ruler_height + track_idx * self.track_height
                        clip_y2 = clip_y1 + self.track_height
                        
                        # Check if clip intersects with selection box
                        if (clip_x2 >= x1 and clip_x1 <= x2 and 
                            clip_y2 >= y1 and clip_y1 <= y2):
                            selected.append((track_idx, clip))
                
                # Update selection
                if selected:
                    self.selected_clips = selected
                    self.selected_clip = selected[0] if selected else None
                    print(f"📦 Selected {len(selected)} clip(s) with box selection")
            
            # Clean up
            self.canvas.delete(self.box_selection_rect)
            self.box_selection_rect = None
        
        self.box_selection_start = None
        self.redraw()

    def select_clip(self, track_idx, clip):
        """Select a single clip (clears previous selection)."""
        # Clear all previous selections
        self.selected_clips = []
        self.selected_clip = None
        
        if clip:
            self.selected_clips = [(track_idx, clip)]
            self.selected_clip = (track_idx, clip)
        
        self.redraw()

    def toggle_clip_selection(self, track_idx, clip):
        """Toggle clip selection (for multi-selection with Ctrl)."""
        # Check if already selected
        clip_tuple = (track_idx, clip)
        
        if clip_tuple in self.selected_clips:
            # Deselect
            self.selected_clips.remove(clip_tuple)
            if self.selected_clip == clip_tuple:
                self.selected_clip = self.selected_clips[0] if self.selected_clips else None
        else:
            # Add to selection
            self.selected_clips.append(clip_tuple)
            self.selected_clip = clip_tuple
        
        self.redraw()

    def clear_selection(self):
        """Clear all clip selections."""
        self.selected_clips = []
        self.selected_clip = None
        self.redraw()

    def get_selected_clip(self):
        """Get currently selected clip (for backward compatibility)."""
        return self.selected_clip
    
    def get_selected_clips(self):
        """Get all selected clips."""
        return self.selected_clips
    
    def copy_selected_clips(self):
        """Copy selected clips to clipboard."""
        if not self.selected_clips:
            return False
        
        # Store clip data in clipboard
        self.clipboard = []
        
        for track_idx, clip in self.selected_clips:
            clip_data = {
                'track_idx': track_idx,
                'name': clip.name,
                'buffer': clip.buffer,
                'sample_rate': clip.sample_rate,
                'start_time': clip.start_time,
                'duration': clip.duration,
                'color': clip.color,
                'file_path': clip.file_path,
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
        if self.player:
            self.paste_position = float(getattr(self.player, "_current_time", 0.0))
        else:
            self.paste_position = 0.0
        self.paste_cursor_visible = True
        self.redraw()
        
        print(f"📋 Copied {len(self.clipboard)} clip(s) to clipboard")
        print(f"📍 Paste position set to {self.paste_position:.2f}s (click on timeline to change, or press Ctrl+V to paste)")
        return True
    
    def paste_clips(self, at_time=None):
        """Paste clips from clipboard.
        
        Args:
            at_time: Optional time to paste at. If None, uses paste_position if set,
                    otherwise uses current playback time.
        """
        if not self.clipboard:
            return []
        
        from src.audio.clip import AudioClip
        
        # Determine paste position (priority: at_time > paste_position > current_time)
        if at_time is None:
            if self.paste_cursor_visible:
                at_time = self.paste_position
            else:
                at_time = float(getattr(self.player, "_current_time", 0.0)) if self.player else 0.0
        
        # Find the earliest clip in clipboard to calculate offset
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
            if self.timeline:
                self.timeline.add_clip(track_idx, new_clip)
                pasted_clips.append((track_idx, new_clip))
        
        # Select pasted clips
        self.selected_clips = pasted_clips
        self.selected_clip = pasted_clips[0] if pasted_clips else None
        
        # Hide paste cursor after pasting
        self.paste_cursor_visible = False
        
        self.redraw()
        print(f"📌 Pasted {len(pasted_clips)} clip(s) at {at_time:.3f}s")
        
        return pasted_clips

    @staticmethod
    def _lighten_color(hex_color, factor=1.3):
        """Lighten a hex color by a factor."""
        try:
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            r = min(255, int(r * factor))
            g = min(255, int(g * factor))
            b = min(255, int(b * factor))
            
            return f"#{r:02x}{g:02x}{b:02x}"
        except Exception:
            return "#60a5fa"

    def _check_loop_marker_click(self, x, y):
        """Check if click is on a loop marker and start dragging."""
        if self.player is None or y > self.ruler_height + 30:
            return False
        
        try:
            loop_enabled, loop_start, loop_end = self.player.get_loop()
            if not loop_enabled:
                return False
            
            loop_x_start = self.left_margin + loop_start * self.px_per_sec
            loop_x_end = self.left_margin + loop_end * self.px_per_sec
            
            # Check click on start marker (15px tolerance)
            if abs(x - loop_x_start) < 15:
                self.dragging_loop_marker = "start"
                self.canvas.config(cursor="sb_h_double_arrow")
                return True
            
            # Check click on end marker
            if abs(x - loop_x_end) < 15:
                self.dragging_loop_marker = "end"
                self.canvas.config(cursor="sb_h_double_arrow")
                return True
        except Exception:
            pass
        
        return False

    def _is_over_loop_marker(self, x, y):
        """Check if mouse is over a loop marker."""
        if self.player is None or y > self.ruler_height + 30:
            return False
        
        try:
            loop_enabled, loop_start, loop_end = self.player.get_loop()
            if not loop_enabled:
                return False
            
            loop_x_start = self.left_margin + loop_start * self.px_per_sec
            loop_x_end = self.left_margin + loop_end * self.px_per_sec
            
            return abs(x - loop_x_start) < 15 or abs(x - loop_x_end) < 15
        except Exception:
            return False

    def _handle_loop_marker_drag(self, x):
        """Handle dragging of loop markers."""
        if self.player is None:
            return
        
        new_time = (x - self.left_margin) / self.px_per_sec
        new_time = max(0, new_time)
        new_time = self.snap_time(new_time)
        
        try:
            loop_enabled, loop_start, loop_end = self.player.get_loop()
            
            if self.dragging_loop_marker == "start":
                # Dragging start marker
                if new_time < loop_end - 0.1:  # Minimum 0.1s loop
                    self.player.set_loop(True, new_time, loop_end)
                    self.redraw()
            elif self.dragging_loop_marker == "end":
                # Dragging end marker
                if new_time > loop_start + 0.1:  # Minimum 0.1s loop
                    self.player.set_loop(True, loop_start, new_time)
                    self.redraw()
        except Exception as e:
            print(f"Error dragging loop marker: {e}")
