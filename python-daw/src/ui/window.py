"""Main window for the Digital Audio Workstation - Refactored OOP version."""

try:
    import tkinter as tk
    from tkinter import ttk, messagebox, filedialog
except Exception:  # pragma: no cover
    tk = None
    ttk = None
    messagebox = None
    filedialog = None

from .timeline_canvas import TimelineCanvas
from .track_controls import TrackControls
from .menu_manager import MenuManager
from .toolbar_manager import ToolbarManager
from .theme_manager import ThemeManager
from .dialogs.add_track_dialog import AddTrackDialog
from .context_menus import ClipContextMenu


class MainWindow:
    """Main application window managing the DAW interface with OOP architecture."""
    
    def __init__(self, project=None, mixer=None, transport=None, timeline=None, player=None):
        self.title = "Digital Audio Workstation"
        self.is_open = False
        self.project = project
        self.mixer = mixer
        self.transport = transport
        self.timeline = timeline
        self.player = player
        
        # UI components
        self._root = None
        self._status = None
        self._zoom_label = None
        
        # Component managers (OOP refactoring)
        self._timeline_canvas = None
        self._track_controls = None
        self._menu_manager = None
        self._toolbar_manager = None
        self._clip_menu = None
        
        # Update jobs
        self._time_job = None
        self._meter_job = None
        
        # Recent files tracking
        self._recent_files = []  # List of recently imported files
        
        # Project file tracking
        self._project_file_path = None  # Current project file path

    def show(self):
        """Show the main window."""
        if tk is None:
            # Fallback to console mode
            self.is_open = True
            print(f"{self.title} (console mode) is now open.")
            return

        try:
            self._root = tk.Tk()
        except Exception as e:
            # Fallback to console mode if GUI cannot be created
            print(f"Warning: GUI not available ({e}). Falling back to console mode.")
            self.is_open = True
            print(f"{self.title} (console mode) is now open.")
            return

        self._root.title(self.title)
        self._root.geometry("1200x700")
        self._root.configure(bg="#1e1e1e")

        # Setup UI components
        self._setup_theme()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_main_layout()
        self._setup_status_bar()
        self._bind_keys()
        
        # Prepare context menu helper
        self._clip_menu = ClipContextMenu(
            self._root,
            on_delete=self._delete_selected_clips,
            on_duplicate=self._duplicate_selected_clip,
            on_properties=self._show_clip_properties,
            on_copy=self._copy_selection,
            on_paste=self._paste_clips
        )
        
        self.is_open = True
        print("GUI window created. If you don't see it, check the taskbar and ensure it's not behind other windows.")

    def _setup_theme(self):
        """Setup the professional dark theme."""
        ThemeManager(self._root).apply_dark_theme()

    def _setup_menu(self):
        """Setup the menu bar using MenuManager."""
        callbacks = {
            'new_project': self._new_project,
            'open_project': self._open_project,
            'save_project': self._save_project,
            'save_project_as': self._save_project_as,
            'import_audio': self._import_audio_dialog,
            'browse_audio': self._browse_audio_files,
            'export_audio': self._export_audio_dialog,
            'get_recent_files': self._get_recent_files,
            'import_recent': self._import_recent_file,
            'exit': self.close,
            'duplicate_loop': self._duplicate_loop,
            'delete_clip': self._delete_selected_clip,
            'zoom_in': lambda: self._zoom(1.25),
            'zoom_out': lambda: self._zoom(0.8),
            'zoom_reset': self._zoom_reset,
            'play': self._on_play,
            'stop': self._on_stop,
        }
        
        self._menu_manager = MenuManager(self._root, callbacks)
        self._menu_manager.build_menu()

    def _setup_toolbar(self):
        """Setup the toolbar using ToolbarManager."""
        callbacks = {
            'play': self._on_play,
            'stop': self._on_stop,
            'zoom_in': lambda: self._zoom(1.25),
            'zoom_out': lambda: self._zoom(0.8),
            'zoom_reset': self._zoom_reset,
            'loop_toggle': self._on_loop_toggle,
            'loop_start': self._set_loop_start,
            'loop_end': self._set_loop_end,
            'bpm_change': self._on_bpm_change,
            'snap_toggle': self._on_snap_toggle,
            'grid_change': self._on_grid_change,
        }
        
        self._toolbar_manager = ToolbarManager(self._root, self.project, callbacks)
        self._toolbar_manager.build_toolbar()
        
        # Show hint for loop selection in status bar after a brief delay
        if self._root and self._status:
            self._root.after(1000, lambda: self._status.set("💡 Shift+Drag to set loop | Drag loop markers to adjust"))

    def _setup_main_layout(self):
        """Setup the main layout with sidebar and timeline."""
        # Main container
        main_container = ttk.Frame(self._root)
        main_container.pack(fill="both", expand=True)
        
        # LEFT SIDEBAR (300px width)
        sidebar = self._create_sidebar(main_container)
        
        # RIGHT SIDE: Timeline area
        timeline_container = ttk.Frame(main_container)
        timeline_container.pack(fill="both", expand=True, side="left")
        
        # Create timeline canvas
        self._timeline_canvas = TimelineCanvas(
            timeline_container,
            self.project,
            self.mixer,
            self.timeline,
            self.player
        )
        
        # Bind context menu to timeline
        if self._timeline_canvas.canvas:
            self._timeline_canvas.canvas.bind('<Button-3>', self._on_timeline_right_click)
        
        # Initial draw
        self._timeline_canvas.redraw()
        
        # Populate tracks
        self._track_controls.populate_tracks(self.timeline)

    def _create_sidebar(self, parent):
        """Create the left sidebar with track controls."""
        sidebar = ttk.Frame(parent, style="Sidebar.TFrame", width=300)
        sidebar.pack(fill="y", side="left")
        sidebar.pack_propagate(False)
        
        # Project info header
        project_name = getattr(self.project, "name", "Untitled Project")
        proj_header = ttk.Frame(sidebar, style="Sidebar.TFrame")
        proj_header.pack(fill="x", padx=12, pady=(8, 4))
        ttk.Label(
            proj_header, text=project_name,
            style="Sidebar.TLabel",
            font=("Segoe UI", 11, "bold")
        ).pack(anchor="w")
        
        # Add track button
        btn_container = ttk.Frame(sidebar, style="Sidebar.TFrame")
        btn_container.pack(fill="x", padx=12, pady=(4, 4))
        ttk.Button(
            btn_container, text="+",
            command=self._add_track_dialog,
            style="Tool.TButton", width=3
        ).pack(side="left")
        
        # Create track controls
        self._track_controls = TrackControls(
            sidebar,
            self.mixer,
            timeline=self.timeline,
            project=self.project,
            redraw_cb=lambda: self._timeline_canvas.redraw() if self._timeline_canvas else None,
        )
        self._track_controls.build_ui()
        
        return sidebar

    def _setup_status_bar(self):
        """Setup the status bar at the bottom."""
        status_bar = ttk.Frame(self._root, style="Toolbar.TFrame", height=28)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)
        
        self._status = tk.StringVar(value="● Ready")
        status_lbl = ttk.Label(status_bar, textvariable=self._status, style="Status.TLabel")
        status_lbl.pack(side="left", padx=8)
        
        zoom_info = ttk.Label(status_bar, text="Zoom: 1.00x", style="Status.TLabel")
        zoom_info.pack(side="right", padx=8)
        self._zoom_label = zoom_info

    def _bind_keys(self):
        """Bind keyboard shortcuts."""
        if self._root is None:
            return
        try:
            self._root.bind('<space>', self._toggle_playback)
            self._root.bind('<Control-n>', lambda e: self._new_project())  # Ctrl+N for New Project
            self._root.bind('<Control-o>', lambda e: self._open_project())  # Ctrl+O for Open
            self._root.bind('<Control-s>', lambda e: self._save_project())  # Ctrl+S for Save
            self._root.bind('<Control-Shift-S>', lambda e: self._save_project_as())  # Ctrl+Shift+S for Save As
            self._root.bind('<Control-e>', lambda e: self._export_audio_dialog())  # Ctrl+E for Export Audio
            self._root.bind('+', lambda e: self._zoom(1.25))
            self._root.bind('-', lambda e: self._zoom(0.8))
            self._root.bind('0', lambda e: self._zoom_reset())
            self._root.bind('<Control-d>', lambda e: self._duplicate_loop())  # Ctrl+D to duplicate loop
            self._root.bind('<Control-c>', lambda e: self._copy_selection())  # Ctrl+C to copy clips
            self._root.bind('<Control-v>', lambda e: self._paste_clips())  # Ctrl+V to paste clips
            self._root.bind('<Control-Shift-C>', lambda e: self._copy_loop())  # Ctrl+Shift+C to copy loop
            self._root.bind('<Control-Shift-V>', lambda e: self._paste_loop())  # Ctrl+Shift+V to paste loop
            self._root.bind('<Delete>', lambda e: self._delete_selected_clips())  # Delete key
        except Exception:
            pass

    def _toggle_playback(self, event=None):
        """Toggle play/stop."""
        if self.player and hasattr(self.player, 'is_playing'):
            if not self.player.is_playing():
                self._on_play()
            else:
                self._on_stop()

    # Transport control methods
    def _on_play(self):
        """Handle play button."""
        # Protection: check if already playing before starting
        if self.player is not None and hasattr(self.player, "is_playing"):
            if self.player.is_playing():
                print("Window: Already playing, ignoring play request.")
                return
        
        if self.transport is not None:
            try:
                self.transport.play()
                if self._status:
                    self._status.set("▶ Playing")
            except Exception as e:
                print(f"Play error: {e}")
        
        if self.player is not None and hasattr(self.player, "is_playing"):
            self._schedule_time_update()
            self._schedule_meter_update()

    def _on_stop(self):
        """Handle stop button."""
        if self.transport is not None:
            try:
                self.transport.stop()
                if self._status:
                    self._status.set("■ Stopped")
            except Exception as e:
                print(f"Stop error: {e}")
        
        if self._root is not None:
            try:
                self._root.after_cancel(self._time_job)
            except Exception:
                pass

    def _on_loop_toggle(self):
        """Toggle loop on/off."""
        if self.player is None:
            return
        
        enabled = self._toolbar_manager.get_loop_enabled()
        loop_info = self.player.get_loop()
        
        # Se il loop viene attivato ma i punti sono invalidi, imposta valori di default
        if enabled and loop_info[1] >= loop_info[2]:
            # Imposta loop da posizione corrente a 4 secondi dopo
            current = self.player.get_current_time()
            self.player.set_loop(True, current, current + 4.0)
            loop_start, loop_end = current, current + 4.0
        else:
            self.player.set_loop(enabled, loop_info[1], loop_info[2])
            loop_start, loop_end = loop_info[1], loop_info[2]
        
        # Aggiorna UI
        if self._timeline_canvas:
            self._timeline_canvas.redraw()
        
        # Feedback visivo migliorato
        if enabled:
            status = f"🔁 Loop ON [{loop_start:.2f}s - {loop_end:.2f}s]"
        else:
            status = "Loop OFF"
        
        if self._status:
            self._status.set(status)
        print(status)

    def _set_loop_start(self):
        """Set loop start to current playback position."""
        if self.player is None:
            return
        
        # Usa la posizione corrente del playback
        current_time = self.player.get_current_time()
        if self._timeline_canvas:
            current_time = self._timeline_canvas.snap_time(current_time)
        
        # Ottieni il loop attuale
        loop_info = self.player.get_loop()
        loop_enabled, loop_start, loop_end = loop_info
        
        # Se il loop non è configurato o ha valori invalidi, crea uno nuovo
        if not loop_enabled or loop_start >= loop_end:
            # Crea un loop di 4 secondi dalla posizione corrente
            new_start = current_time
            new_end = current_time + 4.0
        else:
            # Modifica solo il punto di inizio, mantieni la fine
            new_start = current_time
            new_end = loop_end
            
            # Se il nuovo inizio è dopo la fine, sposta la fine
            if new_start >= new_end:
                new_end = new_start + 0.5
        
        self.player.set_loop(True, new_start, new_end)
        
        # Aggiorna checkbox
        if self._toolbar_manager:
            self._toolbar_manager.set_loop_enabled(True)
        
        if self._timeline_canvas:
            self._timeline_canvas.redraw()
        
        status = f"🔁 Loop start set: {new_start:.3f}s (end: {new_end:.3f}s)"
        if self._status:
            self._status.set(status)
        print(status)

    def _set_loop_end(self):
        """Set loop end to current playback position."""
        if self.player is None:
            return
        
        current_time = self.player.get_current_time()
        if self._timeline_canvas:
            current_time = self._timeline_canvas.snap_time(current_time)
        
        loop_info = self.player.get_loop()
        loop_start = loop_info[1]
        
        # Assicura che end sia sempre dopo start
        if current_time <= loop_start:
            loop_start = max(0, current_time - 1.0)
        
        self.player.set_loop(True, loop_start, current_time)
        
        # Aggiorna checkbox se necessario
        if self._toolbar_manager:
            self._toolbar_manager.set_loop_enabled(True)
        
        if self._timeline_canvas:
            self._timeline_canvas.redraw()
        
        status = f"🔁 Loop end: {loop_start:.3f}s → {current_time:.3f}s"
        if self._status:
            self._status.set(status)
        print(status)

    def _on_bpm_change(self):
        """Update project BPM and adjust loop points and clip positions."""
        if self.project is None or self._toolbar_manager is None:
            return
        
        try:
            old_bpm = self.project.bpm
            new_bpm = self._toolbar_manager.get_bpm()
            
            if abs(old_bpm - new_bpm) < 0.01:
                return
            
            # Store loop points in musical time
            loop_enabled = False
            loop_start_bars = 0.0
            loop_end_bars = 0.0
            
            if self.player is not None:
                try:
                    loop_enabled, loop_start_sec, loop_end_sec = self.player.get_loop()
                    loop_start_bars = self.project.seconds_to_bars(loop_start_sec)
                    loop_end_bars = self.project.seconds_to_bars(loop_end_sec)
                except Exception:
                    pass
            
            # Convert all clip positions to musical time (bars) before changing BPM
            clip_positions = []  # (track_idx, clip, start_bars, duration_bars)
            if self.timeline is not None:
                try:
                    for track_idx, clip in self.timeline.all_placements():
                        start_bars = self.project.seconds_to_bars(clip.start_time)
                        duration_bars = self.project.seconds_to_bars(clip.length_seconds)
                        clip_positions.append((track_idx, clip, start_bars, duration_bars))
                except Exception as e:
                    print(f"Error storing clip positions: {e}")
            
            # Update BPM
            self.project.bpm = float(new_bpm)
            
            # Convert clip positions back to seconds with new BPM
            clips_adjusted = 0
            for track_idx, clip, start_bars, duration_bars in clip_positions:
                try:
                    new_start_time = self.project.bars_to_seconds(start_bars)
                    new_duration = self.project.bars_to_seconds(duration_bars)
                    
                    # Update clip timing
                    clip.start_time = new_start_time
                    # Only update duration if it was explicitly set (not derived from buffer)
                    if clip.duration is not None:
                        clip.duration = new_duration
                    
                    clips_adjusted += 1
                except Exception as e:
                    print(f"Error adjusting clip {clip.name}: {e}")
            
            # Convert loop points back
            if self.player is not None and loop_enabled:
                try:
                    new_loop_start = self.project.bars_to_seconds(loop_start_bars)
                    new_loop_end = self.project.bars_to_seconds(loop_end_bars)
                    self.player.set_loop(loop_enabled, new_loop_start, new_loop_end)
                    print(f"🔁 Loop adjusted: {loop_start_sec:.3f}s → {new_loop_start:.3f}s, {loop_end_sec:.3f}s → {new_loop_end:.3f}s")
                except Exception as e:
                    print(f"Loop adjustment error: {e}")
            
            if self._timeline_canvas:
                self._timeline_canvas.redraw()
            
            print(f"♪ BPM changed: {old_bpm:.1f} → {new_bpm}")
            if clips_adjusted > 0:
                print(f"✓ {clips_adjusted} clip(s) adjusted to maintain musical grid alignment")
        except Exception as e:
            print(f"BPM change error: {e}")

    def _on_snap_toggle(self):
        """Toggle snap to grid."""
        if self._toolbar_manager and self._timeline_canvas:
            enabled = self._toolbar_manager.get_snap_enabled()
            self._timeline_canvas.set_snap(enabled)
            status = "ON" if enabled else "OFF"
            print(f"Snap to grid: {status}")

    def _on_grid_change(self, event=None):
        """Change grid division."""
        if self._toolbar_manager and self._timeline_canvas:
            division = self._toolbar_manager.get_grid_division()
            self._timeline_canvas.set_grid_division(division)

    # Zoom methods
    def _zoom(self, factor):
        """Zoom timeline."""
        if self._timeline_canvas:
            zoom_val = self._timeline_canvas.zoom(factor)
            if self._zoom_label:
                self._zoom_label.config(text=f"Zoom: {zoom_val:.2f}x")
            if self._status:
                self._status.set(f"● Zoom: {zoom_val:.2f}x")

    def _zoom_reset(self):
        """Reset zoom."""
        if self._timeline_canvas:
            self._timeline_canvas.zoom_reset()
            if self._zoom_label:
                self._zoom_label.config(text="Zoom: 1.00x")
            if self._status:
                self._status.set("● Ready")

    # Update methods
    def _schedule_time_update(self):
        """Schedule time display updates."""
        if self._root is None or self._toolbar_manager is None:
            return
        
        try:
            cur = getattr(self.player, "_current_time", 0.0)
            self._toolbar_manager.update_time(cur)
            
            if self._timeline_canvas:
                self._timeline_canvas.update_cursor(cur)
        except Exception:
            pass
        
        self._time_job = self._root.after(100, self._schedule_time_update)

    def _schedule_meter_update(self):
        """Schedule meter updates."""
        if self._root is None or self._track_controls is None:
            return
        
        self._track_controls.update_meters(self.player)
        self._meter_job = self._root.after(100, self._schedule_meter_update)

    # Track/Clip management methods
    def _add_dummy_clip(self):
        """Add a short sine wave clip at current time on selected track."""
        if self.timeline is None:
            return
        
        track_idx = self._track_controls.get_current_track_index()
        if track_idx is None:
            if self._status:
                self._status.set("⚠ Select a track first")
            return
        
        import math
        sr = 44100
        seconds = 0.25
        n = int(sr * seconds)
        buf = [math.sin(2 * math.pi * 440 * (i / sr)) * 0.2 for i in range(n)]
        
        cur = 0.0
        try:
            cur = float(getattr(self.player, "_current_time", 0.0))
        except Exception:
            pass
        
        from src.audio.clip import AudioClip
        self.timeline.add_clip(track_idx, AudioClip("sine440", buf, sr, start_time=cur))
        
        self._track_controls.populate_tracks(self.timeline)
        if self._timeline_canvas:
            self._timeline_canvas.redraw()
        
        if self._status:
            track_name = self.mixer.tracks[track_idx].get("name", f"Track {track_idx+1}")
            self._status.set(f"✓ Clip added to {track_name}")

    def _import_audio_dialog(self):
        """Import audio file (WAV, MP3, FLAC, OGG, etc.) and add to selected track."""
        if self.timeline is None or self.mixer is None or filedialog is None:
            return
        
        track_idx = self._track_controls.get_current_track_index()
        if track_idx is None:
            if self._status:
                self._status.set("⚠ Select a track first")
            return
        
        try:
            # Get supported formats from audio_io utility
            from src.utils.audio_io import get_supported_formats, load_audio_file, get_audio_info
            
            filetypes = get_supported_formats()
            
            file_path = filedialog.askopenfilename(
                title="Import Audio",
                filetypes=filetypes
            )
            
            if not file_path:
                return
            
            # Show loading status
            if self._status:
                self._status.set("⏳ Loading audio file...")
            
            try:
                # Get file info first (fast)
                import os
                clip_name = os.path.splitext(os.path.basename(file_path))[0]
                
                try:
                    info = get_audio_info(file_path)
                    duration = info.get('duration', 0)
                    original_sr = info.get('sample_rate', 44100)
                    
                    # Show info dialog for long files
                    if duration > 60:  # More than 1 minute
                        if messagebox:
                            proceed = messagebox.askyesno(
                                "Large File",
                                f"File duration: {duration:.1f} seconds\n"
                                f"Sample rate: {original_sr} Hz\n"
                                f"This may take a moment to load.\n\n"
                                f"Continue?"
                            )
                            if not proceed:
                                if self._status:
                                    self._status.set("● Ready")
                                return
                except Exception:
                    pass  # Info not available, proceed anyway
                
                # Load the audio file
                target_sr = 44100  # Standard sample rate for DAW
                buffer, sr = load_audio_file(file_path, target_sr=target_sr)
                
                # Get current time for clip placement
                cur = 0.0
                try:
                    cur = float(getattr(self.player, "_current_time", 0.0))
                except Exception:
                    pass
                
                # Create clip
                from src.audio.clip import AudioClip
                clip = AudioClip(clip_name, buffer, sr, start_time=cur, file_path=file_path)
                
                # Add to timeline
                self.timeline.add_clip(track_idx, clip)
                self._track_controls.populate_tracks(self.timeline)
                if self._timeline_canvas:
                    self._timeline_canvas.redraw()
                
                # Success feedback
                if self._status:
                    track_name = self.mixer.tracks[track_idx].get("name", f"Track {track_idx+1}")
                    duration_str = f"{clip.length_seconds:.2f}s"
                    size_mb = len(buffer) * 4 / (1024 * 1024)  # Approximate size in MB
                    self._status.set(
                        f"✓ Imported '{clip_name}' to {track_name} "
                        f"({duration_str}, {sr}Hz, {size_mb:.1f}MB)"
                    )
                
                print(f"✓ Successfully imported: {file_path}")
                print(f"  - Duration: {clip.length_seconds:.2f}s")
                print(f"  - Sample rate: {sr} Hz")
                print(f"  - Samples: {len(buffer):,}")
                    
            except ImportError as e:
                if messagebox:
                    messagebox.showerror(
                        "Import Error",
                        f"Required audio library not available.\n\n{str(e)}\n\n"
                        "Install with:\n"
                        "  pip install soundfile\n"
                        "or\n"
                        "  pip install pydub"
                    )
                if self._status:
                    self._status.set("⚠ Audio library missing")
                    
            except Exception as e:
                if messagebox:
                    messagebox.showerror(
                        "Import Error",
                        f"Failed to load audio file:\n\n{str(e)}\n\n"
                        f"File: {os.path.basename(file_path)}"
                    )
                if self._status:
                    self._status.set(f"⚠ Import failed: {str(e)}")
                print(f"✗ Import error: {e}")
                return
            
            # Add to recent files
            self._add_to_recent_files(file_path)
                    
        except Exception as e:
            print(f"Import dialog error: {e}")
            if self._status:
                self._status.set("⚠ Import error")
    
    def _browse_audio_files(self):
        """Open audio file browser."""
        try:
            from src.ui.audio_browser import AudioBrowser
            
            browser = AudioBrowser(
                self._root,
                on_file_selected=self._import_audio_file
            )
            browser.show()
        except ImportError as e:
            print(f"Audio browser not available: {e}")
            # Fallback to standard dialog
            self._import_audio_dialog()
    
    def _import_audio_file(self, file_path: str):
        """Import a specific audio file (used by browser and drag-drop).
        
        Args:
            file_path: Absolute path to audio file
        """
        if not self.timeline or not self.mixer:
            return
        
        track_idx = self._track_controls.get_current_track_index()
        if track_idx is None:
            if self._status:
                self._status.set("⚠ Select a track first")
            return
        
        try:
            from src.utils.audio_io import load_audio_file
            import os
            
            if self._status:
                self._status.set(f"⏳ Loading {os.path.basename(file_path)}...")
            
            # Load file
            buffer, sr = load_audio_file(file_path, target_sr=44100)
            
            # Get clip name
            clip_name = os.path.splitext(os.path.basename(file_path))[0]
            
            # Get current time
            cur = 0.0
            try:
                cur = float(getattr(self.player, "_current_time", 0.0))
            except Exception:
                pass
            
            # Create and add clip
            from src.audio.clip import AudioClip
            clip = AudioClip(clip_name, buffer, sr, start_time=cur, file_path=file_path)
            
            self.timeline.add_clip(track_idx, clip)
            self._track_controls.populate_tracks(self.timeline)
            if self._timeline_canvas:
                self._timeline_canvas.redraw()
            
            # Success feedback
            if self._status:
                track_name = self.mixer.tracks[track_idx].get("name", f"Track {track_idx+1}")
                self._status.set(f"✓ Imported '{clip_name}' to {track_name}")
            
            print(f"✓ Imported: {file_path}")
            
            # Add to recent files
            self._add_to_recent_files(file_path)
            
        except Exception as e:
            if self._status:
                self._status.set(f"⚠ Failed to import: {str(e)}")
            print(f"✗ Import error: {e}")
    
    def _add_to_recent_files(self, file_path: str):
        """Add file to recent files list."""
        if file_path in self._recent_files:
            self._recent_files.remove(file_path)
        
        self._recent_files.insert(0, file_path)
        
        # Keep only last 10
        self._recent_files = self._recent_files[:10]
    
    def _get_recent_files(self):
        """Get list of recent files."""
        return self._recent_files
    
    def _import_recent_file(self, file_path: str):
        """Import a file from recent files list."""
        import os
        if not os.path.exists(file_path):
            if messagebox:
                messagebox.showerror(
                    "File Not Found",
                    f"The file no longer exists:\n{file_path}"
                )
            # Remove from recent files
            if file_path in self._recent_files:
                self._recent_files.remove(file_path)
            return
        
        self._import_audio_file(file_path)

    def _add_track_dialog(self):
        """Show dialog to add a new track."""
        if self.mixer is None or tk is None:
            return
        
        # Delegate to dialog class
        suggested_name = f"Track {self.mixer.get_track_count() + 1}"
        colors = ["#3b82f6", "#10b981", "#f59e0b", "#ef4444", "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"]
        default_color = colors[self.mixer.get_track_count() % len(colors)]
        
        dialog = AddTrackDialog(self._root, suggested_name, colors)
        result = dialog.show()
        
        if not result:
            return
        
        track_name, color = result
        # Add to mixer
        self.mixer.add_track(name=track_name, volume=1.0, pan=0.0, color=color)
        
        # Also add to project.tracks so it persists in save/load
        from ..core.track import Track
        track = Track(name=track_name)
        track.set_volume(1.0)
        self.project.create_track(track)
        
        self._track_controls.populate_tracks(self.timeline)
        
        if self._timeline_canvas:
            self._timeline_canvas.redraw()
        
        if self._status:
            self._status.set(f"✓ Track '{track_name}' added")

    def _on_timeline_right_click(self, event):
        """Handle right-click context menu on timeline."""
        if not self._timeline_canvas or not self._timeline_canvas.canvas:
            return
        
        x = self._timeline_canvas.canvas.canvasx(event.x)
        y = self._timeline_canvas.canvas.canvasy(event.y)
        
        clicked_clip = self._timeline_canvas._find_clip_at(x, y)
        
        if clicked_clip:
            # Right-click on clip - show clip menu
            track_idx, clip = clicked_clip
            
            # Check if clicked clip is already in selection
            selected_clips = self._timeline_canvas.get_selected_clips()
            is_in_selection = any(c == clip for _, c in selected_clips)
            
            # If not in selection, select only this clip
            if not is_in_selection:
                self._timeline_canvas.select_clip(track_idx, clip)
                selected_clips = [(track_idx, clip)]
            
            # Determine menu label
            if len(selected_clips) > 1:
                clip_name = f"{len(selected_clips)} clips"
                multi_selection = True
            else:
                clip_name = clip.name
                multi_selection = False
            
            # Delegate menu rendering to ClipContextMenu
            if self._clip_menu:
                self._clip_menu.show(event, clip_name, multi_selection=multi_selection)
        else:
            # Right-click on empty timeline - show paste menu
            if y > self._timeline_canvas.ruler_height:
                self._show_timeline_context_menu(event, x, y)
    
    def _show_timeline_context_menu(self, event, x, y):
        """Show context menu for empty timeline area (paste operations)."""
        if tk is None or self._root is None:
            return
        
        # Set paste position at click location
        time = (x - self._timeline_canvas.left_margin) / self._timeline_canvas.px_per_sec
        self._timeline_canvas.paste_position = max(0, self._timeline_canvas.snap_time(time))
        self._timeline_canvas.paste_cursor_visible = bool(self._timeline_canvas.clipboard)
        self._timeline_canvas.redraw()
        
        menu = tk.Menu(self._root, tearoff=0, bg="#2d2d2d", fg="#f5f5f5", activebackground="#3b82f6")
        
        # Show paste position
        time_str = f"{self._timeline_canvas.paste_position:.2f}s"
        menu.add_command(
            label=f"📍 Position: {time_str}",
            state="disabled",
            foreground="#888888"
        )
        menu.add_separator()
        
        # Paste option (enabled only if clipboard has content)
        if self._timeline_canvas.clipboard:
            clip_count = len(self._timeline_canvas.clipboard)
            menu.add_command(
                label=f"📌 Paste {clip_count} clip(s) here",
                command=self._paste_clips
            )
        else:
            menu.add_command(
                label="📌 Paste (clipboard empty)",
                state="disabled",
                foreground="#888888"
            )
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()

    def _delete_selected_clip(self):
        """Delete the selected clip."""
        if not self._timeline_canvas:
            return
        
        selected = self._timeline_canvas.get_selected_clip()
        if not selected:
            return
        
        track_idx, clip = selected
        self.timeline.remove_clip(track_idx, clip)
        self._timeline_canvas.selected_clip = None
        self._timeline_canvas.selected_clips = []
        self._track_controls.populate_tracks(self.timeline)
        self._timeline_canvas.redraw()
        
        if self._status:
            self._status.set(f"✓ Deleted clip '{clip.name}'")
    
    def _delete_selected_clips(self):
        """Delete all selected clips."""
        if not self._timeline_canvas:
            return
        
        selected_clips = self._timeline_canvas.get_selected_clips()
        if not selected_clips:
            return
        
        count = len(selected_clips)
        
        for track_idx, clip in selected_clips:
            self.timeline.remove_clip(track_idx, clip)
        
        self._timeline_canvas.clear_selection()
        self._track_controls.populate_tracks(self.timeline)
        self._timeline_canvas.redraw()
        
        if self._status:
            self._status.set(f"✓ Deleted {count} clip(s)")
    
    def _copy_selection(self):
        """Copy selected clips to clipboard."""
        if not self._timeline_canvas:
            return
        
        if self._timeline_canvas.copy_selected_clips():
            if self._status:
                count = len(self._timeline_canvas.clipboard)
                self._status.set(f"📋 Copied {count} clip(s)")
        else:
            if self._status:
                self._status.set("⚠ No clips selected to copy")
    
    def _paste_clips(self):
        """Paste clips from clipboard."""
        if not self._timeline_canvas:
            return
        
        if not self._timeline_canvas.clipboard:
            if self._status:
                self._status.set("⚠ Clipboard is empty")
            return
        
        pasted_clips = self._timeline_canvas.paste_clips()
        
        if pasted_clips:
            self._track_controls.populate_tracks(self.timeline)
            if self._status:
                self._status.set(f"📌 Pasted {len(pasted_clips)} clip(s)")
        else:
            if self._status:
                self._status.set("⚠ Failed to paste clips")
    
    def _copy_loop(self):
        """Copy all clips within the loop region to clipboard."""
        if not self.player or not self.timeline or not self._timeline_canvas:
            if self._status:
                self._status.set("⚠ No player or timeline available")
            return
        
        try:
            loop_enabled, loop_start, loop_end = self.player.get_loop()
            
            if not loop_enabled:
                if self._status:
                    self._status.set("⚠ Loop is not enabled. Set loop points first (Shift+drag on timeline)")
                return
            
            # Get all clips in the loop region
            clips_in_loop = list(self.timeline.get_clips_for_range(loop_start, loop_end))
            
            if not clips_in_loop:
                if self._status:
                    self._status.set("⚠ No clips found in loop region")
                return
            
            # Select clips in loop and copy them
            self._timeline_canvas.selected_clips = clips_in_loop
            
            if self._timeline_canvas.copy_selected_clips():
                if self._status:
                    count = len(clips_in_loop)
                    self._status.set(f"📋 Copied loop region: {count} clip(s) | {loop_start:.2f}s - {loop_end:.2f}s")
                print(f"🔁 Copied {count} clips from loop region [{loop_start:.3f}s - {loop_end:.3f}s]")
        
        except Exception as e:
            if self._status:
                self._status.set(f"⚠ Error copying loop: {e}")
            print(f"Error copying loop: {e}")
    
    def _paste_loop(self):
        """Paste clips from loop clipboard at loop end position."""
        if not self.player or not self.timeline or not self._timeline_canvas:
            if self._status:
                self._status.set("⚠ No player or timeline available")
            return
        
        if not self._timeline_canvas.clipboard:
            if self._status:
                self._status.set("⚠ Clipboard is empty")
            return
        
        try:
            loop_enabled, loop_start, loop_end = self.player.get_loop()
            
            if not loop_enabled:
                # Paste at current time if no loop
                self._paste_clips()
                return
            
            # Paste at loop end
            pasted_clips = self._timeline_canvas.paste_clips(at_time=loop_end)
            
            if pasted_clips:
                self._track_controls.populate_tracks(self.timeline)
                if self._status:
                    self._status.set(f"📌 Pasted {len(pasted_clips)} clip(s) at loop end ({loop_end:.2f}s)")
            else:
                if self._status:
                    self._status.set("⚠ Failed to paste clips")
        
        except Exception as e:
            if self._status:
                self._status.set(f"⚠ Error pasting loop: {e}")
            print(f"Error pasting loop: {e}")

    def _duplicate_selected_clip(self):
        """Duplicate the selected clip."""
        if not self._timeline_canvas:
            return
        
        selected = self._timeline_canvas.get_selected_clip()
        if not selected:
            return
        
        track_idx, clip = selected
        
        # Create cloned clip carrying all editing properties
        new_start = clip.end_time + 0.1
        new_clip = self._clone_clip(clip, new_start, name=f"{clip.name} (copy)")
        
        self.timeline.add_clip(track_idx, new_clip)
        self._timeline_canvas.select_clip(track_idx, new_clip)
        self._track_controls.populate_tracks(self.timeline)
        self._timeline_canvas.redraw()
        
        if self._status:
            self._status.set(f"✓ Duplicated clip '{clip.name}'")

    def _duplicate_loop(self):
        """Duplicate all clips within the current loop region."""
        if not self.player or not self.timeline:
            if self._status:
                self._status.set("⚠ No player or timeline available")
            return
        
        try:
            loop_enabled, loop_start, loop_end = self.player.get_loop()
            
            if not loop_enabled:
                if self._status:
                    self._status.set("⚠ Loop is not enabled. Set loop points first (Shift+drag on timeline)")
                return
            
            # Get all clips in the loop region
            clips_in_loop = list(self.timeline.get_clips_for_range(loop_start, loop_end))
            
            if not clips_in_loop:
                if self._status:
                    self._status.set("⚠ No clips found in loop region")
                return
            
            loop_duration = loop_end - loop_start
            
            # Duplicate each clip
            duplicated_count = 0
            
            for track_idx, clip in clips_in_loop:
                # Calculate offset from loop start
                clip_offset_from_loop_start = clip.start_time - loop_start
                
                # Calculate new start time (right after the loop end)
                new_start_time = loop_end + clip_offset_from_loop_start
                
                # Clone clip with all properties (trim/fades/pitch/color/file_path/duration)
                new_clip = self._clone_clip(clip, new_start_time)
                
                self.timeline.add_clip(track_idx, new_clip)
                duplicated_count += 1
            
            # Update UI
            if self._track_controls:
                self._track_controls.populate_tracks(self.timeline)
            if self._timeline_canvas:
                self._timeline_canvas.redraw()
            
            if self._status:
                self._status.set(f"✓ Duplicated loop region: {duplicated_count} clip(s) | {loop_start:.2f}s - {loop_end:.2f}s")
            
            print(f"🔁 Duplicated {duplicated_count} clips from loop region [{loop_start:.3f}s - {loop_end:.3f}s]")
            
        except Exception as e:
            if self._status:
                self._status.set(f"⚠ Error duplicating loop: {e}")
            print(f"Error duplicating loop: {e}")

    def _clone_clip(self, clip, new_start_time: float, name=None):
        """Create a new AudioClip copying all user-editable properties.
        
        Args:
            clip: Source AudioClip to clone
            new_start_time: Start time for the new clip
            name: Optional name override (defaults to source clip name)
            
        Returns:
            New AudioClip with all properties copied
        """
        from src.audio.clip import AudioClip
        
        new_clip = AudioClip(
            name or clip.name,
            clip.buffer,
            clip.sample_rate,
            new_start_time,
            duration=clip.duration,
            color=clip.color,
            file_path=clip.file_path,
        )
        
        # Copy editing properties (trim, fades, pitch)
        new_clip.start_offset = getattr(clip, 'start_offset', 0.0)
        new_clip.end_offset = getattr(clip, 'end_offset', 0.0)
        new_clip.fade_in = getattr(clip, 'fade_in', 0.0)
        new_clip.fade_in_shape = getattr(clip, 'fade_in_shape', 'linear')
        new_clip.fade_out = getattr(clip, 'fade_out', 0.0)
        new_clip.fade_out_shape = getattr(clip, 'fade_out_shape', 'linear')
        new_clip.pitch_semitones = getattr(clip, 'pitch_semitones', 0.0)
        new_clip.volume = getattr(clip, 'volume', 1.0)
        
        return new_clip

    def _show_clip_properties(self):
        """Open Clip Inspector to edit clip parameters (trim/fade/pitch)."""
        if not self._timeline_canvas:
            return

        selected = self._timeline_canvas.get_selected_clip()
        if not selected:
            return

        track_idx, clip = selected

        try:
            from .clip_inspector import show_clip_inspector
        except Exception:
            show_clip_inspector = None

        if show_clip_inspector is None or self._root is None:
            # Fallback: simple message box with info
            if messagebox is None:
                return
            props = f"""Clip Properties

Name: {clip.name}
Start Time: {clip.start_time:.3f} s
End Time: {clip.end_time:.3f} s
Duration: {clip.length_seconds:.3f} s
Sample Rate: {clip.sample_rate} Hz
Samples: {len(clip.buffer)}
"""
            if clip.file_path:
                props += f"\nSource: {clip.file_path}"
            messagebox.showinfo("Clip Properties", props)
            return

        def on_apply(_clip):
            # Redraw timeline to reflect changes (length/peaks)
            if self._timeline_canvas:
                self._timeline_canvas.redraw()

        show_clip_inspector(self._root, clip, on_apply=on_apply)

    # Project management methods
    def _new_project(self):
        """Create a new project."""
        if messagebox is None:
            return
        
        # Check if current project has unsaved changes (future enhancement)
        result = messagebox.askyesno(
            "New Project",
            "Create a new project? Current project will be cleared."
        )
        
        if not result:
            return
        
        # Clear current project
        if self.timeline:
            # Remove all clips from timeline using Timeline's API
            # Get all placements and remove them
            all_clips = list(self.timeline.all_placements())
            for track_idx, clip in all_clips:
                self.timeline.remove_clip(track_idx, clip)
        
        # Reset project properties
        self.project.name = "Untitled"
        self.project.bpm = 120.0
        self.project.time_signature_num = 4
        self.project.time_signature_den = 4
        
        # Clear project file path
        self._project_file_path = None
        
        # Update UI
        if self._toolbar_manager:
            self._toolbar_manager.bpm_var.set(120.0)
        
        if self._track_controls:
            self._track_controls.populate_tracks(self.timeline)
        
        if self._timeline_canvas:
            self._timeline_canvas.redraw()
        
        if self._status:
            self._status.set("✓ New project created")
        
        self._root.title(f"{self.title} - Untitled")
    
    def _open_project(self):
        """Open an existing project file."""
        if filedialog is None:
            return
        
        file_path = filedialog.askopenfilename(
            title="Open Project",
            filetypes=[
                ("DAW Project", "*.daw"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            if self._status:
                self._status.set("⏳ Loading project...")
            
            # Load project
            from src.core.project import Project
            loaded_project = Project.load_project(file_path)
            
            # Replace current project
            self.project.name = loaded_project.name
            self.project.bpm = loaded_project.bpm
            self.project.time_signature_num = loaded_project.time_signature_num
            self.project.time_signature_den = loaded_project.time_signature_den
            self.project.tracks = loaded_project.tracks
            
            # Update timeline - clear existing clips and add loaded ones
            if self.timeline:
                # Clear all existing clips from timeline
                self.timeline._placements.clear()
                
                # Add all clips from loaded tracks to timeline using Timeline's API
                for track_idx, track in enumerate(self.project.tracks):
                    # Debug: print what we're loading
                    print(f"  Track {track_idx}: {len(track.audio_files)} clip(s)")
                    for clip in track.audio_files:
                        print(f"    - {clip.name}: {clip.start_time}s, buffer={len(clip.buffer)} samples")
                        # Add clip to timeline using proper API
                        self.timeline.add_clip(track_idx, clip)
            
            # Stop player if running and reset position
            if self.player:
                was_playing = self.player.is_playing()
                if was_playing:
                    self.player.stop()
                # Reset playback position
                self.player.set_current_time(0.0)
            
            # Update mixer
            if self.mixer:
                # Clear existing tracks
                while self.mixer.get_track_count() > 0:
                    self.mixer.tracks.pop()
                
                print(f"Loading {len(self.project.tracks)} tracks into mixer...")
                
                # Add loaded tracks (from project.tracks which are Track objects)
                for idx, track in enumerate(self.project.tracks):
                    track_name = getattr(track, 'name', None) or f"Track {idx + 1}"
                    print(f"  Adding mixer track {idx}: '{track_name}' (volume={track.volume})")
                    self.mixer.add_track(
                        name=track_name,
                        volume=track.volume,
                        pan=0.0
                    )
                
                print(f"Mixer now has {self.mixer.get_track_count()} tracks")
            
            # Update UI
            if self._toolbar_manager:
                self._toolbar_manager.bpm_var.set(self.project.bpm)
            
            if self._track_controls:
                print("Calling populate_tracks...")
                self._track_controls.populate_tracks(self.timeline)
                print("populate_tracks completed")
            
            if self._timeline_canvas:
                self._timeline_canvas.redraw()
            
            # Save project file path
            self._project_file_path = file_path
            
            # Update window title
            import os
            project_name = os.path.basename(file_path)
            self._root.title(f"{self.title} - {project_name}")
            
            if self._status:
                track_count = len(self.project.tracks)
                clip_count = sum(len(track.audio_files) for track in self.project.tracks)
                self._status.set(
                    f"✓ Loaded '{self.project.name}' - "
                    f"{track_count} track(s), {clip_count} clip(s)"
                )
            
            print(f"✓ Project loaded: {file_path}")
            
        except Exception as e:
            if messagebox:
                messagebox.showerror(
                    "Load Error",
                    f"Failed to load project:\n\n{str(e)}"
                )
            if self._status:
                self._status.set(f"⚠ Failed to load project: {str(e)}")
            print(f"✗ Load error: {e}")
    
    def _save_project(self):
        """Save the current project."""
        if self._project_file_path:
            # Save to existing file
            self._do_save_project(self._project_file_path)
        else:
            # No file path yet, do Save As
            self._save_project_as()
    
    def _save_project_as(self):
        """Save the current project with a new name."""
        if filedialog is None:
            return
        
        file_path = filedialog.asksaveasfilename(
            title="Save Project As",
            defaultextension=".daw",
            filetypes=[
                ("DAW Project", "*.daw"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        self._do_save_project(file_path)
        self._project_file_path = file_path
        
        # Update window title
        import os
        project_name = os.path.basename(file_path)
        self._root.title(f"{self.title} - {project_name}")
    
    def _do_save_project(self, file_path: str):
        """Perform the actual save operation.
        
        Args:
            file_path: Path to save the project file
        """
        try:
            if self._status:
                self._status.set("⏳ Saving project...")
            
            # Sync data from timeline and mixer to project tracks before saving
            if self.mixer and self.timeline:
                # Iterate over all tracks (use the count from mixer since it's the UI source of truth)
                for i in range(len(self.mixer.tracks)):
                    mixer_track = self.mixer.tracks[i]
                    
                    # Ensure project has corresponding track
                    if i >= len(self.project.tracks):
                        # Track exists in mixer but not in project - this shouldn't happen with the fix,
                        # but handle it gracefully by skipping
                        print(f"Warning: Track {i} exists in mixer but not in project")
                        continue
                    
                    project_track = self.project.tracks[i]
                    
                    # Sync track name from mixer
                    project_track.name = mixer_track.get("name", f"Track {i + 1}")
                    
                    # Sync track volume from mixer
                    project_track.volume = mixer_track.get("volume", 1.0)
                    
                    # Sync clips from timeline to track using Timeline's API
                    project_track.audio_files = []
                    clips = self.timeline.get_clips_for_track(i)
                    for clip in clips:
                        project_track.audio_files.append(clip)
                    print(f"Syncing track {i}: '{project_track.name}' vol={project_track.volume:.2f} with {len(project_track.audio_files)} clips")
            
            # Save project (default to separate audio files for better performance)
            self.project.save_project(file_path, embed_audio=False)
            
            if self._status:
                import os
                size = os.path.getsize(file_path) / 1024  # KB
                track_count = len(self.project.tracks)
                clip_count = sum(len(track.audio_files) for track in self.project.tracks)
                self._status.set(
                    f"✓ Saved '{os.path.basename(file_path)}' - "
                    f"{track_count} track(s), {clip_count} clip(s) ({size:.1f} KB)"
                )
            
            print(f"✓ Project saved: {file_path}")
            
        except Exception as e:
            if messagebox:
                messagebox.showerror(
                    "Save Error",
                    f"Failed to save project:\n\n{str(e)}"
                )
            if self._status:
                self._status.set(f"⚠ Failed to save project: {str(e)}")
            print(f"✗ Save error: {e}")

    def _export_audio_dialog(self):
        """Export the song as WAV file, respecting loop if present."""
        if filedialog is None:
            return
        
        # Ask user for file path
        file_path = filedialog.asksaveasfilename(
            title="Export Audio",
            defaultextension=".wav",
            filetypes=[
                ("WAV Audio", "*.wav"),
                ("All Files", "*.*")
            ]
        )
        
        if not file_path:
            return
        
        try:
            if self._status:
                self._status.set("⏳ Exporting audio...")
            
            # Determine export range
            start_time = 0.0
            end_time = 0.0
            use_loop = False
            
            # Check if loop is enabled
            if self.player and hasattr(self.player, 'loop_enabled') and self.player.loop_enabled:
                # Use loop range
                start_time = getattr(self.player, 'loop_start', 0.0)
                end_time = getattr(self.player, 'loop_end', 0.0)
                use_loop = True
                print(f"🔁 Exporting loop region: {start_time:.3f}s to {end_time:.3f}s")
            else:
                # Find the extent of all clips in the timeline
                if self.timeline:
                    max_end = 0.0
                    clip_count = 0
                    for track_idx, clip in self.timeline.all_placements():
                        if hasattr(clip, 'end_time'):
                            max_end = max(max_end, clip.end_time)
                            clip_count += 1
                    
                    if clip_count == 0:
                        if messagebox:
                            messagebox.showwarning(
                                "Export Warning",
                                "No clips found in the timeline. Nothing to export."
                            )
                        if self._status:
                            self._status.set("⚠ No clips to export")
                        return
                    
                    start_time = 0.0
                    end_time = max_end
                    print(f"📄 Exporting full song: 0.0s to {end_time:.3f}s ({clip_count} clips)")
            
            if end_time <= start_time:
                if messagebox:
                    messagebox.showwarning(
                        "Export Warning",
                        "Invalid time range. Cannot export."
                    )
                if self._status:
                    self._status.set("⚠ Invalid export range")
                return
            
            duration = end_time - start_time
            sample_rate = 44100  # Standard CD quality
            
            # Collect track volumes from the project
            track_volumes = {}
            if self.project and self.project.tracks:
                for i, track in enumerate(self.project.tracks):
                    track_volumes[i] = track.volume
                print(f"📊 Track volumes: {track_volumes}")
            
            # Render the audio using AudioEngine
            from ..audio.engine import AudioEngine
            engine = AudioEngine()
            engine.initialize()
            
            print(f"🎵 Rendering audio: duration={duration:.3f}s, sample_rate={sample_rate} Hz")
            audio_buffer = engine.render_window(
                self.timeline,
                start_time=start_time,
                duration=duration,
                sample_rate=sample_rate,
                track_volumes=track_volumes,
                mixer=self.mixer  # Pass mixer for mute/solo state
            )
            
            if not audio_buffer or len(audio_buffer) == 0:
                if messagebox:
                    messagebox.showwarning(
                        "Export Warning",
                        "No audio data to export. The timeline may be empty."
                    )
                if self._status:
                    self._status.set("⚠ No audio data")
                return
            
            # Save to WAV file
            from ..utils.audio_io import save_audio_file
            save_audio_file(audio_buffer, file_path, sample_rate, format="wav")
            
            # Show success message
            import os
            file_size = os.path.getsize(file_path) / 1024  # KB
            if self._status:
                loop_text = " (loop region)" if use_loop else ""
                self._status.set(
                    f"✓ Exported '{os.path.basename(file_path)}'{loop_text} - "
                    f"{duration:.2f}s, {file_size:.1f} KB"
                )
            
            print(f"✓ Audio exported: {file_path}")
            print(f"  Duration: {duration:.2f}s")
            print(f"  Sample rate: {sample_rate} Hz")
            print(f"  Samples: {len(audio_buffer):,}")
            print(f"  File size: {file_size:.1f} KB")
            
            if messagebox:
                messagebox.showinfo(
                    "Export Complete",
                    f"Audio successfully exported to:\n{file_path}\n\n"
                    f"Duration: {duration:.2f}s\n"
                    f"Sample rate: {sample_rate} Hz\n"
                    f"File size: {file_size:.1f} KB"
                )
                
        except Exception as e:
            if messagebox:
                messagebox.showerror(
                    "Export Error",
                    f"Failed to export audio:\n\n{str(e)}"
                )
            if self._status:
                self._status.set(f"⚠ Export failed: {str(e)}")
            print(f"✗ Export error: {e}")
            import traceback
            traceback.print_exc()

    # Lifecycle methods
    def run(self):
        """Run the main event loop."""
        if tk is None:
            print("Running in console mode. Press Ctrl+C to exit.")
            try:
                import time
                while True:
                    time.sleep(0.1)
            except KeyboardInterrupt:
                self.close()
            return

        if self._root is None:
            self.show()
        try:
            self._root.mainloop()
        finally:
            self.close()

    def close(self):
        """Close the window."""
        self.is_open = False
        if self._root is not None:
            try:
                self._root.destroy()
            except Exception:
                pass
            self._root = None

    # Legacy compatibility properties for backward compatibility
    @property
    def _track_tree(self):
        """Legacy property for track_tree."""
        return self._track_controls.track_tree if self._track_controls else None
    
    @property
    def _volume_var(self):
        """Legacy property for volume_var."""
        return self._track_controls.volume_var if self._track_controls else None
    
    @property
    def _loop_var(self):
        """Legacy property for loop_var."""
        return self._toolbar_manager.loop_var if self._toolbar_manager else None
    
    @property
    def _bpm_var(self):
        """Legacy property for bpm_var."""
        return self._toolbar_manager.bpm_var if self._toolbar_manager else None
