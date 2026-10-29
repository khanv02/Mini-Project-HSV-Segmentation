"""Small dependency-free tooltip helper for Tk and ttk widgets."""

import tkinter as tk

from .theme import COLORS, FONT_FAMILY


class ToolTip:
    """Show concise help after the pointer rests over a widget."""

    def __init__(self, widget, text: str, *, delay_ms: int = 450):
        self.widget = widget
        self.text = text
        self.delay_ms = delay_ms
        self._after_id = None
        self._window: tk.Toplevel | None = None
        widget.bind("<Enter>", self._schedule, add="+")
        widget.bind("<Leave>", self._hide, add="+")
        widget.bind("<ButtonPress>", self._hide, add="+")

    def _schedule(self, _event=None) -> None:
        self._cancel()
        self._after_id = self.widget.after(self.delay_ms, self._show)

    def _cancel(self) -> None:
        if self._after_id is not None:
            try:
                self.widget.after_cancel(self._after_id)
            except tk.TclError:
                pass
            self._after_id = None

    def _show(self) -> None:
        self._after_id = None
        if self._window is not None or not self.widget.winfo_exists():
            return
        x = self.widget.winfo_rootx() + 12
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        window = tk.Toplevel(self.widget)
        window.wm_overrideredirect(True)
        window.wm_geometry(f"+{x}+{y}")
        tk.Label(
            window,
            text=self.text,
            justify="left",
            background=COLORS["surface_raised"],
            foreground=COLORS["text"],
            highlightbackground=COLORS["border"],
            highlightthickness=1,
            relief="solid",
            borderwidth=1,
            padx=6,
            pady=4,
            wraplength=320,
            font=(FONT_FAMILY, 9),
        ).pack()
        self._window = window

    def _hide(self, _event=None) -> None:
        self._cancel()
        if self._window is not None:
            self._window.destroy()
            self._window = None

