"""Top-level layout for the still-image MVP."""

import tkinter as tk
from tkinter import ttk

from ..models import SegmentationResult
from .image_view import ImageView


class MainWindow:
    """Compose named sections and three synchronized result views."""

    def __init__(self, root: tk.Tk | None = None):
        self.root = root or tk.Tk()
        self.root.title("HSV Color Segmentation")
        self.root.minsize(960, 640)

        container = ttk.Frame(self.root, padding=10)
        container.pack(fill="both", expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(2, weight=1)

        self.input_section = ttk.LabelFrame(container, text="File Input", padding=8)
        self.input_section.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        self.open_image_button = ttk.Button(self.input_section, text="Open Image…")
        self.open_image_button.pack(side="left")
        self.source_label = ttk.Label(self.input_section, text="No image loaded")
        self.source_label.pack(side="left", padx=12)

        self.parameter_section = ttk.LabelFrame(container, text="HSV Parameters", padding=8)
        self.parameter_section.grid(row=1, column=0, sticky="ew", pady=(0, 8))

        self.visualization_section = ttk.LabelFrame(
            container, text="Result Visualization", padding=8
        )
        self.visualization_section.grid(row=2, column=0, sticky="nsew")
        for column in range(3):
            self.visualization_section.columnconfigure(column, weight=1, uniform="view")
        self.visualization_section.rowconfigure(0, weight=1)

        self.original_view = ImageView(self.visualization_section, title="Original")
        self.mask_view = ImageView(
            self.visualization_section, title="Binary Mask", is_mask=True
        )
        self.result_view = ImageView(self.visualization_section, title="Segmented Result")
        self.views = (self.original_view, self.mask_view, self.result_view)
        for column, view in enumerate(self.views):
            view.grid(row=0, column=column, sticky="nsew", padx=4)

        self.status_var = tk.StringVar(value="Ready — open a PNG, JPEG, or BMP image.")
        ttk.Label(container, textvariable=self.status_var, anchor="w").grid(
            row=3, column=0, sticky="ew", pady=(8, 0)
        )

    def show_result(self, result: SegmentationResult) -> None:
        self.original_view.show_array(result.original_rgb)
        self.mask_view.show_array(result.mask)
        self.result_view.show_array(result.segmented_rgb)
        self.source_label.configure(text=result.source.source_path.name)

    def show_status(self, message: str) -> None:
        self.status_var.set(message)

    def set_open_command(self, command) -> None:
        self.open_image_button.configure(command=command)

    def set_loading(self, loading: bool) -> None:
        self.open_image_button.configure(state="disabled" if loading else "normal")
