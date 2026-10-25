"""Scrollable, zoomable image preview; processing arrays stay untouched."""

import tkinter as tk
from tkinter import ttk

import numpy as np
from PIL import Image, ImageTk


class ImageView(ttk.LabelFrame):
    """Display an RGB image or binary mask with fit, zoom and pan controls."""

    MIN_ZOOM = 0.25
    MAX_ZOOM = 8.0
    ZOOM_STEP = 1.25

    def __init__(self, master, *, title: str, is_mask: bool = False, **kwargs):
        super().__init__(master, text=title, padding=2, **kwargs)
        self._is_mask = is_mask
        self._source: np.ndarray | None = None
        self._photo: ImageTk.PhotoImage | None = None
        self._image_item: int | None = None
        self._placeholder_item: int | None = None
        self._render_id: str | None = None
        self._zoom_factor = 1.0

        toolbar = ttk.Frame(self)
        toolbar.pack(fill="x", padx=2, pady=(0, 2))
        ttk.Button(toolbar, text="−", width=3, command=self.zoom_out).pack(side="left")
        ttk.Button(toolbar, text="Fit", width=5, command=self.fit).pack(
            side="left", padx=3
        )
        ttk.Button(toolbar, text="+", width=3, command=self.zoom_in).pack(side="left")
        self._zoom_text = "Fit"
        self._zoom_label = ttk.Label(toolbar, text=self._zoom_text, anchor="e")
        self._zoom_label.pack(side="right", padx=(4, 2))

        viewport = ttk.Frame(self)
        viewport.pack(fill="both", expand=True)
        viewport.columnconfigure(0, weight=1)
        viewport.rowconfigure(0, weight=1)

        self.canvas = tk.Canvas(
            viewport,
            background="#202020",
            borderwidth=0,
            highlightthickness=0,
        )
        self._horizontal = ttk.Scrollbar(
            viewport, orient="horizontal", command=self.canvas.xview
        )
        self._vertical = ttk.Scrollbar(
            viewport, orient="vertical", command=self.canvas.yview
        )
        self.canvas.configure(
            xscrollcommand=self._horizontal.set,
            yscrollcommand=self._vertical.set,
        )
        self.canvas.grid(row=0, column=0, sticky="nsew")
        self._vertical.grid(row=0, column=1, sticky="ns")
        self._horizontal.grid(row=1, column=0, sticky="ew")
        self._vertical.grid_remove()
        self._horizontal.grid_remove()

        self.canvas.bind("<Configure>", self._on_resize, add="+")
        self.canvas.bind("<MouseWheel>", self._on_mouse_wheel, add="+")
        self.canvas.bind("<Button-4>", lambda _event: self._change_zoom(self.ZOOM_STEP))
        self.canvas.bind("<Button-5>", lambda _event: self._change_zoom(1 / self.ZOOM_STEP))
        self.canvas.bind("<Double-Button-1>", lambda _event: self.fit())
        self._show_placeholder()

    @property
    def source_array(self) -> np.ndarray | None:
        return None if self._source is None else self._source.copy()

    @property
    def zoom_factor(self) -> float:
        """Zoom relative to the current fit-to-window scale."""
        return self._zoom_factor

    @property
    def zoom_text(self) -> str:
        return self._zoom_text

    def _set_zoom_text(self, text: str) -> None:
        self._zoom_text = text
        self._zoom_label.configure(text=text)

    def show_array(self, array: np.ndarray | None) -> None:
        if array is None:
            self._source = None
            self._photo = None
            self._zoom_factor = 1.0
            self._set_zoom_text("Fit")
            self._show_placeholder()
            return
        if self._is_mask:
            if not isinstance(array, np.ndarray) or array.dtype != np.uint8 or array.ndim != 2:
                raise ValueError("mask preview requires a uint8 (height, width) array")
        elif (
            not isinstance(array, np.ndarray)
            or array.dtype != np.uint8
            or array.ndim != 3
            or array.shape[2] != 3
        ):
            raise ValueError("image preview requires a uint8 RGB array")
        self._source = array.copy()
        self._hide_placeholder()
        self._schedule_render()

    def fit(self) -> None:
        self._zoom_factor = 1.0
        self._set_zoom_text("Fit")
        self._schedule_render()

    def zoom_in(self) -> None:
        self._change_zoom(self.ZOOM_STEP)

    def zoom_out(self) -> None:
        self._change_zoom(1 / self.ZOOM_STEP)

    def _change_zoom(self, multiplier: float) -> str:
        if self._source is None:
            return "break"
        next_zoom = min(self.MAX_ZOOM, max(self.MIN_ZOOM, self._zoom_factor * multiplier))
        if next_zoom != self._zoom_factor:
            self._zoom_factor = next_zoom
            self._set_zoom_text(f"{round(self._zoom_factor * 100)}%")
            self._schedule_render()
        return "break"

    def _on_mouse_wheel(self, event) -> str:
        multiplier = self.ZOOM_STEP if event.delta > 0 else 1 / self.ZOOM_STEP
        return self._change_zoom(multiplier)

    def _on_resize(self, _event=None) -> None:
        self._schedule_render()

    def _schedule_render(self) -> None:
        if self._source is None or not self.winfo_exists():
            return
        if self._render_id is not None:
            try:
                self.after_cancel(self._render_id)
            except tk.TclError:
                pass
        self._render_id = self.after_idle(self._render)

    def _show_placeholder(self) -> None:
        if self._image_item is not None:
            self.canvas.delete(self._image_item)
            self._image_item = None
        if self._placeholder_item is None:
            self._placeholder_item = self.canvas.create_text(
                0, 0, text="No image", fill="#d0d0d0", anchor="center"
            )
        self.canvas.coords(
            self._placeholder_item,
            max(1, self.canvas.winfo_width()) / 2,
            max(1, self.canvas.winfo_height()) / 2,
        )
        self.canvas.configure(scrollregion=(0, 0, 0, 0))

    def _hide_placeholder(self) -> None:
        if self._placeholder_item is not None:
            self.canvas.delete(self._placeholder_item)
            self._placeholder_item = None

    def _render(self) -> None:
        self._render_id = None
        if self._source is None or not self.winfo_exists():
            return

        horizontal_center = sum(self.canvas.xview()) / 2
        vertical_center = sum(self.canvas.yview()) / 2
        canvas_width = max(1, self.canvas.winfo_width())
        canvas_height = max(1, self.canvas.winfo_height())
        source_height, source_width = self._source.shape[:2]
        fit_scale = min(canvas_width / source_width, canvas_height / source_height)
        scale = fit_scale * self._zoom_factor
        target_width = max(1, round(source_width * scale))
        target_height = max(1, round(source_height * scale))

        image = Image.fromarray(self._source)
        resampling = Image.Resampling.NEAREST if self._is_mask else Image.Resampling.LANCZOS
        if image.size != (target_width, target_height):
            image = image.resize((target_width, target_height), resampling)
        self._photo = ImageTk.PhotoImage(image=image, master=self.canvas)

        content_width = max(canvas_width, target_width)
        content_height = max(canvas_height, target_height)
        x = (content_width - target_width) / 2
        y = (content_height - target_height) / 2
        if self._image_item is None:
            self._image_item = self.canvas.create_image(x, y, image=self._photo, anchor="nw")
        else:
            self.canvas.coords(self._image_item, x, y)
            self.canvas.itemconfigure(self._image_item, image=self._photo)
        self.canvas.configure(scrollregion=(0, 0, content_width, content_height))
        if target_width > canvas_width:
            self._horizontal.grid()
        else:
            self._horizontal.grid_remove()
        if target_height > canvas_height:
            self._vertical.grid()
        else:
            self._vertical.grid_remove()
        horizontal_visible = min(1.0, canvas_width / content_width)
        vertical_visible = min(1.0, canvas_height / content_height)
        self.canvas.xview_moveto(
            max(0.0, min(1.0 - horizontal_visible, horizontal_center - horizontal_visible / 2))
        )
        self.canvas.yview_moveto(
            max(0.0, min(1.0 - vertical_visible, vertical_center - vertical_visible / 2))
        )

    def destroy(self) -> None:
        if self._render_id is not None:
            try:
                self.after_cancel(self._render_id)
            except tk.TclError:
                pass
            self._render_id = None
        super().destroy()
