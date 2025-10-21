try:
    import tkinter as tk
except Exception:  # pragma: no cover
    tk = None

# Import timeline components for modular architecture
from .timeline.geometry import TimelineGeometry
from .timeline.renderers import (
    RulerRenderer, GridRenderer, TrackRenderer,
    ClipRenderer, CursorRenderer, LoopRenderer
)
from .timeline.services import SnapService, ClipboardService
from .timeline.controllers import (
    DragController, ResizeController, BoxSelectController,
    LoopMarkerController, TrackControlsController
)
from .timeline.canvas_manager import CanvasManager
from .timeline.mouse_event_coordinator import MouseEventCoordinator


class TimelineCanvas:
    """Manages the timeline canvas, rendering, and clip interactions.
    
    This class orchestrates various timeline components:
    - CanvasManager: Handles all canvas widgets and scrolling
    - Geometry: Coordinate conversions and dimensions
    - Renderers: Specialized drawing for rulers, grids, clips, etc.
    - Services: Snap-to-grid and clipboard operations
    - Controllers: Drag, resize, selection interactions
    - MouseEventCoordinator: Routes mouse events to appropriate handlers
    """

    def __init__(self, parent, project=None, mixer=None, timeline=None, player=None):
        """Initialize timeline canvas with all components.
        
        Args:
            parent: Parent Tkinter widget
            project: Project object
            mixer: Mixer object
            timeline: Timeline object
            player: Player object
        """
        # Core dependencies (injected)
        self.project = project
        self.mixer = mixer
        self.timeline = timeline
        self.player = player
        
        # Callback for track selection notification
        self.on_track_selected = None
        
        # Initialize geometry (coordinate system and dimensions)
        self.geometry = TimelineGeometry(
            px_per_sec=200,
            track_height=80,
            ruler_height=32,
            left_margin=280
        )
        
        # Initialize canvas manager (UI widget management)
        self.canvas_manager = CanvasManager(self.geometry)
        
        # Build UI and get references to canvases
        canvases = self.canvas_manager.build(parent)
        
        # Maintain backward compatibility - direct canvas references
        self.canvas = canvases.get('canvas')
        self.controls_canvas = canvases.get('controls_canvas')
        self.ruler_canvas = canvases.get('ruler_canvas')
        self.controls_ruler_canvas = canvases.get('controls_ruler_canvas')
        self.scroll = canvases.get('hscroll')  # Legacy name
        self.hscroll = canvases.get('hscroll')
        self.vscroll = canvases.get('vscroll')
        
        # Legacy state for backward compatibility
        self.cursor_id = None
        
        # Initialize renderers (specialized drawing components)
        self._init_renderers()
        
        # Initialize services (snap and clipboard)
        self._init_services()
        
        # Initialize controllers (interaction handlers)
        self._init_controllers()
        
        # Initialize mouse event coordinator (event routing)
        self._init_event_coordinator()
        
        # Clip selection state
        self.selected_clip = None  # (track_index, clip) - backward compatibility
        self.selected_clips = []  # [(track_index, clip), ...] - multi-selection
        self.clip_canvas_ids = {}  # {canvas_id: (track_idx, clip)}
        
        # Track selection state
        self.selected_track_idx = None
        
        # Context menus (set by MainWindow)
        self.track_menu = None
    
    def _init_renderers(self):
        """Initialize all renderer components.
        
        Renderers are responsible for drawing different timeline elements.
        Each renderer is specialized for a specific visual element.
        """
        self.ruler_renderer = RulerRenderer(self.geometry)
        self.grid_renderer = GridRenderer(self.geometry)
        self.track_renderer = TrackRenderer(self.geometry)
        self.clip_renderer = ClipRenderer(self.geometry)
        self.cursor_renderer = CursorRenderer(self.geometry)
        self.loop_renderer = LoopRenderer(self.geometry)
    
    def _init_services(self):
        """Initialize service components.
        
        Services provide utility functions like snapping and clipboard.
        """
        self.snap_service = SnapService(self.project)
        self.clipboard_service = ClipboardService()
    
    def _init_controllers(self):
        """Initialize controller components.
        
        Controllers handle user interactions like dragging and resizing.
        All controllers are configured to trigger redraw on changes.
        """
        self.drag_controller = DragController(self.geometry, self.snap_service)
        self.resize_controller = ResizeController(self.geometry, self.snap_service)
        self.box_select_controller = BoxSelectController(self.geometry)
        self.loop_marker_controller = LoopMarkerController(self.geometry, self.snap_service)
        self.track_controls_controller = TrackControlsController(
            self.geometry, 
            self.geometry.left_margin
        )
        
        # Set invalidation callbacks (trigger redraw on changes)
        self.drag_controller.on_invalidate = self.redraw
        self.resize_controller.on_invalidate = self.redraw
        self.loop_marker_controller.on_invalidate = self.redraw
        self.track_controls_controller.on_invalidate = self.redraw
    
    def _init_event_coordinator(self):
        """Initialize mouse event coordinator.
        
        The coordinator routes mouse events to appropriate controllers
        and maintains separation between event handling and business logic.
        """
        self.event_coordinator = MouseEventCoordinator(self.geometry, self.canvas_manager)
        
        # Inject controllers into coordinator
        self.event_coordinator.drag_controller = self.drag_controller
        self.event_coordinator.resize_controller = self.resize_controller
        self.event_coordinator.box_select_controller = self.box_select_controller
        self.event_coordinator.loop_marker_controller = self.loop_marker_controller
        self.event_coordinator.track_controls_controller = self.track_controls_controller
        
        # Set event callbacks
        self.event_coordinator.on_clip_click = self._handle_clip_click
        self.event_coordinator.on_empty_click = self._handle_empty_click
        self.event_coordinator.on_control_click = self._handle_control_click
        self.event_coordinator.on_loop_selection = self._handle_loop_selection
        self.event_coordinator.on_track_selection = self.select_track
        
        # Connect canvas manager callbacks to event coordinator
        self.canvas_manager.on_mouse_wheel = self._on_mouse_wheel
        self.canvas_manager.on_mouse_click = self._on_mouse_click
        self.canvas_manager.on_mouse_drag = self._on_mouse_drag
        self.canvas_manager.on_mouse_release = self._on_mouse_release
        self.canvas_manager.on_mouse_motion = self._on_mouse_motion
        self.canvas_manager.on_mouse_right_click = self._on_mouse_right_click
    
    # =========================================================================
    # EVENT HANDLERS - Route events from canvas manager to event coordinator
    # =========================================================================
    
    def _on_mouse_wheel(self, event):
        """Route mouse wheel events to coordinator."""
        self.event_coordinator.handle_mouse_wheel(event, self.mixer)
    
    def _on_mouse_click(self, event):
        """Route click events to coordinator."""
        self.event_coordinator.handle_click(
            event,
            mixer=self.mixer,
            timeline=self.timeline,
            player=self.player,
            clip_finder=self._find_clip_at,
            control_finder=self._find_control_at
        )
        # Result contains info about what was clicked for debugging/logging
    
    def _on_mouse_drag(self, event):
        """Route drag events to coordinator."""
        self.event_coordinator.handle_drag(event, self.mixer, self.player)
        # Result contains info about drag operation
    
    def _on_mouse_release(self, event):
        """Route release events to coordinator."""
        result = self.event_coordinator.handle_release(
            event,
            timeline=self.timeline,
            player=self.player,
            snap_func=self.snap_time
        )
        
        # Handle specific release results
        if result['type'] == 'resize_release' and result.get('data'):
            clip = result['data'].get('clip')
            if clip:
                print(f"✓ Resize complete: {clip.name} | "
                     f"Start: {clip.start_time:.3f}s | Duration: {clip.duration:.3f}s")
        
        elif result['type'] == 'volume_release' and result.get('data'):
            track_idx = result['data'].get('track')
            if track_idx is not None and self.mixer:
                volume = self.mixer.tracks[track_idx].get('volume', 1.0)
                print(f"🔊 Volume adjusted: Track {track_idx + 1} = {volume:.2f}")
        
        elif result['type'] == 'pan_release' and result.get('data'):
            track_idx = result['data'].get('track')
            if track_idx is not None and self.mixer:
                pan = self.mixer.tracks[track_idx].get('pan', 0.0)
                pan_text = "C" if abs(pan) < 0.05 else (
                    f"L{abs(pan):.1f}" if pan < 0 else f"R{pan:.1f}"
                )
                print(f"🎚️ Pan adjusted: Track {track_idx + 1} = {pan_text}")
        
        elif result['type'] == 'box_selection_complete':
            selected = result.get('data', [])
            if selected:
                self.selected_clips = selected
                self.selected_clip = selected[0] if selected else None
                print(f"📦 Box selection: {len(selected)} clip(s) selected")
            self.redraw()
    
    def _on_mouse_motion(self, event):
        """Route motion events to coordinator."""
        self.event_coordinator.handle_motion(
            event,
            player=self.player,
            clip_finder=self._find_clip_at,
            control_finder=self._find_control_at
        )
        # Result contains cursor changes already applied by coordinator
    
    def _on_mouse_right_click(self, event):
        """Handle right-click context menu (delegated to MainWindow)."""
        # This is handled by MainWindow's context menu setup
        pass
    
    # =========================================================================
    # CLICK ACTION HANDLERS - Called by event coordinator
    # =========================================================================
    
    def _handle_clip_click(self, track_idx, clip, multi=False):
        """Handle clip click action.
        
        Args:
            track_idx: Track index
            clip: Clip object
            multi: True if Ctrl was pressed (multi-selection)
        """
        if multi:
            self.toggle_clip_selection(track_idx, clip)
        else:
            self.select_clip(track_idx, clip)
    
    def _handle_empty_click(self, x, y, ctrl_pressed):
        """Handle click on empty timeline area.
        
        Args:
            x: Canvas x coordinate
            y: Canvas y coordinate
            ctrl_pressed: True if Ctrl was pressed
        """
        # Clear selection if not holding Ctrl
        if not ctrl_pressed:
            self.clear_selection()
        
        # Check if we have clipboard content - set paste position
        if self.clipboard_service.has_clips() and y > self.geometry.ruler_height:
            time = self.geometry.x_to_time(x)
            self.clipboard_service.set_paste_position(
                max(0, self.snap_time(time)), 
                visible=True
            )
            self.redraw()
            print(f"📍 Paste position set to {self.clipboard_service.paste_position:.2f}s "
                 f"(press Ctrl+V to paste)")
        else:
            # No clipboard or clicked in ruler - hide paste cursor
            self.clipboard_service.paste_cursor_visible = False
            self.redraw()
    
    def _handle_control_click(self, control, x, y):
        """Handle click on track control.
        
        Args:
            control: Control info dict
            x: Canvas x coordinate
            y: Canvas y coordinate
        """
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
            self.select_track(track_idx)
        
        elif control_type == 'volume':
            self.track_controls_controller.start_volume_drag(track_idx, x, self.mixer)
            self.select_track(track_idx)
        
        elif control_type == 'pan':
            self.track_controls_controller.start_pan_drag(track_idx, x, self.mixer)
            self.select_track(track_idx)
    
    def _handle_loop_selection(self, start, end, player):
        """Handle loop region selection completion.
        
        Args:
            start: Loop start time
            end: Loop end time
            player: Player object
        """
        player.set_loop(True, start, end)
        self.redraw()
        print(f"🔁 Loop region set: {start:.3f}s - {end:.3f}s")
    
    # =========================================================================
    # BACKWARD COMPATIBILITY PROPERTIES
    # =========================================================================
    
    @property
    def px_per_sec(self):
        """Get pixels per second (backward compatibility)."""
        return self.geometry.px_per_sec
    
    @px_per_sec.setter
    def px_per_sec(self, value):
        """Set pixels per second (backward compatibility)."""
        self.geometry.px_per_sec = value
    
    @property
    def track_height(self):
        """Get track height (backward compatibility)."""
        return self.geometry.track_height
    
    @property
    def ruler_height(self):
        """Get ruler height (backward compatibility)."""
        return self.geometry.ruler_height
    
    @property
    def left_margin(self):
        """Get left margin (backward compatibility)."""
        return self.geometry.left_margin
    
    @property
    def snap_enabled(self):
        """Get snap enabled state (backward compatibility)."""
        return self.snap_service.enabled
    
    @property
    def grid_division(self):
        """Get grid division (backward compatibility)."""
        return self.snap_service.grid_division
    
    @property
    def clipboard(self):
        """Get clipboard data (backward compatibility)."""
        return self.clipboard_service.clipboard
    
    @property
    def paste_position(self):
        """Get paste position (backward compatibility)."""
        return self.clipboard_service.paste_position
    
    @paste_position.setter
    def paste_position(self, value: float):
        """Set paste position (backward compatibility)."""
        self.clipboard_service.paste_position = value
    
    @property
    def paste_cursor_visible(self):
        """Get paste cursor visibility (backward compatibility)."""
        return self.clipboard_service.paste_cursor_visible
    
    @paste_cursor_visible.setter
    def paste_cursor_visible(self, value: bool):
        """Set paste cursor visibility (backward compatibility)."""
        self.clipboard_service.paste_cursor_visible = value
    
    # =========================================================================
    # DIMENSION CALCULATIONS
    # =========================================================================
    
    def set_vscroll_callback(self, callback):
        """Set callback for vertical scroll position changes.
        
        Args:
            callback: Function(first, last) to call on scroll changes
        """
        if self.canvas:
            def on_scroll(*args):
                callback(*args)
                if self.vscroll:
                    self.vscroll.set(*args)
            self.canvas.configure(yscrollcommand=on_scroll)
    
    def compute_width(self):
        """Calculate timeline width based on content (delegates to geometry).
        
        Returns:
            Width in pixels
        """
        return self.geometry.compute_width(self.timeline, min_width=800)
    
    def compute_height(self):
        """Calculate timeline height based on track count (delegates to geometry).
        
        Returns:
            Height in pixels
        """
        tracks_count = max(1, len(getattr(self.mixer, 'tracks', [])))
        return self.geometry.compute_height(tracks_count)
    
    # =========================================================================
    # RENDERING - Orchestrates specialized renderer components
    # =========================================================================

    def redraw(self):
        """Redraw the entire timeline (delegates to canvas manager and renderers).
        
        This method orchestrates the complete redraw cycle:
        1. Clear all canvases
        2. Update scroll regions
        3. Draw all timeline elements in correct order
        4. Update scrollbar visibility
        """
        if self.canvas is None:
            return
        
        # Step 1: Clear all canvases (delegate to canvas manager)
        self.canvas_manager.clear_all()
        
        # Step 2: Calculate dimensions
        width = self.compute_width()
        height = self.compute_height()
        
        # Step 3: Update scroll regions (delegate to canvas manager)
        self.canvas_manager.update_scroll_regions(width, height)
        
        # Step 4: Reset view if content fits (delegate to canvas manager)
        self.canvas_manager.reset_view_if_fits(width, height)
        
        # Step 5: Draw all elements in correct z-order
        self._draw_ruler(width)
        self._draw_track_controls()
        self._draw_track_backgrounds(width)
        self._draw_grid(width, height)
        self._draw_clips()
        self._draw_loop_markers(height)
        self._draw_cursor(height)
        
        # Step 6: Update scrollbar visibility (delegate to canvas manager)
        try:
            self.canvas_manager.update_scrollbars()
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
        
        # Use cursor renderer
        self.cursor_id = self.cursor_renderer.draw(self.canvas, height, cur)
        
        # Draw paste cursor if visible
        if self.clipboard_service.paste_cursor_visible and self.clipboard_service.has_clips():
            self.clipboard_service.draw_paste_cursor(self.canvas, self.geometry, height)

    def _draw_paste_cursor(self, height):
        """Draw the paste position cursor - deprecated, now handled by ClipboardService."""
        # Delegate to clipboard service
        if self.canvas:
            self.clipboard_service.draw_paste_cursor(self.canvas, self.geometry, height)

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
        zoom_level = self.geometry.zoom(factor)
        self.redraw()
        return zoom_level

    def zoom_reset(self):
        """Reset zoom to default."""
        self.geometry.zoom_reset()
        self.redraw()

    def set_snap(self, enabled):
        """Enable/disable snap to grid."""
        self.snap_service.set_enabled(enabled)
        self.redraw()

    def set_grid_division(self, division):
        """Set grid division (1.0 = bar, 0.25 = quarter, etc.)."""
        self.snap_service.set_grid_division(division)
        self.redraw()

    def snap_time(self, time):
        """Snap time to grid if enabled."""
        return self.snap_service.snap_time(time)

    def _find_control_at(self, x, y):
        """Find which track control (button/slider) is at the given coordinates.
        
        Returns:
            dict with 'type' (button/volume/pan), 'track_idx', and 'action' (mute/solo/fx)
            or None if not on a control
        """
        return self.track_controls_controller.find_control_at(x, y, self.mixer)

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
            marker = self.loop_marker_controller.check_loop_marker_hit(x, y, self.player)
            if marker:
                self.loop_marker_controller.start_drag(marker)
                return
            return
        
        # Click on main timeline canvas
        if self.canvas is None:
            return
            
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Check if clicking on loop markers (legacy, for main canvas)
        marker = self.loop_marker_controller.check_loop_marker_hit(x, y, self.player)
        if marker:
            self.loop_marker_controller.start_drag(marker)
            return
        
        # Check for loop region selection with Shift - only in ruler area
        if event.state & 0x0001 and y <= self.ruler_height:  # Shift key in ruler
            time = self.geometry.x_to_time(x)
            self.loop_selection_start = max(0, time)
            return
        
        # Check for Ctrl key (multi-selection)
        ctrl_pressed = event.state & 0x0004  # Ctrl key
        
        # Find clicked clip
        clicked_clip = self._find_clip_at(x, y)
        
        if clicked_clip:
            track_idx, clip = clicked_clip
            
            # Check for edge resize
            resize_edge = self.resize_controller.check_resize_edge(x, clip, track_idx)
            
            if resize_edge and not ctrl_pressed:
                # Start resize mode
                self.resize_controller.start_resize(clip, track_idx, resize_edge)
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
                    self.drag_controller.start_drag(clip, track_idx, x)
                    self.select_clip(track_idx, clip)
        else:
            # Clicked on empty area
            
            # Check for Shift key first - box selection (only in track area, not ruler)
            if event.state & 0x0001 and y > self.ruler_height:  # Shift key in track area
                self.box_select_controller.start_selection(x, y)
                print(f"📦 Box selection started at ({x:.1f}, {y:.1f})")
                return
            
            # Clear selection if not holding Ctrl
            if not ctrl_pressed:
                self.clear_selection()
            
            # Check if we have clipboard content - set paste position
            if self.clipboard and y > self.ruler_height:
                time = self.geometry.x_to_time(x)
                self.clipboard_service.set_paste_position(max(0, self.snap_time(time)), visible=True)
                self.redraw()
                print(f"📍 Paste position set to {self.clipboard_service.paste_position:.2f}s (press Ctrl+V to paste)")
            else:
                # No clipboard or clicked in ruler - hide paste cursor
                self.clipboard_service.paste_cursor_visible = False
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
            # Start volume drag using controller
            self.track_controls_controller.start_volume_drag(track_idx, x, self.mixer)
            self.select_track(track_idx)
        
        elif control_type == 'pan':
            # Start pan drag using controller
            self.track_controls_controller.start_pan_drag(track_idx, x, self.mixer)
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
            if self.loop_marker_controller.is_dragging():
                self.loop_marker_controller.update_drag(x, self.player)
            return
        
        if self.canvas is None:
            return
            
        x = self.canvas.canvasx(event.x)
        y = self.canvas.canvasy(event.y)
        
        # Drag loop marker
        if self.loop_marker_controller.is_dragging():
            self.loop_marker_controller.update_drag(x, self.player)
            return
        
        # Drag volume slider
        if self.track_controls_controller.dragging_volume is not None:
            self._handle_volume_drag(x)
            return
        
        # Drag pan slider
        if self.track_controls_controller.dragging_pan is not None:
            self._handle_pan_drag(x)
            return
        
        # Loop region selection with Shift
        if self.loop_selection_start is not None:
            # Disegna preview del loop durante il drag
            self.canvas.delete("loop_preview")
            
            end_time = self.geometry.x_to_time(x)
            end_time = max(0, end_time)
            
            start_time = self.loop_selection_start
            
            # Visualizza l'area che sarà selezionata
            loop_x_start = self.geometry.time_to_x(min(start_time, end_time))
            loop_x_end = self.geometry.time_to_x(max(start_time, end_time))
            
            height = self.compute_height()
            self.canvas.create_rectangle(
                loop_x_start, self.ruler_height,
                loop_x_end, height,
                fill="#10b981", stipple="gray25", outline="#10b981",
                width=2, tags="loop_preview"
            )
            return
        
        # Box selection (rectangular clip selection)
        if self.box_select_controller.is_selecting():
            self.box_select_controller.update_selection(self.canvas, x, y)
            return
        
        if self.resize_controller.is_resizing():
            self.resize_controller.update_resize(x)
        elif self.drag_controller.is_dragging():
            self.drag_controller.update_drag(x, y, self.mixer)
    
    def _handle_volume_drag(self, x):
        """Handle volume slider dragging."""
        self.track_controls_controller.update_volume_drag(x, self.mixer)
    
    def _handle_pan_drag(self, x):
        """Handle pan slider dragging."""
        self.track_controls_controller.update_pan_drag(x, self.mixer)

    def on_release(self, event):
        """Handle mouse release."""
        widget = event.widget
        
        # Release loop marker drag
        if self.loop_marker_controller.is_dragging():
            self.loop_marker_controller.end_drag()
            # Reset cursor on appropriate canvas
            if hasattr(self, 'ruler_canvas') and widget == self.ruler_canvas:
                self.ruler_canvas.config(cursor="")
            elif self.canvas:
                self.canvas.config(cursor="")
            return
        
        # Release resize
        if self.resize_controller.is_resizing():
            resize_data = self.resize_controller.end_resize()
            if resize_data:
                clip = resize_data["clip"]
                print(f"✓ Resize complete: {clip.name} | Start: {clip.start_time:.3f}s | Duration: {clip.duration:.3f}s")
            self.canvas.config(cursor="")
            return
        
        # Release volume/pan dragging
        if self.track_controls_controller.dragging_volume is not None:
            vol_data = self.track_controls_controller.end_volume_drag()
            if vol_data:
                track_idx = vol_data['track']
                volume = self.mixer.tracks[track_idx].get('volume', 1.0)
                print(f"🔊 Volume adjusted: Track {track_idx + 1} = {volume:.2f}")
            return
        
        if self.track_controls_controller.dragging_pan is not None:
            pan_data = self.track_controls_controller.end_pan_drag()
            if pan_data:
                track_idx = pan_data['track']
                pan = self.mixer.tracks[track_idx].get('pan', 0.0)
                pan_text = "C" if abs(pan) < 0.05 else (f"L{abs(pan):.1f}" if pan < 0 else f"R{pan:.1f}")
                print(f"🎚️ Pan adjusted: Track {track_idx + 1} = {pan_text}")
            return
        
        # Check loop region selection
        if self.loop_selection_start is not None:
            self.canvas.delete("loop_preview")
            
            x = self.canvas.canvasx(event.x)
            end_time = self.geometry.x_to_time(x)
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
        if self.box_select_controller.is_selecting():
            x = self.canvas.canvasx(event.x)
            y = self.canvas.canvasy(event.y)
            selected = self.box_select_controller.complete_selection(self.canvas, self.timeline, x, y)
            if selected:
                self.selected_clips = selected
                self.selected_clip = selected[0] if selected else None
                print(f"📦 Box selection: {len(selected)} clip(s) selected")
            self.redraw()
            return
        
        # Release drag
        if self.drag_controller.is_dragging():
            self.drag_controller.end_drag()

    def on_motion(self, event):
        """Handle mouse motion for cursor changes."""
        widget = event.widget
        
        # Handle motion on ruler canvas
        if hasattr(self, 'ruler_canvas') and widget == self.ruler_canvas:
            # Don't change cursor while dragging
            if self.loop_marker_controller.is_dragging():
                return
            
            x = self.ruler_canvas.canvasx(event.x)
            y = event.y
            
            # Check if hovering over loop markers on ruler
            marker = self.loop_marker_controller.check_loop_marker_hit(x, y, self.player)
            if marker:
                self.ruler_canvas.config(cursor="sb_h_double_arrow")
            else:
                self.ruler_canvas.config(cursor="")
            return
        
        if self.canvas is None:
            return
        
        # Don't change cursor while dragging
        if (self.drag_controller.is_dragging() or self.resize_controller.is_resizing() or 
            self.loop_marker_controller.is_dragging() or 
            self.track_controls_controller.is_dragging()):
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
        marker = self.loop_marker_controller.check_loop_marker_hit(x, y, self.player)
        if marker:
            self.canvas.config(cursor="sb_h_double_arrow")
            return
        
        clicked_clip = self._find_clip_at(x, y)
        
        if clicked_clip:
            track_idx, clip = clicked_clip
            
            # Check if hovering over resize edge
            resize_edge = self.resize_controller.check_resize_edge(x, clip, track_idx)
            
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
        
        # Use clipboard service to copy
        current_time = float(getattr(self.player, "_current_time", 0.0)) if self.player else 0.0
        num_copied = self.clipboard_service.copy_clips(self.selected_clips, current_time)
        
        self.redraw()
        
        print(f"📋 Copied {num_copied} clip(s) to clipboard")
        print(f"📍 Paste position set to {self.clipboard_service.paste_position:.2f}s (click on timeline to change, or press Ctrl+V to paste)")
        return num_copied > 0
    
    def paste_clips(self, at_time=None):
        """Paste clips from clipboard.
        
        Args:
            at_time: Optional time to paste at. If None, uses paste_position if set,
                    otherwise uses current playback time.
        """
        if not self.clipboard_service.has_clips():
            return []
        
        # Determine paste position
        if at_time is None:
            if self.clipboard_service.paste_cursor_visible:
                at_time = self.clipboard_service.paste_position
            else:
                at_time = float(getattr(self.player, "_current_time", 0.0)) if self.player else 0.0
        
        # Use clipboard service to paste
        pasted_clips = self.clipboard_service.paste_clips(at_time, self.timeline)
        
        # Select pasted clips
        self.selected_clips = pasted_clips
        self.selected_clip = pasted_clips[0] if pasted_clips else None
        
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
