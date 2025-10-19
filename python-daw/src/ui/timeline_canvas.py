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
        # Callback for notifying selection changes to parent (MainWindow)
        self.on_track_selected = None
        
        # Canvas state
        self.canvas = None  # Main timeline canvas (scrollable)
        self.controls_canvas = None  # Fixed controls canvas (left side)
        self.scroll = None
        self.cursor_id = None
        
        # Display settings
        self.px_per_sec = 200  # pixels per second
        self.track_height = 80  # Increased for inline controls
        self.left_margin = 280  # Width of controls area
        self.ruler_height = 32
        
        # Clip interaction state
        self.selected_clip = None  # (track_index, clip_object) - for single selection compatibility
        self.selected_clips = []  # [(track_index, clip_object), ...] - for multiple selection
        self.drag_data = None  # {"clip": clip, "track": idx, "start_x": x, "start_time": t}
        self.resize_data = None  # {"clip": clip, "track": idx, "edge": "left"|"right", ...}
        self.clip_canvas_ids = {}  # {canvas_id: (track_idx, clip_obj)}
        self.resize_handle_size = 12  # Larghezza zona resize ai bordi (più grande = più facile)
        
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
        
        # Track controls interaction state
        self.dragging_volume = None  # {"track": idx, "start_x": x, "start_vol": vol}
        self.dragging_pan = None  # {"track": idx, "start_x": x, "start_pan": pan}
        
        # Context menus (will be set by MainWindow)
        self.track_menu = None

        # Track selection state
        self.selected_track_idx = None

        self._build_canvas(parent)

    def _build_canvas(self, parent):
        """Build the timeline canvas with fixed controls on left and scrollable timeline on right."""
        if parent is None or tk is None:
            return
            
        # Main container
        container = tk.Frame(parent, bg="#0d0d0d")
        container.pack(fill="both", expand=True)
        
        # TOP ROW: Header row with controls ruler (left) and timeline ruler (right)
        header_frame = tk.Frame(container, bg="#0d0d0d", height=self.ruler_height)
        header_frame.pack(side="top", fill="x")
        header_frame.pack_propagate(False)
        
        # Left part of header (above controls)
        self.controls_ruler_canvas = tk.Canvas(
            header_frame,
            bg="#1a1a1a",
            highlightthickness=0,
            borderwidth=0,
            width=self.left_margin,
            height=self.ruler_height
        )
        self.controls_ruler_canvas.pack(side="left", fill="y")
        
        # Right part of header (timeline ruler - scrolls horizontally but NOT vertically)
        self.ruler_canvas = tk.Canvas(
            header_frame,
            bg="#1a1a1a",
            highlightthickness=0,
            borderwidth=0,
            height=self.ruler_height
        )
        self.ruler_canvas.pack(side="left", fill="both", expand=True)
        
        # BOTTOM ROW: Scrollable content
        content_frame = tk.Frame(container, bg="#0d0d0d")
        content_frame.pack(side="top", fill="both", expand=True)
        
        # LEFT: Fixed controls canvas (no horizontal scroll)
        self.controls_canvas = tk.Canvas(
            content_frame,
            bg="#1a1a1a",
            highlightthickness=0,
            borderwidth=0,
            width=self.left_margin
        )
        self.controls_canvas.pack(side="left", fill="y")
        
        # RIGHT: Scrollable timeline canvas
        timeline_frame = tk.Frame(content_frame, bg="#0d0d0d")
        timeline_frame.pack(side="left", fill="both", expand=True)
        
        self.canvas = tk.Canvas(
            timeline_frame,
            bg="#0d0d0d",
            highlightthickness=0,
            borderwidth=0
        )
        
        # Scrollbars
        try:
            from tkinter import ttk
            hscroll = ttk.Scrollbar(timeline_frame, orient="horizontal", command=self._on_xscroll)
            vscroll = ttk.Scrollbar(content_frame, orient="vertical", command=self._on_vscroll)
        except Exception:
            hscroll = tk.Scrollbar(timeline_frame, orient="horizontal", command=self._on_xscroll)
            vscroll = tk.Scrollbar(content_frame, orient="vertical", command=self._on_vscroll)
        
        # Configure canvas scrolling
        self.canvas.configure(
            xscrollcommand=self._on_xscroll_change,
            yscrollcommand=self._on_yscroll_change
        )
        
        # Layout
        self.canvas.grid(row=0, column=0, sticky="nsew")
        vscroll.pack(side="right", fill="y")
        
        timeline_frame.grid_rowconfigure(0, weight=1)
        timeline_frame.grid_columnconfigure(0, weight=1)
        
        self.scroll = hscroll
        self.hscroll = hscroll
        self.vscroll = vscroll
        self._hscroll_visible = False
        self._vscroll_visible = False
        
        # Mouse bindings
        self._bind_mouse_events()

        # Update scrollbar visibility on resize
        self.canvas.bind('<Configure>', lambda e: self._update_scrollbars())
        self.controls_canvas.bind('<Configure>', lambda e: self._sync_controls_height())
    
    def _on_xscroll(self, *args):
        """Handle horizontal scroll - sync timeline canvas and ruler canvas."""
        self.canvas.xview(*args)
        if hasattr(self, 'ruler_canvas'):
            self.ruler_canvas.xview(*args)
    
    def _on_vscroll(self, *args):
        """Handle vertical scroll - sync both canvases."""
        self.canvas.yview(*args)
        self.controls_canvas.yview(*args)
    
    def _sync_controls_height(self):
        """Sync controls canvas scrollregion with main canvas."""
        if self.controls_canvas and self.canvas:
            # Match the height of the controls canvas to the main canvas
            height = self.compute_height()
            self.controls_canvas.config(scrollregion=(0, 0, self.left_margin, height))

    def _bind_mouse_events(self):
        """Bind mouse events for clip interaction."""
        if self.canvas is None:
            return
            
        # Mouse wheel for scrolling (both canvases)
        def on_wheel(event):
            try:
                # Determine if scrolling is needed based on content
                bbox = self.canvas.bbox('all') or (0, 0, 0, 0)
                content_w = max(0, bbox[2] - bbox[0])
                content_h = max(0, bbox[3] - bbox[1])
                cw = max(1, self.canvas.winfo_width())
                ch = max(1, self.canvas.winfo_height())
                need_h = content_w > cw + 1
                need_v = content_h > ch + 1

                if event.state & 0x0001:  # Shift pressed - horizontal scroll
                    if not need_h:
                        return
                    delta = (event.delta or -event.num) / 120.0
                    self.canvas.xview_scroll(int(-delta * 3), 'units')
                else:  # Normal wheel - vertical scroll
                    if not need_v:
                        return
                    delta = (event.delta or -event.num) / 120.0
                    # Sync both canvases vertically
                    self.canvas.yview_scroll(int(-delta), 'units')
                    if self.controls_canvas:
                        self.controls_canvas.yview_scroll(int(-delta), 'units')
            except Exception:
                pass
        
        # Bind to both canvases
        self.canvas.bind('<MouseWheel>', on_wheel)
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.canvas.bind('<Button-3>', self.on_right_click)
        self.canvas.bind('<Motion>', self.on_motion)
        
        if self.controls_canvas:
            self.controls_canvas.bind('<MouseWheel>', on_wheel)
            self.controls_canvas.bind('<Button-1>', self.on_click)
            self.controls_canvas.bind('<B1-Motion>', self.on_drag)
            self.controls_canvas.bind('<ButtonRelease-1>', self.on_release)
            self.controls_canvas.bind('<Motion>', self.on_motion)
        
        # Bind ruler canvas for loop marker dragging
        if hasattr(self, 'ruler_canvas') and self.ruler_canvas:
            self.ruler_canvas.bind('<Button-1>', self.on_click)
            self.ruler_canvas.bind('<B1-Motion>', self.on_drag)
            self.ruler_canvas.bind('<ButtonRelease-1>', self.on_release)
            self.ruler_canvas.bind('<Motion>', self.on_motion)
    
    def set_vscroll_callback(self, callback):
        """Set callback to be called when vertical scroll position changes.
        
        Args:
            callback: Function to call with scroll position (first, last)
        """
        if self.canvas:
            def on_scroll(*args):
                callback(*args)
                self.vscroll.set(*args)
            self.canvas.configure(yscrollcommand=on_scroll)

    def compute_width(self):
        """Calculate timeline width based on content (without left margin)."""
        max_end = 5.0
        try:
            if self.timeline is not None:
                for _, clip in self.timeline.all_placements():
                    if getattr(clip, 'end_time', None) is not None:
                        if clip.end_time > max_end:
                            max_end = clip.end_time
        except Exception:
            pass
        # Don't include left_margin since controls are in separate canvas
        width = int(max_end * self.px_per_sec + 40)
        return max(width, 800)

    def compute_height(self):
        """Calculate timeline height based on track count."""
        tracks_count = max(1, len(getattr(self.mixer, 'tracks', [])))
        # Avoid artificial padding that can create unnecessary scroll space
        return self.ruler_height + (self.track_height * tracks_count)

    def redraw(self):
        """Redraw the entire timeline."""
        if self.canvas is None:
            return
        
        # Clear all canvases
        self.canvas.delete("all")
        if self.controls_canvas:
            self.controls_canvas.delete("all")
        if hasattr(self, 'ruler_canvas'):
            self.ruler_canvas.delete("all")
        if hasattr(self, 'controls_ruler_canvas'):
            self.controls_ruler_canvas.delete("all")
        
        width = self.compute_width()
        height = self.compute_height()
        
        # Set scroll regions
        self.canvas.config(scrollregion=(0, 0, width, height))
        if self.controls_canvas:
            self.controls_canvas.config(scrollregion=(0, 0, self.left_margin, height))
        # Ruler canvas scrolls horizontally like main canvas but has fixed height
        if hasattr(self, 'ruler_canvas'):
            self.ruler_canvas.config(scrollregion=(0, 0, width, self.ruler_height))
        
        # If content fits, reset view to top/left to avoid stray offsets
        try:
            cw = max(1, self.canvas.winfo_width())
            ch = max(1, self.canvas.winfo_height())
            if width <= cw:
                self.canvas.xview_moveto(0)
                if hasattr(self, 'ruler_canvas'):
                    self.ruler_canvas.xview_moveto(0)
            if height <= ch:
                self.canvas.yview_moveto(0)
                if self.controls_canvas:
                    self.controls_canvas.yview_moveto(0)
        except Exception:
            pass
        
        # Draw in correct order
        self._draw_ruler(width)  # Draw ruler on fixed ruler_canvas (scrolls horizontally only)
        self._draw_track_controls()  # Draw controls on left canvas
        self._draw_track_backgrounds(width)  # Draw track backgrounds on main canvas
        self._draw_grid(width, height)
        self._draw_clips()
        self._draw_loop_markers(height)
        self._draw_cursor(height)

        # Ensure scrollbars reflect current content
        try:
            self._update_scrollbars()
        except Exception:
            pass

    def _on_xscroll_change(self, first, last):
        """Sync horizontal scrollbar and ruler canvas."""
        if hasattr(self, 'hscroll') and self.hscroll:
            try:
                self.hscroll.set(first, last)
            except Exception:
                pass
        # Sync ruler canvas horizontal scroll with main canvas
        if hasattr(self, 'ruler_canvas'):
            try:
                self.ruler_canvas.xview_moveto(first)
            except Exception:
                pass
        
    def _on_yscroll_change(self, first, last):
        """Sync vertical scrollbar and possibly update visibility."""
        if hasattr(self, 'vscroll') and self.vscroll:
            try:
                self.vscroll.set(first, last)
            except Exception:
                pass
        # No heavy work here; visibility handled by _update_scrollbars

    def _update_scrollbars(self):
        """Show/hide scrollbars based on content vs viewport size."""
        if self.canvas is None:
            return
        # Determine content size from scrollregion
        try:
            bbox = self.canvas.bbox('all')
            if not bbox:
                return
            content_w = max(0, bbox[2] - bbox[0])
            content_h = max(0, bbox[3] - bbox[1])
            cw = max(1, self.canvas.winfo_width())
            ch = max(1, self.canvas.winfo_height())
            need_h = content_w > cw + 1
            need_v = content_h > ch + 1
        except Exception:
            return
        
        # Horizontal scrollbar
        if need_h and not self._hscroll_visible:
            try:
                self.hscroll.grid(row=1, column=0, sticky='ew')
                self._hscroll_visible = True
            except Exception:
                pass
        elif not need_h and self._hscroll_visible:
            try:
                self.hscroll.grid_remove()
                self._hscroll_visible = False
                self.canvas.xview_moveto(0)
            except Exception:
                pass
        
        # Vertical scrollbar
        if need_v and not self._vscroll_visible:
            try:
                self.vscroll.grid(row=0, column=1, sticky='ns')
                self._vscroll_visible = True
            except Exception:
                pass
        elif not need_v and self._vscroll_visible:
            try:
                self.vscroll.grid_remove()
                self._vscroll_visible = False
                self.canvas.yview_moveto(0)
            except Exception:
                pass
    
    def _draw_ruler(self, width):
        """Draw the time ruler at the top with time markers on the fixed ruler canvas."""
        # Use ruler_canvas if available, otherwise fall back to main canvas
        target_canvas = self.ruler_canvas if hasattr(self, 'ruler_canvas') else self.canvas
        if target_canvas is None:
            return
            
        # Ruler background
        target_canvas.create_rectangle(
            0, 0, width, self.ruler_height,
            fill="#1a1a1a", outline=""
        )
        
        # Draw time markers and divisions
        if self.project is not None:
            # Musical ruler - bars and beats
            bar_duration = self.project.get_bar_duration()
            beat_duration = self.project.get_beat_duration()
            max_time = width / self.px_per_sec
            
            # Draw bar markers
            bar_num = 0
            while True:
                bar_time = bar_num * bar_duration
                if bar_time > max_time:
                    break
                
                x = bar_time * self.px_per_sec
                
                # Bar line in ruler
                target_canvas.create_line(x, 0, x, self.ruler_height, fill="#3b82f6", width=2)
                
                # Bar number
                target_canvas.create_text(
                    x + 4, 8, anchor="nw", text=f"{bar_num + 1}",
                    fill="#60a5fa", font=("Consolas", 9, "bold")
                )
                bar_num += 1
            
            # Draw beat markers
            beat_num = 0
            while True:
                beat_time = beat_num * beat_duration
                if beat_time > max_time:
                    break
                
                x = beat_time * self.px_per_sec
                is_bar = abs(beat_time % bar_duration) < 0.001
                
                if not is_bar:  # Don't overdraw bar lines
                    # Beat line in ruler
                    target_canvas.create_line(x, self.ruler_height - 8, x, self.ruler_height, 
                                          fill="#1e40af", width=1)
                
                beat_num += 1
        else:
            # Simple time ruler - seconds
            total_secs = int(width / self.px_per_sec) + 1
            
            for sec in range(0, total_secs):
                x = sec * self.px_per_sec
                
                # Second marker
                target_canvas.create_line(x, 0, x, self.ruler_height, fill="#3b82f6", width=2)
                
                # Time label
                target_canvas.create_text(
                    x + 4, 8, anchor="nw", text=f"{sec:02d}s",
                    fill="#60a5fa", font=("Consolas", 8, "bold")
                )
                
                # Quarter second markers
                for q in range(1, 4):
                    mx = x + q * (self.px_per_sec / 4.0)
                    target_canvas.create_line(mx, self.ruler_height - 6, mx, self.ruler_height, 
                                          fill="#60a5fa", width=1)

    def _draw_grid(self, width, height):
        """Draw the musical grid or time grid."""
        if self.canvas is None:
            return
            
        if self.project is not None:
            self._draw_musical_grid(width, height)
        else:
            self._draw_time_grid(width, height)

    def _draw_musical_grid(self, width, height):
        """Draw musical grid with bars, beats and subdivisions based on grid_division."""
        bar_duration = self.project.get_bar_duration()
        beat_duration = self.project.get_beat_duration()
        
        max_time = width / self.px_per_sec
        
        # PASS 1: Draw bar lines first (strongest - every bar)
        bar_num = 0
        while True:
            bar_time = bar_num * bar_duration
            if bar_time > max_time:
                break
            
            x = bar_time * self.px_per_sec  # No left_margin offset
            
            # Bar line - thick bright blue (#3b82f6)
            self.canvas.create_line(x, self.ruler_height, x, height, fill="#3b82f6", width=3)
            
            bar_num += 1
        
        # PASS 2: Draw ALL grid subdivision lines based on selected grid_division
        # grid_division is in fractions of a bar (e.g., 0.25 = 1/4 bar, 0.125 = 1/8 bar)
        if self.grid_division > 0:
            grid_time = bar_duration * self.grid_division
            t = grid_time  # Start from first grid point
            
            while t < max_time:
                x = t * self.px_per_sec  # No left_margin offset
                
                # Check what type of line this is
                is_bar = abs(t % bar_duration) < 0.001
                is_beat = abs(t % beat_duration) < 0.001
                
                if is_bar:
                    # Skip - already drawn as bar
                    pass
                elif is_beat:
                    # Beat line - medium blue, solid (#1e40af)
                    self.canvas.create_line(x, self.ruler_height, x, height, fill="#1e40af", width=2)
                else:
                    # Subdivision line - light blue, dashed (#60a5fa)
                    self.canvas.create_line(x, self.ruler_height, x, height, 
                                          fill="#60a5fa", width=1, dash=(3, 3))
                
                t += grid_time

    def _draw_time_grid(self, width, height):
        """Draw simple time-based grid (seconds) - visible on dark background."""
        total_secs = int(width / self.px_per_sec) + 1
        
        for sec in range(0, total_secs):
            x = sec * self.px_per_sec  # No left_margin offset
            
            # Major gridline - bright blue like musical grid
            self.canvas.create_line(x, self.ruler_height, x, height, fill="#3b82f6", width=2)
            
            # Minor ticks (quarters) - light blue dashed
            for q in range(1, 4):
                mx = x + q * (self.px_per_sec / 4.0)
                self.canvas.create_line(mx, self.ruler_height, mx, height, fill="#60a5fa", width=1, dash=(3, 3))

    def _draw_track_controls(self):
        """Draw track controls on the fixed left canvas."""
        if self.controls_canvas is None or self.mixer is None:
            return
            
        tracks_count = len(self.mixer.tracks)
        
        for i in range(tracks_count):
            y0 = self.ruler_height + i * self.track_height
            y1 = y0 + self.track_height
            
            # Controls area background (highlight if selected)
            is_selected = (self.selected_track_idx == i)
            ctrl_bg = "#223a57" if is_selected else "#1a1a1a"
            ctrl_outline = "#3b82f6" if is_selected else "#2d2d2d"
            self.controls_canvas.create_rectangle(
                0, y0, self.left_margin, y1, 
                fill=ctrl_bg, outline=ctrl_outline, width=1
            )
            
            # Track info
            track = self.mixer.tracks[i]
            label = track.get("name", f"Track {i+1}")
            track_color = track.get("color", "#3b82f6")
            volume = track.get("volume", 1.0)
            pan = track.get("pan", 0.0)
            is_muted = track.get("mute", False)
            is_soloed = track.get("solo", False)
            
            # Color indicator strip
            self.controls_canvas.create_rectangle(
                2, y0 + 4, 6, y1 - 4, 
                fill=track_color, outline=""
            )
            
            # Track number and name
            self.controls_canvas.create_text(
                12, y0 + 12, anchor="nw",
                text=f"{i+1}.", fill="#888888",
                font=("Segoe UI", 8)
            )
            self.controls_canvas.create_text(
                28, y0 + 12, anchor="nw",
                text=label, fill=("#ffffff" if is_selected else track_color),
                font=("Segoe UI", 9, "bold")
            )
            
            # M/S/FX Buttons (small, top-right of control area)
            btn_y = y0 + 8
            btn_x = self.left_margin - 95
            
            # Mute button
            mute_color = "#dc2626" if is_muted else "#404040"
            self.controls_canvas.create_rectangle(
                btn_x, btn_y, btn_x + 20, btn_y + 18,
                fill=mute_color, outline="#555555", width=1,
                tags=f"mute_{i}"
            )
            self.controls_canvas.create_text(
                btn_x + 10, btn_y + 9,
                text="M", fill="#ffffff",
                font=("Segoe UI", 8, "bold"),
                tags=f"mute_{i}"
            )
            
            # Solo button
            solo_color = "#eab308" if is_soloed else "#404040"
            self.controls_canvas.create_rectangle(
                btn_x + 25, btn_y, btn_x + 45, btn_y + 18,
                fill=solo_color, outline="#555555", width=1,
                tags=f"solo_{i}"
            )
            self.controls_canvas.create_text(
                btn_x + 35, btn_y + 9,
                text="S", fill="#ffffff",
                font=("Segoe UI", 8, "bold"),
                tags=f"solo_{i}"
            )
            
            # FX button
            self.controls_canvas.create_rectangle(
                btn_x + 50, btn_y, btn_x + 72, btn_y + 18,
                fill="#8b5cf6", outline="#555555", width=1,
                tags=f"fx_{i}"
            )
            self.controls_canvas.create_text(
                btn_x + 61, btn_y + 9,
                text="FX", fill="#ffffff",
                font=("Segoe UI", 7, "bold"),
                tags=f"fx_{i}"
            )
            
            # Volume control (slider representation)
            vol_y = y0 + 35
            vol_x = 40
            vol_width = self.left_margin - 100
            
            self.controls_canvas.create_text(
                12, vol_y, anchor="w",
                text="Vol", fill="#888888",
                font=("Segoe UI", 7)
            )
            
            # Volume track
            self.controls_canvas.create_rectangle(
                vol_x, vol_y - 2, vol_x + vol_width, vol_y + 2,
                fill="#404040", outline=""
            )
            
            # Volume fill
            vol_fill = int(vol_width * volume)
            self.controls_canvas.create_rectangle(
                vol_x, vol_y - 2, vol_x + vol_fill, vol_y + 2,
                fill="#3b82f6", outline=""
            )
            
            # Volume value
            self.controls_canvas.create_text(
                vol_x + vol_width + 5, vol_y, anchor="w",
                text=f"{volume:.2f}", fill="#f5f5f5",
                font=("Segoe UI", 7)
            )
            
            # Pan control
            pan_y = y0 + 55
            
            self.controls_canvas.create_text(
                12, pan_y, anchor="w",
                text="Pan", fill="#888888",
                font=("Segoe UI", 7)
            )
            
            # Pan track
            self.controls_canvas.create_rectangle(
                vol_x, pan_y - 2, vol_x + vol_width, pan_y + 2,
                fill="#404040", outline=""
            )
            
            # Pan center marker
            center_x = vol_x + vol_width // 2
            self.controls_canvas.create_line(
                center_x, pan_y - 4, center_x, pan_y + 4,
                fill="#666666", width=1
            )
            
            # Pan indicator
            pan_pos = int(vol_width / 2 + (pan * vol_width / 2))
            self.controls_canvas.create_oval(
                vol_x + pan_pos - 4, pan_y - 4,
                vol_x + pan_pos + 4, pan_y + 4,
                fill="#10b981", outline="#065f46", width=1
            )
            
            # Pan value
            pan_text = "C" if abs(pan) < 0.05 else (f"L{abs(pan):.1f}" if pan < 0 else f"R{pan:.1f}")
            self.controls_canvas.create_text(
                vol_x + vol_width + 5, pan_y, anchor="w",
                text=pan_text, fill="#f5f5f5",
                font=("Segoe UI", 7)
            )

        # Make the entire controls area clickable for selection and controls actions
        def on_controls_click(event):
            x = self.controls_canvas.canvasx(event.x)
            y = self.controls_canvas.canvasy(event.y)
            if y <= self.ruler_height:
                return
            track_idx = int((y - self.ruler_height) / self.track_height)
            if self.mixer is None or track_idx < 0 or track_idx >= len(self.mixer.tracks):
                return
            # If clicking on a control, handle it; otherwise just select the track
            control = self._find_control_at(x, y)
            if control:
                try:
                    self._handle_control_click(control, x, y)
                except Exception:
                    pass
            else:
                self.select_track(track_idx)
        # Bind once (idempotent for multiple redraws because Tk keeps last binding)
        try:
            self.controls_canvas.bind('<Button-1>', on_controls_click)
        except Exception:
            pass
    
    def _draw_track_backgrounds(self, width):
        """Draw track backgrounds on the main timeline canvas."""
        if self.canvas is None or self.mixer is None:
            return
            
        tracks_count = len(self.mixer.tracks)
        
        for i in range(tracks_count):
            y0 = self.ruler_height + i * self.track_height
            y1 = y0 + self.track_height
            
            # Alternating background for timeline area (highlight if selected)
            if self.selected_track_idx == i:
                bg_color = "#0f172a"  # subtle blue-ish highlight
            else:
                bg_color = "#0d0d0d" if i % 2 == 0 else "#111111"
            self.canvas.create_rectangle(
                0, y0, width, y1,
                fill=bg_color, outline=""
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
        x0 = int(clip.start_time * self.px_per_sec)  # No left_margin offset
        x1 = int(clip.end_time * self.px_per_sec)
        
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
        
        # Draw resize handles se la clip è selezionata
        if is_selected:
            self._draw_resize_handles(x0, x1, y0, y1)

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
    
    def _draw_resize_handles(self, x0, x1, y0, y1):
        """Disegna i handle di ridimensionamento ai bordi della clip selezionata."""
        handle_color = "#ffffff"
        handle_width = 3
        
        # Handle sinistro (linea verticale)
        self.canvas.create_line(
            x0, y0 + 8, x0, y1 - 8,
            fill=handle_color, width=handle_width, tags="resize_handle"
        )
        
        # Handle destro (linea verticale)
        self.canvas.create_line(
            x1, y0 + 8, x1, y1 - 8,
            fill=handle_color, width=handle_width, tags="resize_handle"
        )
        
        # Indicatore visivo centrale sui bordi (per maggiore chiarezza)
        handle_mid_y = (y0 + y1) / 2
        
        # Frecce sinistra
        self.canvas.create_polygon(
            x0 + 1, handle_mid_y,
            x0 + 8, handle_mid_y - 4,
            x0 + 8, handle_mid_y + 4,
            fill=handle_color, outline="", tags="resize_handle"
        )
        
        # Frecce destra
        self.canvas.create_polygon(
            x1 - 1, handle_mid_y,
            x1 - 8, handle_mid_y - 4,
            x1 - 8, handle_mid_y + 4,
            fill=handle_color, outline="", tags="resize_handle"
        )

    def _draw_loop_markers(self, height):
        """Draw loop region markers if loop is enabled."""
        if self.canvas is None or self.player is None:
            return
            
        try:
            loop_enabled, loop_start, loop_end = self.player.get_loop()
            if not loop_enabled:
                return
                
            loop_x_start = loop_start * self.px_per_sec  # No left_margin offset
            loop_x_end = loop_end * self.px_per_sec
            
            # Loop region highlight on main canvas (full height)
            self.canvas.create_rectangle(
                loop_x_start, 0,
                loop_x_end, height,
                fill="#10b981", stipple="gray25", outline=""
            )
            
            # Draw loop markers on ruler canvas (fixed, doesn't scroll vertically)
            ruler_canvas = self.ruler_canvas if hasattr(self, 'ruler_canvas') else self.canvas
            
            # Loop start marker on ruler
            self._draw_loop_marker(loop_x_start, "[", ruler_canvas)
            
            # Loop end marker on ruler
            self._draw_loop_marker(loop_x_end, "]", ruler_canvas, is_end=True)
        except Exception:
            pass

    def _draw_loop_marker(self, x, label, target_canvas, is_end=False):
        """Draw a single loop marker on the ruler canvas."""
        # Marker line (vertical line in ruler area)
        line_id = target_canvas.create_line(
            x, 0, x, self.ruler_height,
            fill="#10b981", width=3, tags=f"loop_marker_{label.lower()}"
        )
        
        # Marker flag (handle draggabile) at bottom of ruler
        marker_y = self.ruler_height - 2
        if is_end:
            # End marker - triangle pointing left
            handle_id = target_canvas.create_polygon(
                x, marker_y,
                x - 10, marker_y - 8,
                x - 10, marker_y,
                fill="#10b981", outline="#065f46", width=2,
                tags=f"loop_marker_{label.lower()}"
            )
            text_id = target_canvas.create_text(
                x - 5, marker_y - 4, text=label,
                fill="#ffffff", font=("Segoe UI", 9, "bold"),
                tags=f"loop_marker_{label.lower()}"
            )
        else:
            # Start marker - triangle pointing right
            handle_id = target_canvas.create_polygon(
                x, marker_y,
                x + 10, marker_y - 8,
                x + 10, marker_y,
                fill="#10b981", outline="#065f46", width=2,
                tags=f"loop_marker_{label.lower()}"
            )
            text_id = target_canvas.create_text(
                x + 5, marker_y - 4, text=label,
                fill="#ffffff", font=("Segoe UI", 9, "bold"),
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
        
        cursor_x = cur * self.px_per_sec  # No left_margin offset
        
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
        
        paste_x = self.paste_position * self.px_per_sec  # No left_margin offset
        
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
            
        x = current_time * self.px_per_sec  # No left_margin offset
        
        try:
            height = self.compute_height()
            self.canvas.coords(self.cursor_id, x, 0, x, height)
            
            # Auto-scroll to keep cursor visible
            vis_left = self.canvas.canvasx(0)
            vis_right = self.canvas.canvasx(self.canvas.winfo_width())
            
            if x < vis_left or x > vis_right:
                self.canvas.xview_moveto(
                    max(0.0, x / max(1, self.compute_width()))
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

    def _find_control_at(self, x, y):
        """Find which track control (button/slider) is at the given coordinates.
        
        Returns:
            dict with 'type' (button/volume/pan), 'track_idx', and 'action' (mute/solo/fx)
            or None if not on a control
        """
        if x >= self.left_margin:
            return None  # Not in controls area
        
        if y <= self.ruler_height:
            return None  # In ruler area
        
        # Calculate track index
        track_idx = int((y - self.ruler_height) / self.track_height)
        
        if self.mixer is None or track_idx >= len(self.mixer.tracks):
            return None
        
        # Calculate y position within track
        y0 = self.ruler_height + track_idx * self.track_height
        y_in_track = y - y0
        
        # Button positions (top-right of control area)
        btn_y = 8
        btn_x = self.left_margin - 95
        
        # Check buttons (M/S/FX)
        if btn_y <= y_in_track <= btn_y + 18:
            # Mute button
            if btn_x <= x <= btn_x + 20:
                return {'type': 'button', 'track_idx': track_idx, 'action': 'mute'}
            # Solo button
            elif btn_x + 25 <= x <= btn_x + 45:
                return {'type': 'button', 'track_idx': track_idx, 'action': 'solo'}
            # FX button
            elif btn_x + 50 <= x <= btn_x + 72:
                return {'type': 'button', 'track_idx': track_idx, 'action': 'fx'}
        
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

    # Mouse event handlers
    def on_click(self, event):
        """Handle mouse click."""
        # Determine which canvas was clicked
        widget = event.widget
        
        if widget == self.controls_canvas:
            # Click on controls canvas - only handle control interactions
            x = self.controls_canvas.canvasx(event.x)
            y = self.controls_canvas.canvasy(event.y)
            
            control = self._find_control_at(x, y)
            if control:
                self._handle_control_click(control, x, y)
            else:
                # Plain click on controls area selects the track
                track_idx = int((y - self.ruler_height) / self.track_height)
                if self.mixer is not None and 0 <= track_idx < len(self.mixer.tracks):
                    self.select_track(track_idx)
            return
        
        # Click on ruler canvas - handle loop markers
        if hasattr(self, 'ruler_canvas') and widget == self.ruler_canvas:
            x = self.ruler_canvas.canvasx(event.x)
            y = event.y  # ruler_canvas doesn't scroll vertically
            
            # Check if clicking on loop markers
            if self._check_loop_marker_click_on_ruler(x, y):
                return
            return
        
        # Click on main timeline canvas
        if self.canvas is None:
            return
            
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Check if clicking on loop markers (legacy, now on ruler)
        if self._check_loop_marker_click(x, y):
            return
        
        # Check for loop region selection with Shift
        if event.state & 0x0001:  # Shift key
            time = x / self.px_per_sec  # No left_margin offset needed anymore
            self.loop_selection_start = max(0, time)
            return
        
        # Check for Ctrl key (multi-selection)
        ctrl_pressed = event.state & 0x0004  # Ctrl key
        
        # Find clicked clip
        clicked_clip = self._find_clip_at(x, y)
        
        if clicked_clip:
            track_idx, clip = clicked_clip
            clip_x0 = clip.start_time * self.px_per_sec  # No left_margin offset
            clip_x1 = clip.end_time * self.px_per_sec
            
            # Check for edge resize con zona più ampia e priorità maggiore
            resize_edge = self._get_resize_edge(x, clip_x0, clip_x1)
            
            if resize_edge and not ctrl_pressed:
                # Modalità resize - ha priorità sul drag
                self.resize_data = {
                    "clip": clip, "track": track_idx,
                    "edge": resize_edge,
                    "orig_start": clip.start_time,
                    "orig_end": clip.end_time,
                    "start_x": x
                }
                # Assicurati che la clip sia selezionata
                if not any(c == clip for _, c in self.selected_clips):
                    self.select_clip(track_idx, clip)
                # Imposta cursore
                self.canvas.config(cursor="sb_h_double_arrow")
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
    
    def _handle_control_click(self, control, x, y):
        """Handle click on a track control (button or slider)."""
        control_type = control['type']
        track_idx = control['track_idx']
        
        if control_type == 'button':
            action = control['action']
            if action == 'mute':
                self._toggle_mute(track_idx)
            elif action == 'solo':
                self._toggle_solo(track_idx)
            elif action == 'fx':
                self._open_effects_dialog(track_idx)
            # Buttons also imply selecting this track
            self.select_track(track_idx)
        
        elif control_type == 'volume':
            # Start volume drag
            self.dragging_volume = {
                'track': track_idx,
                'start_x': x,
                'start_vol': self.mixer.tracks[track_idx].get('volume', 1.0)
            }
            self.select_track(track_idx)
        
        elif control_type == 'pan':
            # Start pan drag
            self.dragging_pan = {
                'track': track_idx,
                'start_x': x,
                'start_pan': self.mixer.tracks[track_idx].get('pan', 0.0)
            }
            self.select_track(track_idx)
    
    def _toggle_mute(self, track_idx):
        """Toggle mute for a track."""
        if self.mixer is None or track_idx >= len(self.mixer.tracks):
            return
        
        try:
            is_muted = self.mixer.toggle_mute(track_idx)
            track_name = self.mixer.tracks[track_idx].get("name", f"Track {track_idx + 1}")
            print(f"🔇 Muted: {track_name}" if is_muted else f"🔊 Unmuted: {track_name}")
            self.redraw()
        except Exception as e:
            print(f"Error toggling mute: {e}")
    
    def _toggle_solo(self, track_idx):
        """Toggle solo for a track."""
        if self.mixer is None or track_idx >= len(self.mixer.tracks):
            return
        
        try:
            is_soloed = self.mixer.toggle_solo(track_idx)
            track_name = self.mixer.tracks[track_idx].get("name", f"Track {track_idx + 1}")
            print(f"🎯 Soloed: {track_name}" if is_soloed else f"▶ Unsoloed: {track_name}")
            self.redraw()
        except Exception as e:
            print(f"Error toggling solo: {e}")
    
    def _open_effects_dialog(self, track_idx):
        """Open effects chain dialog for the given track."""
        if self.project is None or track_idx >= len(self.project.tracks):
            return
        
        track = self.project.tracks[track_idx]
        track_name = getattr(track, 'name', f"Track {track_idx + 1}")
        
        try:
            from .dialogs.effects_chain_dialog import EffectsChainDialog
            # Get parent window from canvas
            parent = self.canvas.winfo_toplevel()
            EffectsChainDialog(parent, track, track_name, redraw_cb=self.redraw)
        except Exception as e:
            print(f"Error opening effects dialog: {e}")
            import traceback
            traceback.print_exc()

    def on_drag(self, event):
        """Handle mouse drag."""
        widget = event.widget
        
        # Handle drag on ruler canvas (for loop markers)
        if hasattr(self, 'ruler_canvas') and widget == self.ruler_canvas:
            x = self.ruler_canvas.canvasx(event.x)
            if self.dragging_loop_marker is not None:
                self._handle_loop_marker_drag(x)
            return
        
        if self.canvas is None:
            return
            
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Drag loop marker
        if self.dragging_loop_marker is not None:
            self._handle_loop_marker_drag(x)
            return
        
        # Drag volume slider
        if self.dragging_volume is not None:
            self._handle_volume_drag(x)
            return
        
        # Drag pan slider
        if self.dragging_pan is not None:
            self._handle_pan_drag(x)
            return
        
        # Loop region selection with Shift
        if self.loop_selection_start is not None:
            # Disegna preview del loop durante il drag
            self.canvas.delete("loop_preview")
            
            end_time = x / self.px_per_sec  # No left_margin offset
            end_time = max(0, end_time)
            
            start_time = self.loop_selection_start
            
            # Visualizza l'area che sarà selezionata
            loop_x_start = min(start_time, end_time) * self.px_per_sec  # No left_margin offset
            loop_x_end = max(start_time, end_time) * self.px_per_sec
            
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
    
    def _handle_volume_drag(self, x):
        """Handle volume slider dragging."""
        if self.dragging_volume is None or self.mixer is None:
            return
        
        track_idx = self.dragging_volume['track']
        if track_idx >= len(self.mixer.tracks):
            return
        
        # Calculate new volume based on mouse position
        vol_x = 40
        vol_width = self.left_margin - 100
        
        # Clamp x to slider bounds
        x = max(vol_x, min(x, vol_x + vol_width))
        
        # Calculate volume (0.0 to 1.0)
        volume = (x - vol_x) / vol_width
        volume = max(0.0, min(1.0, volume))
        
        # Update mixer
        self.mixer.tracks[track_idx]['volume'] = volume
        
        # Redraw to show updated slider
        self.redraw()
    
    def _handle_pan_drag(self, x):
        """Handle pan slider dragging."""
        if self.dragging_pan is None or self.mixer is None:
            return
        
        track_idx = self.dragging_pan['track']
        if track_idx >= len(self.mixer.tracks):
            return
        
        # Calculate new pan based on mouse position
        pan_x = 40
        pan_width = self.left_margin - 100
        center_x = pan_x + pan_width // 2
        
        # Clamp x to slider bounds
        x = max(pan_x, min(x, pan_x + pan_width))
        
        # Calculate pan (-1.0 to 1.0)
        pan = (x - center_x) / (pan_width / 2)
        pan = max(-1.0, min(1.0, pan))
        
        # Snap to center if close
        if abs(pan) < 0.05:
            pan = 0.0
        
        # Update mixer
        self.mixer.tracks[track_idx]['pan'] = pan
        
        # Redraw to show updated slider
        self.redraw()

    def on_release(self, event):
        """Handle mouse release."""
        widget = event.widget
        
        # Release loop marker drag
        if self.dragging_loop_marker is not None:
            self.dragging_loop_marker = None
            # Reset cursor on appropriate canvas
            if hasattr(self, 'ruler_canvas') and widget == self.ruler_canvas:
                self.ruler_canvas.config(cursor="")
            elif self.canvas:
                self.canvas.config(cursor="")
            return
        
        # Release resize
        if self.resize_data is not None:
            clip = self.resize_data["clip"]
            print(f"✓ Resize complete: {clip.name} | Start: {clip.start_time:.3f}s | Duration: {clip.duration:.3f}s")
            self.resize_data = None
            self.canvas.config(cursor="")
            return
        
        # Release volume/pan dragging
        if self.dragging_volume is not None:
            track_idx = self.dragging_volume['track']
            volume = self.mixer.tracks[track_idx].get('volume', 1.0)
            print(f"🔊 Volume adjusted: Track {track_idx + 1} = {volume:.2f}")
            self.dragging_volume = None
            return
        
        if self.dragging_pan is not None:
            track_idx = self.dragging_pan['track']
            pan = self.mixer.tracks[track_idx].get('pan', 0.0)
            pan_text = "C" if abs(pan) < 0.05 else (f"L{abs(pan):.1f}" if pan < 0 else f"R{pan:.1f}")
            print(f"🎚️ Pan adjusted: Track {track_idx + 1} = {pan_text}")
            self.dragging_pan = None
            return
        
        # Check loop region selection
        if self.loop_selection_start is not None:
            self.canvas.delete("loop_preview")
            
            x = self.canvas.canvasx(event.x)
            end_time = x / self.px_per_sec  # No left_margin offset
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
        widget = event.widget
        
        # Handle motion on ruler canvas
        if hasattr(self, 'ruler_canvas') and widget == self.ruler_canvas:
            # Don't change cursor while dragging
            if self.dragging_loop_marker:
                return
            
            x = self.ruler_canvas.canvasx(event.x)
            y = event.y
            
            # Check if hovering over loop markers on ruler
            if self._is_over_loop_marker_on_ruler(x, y):
                self.ruler_canvas.config(cursor="sb_h_double_arrow")
            else:
                self.ruler_canvas.config(cursor="")
            return
        
        if self.canvas is None:
            return
        
        # Don't change cursor while dragging
        if (self.drag_data or self.resize_data or self.dragging_loop_marker or 
            self.dragging_volume or self.dragging_pan):
            return
            
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Check if hovering over track controls
        control = self._find_control_at(x, y)
        if control:
            control_type = control['type']
            if control_type == 'button':
                self.canvas.config(cursor="hand2")
            elif control_type in ('volume', 'pan'):
                self.canvas.config(cursor="sb_h_double_arrow")
            return
        
        # Check if hovering over loop markers
        if self._is_over_loop_marker(x, y):
            self.canvas.config(cursor="sb_h_double_arrow")
            return
        
        clicked_clip = self._find_clip_at(x, y)
        
        if clicked_clip:
            track_idx, clip = clicked_clip
            clip_x0 = clip.start_time * self.px_per_sec  # No left_margin offset
            clip_x1 = clip.end_time * self.px_per_sec
            
            # Usa la stessa logica di resize del click
            resize_edge = self._get_resize_edge(x, clip_x0, clip_x1)
            
            if resize_edge:
                self.canvas.config(cursor="sb_h_double_arrow")
            else:
                self.canvas.config(cursor="hand2")
        else:
            self.canvas.config(cursor="")

    def on_right_click(self, event):
        """Handle right-click context menu."""
        # This will be handled by MainWindow
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
        """Handle clip resize con feedback visivo migliorato."""
        clip = self.resize_data["clip"]
        new_time = x / self.px_per_sec  # No left_margin offset
        new_time = max(0, new_time)
        new_time = self.snap_time(new_time)
        
        if self.resize_data["edge"] == "left":
            # Ridimensiona dal bordo sinistro
            # La clip non può diventare più corta di 0.1 secondi
            if new_time < clip.end_time - 0.1:
                # Aggiorna start_time mantenendo end_time fisso
                old_start = clip.start_time
                clip.start_time = new_time
                # La durata si aggiusta automaticamente tramite la property
                
                # Feedback visivo: mostra il delta tempo
                delta = new_time - old_start
                print(f"⬅ Resize left: {delta:+.3f}s | Duration: {clip.duration:.3f}s")
        else:
            # Ridimensiona dal bordo destro
            # La clip non può diventare più corta di 0.1 secondi
            if new_time > clip.start_time + 0.1:
                # Aggiorna la durata
                old_duration = clip.duration
                clip.duration = new_time - clip.start_time
                
                # Feedback visivo: mostra il delta tempo
                delta = clip.duration - old_duration
                print(f"➡ Resize right: {delta:+.3f}s | Duration: {clip.duration:.3f}s")
        
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
                        # Calcola le coordinate delle clip SENZA left_margin (i canvas sono separati)
                        clip_x1 = clip.start_time * self.px_per_sec
                        clip_x2 = clip.end_time * self.px_per_sec
                        clip_y1 = self.ruler_height + track_idx * self.track_height
                        clip_y2 = clip_y1 + self.track_height
                        
                        # Check if clip intersects with selection box
                        # Verifica che ci sia sovrapposizione sia in X che in Y
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

    # Track selection helpers
    def select_track(self, track_idx: int):
        """Select a track by index, highlight it, and notify callback."""
        try:
            if self.mixer is None or track_idx < 0 or track_idx >= len(self.mixer.tracks):
                return
            self.selected_track_idx = int(track_idx)
            # Notify parent if callback provided
            if callable(self.on_track_selected):
                try:
                    self.on_track_selected(self.selected_track_idx)
                except Exception:
                    pass
            self.redraw()
        except Exception:
            pass

    def get_selected_track(self):
        return self.selected_track_idx

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

    def _get_resize_edge(self, mouse_x, clip_x0, clip_x1):
        """Determina se il mouse è su un bordo ridimensionabile della clip.
        
        Args:
            mouse_x: Posizione X del mouse
            clip_x0: Posizione X inizio clip
            clip_x1: Posizione X fine clip
            
        Returns:
            "left" se sul bordo sinistro, "right" se sul bordo destro, None altrimenti
        """
        # Controlla bordo sinistro (priorità maggiore)
        if abs(mouse_x - clip_x0) <= self.resize_handle_size:
            return "left"
        
        # Controlla bordo destro
        if abs(mouse_x - clip_x1) <= self.resize_handle_size:
            return "right"
        
        return None
    
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

    def _check_loop_marker_click_on_ruler(self, x, y):
        """Check if click is on a loop marker in the ruler canvas and start dragging."""
        if self.player is None:
            return False
        
        try:
            loop_enabled, loop_start, loop_end = self.player.get_loop()
            if not loop_enabled:
                return False
            
            loop_x_start = loop_start * self.px_per_sec
            loop_x_end = loop_end * self.px_per_sec
            
            # Check click on start marker (15px tolerance)
            if abs(x - loop_x_start) < 15 and 0 <= y <= self.ruler_height:
                self.dragging_loop_marker = "start"
                if hasattr(self, 'ruler_canvas'):
                    self.ruler_canvas.config(cursor="sb_h_double_arrow")
                return True
            
            # Check click on end marker
            if abs(x - loop_x_end) < 15 and 0 <= y <= self.ruler_height:
                self.dragging_loop_marker = "end"
                if hasattr(self, 'ruler_canvas'):
                    self.ruler_canvas.config(cursor="sb_h_double_arrow")
                return True
        except Exception:
            pass
        
        return False
    
    def _check_loop_marker_click(self, x, y):
        """Check if click is on a loop marker and start dragging (legacy, for main canvas)."""
        if self.player is None or y > self.ruler_height + 30:
            return False
        
        try:
            loop_enabled, loop_start, loop_end = self.player.get_loop()
            if not loop_enabled:
                return False
            
            loop_x_start = loop_start * self.px_per_sec  # No left_margin offset
            loop_x_end = loop_end * self.px_per_sec
            
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
    
    def _is_over_loop_marker_on_ruler(self, x, y):
        """Check if mouse is over a loop marker on the ruler canvas."""
        if self.player is None:
            return False
        
        try:
            loop_enabled, loop_start, loop_end = self.player.get_loop()
            if not loop_enabled:
                return False
            
            loop_x_start = loop_start * self.px_per_sec
            loop_x_end = loop_end * self.px_per_sec
            
            # Check if hovering over markers in ruler area
            if 0 <= y <= self.ruler_height:
                if abs(x - loop_x_start) < 15 or abs(x - loop_x_end) < 15:
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
            
            loop_x_start = loop_start * self.px_per_sec  # No left_margin offset
            loop_x_end = loop_end * self.px_per_sec
            
            return abs(x - loop_x_start) < 15 or abs(x - loop_x_end) < 15
        except Exception:
            return False

    def _handle_loop_marker_drag(self, x):
        """Handle dragging of loop markers."""
        if self.player is None:
            return
        
        new_time = x / self.px_per_sec  # No left_margin offset
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
