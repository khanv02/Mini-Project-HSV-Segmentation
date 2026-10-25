"""Experiment descriptions and publication action widgets."""

import tkinter as tk
from tkinter import ttk


class ExperimentPanel(ttk.LabelFrame):
    """Collect reproducibility notes without owning publication logic."""

    def __init__(self, master):
        super().__init__(master, text="Experiment Record", padding=8)
        self.columnconfigure(1, weight=1)
        self.lighting_var = tk.StringVar()
        ttk.Label(self, text="Lighting:").grid(row=0, column=0, sticky="w")
        self.lighting_entry = ttk.Entry(self, textvariable=self.lighting_var)
        self.lighting_entry.grid(row=0, column=1, sticky="ew", padx=(6, 8))
        ttk.Label(self, text="Observations:").grid(row=1, column=0, sticky="nw", pady=(6, 0))
        self.observations_text = tk.Text(self, height=2, width=50, wrap="word")
        self.observations_text.grid(row=1, column=1, sticky="ew", padx=(6, 8), pady=(6, 0))
        self.record_button = ttk.Button(self, text="Record Experiment…", state="disabled")
        self.record_button.grid(row=0, column=2, rowspan=2, sticky="ns")

    def set_command(self, command) -> None:
        self.record_button.configure(command=command)

    def set_available(self, available: bool) -> None:
        self.record_button.configure(state="normal" if available else "disabled")

    def descriptions(self) -> tuple[str, str]:
        return self.lighting_var.get().strip(), self.observations_text.get("1.0", "end").strip()

    def set_observations(self, value: str) -> None:
        self.observations_text.delete("1.0", "end")
        self.observations_text.insert("1.0", value)
