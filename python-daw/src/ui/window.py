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
            on_delete=self._delete_selected_clip,
            on_duplicate=self._duplicate_selected_clip,
            on_properties=self._show_clip_properties
        )
        
        self.is_open = True
        print("GUI window created. If you don't see it, check the taskbar and ensure it's not behind other windows.")

    def _setup_theme(self):
        """Setup the professional dark theme."""
        ThemeManager(self._root).apply_dark_theme()

    def _setup_menu(self):
        """Setup the menu bar using MenuManager."""
        callbacks = {
            'import_audio': self._import_audio_dialog,
            'browse_audio': self._browse_audio_files,
            'get_recent_files': self._get_recent_files,
            'import_recent': self._import_recent_file,
            'exit': self.close,
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
        
        # Tracks header with buttons
        tracks_header = ttk.Frame(sidebar, style="Sidebar.TFrame")
        tracks_header.pack(fill="x", padx=12, pady=(8, 4))
        ttk.Label(tracks_header, text="TRACKS", style="SidebarTitle.TLabel").pack(side="left")
        
        btn_container = ttk.Frame(tracks_header, style="Sidebar.TFrame")
        btn_container.pack(side="right")
        ttk.Button(
            btn_container, text="+",
            command=self._add_track_dialog,
            style="Tool.TButton", width=3
        ).pack(side="left", padx=(0, 2))
        ttk.Button(
            btn_container, text="🎵",
            command=self._add_dummy_clip,
            style="Tool.TButton", width=3
        ).pack(side="left")
        
        # Create track controls
        self._track_controls = TrackControls(sidebar, self.mixer)
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
            self._root.bind('+', lambda e: self._zoom(1.25))
            self._root.bind('-', lambda e: self._zoom(0.8))
            self._root.bind('0', lambda e: self._zoom_reset())
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
        """Update project BPM and adjust loop points."""
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
            
            # Update BPM
            self.project.bpm = float(new_bpm)
            
            # Convert loop points back
            if self.player is not None and loop_enabled:
                try:
                    new_loop_start = self.project.bars_to_seconds(loop_start_bars)
                    new_loop_end = self.project.bars_to_seconds(loop_end_bars)
                    self.player.set_loop(loop_enabled, new_loop_start, new_loop_end)
                    print(f"Loop adjusted: {loop_start_sec:.3f}s->{new_loop_start:.3f}s, {loop_end_sec:.3f}s->{new_loop_end:.3f}s")
                except Exception as e:
                    print(f"Loop adjustment error: {e}")
            
            if self._timeline_canvas:
                self._timeline_canvas.redraw()
            print(f"BPM changed: {old_bpm:.1f} → {new_bpm}")
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
        self.mixer.add_track(name=track_name, volume=1.0, pan=0.0, color=color)
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
            track_idx, clip = clicked_clip
            self._timeline_canvas.select_clip(track_idx, clip)
            
            # Delegate menu rendering to ClipContextMenu
            if self._clip_menu:
                self._clip_menu.show(event, clip.name)

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
        self._track_controls.populate_tracks(self.timeline)
        self._timeline_canvas.redraw()
        
        if self._status:
            self._status.set(f"✓ Deleted clip '{clip.name}'")

    def _duplicate_selected_clip(self):
        """Duplicate the selected clip."""
        if not self._timeline_canvas:
            return
        
        selected = self._timeline_canvas.get_selected_clip()
        if not selected:
            return
        
        track_idx, clip = selected
        
        from src.audio.clip import AudioClip
        new_clip = AudioClip(
            f"{clip.name} (copy)",
            clip.buffer,
            clip.sample_rate,
            clip.end_time + 0.1,
            duration=clip.duration,
            color=clip.color,
            file_path=clip.file_path
        )
        
        self.timeline.add_clip(track_idx, new_clip)
        self._timeline_canvas.select_clip(track_idx, new_clip)
        self._track_controls.populate_tracks(self.timeline)
        self._timeline_canvas.redraw()
        
        if self._status:
            self._status.set(f"✓ Duplicated clip '{clip.name}'")

    def _show_clip_properties(self):
        """Show clip properties dialog."""
        if not self._timeline_canvas or messagebox is None:
            return
        
        selected = self._timeline_canvas.get_selected_clip()
        if not selected:
            return
        
        track_idx, clip = selected
        
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
