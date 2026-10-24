"""Aspect-preserving image preview widget; processing arrays stay untouched."""

import tkinter as tk
from tkinter import ttk

import numpy as np
from PIL import Image, ImageTk


class ImageView(ttk.LabelFrame):
    """Display an RGB image or binary mask fitted to the available area."""

    def __init__(self, master, *, title: str, is_mask: bool = False, **kwargs):
        super().__init__(master, text=title, padding=6, **kwargs)
        self._is_mask = is_mask
        self._source: np.ndarray | None = None
        self._photo: ImageTk.PhotoImage | None = None
        self._label = ttk.Label(self, text="No image", anchor="center")
        self._label.pack(fill="both", expand=True)
        self.bind("<Configure>", self._on_resize, add="+")

    @property
    def source_array(self) -> np.ndarray | None:
        return None if self._source is None else self._source.copy()

    def show_array(self, array: np.ndarray | None) -> None:
        if array is None:
            self._source = None
            self._photo = None
            self._label.configure(image="", text="No image")
            return
        if self._is_mask:
            if not isinstance(array, np.ndarray) or array.dtype != np.uint8 or array.ndim != 2:
                raise ValueError("mask preview requires a uint8 (height, width) array")
        elif (
            not isinstance(array, np.ndarray) or array.dtype != np.uint8
            or array.ndim != 3 or array.shape[2] != 3
        ):
            raise ValueError("image preview requires a uint8 RGB array")
        self._source = array.copy()
        self._render()

    def _on_resize(self, _event=None) -> None:
        if self._source is not None:
            self.after_idle(self._render)

    def _render(self) -> None:
        if self._source is None or not self.winfo_exists():
            return
        image = Image.fromarray(self._source)
        width = max(80, self.winfo_width() - 16)
        height = max(80, self.winfo_height() - 28)
        resampling = Image.Resampling.NEAREST if self._is_mask else Image.Resampling.LANCZOS
        image.thumbnail((width, height), resampling)
        self._photo = ImageTk.PhotoImage(image=image, master=self)
        self._label.configure(image=self._photo, text="")
