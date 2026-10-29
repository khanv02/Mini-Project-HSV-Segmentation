"""Compact Tk Canvas rendering for source/frame HSV distributions."""

import colorsys
import tkinter as tk
from tkinter import ttk

from ..models import HSVHistogram, HSVThresholdSet
from .theme import COLORS


class HSVHistogramPanel(ttk.LabelFrame):
    """Render immutable counts and continuous threshold overlays."""

    AXES = (("h", "Hue (°)", 360.0), ("s", "Saturation (%)", 100.0),
            ("v", "Value (%)", 100.0))

    def __init__(self, master, **kwargs):
        super().__init__(master, text="HSV Histogram", padding=4, **kwargs)
        self._histogram: HSVHistogram | None = None
        self._thresholds = HSVThresholdSet()
        self._state_text = "No media — histogram unavailable"
        self._hue_note = "Hue counts only S >= 5%"
        self._grayscale_mode = False
        self._render_ids: dict[str, str] = {}
        self.axis_labels: dict[str, tk.StringVar] = {}

        header = ttk.Frame(self)
        header.pack(fill="x", pady=(0, 2))
        self._state_label = ttk.Label(header, text=self._state_text)
        self._state_label.pack(side="left")
        self._hue_note_label = ttk.Label(header, text=self._hue_note)
        self._hue_note_label.pack(side="right")
        ttk.Label(header, text="Gold band = selected threshold").pack(
            side="right", padx=(0, 12)
        )
        charts = ttk.Frame(self)
        charts.pack(fill="both", expand=True)
        self.canvases: dict[str, tk.Canvas] = {}
        for column, (axis, label, _maximum) in enumerate(self.AXES):
            charts.columnconfigure(column, weight=1, uniform="histogram")
            group = ttk.Frame(charts)
            group.grid(row=0, column=column, sticky="nsew", padx=2)
            label_var = tk.StringVar(value=label)
            self.axis_labels[axis] = label_var
            ttk.Label(group, textvariable=label_var, anchor="center").pack(fill="x")
            canvas = tk.Canvas(
                group, height=52, background=COLORS["surface"], borderwidth=0,
                highlightthickness=1, highlightbackground=COLORS["border"],
            )
            canvas.pack(fill="both", expand=True)
            canvas.bind("<Configure>", lambda _event, selected=axis:
                        self._schedule_draw(selected), add="+")
            self.canvases[axis] = canvas
        self._update_axis_labels()

    @property
    def state_text(self) -> str:
        return self._state_text

    @property
    def hue_note(self) -> str:
        return self._hue_note

    def set_histogram(self, histogram: HSVHistogram, thresholds: HSVThresholdSet) -> None:
        self._histogram = histogram
        self._thresholds = thresholds
        self._set_state("Current source/frame")
        self._set_hue_note(
            f"Hue counts only S >= 5% · {histogram.excluded_hue_count} excluded"
        )
        self._update_axis_labels()
        self._schedule_all()

    def set_grayscale_mode(self, enabled: bool, threshold: int = 128, polarity: str = "bright") -> None:
        """Present Value as intensity and explicitly retire Hue semantics."""
        self._grayscale_mode = bool(enabled)
        if self._grayscale_mode:
            self._set_hue_note("Hue unavailable — grayscale pixels have no meaningful hue")
            self.axis_labels["h"].set("Hue — unavailable")
            self.axis_labels["s"].set("Saturation — 0% for grayscale")
            relation = ">" if polarity == "bright" else "<="
            self.axis_labels["v"].set(f"Intensity (0–255)  |  {relation} {threshold}")
        else:
            if self._histogram is not None:
                self._set_hue_note(
                    f"Hue counts only S >= 5% · {self._histogram.excluded_hue_count} excluded"
                )
            self._update_axis_labels()
        self._schedule_all()

    def mark_pending(self, thresholds: HSVThresholdSet) -> None:
        self._thresholds = thresholds
        self._update_axis_labels()
        if self._histogram is not None:
            self._set_state("Overlay pending — processing current thresholds")
            self._schedule_all()

    def mark_invalid(self) -> None:
        if self._histogram is not None:
            self._set_state("Invalid edit — showing last valid overlay")

    def clear(self) -> None:
        self._histogram = None
        self._set_state("No media — histogram unavailable")
        self._set_hue_note("Hue counts only S >= 5%")
        self._schedule_all()

    def _set_state(self, text: str) -> None:
        self._state_text = text
        self._state_label.configure(text=text)

    def _set_hue_note(self, text: str) -> None:
        self._hue_note = text
        self._hue_note_label.configure(text=text)

    def overlay_segments(self, axis: str) -> tuple[tuple[float, float], ...]:
        bounds = self._thresholds
        if axis == "h":
            lower, upper = float(bounds.lower_h_deg), float(bounds.upper_h_deg)
            return ((lower, 360.0), (0.0, upper)) if bounds.wraps_hue else ((lower, upper),)
        if axis == "s":
            return ((float(bounds.lower_s_pct), float(bounds.upper_s_pct)),)
        if axis == "v":
            return ((float(bounds.lower_v_pct), float(bounds.upper_v_pct)),)
        raise ValueError("axis must be h, s, or v")

    def threshold_text(self, axis: str) -> str:
        bounds = self._thresholds
        if axis == "h":
            suffix = " (wrap)" if bounds.wraps_hue else ""
            return f"{bounds.lower_h_deg}°–{bounds.upper_h_deg}°{suffix}"
        if axis == "s":
            return f"{bounds.lower_s_pct}%–{bounds.upper_s_pct}%"
        if axis == "v":
            return f"{bounds.lower_v_pct}%–{bounds.upper_v_pct}%"
        raise ValueError("axis must be h, s, or v")

    def _update_axis_labels(self) -> None:
        if self._grayscale_mode:
            return
        titles = {axis: label for axis, label, _maximum in self.AXES}
        for axis, variable in self.axis_labels.items():
            variable.set(f"{titles[axis]}  |  {self.threshold_text(axis)}")

    def _schedule_all(self) -> None:
        for axis in self.canvases:
            self._schedule_draw(axis)

    def _schedule_draw(self, axis: str) -> None:
        previous = self._render_ids.get(axis)
        if previous is not None:
            try:
                self.after_cancel(previous)
            except tk.TclError:
                pass
        self._render_ids[axis] = self.after_idle(lambda: self._draw(axis))

    def _counts(self, axis: str):
        if self._histogram is None:
            return None
        return {"h": self._histogram.hue_counts,
                "s": self._histogram.saturation_counts,
                "v": self._histogram.value_counts}[axis]

    def _draw(self, axis: str) -> None:
        self._render_ids.pop(axis, None)
        canvas = self.canvases[axis]
        if not canvas.winfo_exists():
            return
        canvas.delete("all")
        width, height = max(80, canvas.winfo_width()), max(60, canvas.winfo_height())
        left, right, top, bottom = 28, 6, 7, 18
        plot_width, plot_height = max(1, width-left-right), max(1, height-top-bottom)
        maximum = 360.0 if axis == "h" else 100.0
        counts = self._counts(axis)
        for lower, upper in self.overlay_segments(axis):
            x0, x1 = (
                left + plot_width * lower / maximum,
                left + plot_width * upper / maximum,
            )
            canvas.create_rectangle(
                x0,
                top,
                x1,
                top + plot_height,
                fill=COLORS["threshold_band"],
                outline="",
                tags=("threshold-band",),
            )
        canvas.create_line(left, top, left, top+plot_height, fill=COLORS["muted_text"])
        canvas.create_line(left, top+plot_height, left+plot_width, top+plot_height,
                           fill=COLORS["muted_text"])
        canvas.create_text(left, height-3, text="0", anchor="sw", fill=COLORS["text"])
        canvas.create_text(left+plot_width, height-3, text=str(round(maximum)),
                           anchor="se", fill=COLORS["text"])
        if counts is None:
            canvas.create_text(left+plot_width/2, top+plot_height/2,
                               text="No data", fill=COLORS["muted_text"])
            self._draw_threshold_boundaries(canvas, axis, left, top, plot_width, plot_height)
            return
        peak = int(counts.max()) if counts.size else 0
        if peak == 0:
            canvas.create_text(left+plot_width/2, top+plot_height/2,
                               text="No hue data" if axis == "h" else "No data",
                               fill=COLORS["muted_text"])
        else:
            bin_width = plot_width / len(counts)
            for index, count in enumerate(counts):
                if count == 0:
                    continue
                x0, x1 = left+index*bin_width, left+(index+1)*bin_width
                y0 = top+plot_height*(1-int(count)/peak)
                fill = self._bar_color(axis, index, len(counts))
                canvas.create_rectangle(x0, y0, max(x0+1, x1), top+plot_height,
                                        fill=fill, outline="", tags=("histogram-bar",))
            canvas.create_text(2, top, text=str(peak), anchor="nw", fill=COLORS["text"])
        self._draw_threshold_boundaries(canvas, axis, left, top, plot_width, plot_height)

    @staticmethod
    def _bar_color(axis: str, index: int, count: int) -> str:
        if axis != "h":
            return COLORS["primary"] if axis == "s" else COLORS["success"]
        red, green, blue = colorsys.hsv_to_rgb(index / max(1, count), 0.72, 0.82)
        return f"#{round(red * 255):02x}{round(green * 255):02x}{round(blue * 255):02x}"

    def _draw_threshold_boundaries(
        self,
        canvas: tk.Canvas,
        axis: str,
        left: int,
        top: int,
        plot_width: int,
        plot_height: int,
    ) -> None:
        maximum = 360.0 if axis == "h" else 100.0
        boundaries = sorted({value for segment in self.overlay_segments(axis) for value in segment})
        for value in boundaries:
            x = left + plot_width * value / maximum
            canvas.create_line(
                x,
                top,
                x,
                top + plot_height,
                fill=COLORS["warning"],
                width=2,
                tags=("threshold-boundary",),
            )

    def destroy(self) -> None:
        for render_id in self._render_ids.values():
            try:
                self.after_cancel(render_id)
            except tk.TclError:
                pass
        self._render_ids.clear()
        super().destroy()
