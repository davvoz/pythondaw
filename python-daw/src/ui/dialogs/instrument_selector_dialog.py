"""Dialog for selecting an instrument for MIDI tracks."""

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:  # pragma: no cover
    tk = None
    ttk = None


class InstrumentSelectorDialog:
    """Dialog for selecting an instrument type for MIDI tracks.
    
    This dialog uses the InstrumentRegistry to get available instruments,
    making it automatically scalable when new instruments are added.
    """
    
    def __init__(self, parent, current_instrument=None):
        """Initialize the instrument selector dialog.
        
        Args:
            parent: Parent tkinter window
            current_instrument: Current instrument instance (optional)
        """
        self.parent = parent
        self.current_instrument = current_instrument
        self.result = None  # Will contain selected instrument ID or None if cancelled
    
    @staticmethod
    def get_instruments():
        """Get list of available instruments from registry.
        
        Returns:
            List of instrument dictionaries
        """
        from src.instruments import InstrumentRegistry
        return InstrumentRegistry.get_all_instruments()
    
    @staticmethod
    def create_instrument(instrument_id):
        """Create an instrument instance by ID.
        
        Args:
            instrument_id: The ID of the instrument to create
            
        Returns:
            New instrument instance or None
        """
        from src.instruments import InstrumentRegistry
        return InstrumentRegistry.create_instrument(instrument_id)
        
    def show(self):
        """Show the dialog and return the selected instrument ID or None if cancelled."""
        if tk is None:
            return None
            
        dialog = tk.Toplevel(self.parent)
        dialog.title("Select Instrument")
        dialog.geometry("600x500")
        dialog.configure(bg="#1a1a1a")
        dialog.resizable(False, False)
        dialog.transient(self.parent)
        dialog.grab_set()

        # Center dialog
        dialog.update_idletasks()
        x = self.parent.winfo_x() + (self.parent.winfo_width() // 2) - (dialog.winfo_width() // 2)
        y = self.parent.winfo_y() + (self.parent.winfo_height() // 2) - (dialog.winfo_height() // 2)
        dialog.geometry(f"+{x}+{y}")

        # Main container
        main_frame = tk.Frame(dialog, bg="#1a1a1a")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Title
        title_label = tk.Label(
            main_frame,
            text="🎹 Select Instrument",
            font=("Segoe UI", 16, "bold"),
            fg="#3b82f6",
            bg="#1a1a1a"
        )
        title_label.pack(pady=(0, 10))
        
        subtitle_label = tk.Label(
            main_frame,
            text="Choose an instrument for this MIDI track",
            font=("Segoe UI", 10),
            fg="#9ca3af",
            bg="#1a1a1a"
        )
        subtitle_label.pack(pady=(0, 20))

        # Scrollable frame for instruments
        canvas = tk.Canvas(main_frame, bg="#1a1a1a", highlightthickness=0, height=320)
        scrollbar = tk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#1a1a1a")
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw", width=540)
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Get instruments from registry
        instruments = self.get_instruments()
        
        selected_id = tk.StringVar(value="advanced_synth")  # Default to advanced
        
        # Determine current instrument if provided
        if self.current_instrument:
            from src.instruments import InstrumentRegistry
            current_id = InstrumentRegistry.get_instrument_id(self.current_instrument)
            if current_id:
                selected_id.set(current_id)

        # Create instrument cards
        for instrument in instruments:
            self._create_instrument_card(scrollable_frame, instrument, selected_id)

        # Button frame
        btn_frame = tk.Frame(main_frame, bg="#1a1a1a")
        btn_frame.pack(fill="x", pady=(20, 0))

        def on_confirm():
            """Handle Confirm button."""
            self.result = selected_id.get()
            dialog.destroy()

        def on_cancel():
            """Handle Cancel button."""
            self.result = None
            dialog.destroy()

        # Confirm button (pack first with side=right so it appears on the right)
        confirm_btn = tk.Button(
            btn_frame,
            text="✓ Confirm",
            command=on_confirm,
            bg="#10b981",
            fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=10,
            width=14
        )
        confirm_btn.pack(side="right")

        # Cancel button (pack second with side=right so it appears to the left of Confirm)
        cancel_btn = tk.Button(
            btn_frame,
            text="✗ Cancel",
            command=on_cancel,
            bg="#6b7280",
            fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=10,
            width=14
        )
        cancel_btn.pack(side="right", padx=(0, 8))

        dialog.bind('<Return>', lambda e: on_confirm())
        dialog.bind('<Escape>', lambda e: on_cancel())

        dialog.wait_window()
        return self.result
    
    def _create_instrument_card(self, parent, instrument, selected_var):
        """Create a selectable card for an instrument."""
        card = tk.Frame(parent, bg="#2d2d2d", relief="solid", borderwidth=1)
        card.pack(fill="x", pady=8, padx=5)
        
        # Radio button (invisible, just for selection)
        radio = tk.Radiobutton(
            card,
            variable=selected_var,
            value=instrument["id"],
            bg="#2d2d2d",
            activebackground="#2d2d2d",
            selectcolor="#3b82f6",
            font=("Segoe UI", 1)  # Tiny font to make it almost invisible
        )
        radio.pack(side="left", padx=(10, 5))
        
        # Content frame
        content = tk.Frame(card, bg="#2d2d2d")
        content.pack(side="left", fill="both", expand=True, padx=10, pady=12)
        
        # Header with icon and name
        header = tk.Frame(content, bg="#2d2d2d")
        header.pack(fill="x", pady=(0, 8))
        
        icon_label = tk.Label(
            header,
            text=instrument["icon"],
            font=("Segoe UI", 20),
            bg="#2d2d2d",
            fg="#ffffff"
        )
        icon_label.pack(side="left", padx=(0, 10))
        
        name_label = tk.Label(
            header,
            text=instrument["name"],
            font=("Segoe UI", 12, "bold"),
            fg="#ffffff",
            bg="#2d2d2d",
            anchor="w"
        )
        name_label.pack(side="left", fill="x")
        
        # Description
        desc_label = tk.Label(
            content,
            text=instrument["description"],
            font=("Segoe UI", 9),
            fg="#9ca3af",
            bg="#2d2d2d",
            wraplength=450,
            justify="left",
            anchor="w"
        )
        desc_label.pack(fill="x")
        
        # Make the entire card clickable
        def select_instrument(event=None):
            selected_var.set(instrument["id"])
            
        for widget in [card, content, header, icon_label, name_label, desc_label]:
            widget.bind("<Button-1>", select_instrument)
            widget.config(cursor="hand2")
        
        # Highlight selected card
        def update_highlight(*args):
            if selected_var.get() == instrument["id"]:
                card.config(bg="#3b82f6", borderwidth=2)
                content.config(bg="#3b82f6")
                header.config(bg="#3b82f6")
                icon_label.config(bg="#3b82f6")
                name_label.config(bg="#3b82f6")
                desc_label.config(bg="#3b82f6")
            else:
                card.config(bg="#2d2d2d", borderwidth=1)
                content.config(bg="#2d2d2d")
                header.config(bg="#2d2d2d")
                icon_label.config(bg="#2d2d2d")
                name_label.config(bg="#2d2d2d")
                desc_label.config(bg="#2d2d2d")
        
        selected_var.trace_add("write", update_highlight)
        update_highlight()
