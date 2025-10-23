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
from .menu_manager import MenuManager
from .toolbar_manager import ToolbarManager
from .theme_manager import ThemeManager
from .project_manager import ProjectManager
from .track_clip_manager import TrackClipManager
from .context_menus import ClipContextMenu, TrackContextMenu
from .transport_controller import TransportController


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
        self._current_track_idx = 0  # Currently selected track for operations
        
        # Component managers (OOP refactoring)
        self._timeline_canvas = None
        self._track_controls = None  # Deprecated - now in canvas
        self._menu_manager = None
        self._toolbar_manager = None
        self._clip_menu = None
        self._transport_controller = None  # Transport control manager
        self._track_clip_manager = None  # Track/Clip operations manager
        
        # Master controls
        self._master_volume_var = None
        self._master_vol_label = None
        self._meter_L = None
        self._meter_R = None
        
        # Update jobs
        self._time_job = None
        self._meter_job = None
        
        
        # Project manager (handles new/open/save/export)
        self._project_manager = None

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

        # Prepare context menu helpers
        self._clip_menu = ClipContextMenu(
            self._root,
            on_delete=lambda: self._track_clip_manager.delete_selected_clips(),
            on_duplicate=lambda: self._track_clip_manager.duplicate_selected_clip(),
            on_properties=lambda: self._track_clip_manager.show_clip_properties(),
            on_copy=lambda: self._track_clip_manager.copy_selection(),
            on_paste=lambda: self._track_clip_manager.paste_clips()
        )
        
        self._track_menu = TrackContextMenu(
            self._root,
            on_add_audio_clip=lambda track_idx: self._track_clip_manager.add_audio_clip_to_track(track_idx),
            on_rename=lambda track_idx: self._track_clip_manager.rename_track(track_idx),
            on_delete=lambda track_idx: self._track_clip_manager.delete_track(track_idx),
            on_duplicate=lambda track_idx: self._track_clip_manager.duplicate_track(track_idx),
            on_color=lambda track_idx: self._track_clip_manager.change_track_color(track_idx),
            on_add_midi_demo=lambda track_idx: self._track_clip_manager.add_midi_demo_clip_to_track(track_idx),
            on_edit_synth=lambda track_idx: self._track_clip_manager.edit_track_synth(track_idx),
            on_change_instrument=lambda track_idx: self._track_clip_manager.change_instrument(track_idx)
        )

        # Setup UI components
        self._setup_theme()
        self._setup_project_manager()
        self._setup_track_clip_manager()
        self._setup_transport_controller()
        self._setup_menu()
        self._setup_toolbar()
        self._setup_main_layout()
        self._setup_status_bar()
        self._bind_keys()
        
        self.is_open = True
        print("GUI window created. If you don't see it, check the taskbar and ensure it's not behind other windows.")

    def _setup_theme(self):
        """Setup the professional dark theme."""
        ThemeManager(self._root).apply_dark_theme()
    
    def _setup_project_manager(self):
        """Setup the project manager."""
        self._project_manager = ProjectManager(self)
    
    def _setup_track_clip_manager(self):
        """Setup the track/clip manager."""
        self._track_clip_manager = TrackClipManager(self)
    
    def _setup_transport_controller(self):
        """Setup the transport controller."""
        self._transport_controller = TransportController(
            transport=self.transport,
            player=self.player,
            project=self.project,
            timeline=self.timeline
        )
        
        # Setup callbacks for UI updates
        self._transport_controller.on_status_change = self._set_status
        self._transport_controller.on_timeline_redraw = self._redraw_timeline
        self._transport_controller.on_time_update_start = self._schedule_time_update
        self._transport_controller.on_meter_update_start = self._schedule_meter_update
        self._transport_controller.on_time_update_stop = self._cancel_time_update

    def _setup_menu(self):
        """Setup the menu bar using MenuManager."""
        callbacks = {
            'new_project': lambda: self._project_manager.new_project(),
            'open_project': lambda: self._project_manager.open_project(),
            'save_project': lambda: self._project_manager.save_project(),
            'save_project_as': lambda: self._project_manager.save_project_as(),
            'import_audio': lambda: self._track_clip_manager.import_audio_dialog(),
            'export_audio': lambda: self._project_manager.export_audio_dialog(),
            'exit': self.close,
            'duplicate_loop': lambda: self._track_clip_manager.duplicate_loop(),
            'delete_clip': lambda: self._track_clip_manager.delete_selected_clip(),
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
            'add_track': lambda: self._track_clip_manager.add_track_dialog(),
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
        
        # Connect transport controller to toolbar
        if self._transport_controller:
            self._transport_controller.set_toolbar_manager(self._toolbar_manager)
        
        # Show hint for loop selection in status bar after a brief delay
        if self._root and self._status:
            self._root.after(1000, lambda: self._status.set("💡 Shift+Drag to set loop | Drag loop markers to adjust"))

    def _setup_main_layout(self):
        """Setup the main layout with timeline canvas only."""
        # Main container
        main_container = ttk.Frame(self._root)
        main_container.pack(fill="both", expand=True)
        
        # Timeline area (full width, no sidebar)
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
        
        # Connect transport controller to timeline canvas
        if self._transport_controller:
            self._transport_controller.set_timeline_canvas(self._timeline_canvas)
        
        # Set track context menu reference
        self._timeline_canvas.track_menu = self._track_menu
        # When a track is selected on the canvas controls, update current track index
        self._timeline_canvas.on_track_selected = self._set_current_track_index
        
        # Bind context menus to both canvases
        if self._timeline_canvas.canvas:
            self._timeline_canvas.canvas.bind('<Button-3>', self._on_timeline_right_click)
        if self._timeline_canvas.controls_canvas:
            self._timeline_canvas.controls_canvas.bind('<Button-3>', self._on_track_controls_right_click)
        
        # Initial draw
        self._timeline_canvas.redraw()

    def _setup_status_bar(self):
        """Setup the status bar at the bottom with master controls."""
        status_bar = ttk.Frame(self._root, style="Toolbar.TFrame", height=32)
        status_bar.pack(fill="x", side="bottom")
        status_bar.pack_propagate(False)
        
        # Left: Status message
        self._status = tk.StringVar(value="● Ready")
        status_lbl = ttk.Label(status_bar, textvariable=self._status, style="Status.TLabel")
        status_lbl.pack(side="left", padx=8)
        
        # Right side: Master controls
        master_frame = ttk.Frame(status_bar, style="Toolbar.TFrame")
        master_frame.pack(side="right", padx=8)
        
        # Zoom info
        zoom_info = ttk.Label(master_frame, text="Zoom: 1.00x", style="Status.TLabel")
        zoom_info.pack(side="right", padx=(0, 12))
        self._zoom_label = zoom_info
        
        # Master volume
        ttk.Label(master_frame, text="🔊 Master:", style="Status.TLabel").pack(side="right", padx=(12, 4))
        
        self._master_volume_var = tk.DoubleVar(value=getattr(self.mixer, 'master_volume', 1.0))
        master_vol_scale = ttk.Scale(
            master_frame, from_=0.0, to=1.0, orient="horizontal",
            variable=self._master_volume_var,
            command=self._on_master_volume_change,
            length=100
        )
        master_vol_scale.pack(side="right", padx=4)
        
        self._master_vol_label = ttk.Label(master_frame, text="1.00", style="Status.TLabel", width=4)
        self._master_vol_label.pack(side="right", padx=4)
        
        # Output meters (L/R)
        ttk.Label(master_frame, text="L", style="Status.TLabel", width=2).pack(side="right", padx=(12, 2))
        self._meter_L = ttk.Progressbar(
            master_frame, mode="determinate", maximum=1.0,
            style="Meter.Horizontal.TProgressbar", length=60
        )
        self._meter_L.pack(side="right", padx=2)
        
        ttk.Label(master_frame, text="R", style="Status.TLabel", width=2).pack(side="right", padx=(8, 2))
        self._meter_R = ttk.Progressbar(
            master_frame, mode="determinate", maximum=1.0,
            style="Meter.Horizontal.TProgressbar", length=60
        )
        self._meter_R.pack(side="right", padx=2)
    
    def _on_master_volume_change(self, value=None):
        """Handle master volume change."""
        if self.mixer is None:
            return
        try:
            vol = float(self._master_volume_var.get())
            if hasattr(self.mixer, 'set_master_volume'):
                self.mixer.set_master_volume(vol)
            else:
                self.mixer.master_volume = vol
            
            if self._master_vol_label:
                self._master_vol_label.configure(text=f"{vol:.2f}")
        except Exception as e:
            print(f"Error updating master volume: {e}")

    def _bind_keys(self):
        """Bind keyboard shortcuts."""
        if self._root is None:
            return
        try:
            self._root.bind('<space>', self._toggle_playback)
            self._root.bind('<Control-n>', lambda e: self._project_manager.new_project())  # Ctrl+N for New Project
            self._root.bind('<Control-o>', lambda e: self._project_manager.open_project())  # Ctrl+O for Open
            self._root.bind('<Control-s>', lambda e: self._project_manager.save_project())  # Ctrl+S for Save
            self._root.bind('<Control-Shift-S>', lambda e: self._project_manager.save_project_as())  # Ctrl+Shift+S for Save As
            self._root.bind('<Control-e>', lambda e: self._project_manager.export_audio_dialog())  # Ctrl+E for Export Audio
            self._root.bind('+', lambda e: self._zoom(1.25))
            self._root.bind('-', lambda e: self._zoom(0.8))
            self._root.bind('0', lambda e: self._zoom_reset())
            self._root.bind('<Control-d>', lambda e: self._track_clip_manager.duplicate_loop())  # Ctrl+D to duplicate loop
            self._root.bind('<Control-c>', lambda e: self._track_clip_manager.copy_selection())  # Ctrl+C to copy clips
            self._root.bind('<Control-v>', lambda e: self._track_clip_manager.paste_clips())  # Ctrl+V to paste clips
            self._root.bind('<Control-Shift-C>', lambda e: self._track_clip_manager.copy_loop())  # Ctrl+Shift+C to copy loop
            self._root.bind('<Control-Shift-V>', lambda e: self._track_clip_manager.paste_loop())  # Ctrl+Shift+V to paste loop
            self._root.bind('<Delete>', lambda e: self._track_clip_manager.delete_selected_clips())  # Delete key
        except Exception:
            pass

    def _toggle_playback(self, event=None):
        """Toggle play/stop."""
        if self.player and hasattr(self.player, 'is_playing'):
            if not self.player.is_playing():
                self._on_play()
            else:
                self._on_stop()
    
    # Helper methods for transport controller callbacks
    def _set_status(self, status_text):
        """Set status bar text."""
        if self._status:
            self._status.set(status_text)
    
    def _redraw_timeline(self):
        """Redraw timeline canvas."""
        if self._timeline_canvas:
            self._timeline_canvas.redraw()
    
    def _cancel_time_update(self):
        """Cancel time update job."""
        if self._root is not None:
            try:
                self._root.after_cancel(self._time_job)
            except Exception:
                pass

    # Transport control methods - delegated to TransportController
    def _on_play(self):
        """Handle play button."""
        if self._transport_controller:
            self._transport_controller.play()

    def _on_stop(self):
        """Handle stop button."""
        if self._transport_controller:
            self._transport_controller.stop()

    def _on_loop_toggle(self):
        """Toggle loop on/off."""
        if self._transport_controller:
            self._transport_controller.toggle_loop()

    def _set_loop_start(self):
        """Set loop start to current playback position."""
        if self._transport_controller:
            self._transport_controller.set_loop_start()

    def _set_loop_end(self):
        """Set loop end to current playback position."""
        if self._transport_controller:
            self._transport_controller.set_loop_end()

    def _on_bpm_change(self):
        """Update project BPM and adjust loop points and clip positions."""
        if self._transport_controller and self._toolbar_manager:
            new_bpm = self._toolbar_manager.get_bpm()
            self._transport_controller.change_bpm(new_bpm)

    def _on_snap_toggle(self):
        """Toggle snap to grid."""
        if self._toolbar_manager and self._timeline_canvas:
            enabled = self._toolbar_manager.get_snap_enabled()
            self._timeline_canvas.set_snap(enabled)
            status = "ON" if enabled else "OFF"
            print(f"Snap to grid: {status}")

    def _on_grid_change(self, event=None):
        """Change grid division and redraw timeline."""
        if self._toolbar_manager and self._timeline_canvas:
            division = self._toolbar_manager.get_grid_division()
            self._timeline_canvas.set_grid_division(division)
            # Redraw to show new grid
            self._timeline_canvas.redraw()
            if self._status:
                # Show feedback
                grid_str = self._toolbar_manager.grid_var.get() if hasattr(self._toolbar_manager, 'grid_var') else str(division)
                self._status.set(f"Grid: {grid_str}")

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
        if self._root is None:
            return
        
        # Update master meters
        if self.player and hasattr(self, '_meter_L') and hasattr(self, '_meter_R'):
            try:
                peakL = float(getattr(self.player, "_last_peak_L", 0.0))
                peakR = float(getattr(self.player, "_last_peak_R", 0.0))
                
                self._meter_L['value'] = max(0.0, min(1.0, peakL))
                self._meter_R['value'] = max(0.0, min(1.0, peakR))
            except Exception:
                pass
        
        self._meter_job = self._root.after(100, self._schedule_meter_update)

    def _get_current_track_index(self):
        """Get currently selected track index."""
        return self._current_track_idx
    
    def _set_current_track_index(self, idx):
        """Set currently selected track index."""
        if idx is not None and 0 <= idx < len(self.mixer.tracks):
            self._current_track_idx = idx
    
    def _on_track_controls_right_click(self, event):
        """Handle right-click on track controls area (left side)."""
        if not self._timeline_canvas or not self._timeline_canvas.controls_canvas:
            return
        
        x = self._timeline_canvas.controls_canvas.canvasx(event.x)
        y = self._timeline_canvas.controls_canvas.canvasy(event.y)
        
        # Find which track was clicked
        if y <= self._timeline_canvas.ruler_height:
            return  # Clicked on ruler
        
        track_idx = int((y - self._timeline_canvas.ruler_height) / self._timeline_canvas.track_height)
        
        if self.mixer is None or track_idx >= len(self.mixer.tracks):
            return
        # Select the track before opening the menu and update highlight
        self._set_current_track_index(track_idx)
        if hasattr(self._timeline_canvas, 'select_track'):
            self._timeline_canvas.select_track(track_idx)
        
        # Show track context menu
        if self._track_menu:
            track_obj = self.mixer.tracks[track_idx]
            track_name = track_obj.get("name", f"Track {track_idx+1}")
            track_type = track_obj.get("type", "audio")
            self._track_menu.show(event, track_name, track_idx, track_type=track_type)
    
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
            is_midi = False
            try:
                from src.midi.clip import MidiClip
                is_midi = isinstance(clip, MidiClip)
            except Exception:
                is_midi = False
            
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
        
        # Determine which track was clicked
        track_idx = None
        track_name = None
        if y > self._timeline_canvas.ruler_height:
            track_idx = int((y - self._timeline_canvas.ruler_height) / self._timeline_canvas.track_height)
            if self.mixer and track_idx < len(self.mixer.tracks):
                track_name = self.mixer.tracks[track_idx].get("name", f"Track {track_idx+1}")
        
        # Set paste position at click location (no left_margin offset needed)
        time = x / self._timeline_canvas.px_per_sec
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
        
        # Add Clip option (MIDI or Audio depending on track type)
        if track_idx is not None and track_name and self.mixer:
            track_type = (self.mixer.tracks[track_idx].get("type") or "audio").lower()
            if track_type == 'midi':
                menu.add_command(
                    label=f"🎹 Add MIDI Clip to '{track_name}'",
                    command=lambda: self._track_clip_manager.add_midi_demo_clip_to_track(track_idx)
                )
            else:
                menu.add_command(
                    label=f"🎵 Add Audio Clip to '{track_name}'",
                    command=lambda: self._track_clip_manager.add_audio_clip_to_track(track_idx)
                )
        
        menu.add_separator()
        
        # Paste option (enabled only if clipboard has content)
        if self._timeline_canvas.clipboard:
            clip_count = len(self._timeline_canvas.clipboard)
            menu.add_command(
                label=f"📌 Paste {clip_count} clip(s) here",
                command=lambda: self._track_clip_manager.paste_clips()
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

    def _open_piano_roll_editor(self, clip):
        """Open the Piano Roll editor for a MIDI clip and refresh on apply."""
        try:
            # Lazy import to avoid hard dependency when MIDI is not used
            from .piano_roll import PianoRollEditor
        except Exception:
            PianoRollEditor = None
        if tk is None or PianoRollEditor is None or self._root is None:
            return

        def _on_apply(_clip):
            # Redraw the timeline to reflect note edits and potential length changes
            try:
                if self._timeline_canvas:
                    self._timeline_canvas.redraw()
            except Exception:
                pass

        try:
            editor = PianoRollEditor(self._root, clip, on_apply=_on_apply, player=self.player, project=self.project)
            editor.show()
        except Exception as e:
            print(f"Failed to open Piano Roll: {e}")

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
