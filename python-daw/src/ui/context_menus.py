"""Context menu components for the DAW UI."""

try:
    import tkinter as tk
except Exception:  # pragma: no cover
    tk = None


class ClipContextMenu:
    """Context menu for clip operations (delete, duplicate, properties)."""
    
    def __init__(self, root, on_delete=None, on_duplicate=None, on_properties=None):
        self.root = root
        self.on_delete = on_delete
        self.on_duplicate = on_duplicate
        self.on_properties = on_properties

    def show(self, event, clip_name: str):
        """Show the context menu at the given event location."""
        if tk is None or self.root is None:
            return
            
        menu = tk.Menu(self.root, tearoff=0, bg="#2d2d2d", fg="#f5f5f5", activebackground="#3b82f6")
        
        if self.on_delete:
            menu.add_command(label=f"✂ Delete '{clip_name}'", command=self.on_delete)
        
        if self.on_duplicate:
            menu.add_command(label=f"📋 Duplicate '{clip_name}'", command=self.on_duplicate)
        
        if self.on_delete or self.on_duplicate:
            menu.add_separator()
        
        if self.on_properties:
            menu.add_command(label="Properties...", command=self.on_properties)
        
        try:
            menu.tk_popup(event.x_root, event.y_root)
        finally:
            menu.grab_release()
