"""Shared semantic styling for the desktop analysis workspace."""

from tkinter import ttk


COLORS = {
    "background": "#090f1c",
    "surface": "#111827",
    "surface_subtle": "#172033",
    "surface_raised": "#1e293b",
    "text": "#e5edf8",
    "muted_text": "#a7b4c8",
    "border": "#334155",
    "primary": "#3b82f6",
    "primary_hover": "#2563eb",
    "on_primary": "#ffffff",
    "focus": "#60a5fa",
    "disabled": "#64748b",
    "error": "#f87171",
    "image_background": "#050914",
    "selection": "#fbbf24",
    "threshold_band": "#3b2f16",
    "success": "#34d399",
    "warning": "#fbbf24",
}

SPACING = {"xs": 4, "sm": 8, "md": 12, "lg": 16, "xl": 24}
FONT_FAMILY = "Segoe UI"


def configure_theme(root) -> ttk.Style:
    """Apply the dependency-free dark workspace theme."""
    style = ttk.Style(root)
    if "clam" in style.theme_names():
        style.theme_use("clam")

    root.configure(background=COLORS["background"])
    root.option_add("*Font", (FONT_FAMILY, 10))
    root.option_add("*insertBackground", COLORS["text"])
    root.option_add("*selectBackground", COLORS["primary"])
    root.option_add("*selectForeground", COLORS["on_primary"])
    root.option_add("*TCombobox*Listbox.background", COLORS["surface_raised"])
    root.option_add("*TCombobox*Listbox.foreground", COLORS["text"])
    root.option_add("*TCombobox*Listbox.selectBackground", COLORS["primary_hover"])
    root.option_add("*TCombobox*Listbox.selectForeground", COLORS["on_primary"])

    style.configure("TFrame", background=COLORS["surface"])
    style.configure("App.TFrame", background=COLORS["background"])
    style.configure("Card.TFrame", background=COLORS["surface"])
    style.configure("Surface.TFrame", background=COLORS["surface"])
    style.configure("Sidebar.TFrame", background=COLORS["surface_subtle"])
    style.configure("Toolbar.TFrame", background=COLORS["surface"])
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
        "Eyebrow.TLabel",
        foreground=COLORS["primary"],
        font=(FONT_FAMILY, 8, "bold"),
    )
    style.configure(
        "Title.TLabel",
        foreground=COLORS["text"],
        font=(FONT_FAMILY, 12, "bold"),
    )
    style.configure(
        "Subtitle.TLabel",
        foreground=COLORS["muted_text"],
        font=(FONT_FAMILY, 9),
    )
    style.configure(
        "Metric.TLabel",
        foreground=COLORS["primary"],
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
        padding=(10, 5),
    )
    style.map(
        "TButton",
        background=[
            ("active", COLORS["surface_raised"]),
            ("pressed", COLORS["border"]),
            ("disabled", COLORS["surface"]),
        ],
        foreground=[("disabled", COLORS["disabled"])],
        bordercolor=[("focus", COLORS["focus"])],
    )
    style.configure(
        "Primary.TButton",
        background=COLORS["primary"],
        foreground=COLORS["on_primary"],
        bordercolor=COLORS["primary"],
        focuscolor=COLORS["focus"],
        padding=(SPACING["lg"], 6),
    )
    style.map(
        "Primary.TButton",
        background=[
            ("active", COLORS["primary_hover"]),
            ("pressed", COLORS["primary_hover"]),
            ("disabled", COLORS["surface_raised"]),
        ],
        foreground=[("disabled", COLORS["disabled"])],
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
        style.map(
            name,
            fieldbackground=[("disabled", COLORS["surface_subtle"])],
            foreground=[("disabled", COLORS["disabled"])],
            bordercolor=[("focus", COLORS["focus"])],
        )
    style.configure(
        "TCheckbutton",
        background=COLORS["surface"],
        foreground=COLORS["text"],
        focuscolor=COLORS["focus"],
        padding=(2, 2),
    )
    style.map(
        "TCheckbutton",
        background=[("active", COLORS["surface_raised"])],
        foreground=[("disabled", COLORS["disabled"])],
        indicatorcolor=[
            ("selected", COLORS["primary"]),
            ("disabled", COLORS["surface_raised"]),
        ],
    )
    style.configure(
        "TNotebook",
        background=COLORS["surface_subtle"],
        bordercolor=COLORS["border"],
        tabmargins=(4, 4, 4, 0),
    )
    style.configure(
        "TNotebook.Tab",
        background=COLORS["surface_subtle"],
        foreground=COLORS["muted_text"],
        padding=(14, 7),
        font=(FONT_FAMILY, 9, "bold"),
    )
    style.map(
        "TNotebook.Tab",
        background=[
            ("selected", COLORS["surface_raised"]),
            ("active", COLORS["surface_raised"]),
        ],
        foreground=[("selected", COLORS["primary"]), ("active", COLORS["text"])],
        focuscolor=[("focus", COLORS["focus"])],
    )
    style.configure(
        "Treeview",
        background=COLORS["surface"],
        fieldbackground=COLORS["surface"],
        foreground=COLORS["text"],
        bordercolor=COLORS["border"],
        rowheight=24,
        font=(FONT_FAMILY, 9),
    )
    style.configure(
        "Treeview.Heading",
        background=COLORS["surface_subtle"],
        foreground=COLORS["text"],
        font=(FONT_FAMILY, 9, "bold"),
        padding=(4, 5),
    )
    style.map(
        "Treeview",
        background=[("selected", COLORS["primary_hover"])],
        foreground=[("selected", COLORS["on_primary"])],
    )
    style.configure(
        "Horizontal.TScale",
        background=COLORS["surface"],
        troughcolor=COLORS["surface_raised"],
        bordercolor=COLORS["border"],
        lightcolor=COLORS["primary"],
        darkcolor=COLORS["primary"],
    )
    style.configure(
        "TScrollbar",
        background=COLORS["surface_raised"],
        troughcolor=COLORS["surface_subtle"],
        bordercolor=COLORS["surface_subtle"],
        arrowcolor=COLORS["muted_text"],
    )
    style.configure("TSeparator", background=COLORS["border"])
    style.configure("Error.TLabel", foreground=COLORS["error"])
    return style
