"""Context menu components for the DAW UI."""

try:
    import tkinter as tk
except Exception:  # pragma: no cover
    tk = None


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
