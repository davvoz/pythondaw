"""Dialog for managing per-track effects chain."""

try:
    import tkinter as tk
    from tkinter import ttk, messagebox
except Exception:
    tk = None
    ttk = None
    messagebox = None


class EffectsChainDialog:
    """Dialog to add, remove, reorder, and configure effects on a track."""

    def __init__(self, parent, track, track_name="Track", redraw_cb=None):
        """
        Args:
            parent: Parent Tk widget
            track: Track instance with .effects attribute
            track_name: Display name for the track
            redraw_cb: Optional callback to redraw UI after changes
        """
        self.track = track
        self.track_name = track_name
        self.redraw_cb = redraw_cb
        self.dialog = None
        self.listbox = None
        self.wet_slider = None
        self.wet_var = None
        self.bypass_var = None
        self.current_selection = None

        # Available effect types (registry)
        self.effect_types = self._build_effect_registry()

        # Create dialog
        self._create_dialog(parent)

    def _build_effect_registry(self):
        """Build a registry of available effect types."""
        registry = {}
        try:
            from ...effects.reverb import Reverb
            registry["Reverb"] = Reverb
        except Exception:
            pass
        try:
            from ...effects.delay import Delay
            registry["Delay"] = Delay
        except Exception:
            pass
        try:
            from ...effects.compressor import Compressor
            registry["Compressor"] = Compressor
        except Exception:
            pass
        try:
            from ...effects.equalizer import Equalizer
            registry["Equalizer (Simple Gain)"] = Equalizer
        except Exception:
            pass
        return registry

    def _create_dialog(self, parent):
        """Create the effects chain dialog window."""
        if tk is None:
            return

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Effects Chain - {self.track_name}")
        self.dialog.geometry("500x500")
        self.dialog.configure(bg="#2d2d2d")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Title
        title = tk.Label(
            self.dialog,
            text=f"Effects Chain: {self.track_name}",
            font=("Segoe UI", 12, "bold"),
            bg="#2d2d2d",
            fg="#f5f5f5"
        )
        title.pack(pady=10)

        # Effects list container
        list_frame = tk.Frame(self.dialog, bg="#1e1e1e", relief="flat", bd=1)
        list_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Listbox with scrollbar
        list_scroll = tk.Scrollbar(list_frame, orient="vertical")
        self.listbox = tk.Listbox(
            list_frame,
            yscrollcommand=list_scroll.set,
            bg="#1e1e1e",
            fg="#f5f5f5",
            selectbackground="#3b82f6",
            selectforeground="#ffffff",
            font=("Segoe UI", 10),
            activestyle="none",
            relief="flat",
            highlightthickness=0
        )
        list_scroll.config(command=self.listbox.yview)
        list_scroll.pack(side="right", fill="y")
        self.listbox.pack(side="left", fill="both", expand=True)
        self.listbox.bind("<<ListboxSelect>>", self._on_select_effect)

        # Controls for selected effect
        controls_frame = tk.Frame(self.dialog, bg="#2d2d2d")
        controls_frame.pack(fill="x", padx=10, pady=5)

        # Bypass checkbox
        self.bypass_var = tk.BooleanVar()
        bypass_check = tk.Checkbutton(
            controls_frame,
            text="Bypass",
            variable=self.bypass_var,
            command=self._on_bypass_toggle,
            bg="#2d2d2d",
            fg="#f5f5f5",
            selectcolor="#1e1e1e",
            activebackground="#2d2d2d",
            activeforeground="#f5f5f5",
            font=("Segoe UI", 9)
        )
        bypass_check.pack(side="left", padx=5)

        # Wet/Dry slider
        tk.Label(
            controls_frame,
            text="Wet:",
            bg="#2d2d2d",
            fg="#f5f5f5",
            font=("Segoe UI", 9)
        ).pack(side="left", padx=(10, 5))

        self.wet_var = tk.DoubleVar(value=1.0)
        self.wet_slider = tk.Scale(
            controls_frame,
            from_=0.0,
            to=1.0,
            resolution=0.01,
            orient="horizontal",
            variable=self.wet_var,
            command=self._on_wet_change,
            bg="#2d2d2d",
            fg="#f5f5f5",
            troughcolor="#1e1e1e",
            highlightthickness=0,
            activebackground="#3b82f6",
            length=150
        )
        self.wet_slider.pack(side="left", padx=5)

        # Button row
        button_frame = tk.Frame(self.dialog, bg="#2d2d2d")
        button_frame.pack(fill="x", padx=10, pady=15)

        # Add button - larger
        add_btn = tk.Button(
            button_frame,
            text="➕ Add Effect",
            command=self._on_add_effect,
            bg="#10b981",
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=8
        )
        add_btn.pack(side="left", padx=5)

        # Edit parameters button - larger
        edit_btn = tk.Button(
            button_frame,
            text="⚙ Edit",
            command=self._on_edit_parameters,
            bg="#8b5cf6",
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=8
        )
        edit_btn.pack(side="left", padx=5)

        # Remove button - larger
        remove_btn = tk.Button(
            button_frame,
            text="🗑 Remove",
            command=self._on_remove_effect,
            bg="#ef4444",
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=8
        )
        remove_btn.pack(side="left", padx=5)

        # Move up/down buttons - larger
        tk.Button(
            button_frame,
            text="▲ Up",
            command=self._on_move_up,
            bg="#6b7280",
            fg="#ffffff",
            font=("Segoe UI", 10),
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=8
        ).pack(side="left", padx=2)

        tk.Button(
            button_frame,
            text="▼ Down",
            command=self._on_move_down,
            bg="#6b7280",
            fg="#ffffff",
            font=("Segoe UI", 10),
            relief="flat",
            cursor="hand2",
            padx=12,
            pady=8
        ).pack(side="left", padx=2)

        # Close button - larger
        close_btn = tk.Button(
            button_frame,
            text="Close",
            command=self.dialog.destroy,
            bg="#3b82f6",
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief="flat",
            cursor="hand2",
            padx=15,
            pady=8
        )
        close_btn.pack(side="right", padx=5)

        # Populate list
        self._refresh_list()

    def _refresh_list(self):
        """Refresh the effects listbox from track.effects."""
        if self.listbox is None:
            return
        self.listbox.delete(0, tk.END)

        fx_chain = getattr(self.track, 'effects', None)
        if fx_chain is None or not hasattr(fx_chain, 'slots'):
            return

        for idx, slot in enumerate(fx_chain.slots):
            name = slot.name or type(slot.effect).__name__
            bypass_str = " [BYPASSED]" if slot.bypass else ""
            wet_str = f" (Wet: {slot.wet * 100:.0f}%)"
            self.listbox.insert(tk.END, f"{idx + 1}. {name}{wet_str}{bypass_str}")

    def _on_select_effect(self, event=None):
        """Handle effect selection in the listbox."""
        if self.listbox is None:
            return
        selection = self.listbox.curselection()
        if not selection:
            self.current_selection = None
            return

        idx = selection[0]
        self.current_selection = idx

        fx_chain = getattr(self.track, 'effects', None)
        if fx_chain is None or idx >= len(fx_chain.slots):
            return

        slot = fx_chain.slots[idx]
        self.bypass_var.set(slot.bypass)
        self.wet_var.set(slot.wet)

    def _on_bypass_toggle(self):
        """Toggle bypass for selected effect."""
        if self.current_selection is None:
            return

        fx_chain = getattr(self.track, 'effects', None)
        if fx_chain is None or self.current_selection >= len(fx_chain.slots):
            return

        fx_chain.slots[self.current_selection].bypass = self.bypass_var.get()
        self._refresh_list()
        if self.redraw_cb:
            self.redraw_cb()

    def _on_wet_change(self, value):
        """Update wet amount for selected effect."""
        if self.current_selection is None:
            return

        fx_chain = getattr(self.track, 'effects', None)
        if fx_chain is None or self.current_selection >= len(fx_chain.slots):
            return

        fx_chain.slots[self.current_selection].wet = float(value)
        self._refresh_list()
        if self.redraw_cb:
            self.redraw_cb()

    def _on_add_effect(self):
        """Show menu to add a new effect."""
        if not self.effect_types:
            if messagebox:
                messagebox.showwarning("No Effects", "No effect types available.")
            return

        # Create popup menu
        menu = tk.Menu(self.dialog, tearoff=0, bg="#1e1e1e", fg="#f5f5f5", font=("Segoe UI", 9))
        for name, cls in self.effect_types.items():
            menu.add_command(label=name, command=lambda c=cls, n=name: self._add_effect_instance(c, n))

        # Show at mouse position
        try:
            menu.post(self.dialog.winfo_pointerx(), self.dialog.winfo_pointery())
        except Exception:
            pass

    def _add_effect_instance(self, effect_class, effect_name):
        """Add an effect instance to the track."""
        fx_chain = getattr(self.track, 'effects', None)
        if fx_chain is None:
            if messagebox:
                messagebox.showerror("Error", "Track has no effects chain.")
            return

        try:
            effect = effect_class()
            fx_chain.add(effect, name=effect_name, wet=1.0)
            self._refresh_list()
            if self.redraw_cb:
                self.redraw_cb()
        except Exception as e:
            if messagebox:
                messagebox.showerror("Error", f"Failed to add effect: {e}")

    def _on_remove_effect(self):
        """Remove selected effect."""
        if self.current_selection is None:
            if messagebox:
                messagebox.showwarning("No Selection", "Please select an effect to remove.")
            return

        fx_chain = getattr(self.track, 'effects', None)
        if fx_chain is None or self.current_selection >= len(fx_chain.slots):
            return

        fx_chain.remove(self.current_selection)
        self.current_selection = None
        self._refresh_list()
        if self.redraw_cb:
            self.redraw_cb()

    def _on_move_up(self):
        """Move selected effect up in the chain."""
        if self.current_selection is None or self.current_selection == 0:
            return

        fx_chain = getattr(self.track, 'effects', None)
        if fx_chain is None:
            return

        new_idx = self.current_selection - 1
        fx_chain.move(self.current_selection, new_idx)
        self.current_selection = new_idx
        self._refresh_list()
        self.listbox.selection_set(new_idx)
        if self.redraw_cb:
            self.redraw_cb()

    def _on_move_down(self):
        """Move selected effect down in the chain."""
        fx_chain = getattr(self.track, 'effects', None)
        if fx_chain is None:
            return
        if self.current_selection is None or self.current_selection >= len(fx_chain.slots) - 1:
            return

        new_idx = self.current_selection + 1
        fx_chain.move(self.current_selection, new_idx)
        self.current_selection = new_idx
        self._refresh_list()
        self.listbox.selection_set(new_idx)
        if self.redraw_cb:
            self.redraw_cb()

    def _on_edit_parameters(self):
        """Open parameter editor for selected effect."""
        if self.current_selection is None:
            if messagebox:
                messagebox.showwarning("No Selection", "Please select an effect to edit.")
            return

        fx_chain = getattr(self.track, 'effects', None)
        if fx_chain is None or self.current_selection >= len(fx_chain.slots):
            return

        slot = fx_chain.slots[self.current_selection]
        effect_name = slot.name or type(slot.effect).__name__

        try:
            from .effect_parameters_dialog import EffectParametersDialog
            EffectParametersDialog(
                self.dialog,
                slot,
                effect_name,
                on_change_cb=lambda: self._refresh_list() if self.redraw_cb else None
            )
        except Exception as e:
            if messagebox:
                messagebox.showerror("Error", f"Failed to open parameter editor: {e}")
