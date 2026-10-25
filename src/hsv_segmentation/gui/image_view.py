"""Scrollable, zoomable image preview; processing arrays stay untouched."""

from collections.abc import Callable
import tkinter as tk
from tkinter import ttk

import numpy as np
from PIL import Image, ImageTk

from .theme import COLORS


class ImageView(ttk.LabelFrame):
    """Display an RGB image or binary mask with fit, zoom and pan controls."""

    MIN_ZOOM = 0.25
    MAX_ZOOM = 8.0
    ZOOM_STEP = 1.25
    IMAGE_BACKGROUND = COLORS["image_background"]
    DEFAULT_PLACEHOLDER = "Open an image or video to begin"

    def __init__(
        self, master, *, title: str, is_mask: bool = False,
        placeholder_text: str = DEFAULT_PLACEHOLDER,
        on_sample: Callable[[int, int], None] | None = None,
        on_roi_sample: Callable[[int, int, int, int], None] | None = None,
        **kwargs,
    ):
        super().__init__(master, text=title, padding=2, **kwargs)
        self._is_mask = is_mask
        self._placeholder_text = placeholder_text
        self._sample_callback = on_sample
        self._roi_sample_callback = on_roi_sample
        self._sampling_mode = "pixel"
        self._sampling_enabled = False
        self._sampled_pixel: tuple[int, int] | None = None
        self._sampled_roi: tuple[int, int, int, int] | None = None
        self._sample_marker: int | None = None
        self._drag_start: tuple[float, float] | None = None
        self._display_bounds: tuple[float, float, int, int] | None = None
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

        style = ttk.Style(self)
        self._empty_background = style.lookup("TFrame", "background") or "#f0f0f0"
        self._placeholder_foreground = style.lookup("TLabel", "foreground") or "#505050"
        self.canvas = tk.Canvas(
            viewport,
            background=self._empty_background,
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
        self.canvas.bind("<ButtonPress-1>", self._on_sample_press, add="+")
        self.canvas.bind("<B1-Motion>", self._on_sample_drag, add="+")
        self.canvas.bind("<ButtonRelease-1>", self._on_sample_release, add="+")
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

    @property
    def placeholder_text(self) -> str:
        return self._placeholder_text

    @property
    def sampling_enabled(self) -> bool:
        return self._sampling_enabled

    @property
    def sampling_mode(self) -> str:
        return self._sampling_mode

    def set_sample_callback(self, callback: Callable[[int, int], None] | None) -> None:
        self._sample_callback = callback

    def set_roi_sample_callback(
        self, callback: Callable[[int, int, int, int], None] | None
    ) -> None:
        self._roi_sample_callback = callback

    def set_sampling_mode(self, mode: str) -> None:
        if mode not in {"pixel", "roi"}:
            raise ValueError("sampling mode must be pixel or roi")
        if mode != self._sampling_mode:
            self._sampling_mode = mode
            self._sampled_pixel = None
            self._sampled_roi = None
            if self._sample_marker is not None:
                self.canvas.delete(self._sample_marker)
                self._sample_marker = None

    def set_sampling_enabled(self, enabled: bool) -> None:
        self._sampling_enabled = bool(enabled and self._source is not None)
        self._drag_start = None
        self.canvas.configure(cursor="crosshair" if self._sampling_enabled else "")

    def source_pixel_at_canvas(self, canvas_x: float, canvas_y: float) -> tuple[int, int] | None:
        """Map scroll-region canvas coordinates to a source pixel."""
        if self._source is None or self._display_bounds is None:
            return None
        left, top, displayed_width, displayed_height = self._display_bounds
        if not (
            left <= canvas_x < left + displayed_width
            and top <= canvas_y < top + displayed_height
        ):
            return None
        source_height, source_width = self._source.shape[:2]
        x = min(source_width - 1, int((canvas_x - left) * source_width / displayed_width))
        y = min(source_height - 1, int((canvas_y - top) * source_height / displayed_height))
        return x, y

    def source_roi_at_canvas(
        self, start_x: float, start_y: float, end_x: float, end_y: float
    ) -> tuple[int, int, int, int] | None:
        """Map two scroll-region points to nonempty, end-exclusive source bounds."""
        if self._source is None or self._display_bounds is None:
            return None
        left, top, displayed_width, displayed_height = self._display_bounds
        epsilon = 1e-6
        points = []
        for x, y in ((start_x, start_y), (end_x, end_y)):
            clamped_x = min(left + displayed_width - epsilon, max(left, x))
            clamped_y = min(top + displayed_height - epsilon, max(top, y))
            points.append(self.source_pixel_at_canvas(clamped_x, clamped_y))
        if points[0] is None or points[1] is None:
            return None
        first_x, first_y = points[0]
        second_x, second_y = points[1]
        return (
            min(first_x, second_x),
            min(first_y, second_y),
            max(first_x, second_x) + 1,
            max(first_y, second_y) + 1,
        )

    def _event_canvas_point(self, event) -> tuple[float, float]:
        return self.canvas.canvasx(event.x), self.canvas.canvasy(event.y)

    def _on_sample_press(self, event) -> None:
        if not self._sampling_enabled:
            return
        point = self._event_canvas_point(event)
        pixel = self.source_pixel_at_canvas(*point)
        if pixel is None:
            return
        self._drag_start = point
        if self._sampling_mode == "roi":
            self._sampled_pixel = None
            self._sampled_roi = None
            if self._sample_marker is None:
                self._sample_marker = self.canvas.create_rectangle(
                    point[0], point[1], point[0], point[1],
                    outline=COLORS["selection"], width=2, dash=(4, 2),
                )

    def _on_sample_drag(self, event) -> None:
        if not self._sampling_enabled or self._sampling_mode != "roi" or self._drag_start is None:
            return
        current = self._event_canvas_point(event)
        if self._sample_marker is not None:
            self.canvas.coords(self._sample_marker, *self._drag_start, *current)

    def _on_sample_release(self, event) -> None:
        if not self._sampling_enabled or self._drag_start is None:
            return
        start = self._drag_start
        self._drag_start = None
        current = self._event_canvas_point(event)
        if self._sampling_mode == "pixel":
            pixel = self.source_pixel_at_canvas(*current) or self.source_pixel_at_canvas(*start)
            if pixel is None or self._sample_callback is None:
                return
            self._sampled_pixel = pixel
            self._sampled_roi = None
            self._replace_sample_marker("oval")
            self._draw_sample_marker()
            self._sample_callback(*pixel)
            return
        roi = self.source_roi_at_canvas(*start, *current)
        if roi is None or self._roi_sample_callback is None:
            return
        self._sampled_pixel = None
        self._sampled_roi = roi
        self._replace_sample_marker("rectangle")
        self._draw_sample_marker()
        self._roi_sample_callback(*roi)

    def _set_zoom_text(self, text: str) -> None:
        self._zoom_text = text
        self._zoom_label.configure(text=text)

    def show_array(self, array: np.ndarray | None) -> None:
        if array is None:
            self._source = None
            self._photo = None
            self._zoom_factor = 1.0
            self._display_bounds = None
            self._sampled_pixel = None
            self._sampled_roi = None
            if self._sample_marker is not None:
                self.canvas.delete(self._sample_marker)
            self._sample_marker = None
            self.set_sampling_enabled(False)
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
        self._sampled_pixel = None
        self._sampled_roi = None
        if self._sample_marker is not None:
            self.canvas.delete(self._sample_marker)
            self._sample_marker = None
        self.canvas.configure(background=self.IMAGE_BACKGROUND)
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
        if self._source is None:
            self._show_placeholder()
        else:
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
        self.canvas.configure(background=self._empty_background)
        if self._image_item is not None:
            self.canvas.delete(self._image_item)
            self._image_item = None
        if self._placeholder_item is None:
            self._placeholder_item = self.canvas.create_text(
                0, 0,
                text=self._placeholder_text,
                fill=self._placeholder_foreground,
                anchor="center",
                justify="center",
            )
        canvas_width = max(1, self.canvas.winfo_width())
        canvas_height = max(1, self.canvas.winfo_height())
        self.canvas.itemconfigure(
            self._placeholder_item, width=max(120, canvas_width - 32)
        )
        self.canvas.coords(
            self._placeholder_item,
            canvas_width / 2,
            canvas_height / 2,
        )
        self.canvas.configure(scrollregion=(0, 0, 0, 0))

    def _hide_placeholder(self) -> None:
        if self._placeholder_item is not None:
            self.canvas.delete(self._placeholder_item)
            self._placeholder_item = None

    def _draw_sample_marker(self) -> None:
        if self._display_bounds is None or self._source is None:
            return
        left, top, displayed_width, displayed_height = self._display_bounds
        source_height, source_width = self._source.shape[:2]
        if self._sampled_roi is not None:
            roi_left, roi_top, roi_right, roi_bottom = self._sampled_roi
            self._replace_sample_marker("rectangle")
            self.canvas.coords(
                self._sample_marker,
                left + roi_left * displayed_width / source_width,
                top + roi_top * displayed_height / source_height,
                left + roi_right * displayed_width / source_width,
                top + roi_bottom * displayed_height / source_height,
            )
        elif self._sampled_pixel is not None:
            pixel_x, pixel_y = self._sampled_pixel
            x = left + (pixel_x + 0.5) * displayed_width / source_width
            y = top + (pixel_y + 0.5) * displayed_height / source_height
            radius = 6
            self._replace_sample_marker("oval")
            self.canvas.coords(
                self._sample_marker, x - radius, y - radius, x + radius, y + radius
            )
        if self._sample_marker is not None:
            self.canvas.tag_raise(self._sample_marker)

    def _replace_sample_marker(self, kind: str) -> None:
        current_kind = None
        if self._sample_marker is not None:
            current_kind = self.canvas.type(self._sample_marker)
        if current_kind == kind:
            return
        if self._sample_marker is not None:
            self.canvas.delete(self._sample_marker)
        create = self.canvas.create_oval if kind == "oval" else self.canvas.create_rectangle
        self._sample_marker = create(
            0, 0, 0, 0, outline=COLORS["selection"], width=2, dash=(4, 2)
        )

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
        self._display_bounds = (x, y, target_width, target_height)
        if self._image_item is None:
            self._image_item = self.canvas.create_image(x, y, image=self._photo, anchor="nw")
        else:
            self.canvas.coords(self._image_item, x, y)
            self.canvas.itemconfigure(self._image_item, image=self._photo)
        self._draw_sample_marker()
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
