"""Dialog for editing effect parameters."""

try:
    import tkinter as tk
    from tkinter import ttk
except Exception:
    tk = None
    ttk = None


class EffectParametersDialog:
    """Dialog to edit parameters of a specific effect."""

    def __init__(self, parent, effect_slot, effect_name="Effect", on_change_cb=None):
        """
        Args:
            parent: Parent Tk widget
            effect_slot: EffectSlot instance with .effect attribute
            effect_name: Display name for the effect
            on_change_cb: Optional callback when parameters change
        """
        self.effect_slot = effect_slot
        self.effect = effect_slot.effect
        self.effect_name = effect_name
        self.on_change_cb = on_change_cb
        self.dialog = None
        self.param_widgets = {}  # Maps param_name -> widget

        # Create dialog
        self._create_dialog(parent)

    def _create_dialog(self, parent):
        """Create the parameter editor dialog."""
        if tk is None:
            return

        self.dialog = tk.Toplevel(parent)
        self.dialog.title(f"Parameters - {self.effect_name}")
        self.dialog.geometry("450x480")
        self.dialog.configure(bg="#2d2d2d")
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # Title
        title = tk.Label(
            self.dialog,
            text=f"📝 {self.effect_name} Parameters",
            font=("Segoe UI", 12, "bold"),
            bg="#2d2d2d",
            fg="#f5f5f5"
        )
        title.pack(pady=10)

        # Info about current effect
        info_frame = tk.Frame(self.dialog, bg="#1e1e1e", relief="flat")
        info_frame.pack(fill="x", padx=10, pady=5)

        tk.Label(
            info_frame,
            text=f"Effect: {type(self.effect).__name__}",
            font=("Segoe UI", 9),
            bg="#1e1e1e",
            fg="#9ca3af"
        ).pack(side="left", padx=10, pady=5)

        tk.Label(
            info_frame,
            text=f"Wet: {self.effect_slot.wet * 100:.0f}%",
            font=("Segoe UI", 9),
            bg="#1e1e1e",
            fg="#9ca3af"
        ).pack(side="right", padx=10, pady=5)

        # Parameters frame (scrollable)
        params_container = tk.Frame(self.dialog, bg="#2d2d2d")
        params_container.pack(fill="both", expand=True, padx=10, pady=10)

        canvas = tk.Canvas(params_container, bg="#2d2d2d", highlightthickness=0)
        scrollbar = tk.Scrollbar(params_container, orient="vertical", command=canvas.yview)
        scrollable_frame = tk.Frame(canvas, bg="#2d2d2d")

        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )

        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        # Build parameter controls
        self._build_parameter_controls(scrollable_frame)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        # Button frame
        button_frame = tk.Frame(self.dialog, bg="#2d2d2d")
        button_frame.pack(fill="x", padx=10, pady=15)

        # Reset button - larger and more visible
        reset_btn = tk.Button(
            button_frame,
            text="🔄 Reset to Defaults",
            command=self._on_reset,
            bg="#f59e0b",
            fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=10,
            width=18
        )
        reset_btn.pack(side="left", padx=5)

        # Close button - larger and more visible
        close_btn = tk.Button(
            button_frame,
            text="✓ Done",
            command=self.dialog.destroy,
            bg="#10b981",
            fg="#ffffff",
            font=("Segoe UI", 11, "bold"),
            relief="flat",
            cursor="hand2",
            padx=20,
            pady=10,
            width=18
        )
        close_btn.pack(side="right", padx=5)

    def _build_parameter_controls(self, parent):
        """Build UI controls for each parameter."""
        if not hasattr(self.effect, 'parameters') or not self.effect.parameters:
            tk.Label(
                parent,
                text="⚠ No configurable parameters",
                font=("Segoe UI", 10),
                bg="#2d2d2d",
                fg="#9ca3af"
            ).pack(pady=20)
            return

        for param_name, param_value in self.effect.parameters.items():
            self._create_parameter_widget(parent, param_name, param_value)

    def _create_parameter_widget(self, parent, param_name, param_value):
        """Create a widget for a single parameter."""
        # Parameter frame
        param_frame = tk.Frame(parent, bg="#1e1e1e", relief="flat", bd=1)
        param_frame.pack(fill="x", padx=5, pady=5)

        # Label frame
        label_frame = tk.Frame(param_frame, bg="#1e1e1e")
        label_frame.pack(fill="x", padx=10, pady=(8, 2))

        tk.Label(
            label_frame,
            text=param_name.replace("_", " ").title(),
            font=("Segoe UI", 10, "bold"),
            bg="#1e1e1e",
            fg="#f5f5f5",
            anchor="w"
        ).pack(side="left")

        # Value label (updated dynamically)
        value_label = tk.Label(
            label_frame,
            text=f"{param_value}",
            font=("Segoe UI", 9),
            bg="#1e1e1e",
            fg="#3b82f6",
            anchor="e"
        )
        value_label.pack(side="right")

        # Control frame
        control_frame = tk.Frame(param_frame, bg="#1e1e1e")
        control_frame.pack(fill="x", padx=10, pady=(2, 8))

        # Determine parameter type and range
        param_type = type(param_value)
        
        if param_type == bool:
            # Boolean -> Checkbutton
            var = tk.BooleanVar(value=param_value)
            check = tk.Checkbutton(
                control_frame,
                text="Enabled",
                variable=var,
                command=lambda: self._on_param_change(param_name, var.get(), value_label),
                bg="#1e1e1e",
                fg="#f5f5f5",
                selectcolor="#2d2d2d",
                activebackground="#1e1e1e",
                activeforeground="#f5f5f5",
                font=("Segoe UI", 9)
            )
            check.pack(side="left")
            self.param_widgets[param_name] = var

        elif param_type in (int, float):
            # Numeric -> Scale with Entry
            var = tk.DoubleVar(value=float(param_value))
            
            # Determine reasonable range based on parameter name and value
            min_val, max_val, resolution = self._get_param_range(param_name, param_value)

            # Scale
            scale = tk.Scale(
                control_frame,
                from_=min_val,
                to=max_val,
                resolution=resolution,
                orient="horizontal",
                variable=var,
                command=lambda v: self._on_param_change(param_name, float(v), value_label),
                bg="#1e1e1e",
                fg="#f5f5f5",
                troughcolor="#2d2d2d",
                highlightthickness=0,
                activebackground="#3b82f6",
                showvalue=0,
                length=250
            )
            scale.pack(side="left", fill="x", expand=True, padx=(0, 10))

            # Entry for precise input
            entry = tk.Entry(
                control_frame,
                textvariable=var,
                width=10,
                bg="#2d2d2d",
                fg="#f5f5f5",
                insertbackground="#f5f5f5",
                relief="flat",
                font=("Segoe UI", 9)
            )
            entry.pack(side="right")
            entry.bind("<Return>", lambda e: self._on_param_change(param_name, var.get(), value_label))

            self.param_widgets[param_name] = var

        else:
            # String or other -> Entry field
            var = tk.StringVar(value=str(param_value))
            entry = tk.Entry(
                control_frame,
                textvariable=var,
                bg="#2d2d2d",
                fg="#f5f5f5",
                insertbackground="#f5f5f5",
                relief="flat",
                font=("Segoe UI", 9)
            )
            entry.pack(fill="x", padx=5)
            entry.bind("<Return>", lambda e: self._on_param_change(param_name, var.get(), value_label))
            self.param_widgets[param_name] = var

    def _get_param_range(self, param_name, current_value):
        """Determine reasonable min/max/resolution for a parameter."""
        name_lower = param_name.lower()
        
        # Predefined ranges for common parameters
        if "threshold" in name_lower:
            return -60.0, 0.0, 0.5  # dB
        elif "ratio" in name_lower:
            return 1.0, 20.0, 0.1
        elif "attack" in name_lower or "release" in name_lower:
            return 0.001, 1.0, 0.001  # seconds
        elif "gain" in name_lower or "makeup" in name_lower:
            return -24.0, 24.0, 0.5  # dB
        elif "frequency" in name_lower or "freq" in name_lower:
            return 20.0, 20000.0, 10.0  # Hz
        elif "q" in name_lower:
            return 0.1, 10.0, 0.1
        elif "feedback" in name_lower or "damping" in name_lower:
            return 0.0, 1.0, 0.01
        elif "mix" in name_lower or "wet" in name_lower or "dry" in name_lower:
            return 0.0, 1.0, 0.01
        elif "room" in name_lower or "size" in name_lower:
            return 0.0, 1.0, 0.01
        elif "delay" in name_lower and "time" in name_lower:
            return 0.0, 2.0, 0.01  # seconds
        
        # Default ranges based on current value
        if isinstance(current_value, int):
            return 0, max(100, abs(current_value) * 2), 1
        else:
            val = abs(float(current_value))
            if val < 1.0:
                return 0.0, 1.0, 0.01
            elif val < 10.0:
                return 0.0, 10.0, 0.1
            else:
                return 0.0, max(100.0, val * 2), 1.0

    def _on_param_change(self, param_name, new_value, value_label=None):
        """Handle parameter value change."""
        # Update effect parameter
        if hasattr(self.effect, 'parameters'):
            old_type = type(self.effect.parameters.get(param_name))
            
            # Convert to appropriate type
            if old_type == bool:
                new_value = bool(new_value)
            elif old_type == int:
                new_value = int(float(new_value))
            elif old_type == float:
                new_value = float(new_value)
            
            self.effect.parameters[param_name] = new_value

        # Update value label
        if value_label:
            if isinstance(new_value, float):
                value_label.config(text=f"{new_value:.3f}")
            else:
                value_label.config(text=f"{new_value}")

        # Notify callback
        if self.on_change_cb:
            self.on_change_cb()

    def _on_reset(self):
        """Reset all parameters to default values."""
        # Get a fresh instance to extract defaults
        effect_class = type(self.effect)
        try:
            default_effect = effect_class()
            default_params = getattr(default_effect, 'parameters', {})
            
            if hasattr(self.effect, 'parameters'):
                self.effect.parameters.update(default_params)
            
            # Update UI widgets
            for param_name, widget_var in self.param_widgets.items():
                if param_name in default_params:
                    widget_var.set(default_params[param_name])
            
            if self.on_change_cb:
                self.on_change_cb()
                
        except Exception as e:
            print(f"Error resetting parameters: {e}")
