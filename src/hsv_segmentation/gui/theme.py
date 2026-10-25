"""Shared semantic styling for the desktop analysis workspace."""

from tkinter import ttk


COLORS = {
    "background": "#f1f5f9",
    "surface": "#ffffff",
    "surface_subtle": "#f8fafc",
    "text": "#0f172a",
    "muted_text": "#475569",
    "border": "#cbd5e1",
    "primary": "#1d4ed8",
    "primary_hover": "#1e40af",
    "on_primary": "#ffffff",
    "focus": "#2563eb",
    "disabled": "#94a3b8",
    "error": "#b91c1c",
    "image_background": "#172033",
    "selection": "#f59e0b",
    "threshold_band": "#fef3c7",
}

SPACING = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24}
FONT_FAMILY = "Segoe UI"


def configure_theme(root) -> ttk.Style:
    """Apply one dependency-free light theme and return its ttk style object."""
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    root.configure(background=COLORS["background"])
    root.option_add("*Font", (FONT_FAMILY, 10))
    root.option_add("*insertBackground", COLORS["text"])
    root.option_add("*selectBackground", COLORS["primary"])
    root.option_add("*selectForeground", COLORS["on_primary"])

    style.configure("TFrame", background=COLORS["surface"])
    style.configure("Surface.TFrame", background=COLORS["surface"])
    style.configure(
        "TLabel",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        font=(FONT_FAMILY, 10),
    )
    style.configure(
        "Surface.TLabel", background=COLORS["surface"], foreground=COLORS["text"]
    )
    style.configure(
        "Muted.TLabel", foreground=COLORS["muted_text"], font=(FONT_FAMILY, 9)
    )
    style.configure(
        "Status.TLabel",
        background=COLORS["surface"],
        foreground=COLORS["muted_text"],
        padding=(SPACING["md"], SPACING["xs"]),
    )
    style.configure(
        "Section.TLabel",
        foreground=COLORS["text"],
        font=(FONT_FAMILY, 10, "bold"),
    )
    style.configure(
        "TLabelframe",
        background=COLORS["surface"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["border"],
        darkcolor=COLORS["border"],
        relief="solid",
    )
    style.configure(
        "TLabelframe.Label",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        font=(FONT_FAMILY, 10, "bold"),
    )
    style.configure(
        "TButton",
        background=COLORS["surface_subtle"],
        foreground=COLORS["text"],
        bordercolor=COLORS["border"],
        focuscolor=COLORS["focus"],
        padding=(SPACING["md"], 6),
    )
    style.map(
        "TButton",
        background=[("active", "#e2e8f0"), ("pressed", "#cbd5e1")],
        foreground=[("disabled", COLORS["disabled"])],
        bordercolor=[("focus", COLORS["focus"])],
    )
    style.configure(
        "Primary.TButton",
        background=COLORS["primary"],
        foreground=COLORS["on_primary"],
        bordercolor=COLORS["primary"],
        focuscolor=COLORS["focus"],
        padding=(SPACING["lg"], 7),
    )
    style.map(
        "Primary.TButton",
        background=[
            ("active", COLORS["primary_hover"]),
            ("pressed", COLORS["primary_hover"]),
            ("disabled", "#bfdbfe"),
        ],
        foreground=[("disabled", "#64748b")],
    )
    for name in ("TEntry", "TSpinbox", "TCombobox"):
        style.configure(
            name,
            fieldbackground=COLORS["surface"],
            foreground=COLORS["text"],
            bordercolor=COLORS["border"],
            lightcolor=COLORS["border"],
            darkcolor=COLORS["border"],
            focuscolor=COLORS["focus"],
            padding=4,
        )
        style.map(name, bordercolor=[("focus", COLORS["focus"])])
    style.configure(
        "TCheckbutton",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        focuscolor=COLORS["focus"],
    )
    style.configure(
        "Horizontal.TScale",
        background=COLORS["surface"],
        troughcolor="#dbe4f0",
        bordercolor=COLORS["border"],
        lightcolor=COLORS["primary"],
        darkcolor=COLORS["primary"],
    )
    style.configure("Error.TLabel", foreground=COLORS["error"])
    return style
