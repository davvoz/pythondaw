"""Context menu components for the DAW UI."""

try:
    import tkinter as tk
except Exception:  # pragma: no cover
    tk = None


class TrackContextMenu:
    """Context menu for track operations (add clip, rename, delete, etc)."""
    
    def __init__(self, root, on_add_audio_clip=None, on_rename=None, on_delete=None, 
                 on_duplicate=None, on_color=None, on_add_midi_demo=None, on_edit_synth=None):
        self.root = root
        self.on_add_audio_clip = on_add_audio_clip
        self.on_add_midi_demo = on_add_midi_demo
        self.on_edit_synth = on_edit_synth
        self.on_rename = on_rename
        self.on_delete = on_delete
        self.on_duplicate = on_duplicate
        self.on_color = on_color

    def show(self, event, track_name: str, track_idx: int, track_type: str = "audio"):
        """Show the context menu at the given event location.
        
        Args:
            event: Mouse event with position
            track_name: Name of the clicked track
            track_idx: Index of the clicked track
        """
        if tk is None or self.root is None:
            return
            
        menu = tk.Menu(self.root, tearoff=0, bg="#2d2d2d", fg="#f5f5f5", activebackground="#3b82f6")
        
        # Add Clip items
        if track_type.lower() == 'midi':
            if self.on_add_midi_demo:
                menu.add_command(
                    label=f"➕ Add MIDI Clip to '{track_name}'",
                    command=lambda: self.on_add_midi_demo(track_idx)
                )
            if self.on_edit_synth:
                menu.add_command(
                    label=f"🎛️ Edit Synthesizer",
                    command=lambda: self.on_edit_synth(track_idx)
                )
            if self.on_add_midi_demo or self.on_edit_synth:
                menu.add_separator()
        else:
            if self.on_add_audio_clip:
                menu.add_command(
                    label=f"🎵 Add Audio Clip to '{track_name}'", 
                    command=lambda: self.on_add_audio_clip(track_idx)
                )
                menu.add_separator()
        
        # Rename Track
        if self.on_rename:
            menu.add_command(
                label=f"✏ Rename '{track_name}'", 
                command=lambda: self.on_rename(track_idx)
            )
        
        # Change Color
        if self.on_color:
            menu.add_command(
                label=f"🎨 Change Color", 
                command=lambda: self.on_color(track_idx)
            )
        
        if (self.on_rename or self.on_color) and (self.on_duplicate or self.on_delete):
            menu.add_separator()
        
        # Duplicate Track
        if self.on_duplicate:
            menu.add_command(
                label=f"📋 Duplicate '{track_name}'", 
                command=lambda: self.on_duplicate(track_idx)
            )
        
        # Delete Track
        if self.on_delete:
            menu.add_command(
                label=f"✂ Delete '{track_name}'", 
                command=lambda: self.on_delete(track_idx)
            )
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()


class ClipContextMenu:
    """Context menu for clip operations (delete, duplicate, properties)."""
    
    def __init__(self, root, on_delete=None, on_duplicate=None, on_properties=None, 
                 on_copy=None, on_paste=None):
        self.root = root
        self.on_delete = on_delete
        self.on_duplicate = on_duplicate
        self.on_properties = on_properties
        self.on_copy = on_copy
        self.on_paste = on_paste

    def show(self, event, clip_name: str, multi_selection=False):
        """Show the context menu at the given event location.
        
        Args:
            event: Mouse event with position
            clip_name: Name of the clicked clip (or description if multi-selection)
            multi_selection: True if multiple clips are selected
        """
        if tk is None or self.root is None:
            return
            
        menu = tk.Menu(self.root, tearoff=0, bg="#2d2d2d", fg="#f5f5f5", activebackground="#3b82f6")
        
        # Copy/Paste
        if self.on_copy:
            if multi_selection:
                menu.add_command(label=f"📋 Copy {clip_name}", command=self.on_copy)
            else:
                menu.add_command(label=f"📋 Copy '{clip_name}'", command=self.on_copy)
        
        if self.on_paste:
            menu.add_command(label="📌 Paste", command=self.on_paste)
        
        if (self.on_copy or self.on_paste) and (self.on_delete or self.on_duplicate):
            menu.add_separator()
        
        # Delete/Duplicate
        if self.on_delete:
            if multi_selection:
                menu.add_command(label=f"✂ Delete {clip_name}", command=self.on_delete)
            else:
                menu.add_command(label=f"✂ Delete '{clip_name}'", command=self.on_delete)
        
        if self.on_duplicate and not multi_selection:
            menu.add_command(label=f"📋 Duplicate '{clip_name}'", command=self.on_duplicate)
        
        if (self.on_delete or self.on_duplicate) and self.on_properties:
            menu.add_separator()
        
        # Properties (only for single selection)
        if self.on_properties and not multi_selection:
            menu.add_command(label="⚙ Properties...", command=self.on_properties)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
