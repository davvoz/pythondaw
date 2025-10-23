"""Professional Piano Roll Editor for MIDI editing.

Features:
- Full MIDI note editing with drag, resize, and velocity control
- Piano keyboard sidebar with visual feedback
- Snap-to-grid with multiple quantization options
- Note selection (single and multi-select with box selection)
- Copy/paste/duplicate functionality
- Velocity editing with visual indicators
- Professional dark theme
- Real-time preview
- Undo/redo support
"""

try:
    import tkinter as tk
    from tkinter import ttk, font as tkfont
except Exception:  # pragma: no cover
    tk = None
    ttk = None
    tkfont = None

from typing import List, Optional, Tuple, Set
from dataclasses import dataclass


@dataclass
class EditAction:
    """Represents an undoable action."""
    action_type: str  # 'add', 'delete', 'move', 'resize', 'velocity'
    notes_state: list  # Snapshot of notes before action
    

class PianoRollEditor:
    """Professional Piano Roll Editor for MIDI note editing.
    
    Features:
    - Drag to move notes, resize from edges
    - Click to add/select notes
    - Box selection for multiple notes
    - Snap to grid with configurable quantization
    - Velocity editing
    - Copy/paste/duplicate
    - Undo/redo
    - Piano keyboard sidebar
    """

    # Note dimensions
    NOTE_HEIGHT = 14
    KEY_WIDTH = 60
    RULER_HEIGHT = 30
    
    # Grid snap options (in beats, assuming 4/4 time)
    SNAP_OPTIONS = {
        "1/32": 0.03125,
        "1/16": 0.0625,
        "1/8": 0.125,
        "1/4": 0.25,
        "1/2": 0.5,
        "1 bar": 1.0,
        "Off": 0.0
    }

    def __init__(self, parent, midi_clip, on_apply=None, px_per_sec=200, pitch_min=21, pitch_max=108, player=None, project=None):
        self.parent = parent
        self.clip = midi_clip
        self.on_apply = on_apply
        self.px_per_sec = px_per_sec
        self.pitch_min = int(pitch_min)
        self.pitch_max = int(pitch_max)
        # Optional player reference to track playback time
        self._player = player
        # Reference to project for BPM updates
        self._project = project
        
        # Grid and snap settings
        self.snap_value = 0.25  # Default 1/4 note
        self.snap_enabled = True
        
        # UI state
        self._win = None
        self._canvas = None
        self._keyboard_canvas = None
        self._ruler_canvas = None
        self._notes_ids = {}  # Maps canvas item ID to MidiNote
        self._selected_notes: List[object] = []  # List instead of set because MidiNote is not hashable
        
        # Playhead position (for visualization)
        self._playhead_time = 0.0
        self._playhead_line = None
        self._playhead_job = None  # after() job id for periodic updates
        
        # Prevent recursive redraws
        self._is_drawing = False
        
        # Interaction state
        self._drag_mode = None  # None, 'move', 'resize_left', 'resize_right', 'box_select', 'velocity'
        self._drag_start_pos = None
        self._drag_notes_original = []  # List of (note, start, duration, pitch) tuples
        self._box_select_rect = None
        self._current_hover_note = None
        
        # Clipboard
        self._clipboard: List[dict] = []
        
        # Undo/redo
        self._undo_stack: List[EditAction] = []
        self._redo_stack: List[EditAction] = []
        self._max_undo = 50
        
        # Piano key state
        self._pressed_keys: Set[int] = set()
        
        # Zoom
        self.zoom_level = 1.0
        
        # Performance optimization
        self._redraw_pending = False
        self._last_redraw_time = 0
        self._redraw_throttle = 0.016  # ~60 FPS max
        
        # Headplay (audio preview)
        self._headplay_enabled = True
        
    def _get_current_bpm(self) -> float:
        """Get current BPM from project (live) or fallback to default."""
        try:
            if self._project and hasattr(self._project, 'bpm'):
                bpm = float(self._project.bpm)
                # Debug: print when BPM is read
                # print(f"Piano Roll reading BPM: {bpm}")
                return bpm
            if hasattr(self.clip, 'project') and self.clip.project and hasattr(self.clip.project, 'bpm'):
                bpm = float(self.clip.project.bpm)
                # print(f"Piano Roll reading BPM from clip.project: {bpm}")
                return bpm
        except Exception as e:
            # print(f"Error reading BPM: {e}")
            pass
        return 120.0  # Fallback default
    
    def _get_bar_duration(self) -> float:
        """Get bar duration in seconds from project (considers time signature)."""
        try:
            if self._project and hasattr(self._project, 'get_bar_duration'):
                return float(self._project.get_bar_duration())
            if hasattr(self.clip, 'project') and self.clip.project and hasattr(self.clip.project, 'get_bar_duration'):
                return float(self.clip.project.get_bar_duration())
        except Exception:
            pass
        # Fallback: 4/4 at 120 BPM = 2 seconds per bar
        bpm = self._get_current_bpm()
        return (60.0 / bpm) * 4.0
        
    def _schedule_redraw(self):
        """Schedule a redraw with throttling for performance."""
        import time
        current_time = time.time()
        
        if current_time - self._last_redraw_time < self._redraw_throttle:
            if not self._redraw_pending:
                self._redraw_pending = True
                if self._win:
                    self._win.after(16, self._do_scheduled_redraw)
        else:
            self._redraw()
            
    def _do_scheduled_redraw(self):
        """Execute scheduled redraw."""
        self._redraw_pending = False
        self._redraw()
        
    def _play_note_preview(self, pitch: int, duration: float = 0.1):
        """Play a note preview (headplay) when clicking/editing."""
        if not self._headplay_enabled:
            return
            
        try:
            # Try to use the clip's instrument if available
            instrument = getattr(self.clip, 'instrument', None)
            if instrument and hasattr(instrument, 'play_note'):
                instrument.play_note(pitch, 100)
                # Schedule note off
                if self._win and hasattr(instrument, 'stop_note'):
                    self._win.after(int(duration * 1000), lambda: instrument.stop_note(pitch))
        except Exception:
            pass  # Silently fail if no instrument available
        
    def _is_note_selected(self, note) -> bool:
        """Check if a note is selected using identity comparison."""
        return any(n is note for n in self._selected_notes)
        
    def _add_to_selection(self, note):
        """Add note to selection if not already selected."""
        if not self._is_note_selected(note):
            self._selected_notes.append(note)
            
    def _remove_from_selection(self, note):
        """Remove note from selection."""
        self._selected_notes = [n for n in self._selected_notes if n is not note]


    def show(self):
        """Create and display the piano roll window."""
        if tk is None:
            return
        
        # Debug: print clip and project info
        print(f"\n=== PIANO ROLL OPENED ===")
        print(f"Clip: {getattr(self.clip, 'name', 'Unknown')}")
        print(f"Clip start_time: {getattr(self.clip, 'start_time', 'N/A')}")
        print(f"Clip duration: {getattr(self.clip, 'duration', 'N/A')}")
        print(f"Project BPM: {self._get_current_bpm()}")
        print(f"Bar duration: {self._get_bar_duration():.3f}s")
        notes = getattr(self.clip, 'notes', []) or []
        print(f"Total notes: {len(notes)}")
        if notes:
            print(f"  Note 1: start={notes[0].start:.3f}s, dur={notes[0].duration:.3f}s, pitch={notes[0].pitch}")
            if len(notes) > 1:
                print(f"  Note 2: start={notes[1].start:.3f}s, dur={notes[1].duration:.3f}s, pitch={notes[1].pitch}")
            if len(notes) > 2:
                print(f"  Note {len(notes)}: start={notes[-1].start:.3f}s, dur={notes[-1].duration:.3f}s, pitch={notes[-1].pitch}")
        print(f"========================\n")
        
        try:
            self._win = tk.Toplevel(self.parent)
            self._win.title(f"Piano Roll - {getattr(self.clip, 'name', 'MIDI Clip')}")
            self._win.geometry("1200x700")
            self._win.configure(bg="#1e1e1e")
            self._win.protocol("WM_DELETE_WINDOW", self._close)
            
            self._create_toolbar()
            self._create_main_area()
            self._setup_bindings()
            
            # Use after() for delayed draw to avoid configure() recursion
            self._win.update_idletasks()
            self._win.after(100, self._safe_initial_draw)
            # Start periodic playhead updates if a player is available
            self._start_playhead_updates()
            
        except Exception as e:
            print(f"ERROR creating piano roll: {e}")
            import traceback
            traceback.print_exc()
    
    def _safe_initial_draw(self):
        """Safely draw after window is ready."""
        try:
            if self._canvas and self._win and self._canvas.winfo_width() > 1:
                self._redraw()
        except Exception as e:
            print(f"ERROR in _safe_initial_draw: {e}")
            import traceback
            traceback.print_exc()
    
    def _on_canvas_mapped(self, event=None):
        """NOT USED - causes freezing."""
        pass
        
    def _create_toolbar(self):
        """Create the top toolbar with controls."""
        toolbar = tk.Frame(self._win, bg="#252525", height=60)
        toolbar.pack(fill="x", pady=(0, 2))
        toolbar.pack_propagate(False)
        
        # Snap selector - use buttons instead of combobox for visibility
        snap_frame = tk.Frame(toolbar, bg="#252525")
        snap_frame.pack(side="left", padx=10, pady=5)
        
        tk.Label(snap_frame, text="Snap:", bg="#252525", fg="#f5f5f5", 
                font=("Segoe UI", 9, "bold")).pack(side="top", anchor="w")
        
        snap_btn_frame = tk.Frame(snap_frame, bg="#252525")
        snap_btn_frame.pack(side="top")
        
        self._snap_buttons = {}
        snap_values = ["1/16", "1/8", "1/4", "1/2", "Off"]
        for snap in snap_values:
            btn = tk.Button(snap_btn_frame, text=snap, command=lambda s=snap: self._set_snap(s),
                          bg="#3a3a3a", fg="#f5f5f5", font=("Segoe UI", 8),
                          relief="flat", padx=8, pady=2, cursor="hand2", width=4)
            btn.pack(side="left", padx=1)
            self._snap_buttons[snap] = btn
        self._set_snap("1/4")  # Set default
        
        # Separator
        tk.Frame(toolbar, bg="#404040", width=2).pack(side="left", fill="y", padx=10, pady=5)
        
        # Tool buttons
        btn_frame = tk.Frame(toolbar, bg="#252525")
        btn_frame.pack(side="left", padx=5, pady=5)
        
        tk.Label(btn_frame, text="Tools:", bg="#252525", fg="#f5f5f5",
                font=("Segoe UI", 9, "bold")).pack(side="top", anchor="w")
        
        tool_btn_frame = tk.Frame(btn_frame, bg="#252525")
        tool_btn_frame.pack(side="top")
        
        self._create_tool_button(tool_btn_frame, "Cut", self._cut_selected)
        self._create_tool_button(tool_btn_frame, "Copy", self._copy_selected)
        self._create_tool_button(tool_btn_frame, "Paste", self._paste_clipboard)
        self._create_tool_button(tool_btn_frame, "Del", self._delete_selected)
        
        # Separator
        tk.Frame(toolbar, bg="#404040", width=2).pack(side="left", fill="y", padx=10, pady=5)
        
        # Undo/Redo
        undo_frame = tk.Frame(toolbar, bg="#252525")
        undo_frame.pack(side="left", padx=5, pady=5)
        
        tk.Label(undo_frame, text="History:", bg="#252525", fg="#f5f5f5",
                font=("Segoe UI", 9, "bold")).pack(side="top", anchor="w")
        
        undo_btn_frame = tk.Frame(undo_frame, bg="#252525")
        undo_btn_frame.pack(side="top")
        
        self._create_tool_button(undo_btn_frame, "Undo", self._undo)
        self._create_tool_button(undo_btn_frame, "Redo", self._redo)
        
        # Separator
        tk.Frame(toolbar, bg="#404040", width=2).pack(side="left", fill="y", padx=10, pady=5)
        
        # Zoom controls
        zoom_frame = tk.Frame(toolbar, bg="#252525")
        zoom_frame.pack(side="left", padx=10, pady=5)
        
        tk.Label(zoom_frame, text="Zoom:", bg="#252525", fg="#f5f5f5",
                font=("Segoe UI", 9, "bold")).pack(side="top", anchor="w")
        
        zoom_btn_frame = tk.Frame(zoom_frame, bg="#252525")
        zoom_btn_frame.pack(side="top")
        
        self._create_tool_button(zoom_btn_frame, "−", self._zoom_out)
        self._zoom_label = tk.Label(zoom_btn_frame, text="100%", bg="#252525", fg="#f5f5f5",
                                    font=("Segoe UI", 9), width=6)
        self._zoom_label.pack(side="left", padx=5)
        self._create_tool_button(zoom_btn_frame, "+", self._zoom_in)
        
    def _create_tool_button(self, parent, text, command):
        """Create a styled toolbar button."""
        btn = tk.Button(parent, text=text, command=command,
                       bg="#404040", fg="#f5f5f5", font=("Segoe UI", 9),
                       relief="flat", padx=10, pady=5, cursor="hand2")
        btn.pack(side="left", padx=2)
        btn.bind("<Enter>", lambda e: btn.config(bg="#4a4a4a"))
        btn.bind("<Leave>", lambda e: btn.config(bg="#404040"))
        return btn
    
    def _set_snap(self, snap_value: str):
        """Set snap value and update button appearance."""
        self.snap_value = self.SNAP_OPTIONS[snap_value]
        # Update button colors
        for snap, btn in self._snap_buttons.items():
            if snap == snap_value:
                btn.config(bg="#10b981", fg="#ffffff")
            else:
                btn.config(bg="#3a3a3a", fg="#f5f5f5")
        # Redraw immediately to show new grid
        self._redraw()
        
    def _create_main_area(self):
        """Create the main editing area with keyboard and canvas."""
        main_frame = tk.Frame(self._win, bg="#1e1e1e")
        main_frame.pack(fill="both", expand=True)
        
        # Ruler at top
        ruler_frame = tk.Frame(main_frame, bg="#1e1e1e")
        ruler_frame.pack(fill="x")
        
        # Spacer for keyboard width
        tk.Frame(ruler_frame, bg="#1e1e1e", width=self.KEY_WIDTH).pack(side="left")
        
        # Ruler canvas
        self._ruler_canvas = tk.Canvas(ruler_frame, bg="#252525", height=self.RULER_HEIGHT,
                                       highlightthickness=0)
        self._ruler_canvas.pack(side="left", fill="x", expand=True)
        
        # Content frame (keyboard + notes)
        content_frame = tk.Frame(main_frame, bg="#1e1e1e")
        content_frame.pack(fill="both", expand=True)
        
        # Piano keyboard on left
        keyboard_frame = tk.Frame(content_frame, bg="#1e1e1e")
        keyboard_frame.pack(side="left", fill="y")
        
        self._keyboard_canvas = tk.Canvas(keyboard_frame, bg="#2d2d2d", width=self.KEY_WIDTH,
                                          highlightthickness=0)
        self._keyboard_canvas.pack(fill="y", expand=True)
        
        # Notes canvas with scrollbars
        notes_frame = tk.Frame(content_frame, bg="#1e1e1e")
        notes_frame.pack(side="left", fill="both", expand=True)
        
        self._canvas = tk.Canvas(notes_frame, bg="#0d0d0d", highlightthickness=0)
        
        v_scroll = tk.Scrollbar(notes_frame, orient="vertical", command=self._on_scroll_y)
        h_scroll = tk.Scrollbar(notes_frame, orient="horizontal", command=self._on_scroll_x)
        # keep references so wrapper commands can access them
        self._v_scroll = v_scroll
        self._h_scroll = h_scroll
        # Use wrapper commands so any canvas view changes trigger a redraw
        self._canvas.configure(yscrollcommand=self._on_yscroll_command, xscrollcommand=self._on_xscroll_command)
        
        self._canvas.grid(row=0, column=0, sticky="nsew")
        v_scroll.grid(row=0, column=1, sticky="ns")
        h_scroll.grid(row=1, column=0, sticky="ew")
        
        notes_frame.rowconfigure(0, weight=1)
        notes_frame.columnconfigure(0, weight=1)
        
        # Status bar at bottom
        self._status_bar = tk.Label(self._win, text="Ready", bg="#252525", fg="#a0a0a0",
                                    font=("Segoe UI", 8), anchor="w", padx=10, pady=5)
        self._status_bar.pack(fill="x")
        
    def _on_scroll_y(self, *args):
        """Synchronize vertical scrolling between keyboard and notes."""
        self._canvas.yview(*args)
        self._keyboard_canvas.yview(*args)
        # Immediate redraw so grid/notes update while scrolling
        try:
            self._redraw()
        except Exception:
            pass

    def _on_scroll_x(self, *args):
        """Handle horizontal scrolling and force redraw."""
        # delegate to canvas xview
        try:
            self._canvas.xview(*args)
        except Exception:
            pass
        # Force redraw to update grid immediately
        try:
            self._redraw()
        except Exception:
            pass

    def _on_yscroll_command(self, first, last):
        """Wrapper for canvas yscrollcommand: update scrollbar."""
        try:
            if hasattr(self, '_v_scroll') and self._v_scroll:
                self._v_scroll.set(first, last)
        except Exception:
            pass

    def _on_xscroll_command(self, first, last):
        """Wrapper for canvas xscrollcommand: update scrollbar."""
        try:
            if hasattr(self, '_h_scroll') and self._h_scroll:
                self._h_scroll.set(first, last)
        except Exception:
            pass
        
    def _setup_bindings(self):
        """Setup mouse and keyboard bindings."""
        # Mouse events
        self._canvas.bind("<Button-1>", self._on_mouse_down)
        self._canvas.bind("<B1-Motion>", self._on_mouse_drag)
        self._canvas.bind("<ButtonRelease-1>", self._on_mouse_up)
        self._canvas.bind("<Button-3>", self._on_right_click)
        self._canvas.bind("<Motion>", self._on_mouse_move)
        self._canvas.bind("<Double-Button-1>", self._on_double_click)
        
        # Keyboard shortcuts
        self._win.bind("<Delete>", lambda e: self._delete_selected())
        self._win.bind("<Control-c>", lambda e: self._copy_selected())
        self._win.bind("<Control-x>", lambda e: self._cut_selected())
        self._win.bind("<Control-v>", lambda e: self._paste_clipboard())
        self._win.bind("<Control-d>", lambda e: self._duplicate_selected())
        self._win.bind("<Control-z>", lambda e: self._undo())
        self._win.bind("<Control-y>", lambda e: self._redo())
        self._win.bind("<Control-a>", lambda e: self._select_all())
        self._win.bind("<Escape>", lambda e: self._clear_selection())
        
        # Mouse wheel zoom
        self._canvas.bind("<MouseWheel>", self._on_mouse_wheel)
        self._canvas.bind("<Control-MouseWheel>", self._on_ctrl_mouse_wheel)


    def _close(self):
        """Close the editor and apply changes."""
        # Stop periodic updates
        try:
            if self._win is not None and self._playhead_job is not None:
                self._win.after_cancel(self._playhead_job)
        except Exception:
            pass
        self._playhead_job = None
        if callable(self.on_apply):
            try:
                self.on_apply(self.clip)
            except Exception:
                pass
        if self._win is not None:
            try:
                self._win.destroy()
            except Exception:
                pass
            self._win = None

    # =============================================================================
    # PLAYHEAD UPDATE LOOP
    # =============================================================================
    def _start_playhead_updates(self):
        """Begin periodic updates of the playhead position if player is provided."""
        if self._win is None:
            return
        # Schedule the first tick; subsequent ticks will reschedule themselves
        try:
            self._playhead_job = self._win.after(50, self._playhead_tick)
        except Exception:
            self._playhead_job = None

    def _playhead_tick(self):
        """Update playhead from player and reschedule next tick."""
        try:
            if self._win is None:
                return
            # Read current time from player if available
            cur_time = None
            if self._player is not None:
                try:
                    if hasattr(self._player, 'get_current_time'):
                        cur_time = float(self._player.get_current_time())
                    elif hasattr(self._player, '_current_time'):
                        cur_time = float(getattr(self._player, '_current_time'))
                except Exception:
                    cur_time = None
            if cur_time is not None:
                self.update_playhead(cur_time)
        finally:
            # Reschedule next update if window still exists
            try:
                if self._win is not None:
                    self._playhead_job = self._win.after(50, self._playhead_tick)
            except Exception:
                self._playhead_job = None
            
    # =============================================================================
    # DRAWING METHODS
    # =============================================================================
    
    def _content_size(self):
        """Calculate canvas content size based on actual notes extent and musical bars."""
        try:
            # Start with clip's declared length in seconds
            clip_length = float(getattr(self.clip, 'duration', 4.0) or 4.0)
            
            # Expand to include all notes
            notes = getattr(self.clip, 'notes', []) or []
            if notes:
                # Find the rightmost note
                max_note_end = max((n.start + n.duration for n in notes), default=0.0)
                clip_length = max(clip_length, max_note_end)
            
            # Get bar duration from project (considers time signature correctly)
            seconds_per_bar = self._get_bar_duration()
            
            # Round up to complete bars and add padding of 2 bars
            bars_needed = int((clip_length / seconds_per_bar) + 0.999)  # Round up
            total_bars = bars_needed + 2  # Add 2 bars padding
            total_width = total_bars * seconds_per_bar
        except Exception:
            total_width = 8.0
        
        w = max(1200, int(total_width * self.px_per_sec * self.zoom_level))
        rows = self.pitch_max - self.pitch_min + 1
        h = max(400, rows * self.NOTE_HEIGHT)
        return w, h
        
    def _redraw(self):
        """Redraw all elements."""
        if self._canvas is None or self._is_drawing:
            return
        
        self._is_drawing = True
        try:
            import time
            self._last_redraw_time = time.time()
                
            self._canvas.delete("all")
            w, h = self._content_size()
            self._canvas.configure(scrollregion=(0, 0, w, h))
            
            # Draw components
            self._draw_grid(w, h)
            self._draw_notes()
            self._draw_playhead()
            self._draw_keyboard()
            self._draw_ruler(w)
        finally:
            self._is_drawing = False
    
    def _draw_playhead(self):
        """Draw playhead marker on the canvas."""
        if self._canvas is None or self._playhead_time < 0:
            return
        
        x = self._time_to_x(self._playhead_time)
        
        # Get canvas visible height
        try:
            scroll_region = self._canvas.cget("scrollregion").split()
            if len(scroll_region) >= 4:
                canvas_height = int(float(scroll_region[3]))
            else:
                canvas_height = 600
        except:
            canvas_height = 600
        
        # Draw red vertical line
        self._playhead_line = self._canvas.create_line(
            x, 0, x, canvas_height,
            fill="#ef4444", width=2, tags="playhead"
        )
    
    def update_playhead(self, time: float):
        """Update playhead position during playback.
        
        Args:
            time: Absolute time from timeline player
        """
        # Convert from absolute timeline time to clip-local time
        clip_start = float(getattr(self.clip, 'start_time', 0.0))
        clip_local_time = time - clip_start
        
        # Debug
        print(f"Playhead: absolute={time:.3f}s, clip_start={clip_start:.3f}s, local={clip_local_time:.3f}s, BPM={self._get_current_bpm()}")
        
        self._playhead_time = clip_local_time
        
        # Redraw only playhead for performance
        if self._canvas and self._playhead_line:
            self._canvas.delete("playhead")
            self._draw_playhead()
            # Force immediate canvas update
            try:
                self._canvas.update_idletasks()
            except Exception:
                pass
            
        # Update ruler playhead too
        if self._ruler_canvas:
            self._ruler_canvas.delete("playhead")
            playhead_x = self._time_to_x(clip_local_time)
            self._ruler_canvas.create_line(playhead_x, 0, playhead_x, self.RULER_HEIGHT,
                                          fill="#ef4444", width=2, tags="playhead")
            self._ruler_canvas.create_polygon(
                playhead_x - 5, 0,
                playhead_x + 5, 0,
                playhead_x, 8,
                fill="#ef4444", outline="", tags="playhead"
            )
            # Force immediate ruler update
            try:
                self._ruler_canvas.update_idletasks()
            except Exception:
                pass
        
    def _draw_grid(self, width, height):
        """Draw the background grid - optimized to draw only visible area."""
        # Get visible area
        try:
            x_view = self._canvas.xview()
            y_view = self._canvas.yview()
            visible_x_start = int(x_view[0] * width)
            visible_x_end = int(x_view[1] * width)
            visible_y_start = int(y_view[0] * height)
            visible_y_end = int(y_view[1] * height)
        except:
            visible_x_start, visible_x_end = 0, width
            visible_y_start, visible_y_end = 0, height
        
        # Horizontal lines (piano keys) - iterate full pitch range but only draw visible rows
        for p in range(self.pitch_min, self.pitch_max + 1):
            y = self._pitch_to_y(p)
            # Skip rows completely outside visible Y range
            if y + self.NOTE_HEIGHT < visible_y_start or y > visible_y_end:
                continue
            # Color black keys differently
            is_black_key = (p % 12) in (1, 3, 6, 8, 10)
            color = "#1a1a1a" if is_black_key else "#0f0f0f"
            self._canvas.create_rectangle(visible_x_start, y, visible_x_end, y + self.NOTE_HEIGHT, 
                                         fill=color, outline="#2a2a2a", width=1)
            # Highlight C notes
            if p % 12 == 0:
                self._canvas.create_line(visible_x_start, y, visible_x_end, y, fill="#3a3a3a", width=2)
        
        # Vertical lines (time grid) - bars, beats, and snap subdivisions
        seconds_per_beat = 60.0 / self._get_current_bpm()
        
        # Get beats per bar from project time signature
        beats_per_bar = 4  # Default 4/4
        try:
            if self._project and hasattr(self._project, 'time_signature_num'):
                beats_per_bar = int(self._project.time_signature_num)
            elif hasattr(self.clip, 'project') and hasattr(self.clip.project, 'time_signature_num'):
                beats_per_bar = int(self.clip.project.time_signature_num)
        except Exception:
            pass
        
        seconds_per_bar = seconds_per_beat * beats_per_bar
        
        try:
            clip_length = float(getattr(self.clip, 'duration', 4.0) or 4.0)
            notes = getattr(self.clip, 'notes', []) or []
            if notes:
                max_note_end = max((n.start + n.duration for n in notes), default=0.0)
                clip_length = max(clip_length, max_note_end)
            seconds_per_bar = self._get_bar_duration()
            bars_needed = int((clip_length / seconds_per_bar) + 0.999)
            total_bars = bars_needed + 2
            total_secs = total_bars * seconds_per_bar
        except:
            total_secs = 8.0
        
        # Draw snap subdivisions if snap is enabled and not "Off"
        if self.snap_enabled and self.snap_value > 0:
            # Calculate snap grid in seconds
            snap_seconds = self.snap_value * seconds_per_beat
            
            # Calculate visible snap divisions
            start_snap = max(0, int(visible_x_start / (self.px_per_sec * self.zoom_level * snap_seconds)))
            end_snap = int(visible_x_end / (self.px_per_sec * self.zoom_level * snap_seconds)) + 1
            
            for snap_idx in range(start_snap, end_snap):
                t = snap_idx * snap_seconds
                x = self._time_to_x(t)
                
                # Check if this is a bar (every beats_per_bar beats)
                is_bar = abs(t % seconds_per_bar) < 0.001
                # Check if this is a beat
                is_beat = abs(t % seconds_per_beat) < 0.001
                
                if is_bar:
                    # Bar line - strongest (blue)
                    color = "#3a5a8a"
                    width_line = 2
                elif is_beat:
                    # Beat line - medium (gray)
                    color = "#2a2a2a"
                    width_line = 1
                else:
                    # Subdivision line - subtle (dark gray, dashed)
                    color = "#1a1a1a"
                    width_line = 1
                    self._canvas.create_line(x, visible_y_start, x, visible_y_end, 
                                           fill=color, width=width_line, dash=(2, 4))
                    continue
                
                # Draw solid lines for bars and beats
                self._canvas.create_line(x, visible_y_start, x, visible_y_end, 
                                       fill=color, width=width_line)
        else:
            # Snap off - draw only bars and beats
            start_beat = max(0, int(visible_x_start / (self.px_per_sec * self.zoom_level * seconds_per_beat)))
            end_beat = int(visible_x_end / (self.px_per_sec * self.zoom_level * seconds_per_beat)) + 1
            
            for beat_idx in range(start_beat, end_beat):
                t = beat_idx * seconds_per_beat
                x = self._time_to_x(t)
                
                # Stronger lines every 4 beats (bars)
                if beat_idx % 4 == 0:
                    color = "#3a5a8a"
                    width_line = 2
                else:
                    color = "#2a2a2a"
                    width_line = 1
                    
                self._canvas.create_line(x, visible_y_start, x, visible_y_end, fill=color, width=width_line)
            
    def _draw_notes(self):
        """Draw all MIDI notes - optimized to draw only visible notes."""
        self._notes_ids.clear()
        
        # Get visible area for culling
        try:
            x_view = self._canvas.xview()
            y_view = self._canvas.yview()
            scroll_region = self._canvas.cget("scrollregion").split()
            if len(scroll_region) >= 4:
                total_width = float(scroll_region[2])
                total_height = float(scroll_region[3])
                visible_x_start = x_view[0] * total_width
                visible_x_end = x_view[1] * total_width
                visible_y_start = y_view[0] * total_height
                visible_y_end = y_view[1] * total_height
            else:
                raise ValueError
        except:
            visible_x_start = 0
            visible_x_end = 10000
            visible_y_start = 0
            visible_y_end = 1000
        
        clip_color = getattr(self.clip, 'color', '#22c55e') or '#22c55e'
        
        for note in getattr(self.clip, 'notes', []) or []:
            x0 = self._time_to_x(note.start)
            x1 = self._time_to_x(note.start + note.duration)
            y = self._pitch_to_y(int(note.pitch))
            
            # Cull notes outside visible area (with small margin)
            if x1 < visible_x_start - 50 or x0 > visible_x_end + 50:
                continue
            if y + self.NOTE_HEIGHT < visible_y_start - 20 or y > visible_y_end + 20:
                continue
            
            # Color based on selection and velocity
            if self._is_note_selected(note):
                fill_color = "#fbbf24"  # Gold for selected
                outline_color = "#f59e0b"
                width = 2
            else:
                # Vary brightness by velocity
                vel_factor = note.velocity / 127.0
                fill_color = self._adjust_color_brightness(clip_color, vel_factor)
                outline_color = "#064e3b"
                width = 1
            
            # Draw note rectangle
            rect_id = self._canvas.create_rectangle(
                x0, y + 1, x1, y + self.NOTE_HEIGHT - 1,
                fill=fill_color, outline=outline_color, width=width,
                tags="note"
            )
            
            self._notes_ids[rect_id] = note
            
            # Draw velocity indicator only if note is wide enough
            if x1 - x0 > 8:
                vel_height = max(2, (note.velocity / 127.0) * (self.NOTE_HEIGHT - 4))
                self._canvas.create_rectangle(
                    x0 + 2, y + self.NOTE_HEIGHT - vel_height - 1,
                    x0 + 6, y + self.NOTE_HEIGHT - 1,
                    fill="#10b981" if not self._is_note_selected(note) else "#fef3c7",
                    outline=""
                )
            
    def _draw_keyboard(self):
        """Draw the piano keyboard sidebar."""
        if self._keyboard_canvas is None:
            return
            
        self._keyboard_canvas.delete("all")
        
        # Get visible area
        try:
            y_view = self._canvas.yview()
            scroll_region = self._canvas.cget("scrollregion").split()
            total_height = float(scroll_region[3]) if len(scroll_region) >= 4 else 600
            
            y_start = int(y_view[0] * total_height)
            y_end = int(y_view[1] * total_height)
        except:
            y_start = 0
            y_end = 600
            
        # Configure keyboard canvas scroll region
        rows = self.pitch_max - self.pitch_min + 1
        kb_height = rows * self.NOTE_HEIGHT
        self._keyboard_canvas.configure(scrollregion=(0, 0, self.KEY_WIDTH, kb_height))
        
        # Sync with main canvas
        self._keyboard_canvas.yview_moveto(self._canvas.yview()[0])
        
        # Draw keys
        for p in range(self.pitch_min, self.pitch_max + 1):
            y = self._pitch_to_y(p)
            
            is_black_key = (p % 12) in (1, 3, 6, 8, 10)
            note_name = self._get_note_name(p)
            
            # Key colors
            if p in self._pressed_keys:
                key_color = "#3b82f6"  # Blue when pressed
                text_color = "#ffffff"
            elif is_black_key:
                key_color = "#374151"
                text_color = "#9ca3af"
            else:
                key_color = "#e5e7eb"
                text_color = "#1f2937"
            
            # Draw key
            self._keyboard_canvas.create_rectangle(
                0, y, self.KEY_WIDTH, y + self.NOTE_HEIGHT,
                fill=key_color, outline="#6b7280", width=1
            )
            
            # Draw note name on white keys and C notes
            if not is_black_key or p % 12 == 0:
                self._keyboard_canvas.create_text(
                    self.KEY_WIDTH - 8, y + self.NOTE_HEIGHT // 2,
                    text=note_name, anchor="e",
                    fill=text_color, font=("Segoe UI", 7)
                )
                
    def _draw_ruler(self, width):
        """Draw the time ruler with bars and beats."""
        if self._ruler_canvas is None:
            return
            
        self._ruler_canvas.delete("all")
        
        # Sync horizontal scroll with main canvas
        x_view = self._canvas.xview()
        self._ruler_canvas.configure(scrollregion=(0, 0, width, self.RULER_HEIGHT))
        self._ruler_canvas.xview_moveto(x_view[0])
        
        # Calculate beats per second - ALWAYS use current project BPM
        beats_per_minute = self._get_current_bpm()
        beats_per_second = beats_per_minute / 60.0
        seconds_per_beat = 60.0 / beats_per_minute
        
        # Get beats per bar from project time signature
        beats_per_bar = 4  # Default 4/4
        try:
            if self._project and hasattr(self._project, 'time_signature_num'):
                beats_per_bar = int(self._project.time_signature_num)
            elif hasattr(self.clip, 'project') and hasattr(self.clip.project, 'time_signature_num'):
                beats_per_bar = int(self.clip.project.time_signature_num)
        except Exception:
            pass
        
        # Calculate total bars to display (match canvas size calculation)
        try:
            clip_length = float(getattr(self.clip, 'duration', 4.0) or 4.0)
            notes = getattr(self.clip, 'notes', []) or []
            if notes:
                max_note_end = max((n.start + n.duration for n in notes), default=0.0)
                clip_length = max(clip_length, max_note_end)
            seconds_per_bar = self._get_bar_duration()
            bars_needed = int((clip_length / seconds_per_bar) + 0.999)
            total_bars = bars_needed + 2
            total_secs = total_bars * seconds_per_bar
        except:
            total_secs = 8.0
        total_beats = int(total_secs * beats_per_second) + 1
        
        for beat_idx in range(total_beats):
            t = beat_idx * seconds_per_beat
            x = self._time_to_x(t)
            
            # Check if this is a bar (every beats_per_bar beats)
            is_bar = (beat_idx % beats_per_bar) == 0
            
            if is_bar:
                # Bar marker - taller and thicker
                self._ruler_canvas.create_line(x, 0, x, self.RULER_HEIGHT,
                                              fill="#3b82f6", width=2)
                # Bar number
                bar_num = (beat_idx // beats_per_bar) + 1
                self._ruler_canvas.create_text(x + 3, 3, text=f"{bar_num}", anchor="nw",
                                              fill="#f5f5f5", font=("Segoe UI", 8, "bold"))
            else:
                # Beat marker - shorter
                self._ruler_canvas.create_line(x, self.RULER_HEIGHT - 8, x, self.RULER_HEIGHT,
                                              fill="#6b7280", width=1)
                # Beat number within bar
                beat_in_bar = (beat_idx % beats_per_bar) + 1
                self._ruler_canvas.create_text(x + 2, self.RULER_HEIGHT - 18, text=f".{beat_in_bar}",
                                              anchor="nw", fill="#9ca3af", font=("Segoe UI", 7))
        
        # Draw playhead marker on ruler
        if self._playhead_time >= 0:
            playhead_x = self._time_to_x(self._playhead_time)
            self._ruler_canvas.create_line(playhead_x, 0, playhead_x, self.RULER_HEIGHT,
                                          fill="#ef4444", width=2, tags="playhead")
            # Triangle at top
            self._ruler_canvas.create_polygon(
                playhead_x - 5, 0,
                playhead_x + 5, 0,
                playhead_x, 8,
                fill="#ef4444", outline="", tags="playhead"
            )



    # =============================================================================
    # COORDINATE CONVERSION
    # =============================================================================
    
    def _pitch_to_y(self, pitch: int) -> int:
        """Convert MIDI pitch to Y coordinate."""
        pitch = max(self.pitch_min, min(self.pitch_max, int(pitch)))
        row = self.pitch_max - pitch
        return int(row * self.NOTE_HEIGHT)
        
    def _y_to_pitch(self, y: int) -> int:
        """Convert Y coordinate to MIDI pitch."""
        row = int(y // self.NOTE_HEIGHT)
        pitch = self.pitch_max - row
        return max(self.pitch_min, min(self.pitch_max, pitch))
        
    def _time_to_x(self, time: float) -> int:
        """Convert time to X coordinate."""
        return int(time * self.px_per_sec * self.zoom_level)
        
    def _x_to_time(self, x: int) -> float:
        """Convert X coordinate to time."""
        time = x / (self.px_per_sec * self.zoom_level)
        if self.snap_enabled and self.snap_value > 0:
            time = round(time / self.snap_value) * self.snap_value
        return max(0.0, time)
        
    def _get_note_name(self, pitch: int) -> str:
        """Get note name from MIDI pitch."""
        notes = ['C', 'C#', 'D', 'D#', 'E', 'F', 'F#', 'G', 'G#', 'A', 'A#', 'B']
        octave = (pitch // 12) - 1
        note = notes[pitch % 12]
        return f"{note}{octave}"
        
    def _adjust_color_brightness(self, hex_color: str, factor: float) -> str:
        """Adjust color brightness by factor (0.0-1.0)."""
        try:
            # Remove # if present
            hex_color = hex_color.lstrip('#')
            
            # Convert to RGB
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            
            # Adjust brightness
            factor = max(0.3, min(1.0, factor))  # Clamp to reasonable range
            r = int(r * factor)
            g = int(g * factor)
            b = int(b * factor)
            
            # Convert back to hex
            return f"#{r:02x}{g:02x}{b:02x}"
        except:
            return hex_color
            
    # =============================================================================
    # MOUSE EVENT HANDLERS
    # =============================================================================
    
    def _on_mouse_down(self, event):
        """Handle mouse button down."""
        x = self._canvas.canvasx(event.x)
        y = self._canvas.canvasy(event.y)
        
        # Find clicked note
        clicked_note = self._find_note_at(x, y)
        
        if clicked_note:
            # Play note preview (headplay) when clicking on a note
            self._play_note_preview(clicked_note.pitch, 0.15)
            
            # Check if clicking on edge for resize
            note_x0 = self._time_to_x(clicked_note.start)
            note_x1 = self._time_to_x(clicked_note.start + clicked_note.duration)
            
            edge_threshold = 5
            
            if abs(x - note_x0) < edge_threshold:
                self._drag_mode = 'resize_left'
                if not self._is_note_selected(clicked_note):
                    if not event.state & 0x0004:  # Ctrl not pressed
                        self._selected_notes.clear()
                    self._add_to_selection(clicked_note)
            elif abs(x - note_x1) < edge_threshold:
                self._drag_mode = 'resize_right'
                if not self._is_note_selected(clicked_note):
                    if not event.state & 0x0004:
                        self._selected_notes.clear()
                    self._add_to_selection(clicked_note)
            else:
                # Move mode
                self._drag_mode = 'move'
                if not self._is_note_selected(clicked_note):
                    if not event.state & 0x0004:  # Ctrl not pressed
                        self._selected_notes.clear()
                    self._add_to_selection(clicked_note)
                    
            # Store original state for dragging
            self._drag_start_pos = (x, y)
            self._drag_notes_original = [
                (n, n.start, n.duration, n.pitch) 
                for n in self._selected_notes
            ]
            
            self._redraw()
        else:
            # Start box selection or create new note
            self._drag_mode = 'box_select'
            self._drag_start_pos = (x, y)
            
            if not event.state & 0x0004:  # Ctrl not pressed
                self._selected_notes.clear()
                
            self._redraw()
            
    def _on_mouse_drag(self, event):
        """Handle mouse drag."""
        if not self._drag_mode or not self._drag_start_pos:
            return
            
        x = self._canvas.canvasx(event.x)
        y = self._canvas.canvasy(event.y)
        
        if self._drag_mode == 'box_select':
            self._update_box_selection(x, y)
        elif self._drag_mode == 'move':
            self._move_selected_notes(x, y)
        elif self._drag_mode in ('resize_left', 'resize_right'):
            self._resize_selected_notes(x)
            
        self._schedule_redraw()  # Use throttled redraw during drag for better performance
        
    def _on_mouse_up(self, event):
        """Handle mouse button release."""
        if self._drag_mode == 'box_select':
            # Finalize box selection
            self._finalize_box_selection()
        elif self._drag_mode in ('move', 'resize_left', 'resize_right'):
            # Save undo state
            self._save_undo_state('edit')
            
        self._drag_mode = None
        self._drag_start_pos = None
        self._drag_notes_original = []
        
        if self._box_select_rect:
            self._canvas.delete(self._box_select_rect)
            self._box_select_rect = None
            
        self._redraw()
        
    def _on_right_click(self, event):
        """Handle right-click to delete note or show context menu."""
        x = self._canvas.canvasx(event.x)
        y = self._canvas.canvasy(event.y)
        
        clicked_note = self._find_note_at(x, y)
        
        if clicked_note:
            self._save_undo_state('delete')
            try:
                self.clip.notes.remove(clicked_note)
                if self._is_note_selected(clicked_note):
                    self._remove_from_selection(clicked_note)
            except ValueError:
                pass
            self._redraw()
            self._update_status(f"Deleted note {self._get_note_name(clicked_note.pitch)}")
        
    def _on_double_click(self, event):
        """Handle double-click to add note."""
        x = self._canvas.canvasx(event.x)
        y = self._canvas.canvasy(event.y)
        
        # Don't add if clicked on existing note
        if self._find_note_at(x, y):
            return
            
        time = self._x_to_time(x)
        pitch = self._y_to_pitch(y)
        
        # Create new note
        try:
            from src.midi.note import MidiNote
        except Exception:
            return
            
        duration = self.snap_value if self.snap_value > 0 else 0.25
        new_note = MidiNote(pitch=pitch, start=time, duration=duration, velocity=100)
        
        self._save_undo_state('add')
        self.clip.notes.append(new_note)
        
        self._selected_notes.clear()
        self._selected_notes.append(new_note)
        
        # Play note preview (headplay)
        self._play_note_preview(pitch, duration)
        
        self._redraw()
        self._update_status(f"Added note {self._get_note_name(pitch)} at {time:.2f}s")
        
    def _on_mouse_move(self, event):
        """Handle mouse movement for cursor feedback."""
        x = self._canvas.canvasx(event.x)
        y = self._canvas.canvasy(event.y)
        
        note = self._find_note_at(x, y)
        
        if note:
            # Check if near edge
            note_x0 = self._time_to_x(note.start)
            note_x1 = self._time_to_x(note.start + note.duration)
            
            if abs(x - note_x0) < 5 or abs(x - note_x1) < 5:
                self._canvas.config(cursor="sb_h_double_arrow")
            else:
                self._canvas.config(cursor="hand2")
                
            # Show note info
            note_name = self._get_note_name(note.pitch)
            self._update_status(
                f"Note: {note_name} | Start: {note.start:.3f}s | "
                f"Duration: {note.duration:.3f}s | Velocity: {note.velocity}"
            )
        else:
            self._canvas.config(cursor="")
            time = self._x_to_time(x)
            pitch = self._y_to_pitch(y)
            note_name = self._get_note_name(pitch)
            self._update_status(f"Position: {time:.3f}s | Pitch: {note_name}")
            
    def _on_mouse_wheel(self, event):
        """Handle mouse wheel for vertical scrolling."""
        if event.delta > 0:
            self._canvas.yview_scroll(-1, "units")
            self._keyboard_canvas.yview_scroll(-1, "units")
        else:
            self._canvas.yview_scroll(1, "units")
            self._keyboard_canvas.yview_scroll(1, "units")
        # Ensure immediate redraw during wheel scrolling
        try:
            self._redraw()
        except Exception:
            pass
            
    def _on_ctrl_mouse_wheel(self, event):
        """Handle Ctrl+mouse wheel for horizontal zoom."""
        if event.delta > 0:
            self._zoom_in()
        else:
            self._zoom_out()

    # =============================================================================
    # NOTE MANIPULATION
    # =============================================================================
    
    def _find_note_at(self, x: int, y: int):
        """Find note at given coordinates."""
        time = self._x_to_time(x)
        pitch = self._y_to_pitch(y)
        
        for note in getattr(self.clip, 'notes', []) or []:
            if (note.start <= time <= note.start + note.duration and
                note.pitch == pitch):
                return note
        return None
        
    def _update_box_selection(self, x: int, y: int):
        """Update box selection rectangle."""
        if not self._drag_start_pos:
            return
            
        x0, y0 = self._drag_start_pos
        
        # Draw selection box
        if self._box_select_rect:
            self._canvas.delete(self._box_select_rect)
            
        self._box_select_rect = self._canvas.create_rectangle(
            x0, y0, x, y,
            outline="#3b82f6", width=2, dash=(4, 4)
        )
        
    def _finalize_box_selection(self):
        """Finalize box selection and select notes within."""
        if not self._drag_start_pos:
            return
            
        try:
            x = self._canvas.canvasx(self._canvas.winfo_pointerx() - self._canvas.winfo_rootx())
            y = self._canvas.canvasy(self._canvas.winfo_pointery() - self._canvas.winfo_rooty())
        except:
            return
        
        x0, y0 = self._drag_start_pos
        x0, x = (min(x0, x), max(x0, x))
        y0, y = (min(y0, y), max(y0, y))
        
        t0 = self._x_to_time(x0)
        t1 = self._x_to_time(x)
        p0 = self._y_to_pitch(y0)
        p1 = self._y_to_pitch(y)
        p0, p1 = (min(p0, p1), max(p0, p1))
        
        # Select notes in box
        for note in getattr(self.clip, 'notes', []) or []:
            if (t0 <= note.start <= t1 and p0 <= note.pitch <= p1):
                self._add_to_selection(note)

    def _move_selected_notes(self, x: int, y: int):
        """Move selected notes."""
        if not self._drag_start_pos or not self._drag_notes_original:
            return
            
        x0, y0 = self._drag_start_pos
        dx = x - x0
        dy = y - y0
        
        dt = dx / (self.px_per_sec * self.zoom_level)
        dp = -int(dy // self.NOTE_HEIGHT)
        
        if self.snap_enabled and self.snap_value > 0:
            dt = round(dt / self.snap_value) * self.snap_value
        
        # Update each note based on its original state
        for note_data in self._drag_notes_original:
            note, orig_start, orig_dur, orig_pitch = note_data
            
            note.start = max(0.0, orig_start + dt)
            note.pitch = max(0, min(127, orig_pitch + dp))
                
    def _resize_selected_notes(self, x: int):
        """Resize selected notes."""
        if not self._drag_start_pos or not self._drag_notes_original:
            return
            
        x0, _ = self._drag_start_pos
        dx = x - x0
        dt = dx / (self.px_per_sec * self.zoom_level)
        
        if self.snap_enabled and self.snap_value > 0:
            dt = round(dt / self.snap_value) * self.snap_value
        
        # Update each note based on its original state
        for note_data in self._drag_notes_original:
            note, orig_start, orig_dur, orig_pitch = note_data
            
            if self._drag_mode == 'resize_left':
                # Resize from left (change start and duration)
                new_start = max(0.0, orig_start + dt)
                duration_change = orig_start - new_start
                note.start = new_start
                note.duration = max(0.0625, orig_dur + duration_change)
            else:  # resize_right
                # Resize from right (change duration)
                note.duration = max(0.0625, orig_dur + dt)
                    
    # =============================================================================
    # EDITING ACTIONS
    # =============================================================================
    
    def _delete_selected(self):
        """Delete selected notes."""
        if not self._selected_notes:
            return
            
        self._save_undo_state('delete')
        
        for note in list(self._selected_notes):
            try:
                self.clip.notes.remove(note)
            except ValueError:
                pass
                
        count = len(self._selected_notes)
        self._selected_notes.clear()
        self._redraw()
        self._update_status(f"Deleted {count} note(s)")
        
    def _copy_selected(self):
        """Copy selected notes to clipboard."""
        if not self._selected_notes:
            return
            
        self._clipboard = [
            {
                'pitch': n.pitch,
                'start': n.start,
                'duration': n.duration,
                'velocity': n.velocity
            }
            for n in self._selected_notes
        ]
        
        self._update_status(f"Copied {len(self._clipboard)} note(s)")
        
    def _cut_selected(self):
        """Cut selected notes to clipboard."""
        self._copy_selected()
        self._delete_selected()
        
    def _paste_clipboard(self):
        """Paste notes from clipboard."""
        if not self._clipboard:
            return
            
        try:
            from src.midi.note import MidiNote
        except Exception:
            return
            
        self._save_undo_state('add')
        
        # Find earliest start time in clipboard
        min_start = min(n['start'] for n in self._clipboard)
        
        # Paste at current time (or 0)
        paste_time = 0.0
        
        self._selected_notes.clear()
        
        for note_data in self._clipboard:
            new_note = MidiNote(
                pitch=note_data['pitch'],
                start=paste_time + (note_data['start'] - min_start),
                duration=note_data['duration'],
                velocity=note_data['velocity']
            )
            self.clip.notes.append(new_note)
            self._selected_notes.append(new_note)
            
        self._redraw()
        self._update_status(f"Pasted {len(self._clipboard)} note(s)")
        
    def _duplicate_selected(self):
        """Duplicate selected notes."""
        if not self._selected_notes:
            return
            
        try:
            from src.midi.note import MidiNote
        except Exception:
            return
            
        self._save_undo_state('add')
        
        # Find the rightmost note
        max_end = max(n.start + n.duration for n in self._selected_notes)
        
        new_notes = []
        for note in self._selected_notes:
            new_note = MidiNote(
                pitch=note.pitch,
                start=note.start + (max_end - min(n.start for n in self._selected_notes)),
                duration=note.duration,
                velocity=note.velocity
            )
            self.clip.notes.append(new_note)
            new_notes.append(new_note)
            
        self._selected_notes.clear()
        self._selected_notes.extend(new_notes)
        
        self._redraw()
        self._update_status(f"Duplicated {len(new_notes)} note(s)")
        
    def _select_all(self):
        """Select all notes."""
        self._selected_notes = list(getattr(self.clip, 'notes', []) or [])
        self._redraw()
        self._update_status(f"Selected {len(self._selected_notes)} note(s)")
        
    def _clear_selection(self):
        """Clear note selection."""
        self._selected_notes.clear()
        self._redraw()
        self._update_status("Selection cleared")
        
    # =============================================================================
    # UNDO/REDO
    # =============================================================================
    
    def _save_undo_state(self, action_type: str):
        """Save current state to undo stack."""
        try:
            from src.midi.note import MidiNote
        except Exception:
            return
            
        # Create snapshot of all notes
        notes_snapshot = [
            MidiNote(
                pitch=n.pitch,
                start=n.start,
                duration=n.duration,
                velocity=n.velocity
            )
            for n in getattr(self.clip, 'notes', []) or []
        ]
        
        action = EditAction(action_type=action_type, notes_state=notes_snapshot)
        self._undo_stack.append(action)
        
        # Limit stack size
        if len(self._undo_stack) > self._max_undo:
            self._undo_stack.pop(0)
            
        # Clear redo stack
        self._redo_stack.clear()
        
    def _undo(self):
        """Undo last action."""
        if not self._undo_stack:
            self._update_status("Nothing to undo")
            return
            
        try:
            from src.midi.note import MidiNote
        except Exception:
            return
            
        # Save current state to redo
        current_snapshot = [
            MidiNote(
                pitch=n.pitch,
                start=n.start,
                duration=n.duration,
                velocity=n.velocity
            )
            for n in getattr(self.clip, 'notes', []) or []
        ]
        
        action = self._undo_stack.pop()
        self._redo_stack.append(EditAction(action_type='redo', notes_state=current_snapshot))
        
        # Restore state
        self.clip.notes = action.notes_state
        self._selected_notes.clear()
        
        self._redraw()
        self._update_status(f"Undo: {action.action_type}")
        
    def _redo(self):
        """Redo last undone action."""
        if not self._redo_stack:
            self._update_status("Nothing to redo")
            return
            
        try:
            from src.midi.note import MidiNote
        except Exception:
            return
            
        # Save current state to undo
        current_snapshot = [
            MidiNote(
                pitch=n.pitch,
                start=n.start,
                duration=n.duration,
                velocity=n.velocity
            )
            for n in getattr(self.clip, 'notes', []) or []
        ]
        
        action = self._redo_stack.pop()
        self._undo_stack.append(EditAction(action_type='undo', notes_state=current_snapshot))
        
        # Restore state
        self.clip.notes = action.notes_state
        self._selected_notes.clear()
        
        self._redraw()
        self._update_status("Redo")
        
    # =============================================================================
    # TOOLBAR ACTIONS
    # =============================================================================
    
    def _set_draw_mode(self):
        """Set draw mode (double-click to add notes)."""
        self._update_status("Draw mode: Double-click to add notes")
        
    def _set_select_mode(self):
        """Set select mode (default)."""
        self._update_status("Select mode: Click to select, drag to move")
        
    def _toggle_headplay(self):
        """Toggle headplay on/off"""
        self._headplay_enabled = not self._headplay_enabled
        self._update_headplay_button()
    
    def _update_headplay_button(self):
        """Update headplay button appearance"""
        if self._headplay_enabled:
            self._headplay_btn.config(bg="#10b981", fg="#ffffff")
        else:
            self._headplay_btn.config(bg="#3a3a3a", fg="#a0a0a0")
    
    def _zoom_in(self):
        """Zoom in horizontally."""
        self.zoom_level = min(4.0, self.zoom_level * 1.2)
        self._zoom_label.config(text=f"{int(self.zoom_level * 100)}%")
        self._redraw()
        self._update_status(f"Zoom: {int(self.zoom_level * 100)}%")
        
    def _zoom_out(self):
        """Zoom out horizontally."""
        self.zoom_level = max(0.25, self.zoom_level / 1.2)
        self._zoom_label.config(text=f"{int(self.zoom_level * 100)}%")
        self._redraw()
        self._update_status(f"Zoom: {int(self.zoom_level * 100)}%")
        
    def _update_status(self, message: str):
        """Update status bar message."""
        if self._status_bar:
            self._status_bar.config(text=message)
