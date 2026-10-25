"""Compact experiment-record dialog and persistent description fields."""

import tkinter as tk
from tkinter import ttk

from .theme import COLORS, FONT_FAMILY


class ExperimentPanel:
    """Collect reproducibility notes in a reusable, non-modal dialog."""

    def __init__(self, master):
        self.window = tk.Toplevel(master)
        self.window.title("Record Experiment")
        self.window.withdraw()
        self.window.transient(master.winfo_toplevel())
        self.window.resizable(False, False)
        self.window.protocol("WM_DELETE_WINDOW", self.hide)

        content = ttk.Frame(self.window, padding=12)
        content.grid(row=0, column=0, sticky="nsew")
        content.columnconfigure(1, weight=1)
        ttk.Label(
            content,
            text="Save the current source, thresholds, mask, result, and notes.",
        ).grid(row=0, column=0, columnspan=2, sticky="w", pady=(0, 10))

        self.lighting_var = tk.StringVar(master=self.window)
        ttk.Label(content, text="Lighting conditions:").grid(row=1, column=0, sticky="w")
        self.lighting_entry = ttk.Entry(
            content, textvariable=self.lighting_var, width=48
        )
        self.lighting_entry.grid(row=1, column=1, sticky="ew", padx=(8, 0))

        ttk.Label(content, text="Observations:").grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(8, 3)
        )
        self.observations_text = tk.Text(content, height=5, width=60, wrap="word")
        self.observations_text.configure(
            background=COLORS["surface"],
            foreground=COLORS["text"],
            insertbackground=COLORS["text"],
            selectbackground=COLORS["primary"],
            selectforeground=COLORS["on_primary"],
            relief="solid",
            borderwidth=1,
            highlightthickness=1,
            highlightbackground=COLORS["border"],
            highlightcolor=COLORS["focus"],
            font=(FONT_FAMILY, 10),
        )
        self.observations_text.grid(row=3, column=0, columnspan=2, sticky="ew")

        actions = ttk.Frame(content)
        actions.grid(row=4, column=0, columnspan=2, sticky="e", pady=(10, 0))
        ttk.Button(actions, text="Cancel", command=self.hide).pack(side="right")
        self.record_button = ttk.Button(
            actions, text="Choose Folder and Record…", state="disabled"
        )
        self.record_button.pack(side="right", padx=(0, 6))

    @property
    def visible(self) -> bool:
        return self.window.state() != "withdrawn"

    def show(self) -> None:
        self.window.deiconify()
        self.window.lift()
        self.lighting_entry.focus_set()

    def hide(self) -> None:
        self.window.withdraw()

    def set_command(self, command) -> None:
        self.record_button.configure(command=command)

    def set_available(self, available: bool) -> None:
        self.record_button.configure(state="normal" if available else "disabled")

    def descriptions(self) -> tuple[str, str]:
        return self.lighting_var.get().strip(), self.observations_text.get("1.0", "end").strip()

    def set_observations(self, value: str) -> None:
        self.observations_text.delete("1.0", "end")
        self.observations_text.insert("1.0", value)
