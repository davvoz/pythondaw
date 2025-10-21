"""Dialog for adding a new track to the project."""

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover
    tk = None
    ttk = None


class AddTrackDialog:
    """Dialog for adding a new track with name and color selection."""
    
    def __init__(self, parent, suggested_name: str, available_colors=None):
        self.parent = parent
        self.suggested_name = suggested_name
        self.available_colors = available_colors or [
            "#3b82f6", "#10b981", "#f59e0b", "#ef4444",
            "#8b5cf6", "#ec4899", "#06b6d4", "#84cc16"
        ]
        self.result = None  # (name, color, type) or None if cancelled

    def show(self):
        """Show the dialog and return (name, color) tuple or None if cancelled."""
        if tk is None:
            return None
            
        dialog = tk.Toplevel(self.parent)
        dialog.title("Add Track")
        dialog.geometry("380x280")
        dialog.configure(bg="#2d2d2d")
        dialog.resizable(False, False)
        dialog.transient(self.parent)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Dialog content
        content = ttk.Frame(dialog, style="Sidebar.TFrame")
        content.pack(fill="both", expand=True, padx=20, pady=20)

        # Track name
        ttk.Label(content, text="Track Name:", style="Sidebar.TLabel").pack(anchor="w", pady=(0, 4))
        name_var = tk.StringVar(value=self.suggested_name)
        name_entry = ttk.Entry(content, textvariable=name_var, font=("Segoe UI", 10))
        name_entry.pack(fill="x", pady=(0, 16))
        name_entry.focus_set()
        name_entry.select_range(0, tk.END)

        # Track type
        ttk.Label(content, text="Track Type:", style="Sidebar.TLabel").pack(anchor="w", pady=(0, 4))
        type_var = tk.StringVar(value="Audio")
        type_frame = ttk.Frame(content, style="Sidebar.TFrame")
        type_frame.pack(fill="x", pady=(0, 12))
        for t in ("Audio", "MIDI"):
            ttk.Radiobutton(type_frame, text=t, value=t, variable=type_var).pack(side="left", padx=6)

        # Track color
        ttk.Label(content, text="Track Color:", style="Sidebar.TLabel").pack(anchor="w", pady=(0, 8))
        color_frame = ttk.Frame(content, style="Sidebar.TFrame")
        color_frame.pack(fill="x", pady=(0, 16))

        selected_color = tk.StringVar(value=self.available_colors[0])

        # Color buttons
        color_buttons = []
        
        def make_color_button(col):
            btn = tk.Button(
                color_frame, bg=col, width=3, height=1,
                relief="raised", borderwidth=2,
                command=lambda: [selected_color.set(col), update_preview()]
            )
            return btn

        for col in self.available_colors:
            btn = make_color_button(col)
            btn.pack(side="left", padx=2)
            color_buttons.append(btn)

        # Preview
        preview_frame = ttk.Frame(content, style="Sidebar.TFrame")
        preview_frame.pack(fill="x", pady=(0, 16))
        ttk.Label(preview_frame, text="Preview:", style="Sidebar.TLabel").pack(side="left", padx=(0, 8))
        preview_canvas = tk.Canvas(preview_frame, width=120, height=24, bg="#1a1a1a", highlightthickness=0)
        preview_canvas.pack(side="left")

        def update_preview():
            """Update the preview canvas and color button states."""
            preview_canvas.delete("all")
            preview_canvas.create_rectangle(2, 2, 118, 22, fill=selected_color.get(), outline=selected_color.get())
            preview_canvas.create_text(60, 12, text=name_var.get() or "Track", fill="#ffffff", font=("Segoe UI", 9, "bold"))
            
            # Highlight selected button
            for i, col in enumerate(self.available_colors):
                if col == selected_color.get():
                    color_buttons[i].config(relief="sunken", borderwidth=3)
                else:
                    color_buttons[i].config(relief="raised", borderwidth=2)

        update_preview()
        name_var.trace_add("write", lambda *args: update_preview())

        # Buttons
        btn_frame = ttk.Frame(content, style="Sidebar.TFrame")
        btn_frame.pack(fill="x", pady=(8, 0))

        def on_ok():
            """Handle OK button."""
            name = (name_var.get() or "").strip()
            if not name:
                name = self.suggested_name
            self.result = (name, selected_color.get(), type_var.get())
            dialog.destroy()

        def on_cancel():
            """Handle Cancel button."""
            self.result = None
            dialog.destroy()

        # Larger, more visible buttons
        cancel_btn = tk.Button(
            btn_frame,
            text="Cancel",
            command=on_cancel,
            bg="#6b7280",
            fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=10,
            width=10
        )
        cancel_btn.pack(side="right", padx=(8, 0))

        ok_btn = tk.Button(
            btn_frame,
            text="OK",
            command=on_ok,
            bg="#10b981",
            fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=10,
            width=10
        )
        ok_btn.pack(side="right")

        dialog.bind('<Return>', lambda e: on_ok())
        dialog.bind('<Escape>', lambda e: on_cancel())

        dialog.wait_window()
        return self.result
