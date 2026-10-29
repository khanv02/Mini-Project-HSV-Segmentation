"""Tk histogram panel layout and overlay behavior."""

import time

import numpy as np
import pytest

from hsv_segmentation.application.processing_worker import ProcessingWorker
from hsv_segmentation.gui.hsv_histogram import HSVHistogramPanel
from hsv_segmentation.gui.main_window import MainWindow
from hsv_segmentation.models import (
    HSVHistogram,
    HSVThresholdSet,
    InputMedia,
    ProcessingRequest,
)
from hsv_segmentation.processing.segmentation import generate_mask


def _root(tkinter):
    last_error = None
    for _attempt in range(3):
        try:
            return tkinter.Tk()
        except tkinter.TclError as error:
            last_error = error
            time.sleep(0.05)
    pytest.fail(f"Tk root could not be created: {last_error}")


def _histogram() -> HSVHistogram:
    hue = np.zeros(360, dtype=np.int64)
    hue[[0, 120, 240, 359]] = [2, 3, 4, 1]
    saturation = np.zeros(101, dtype=np.int64)
    saturation[[0, 5, 50, 100]] = [2, 3, 4, 1]
    value = np.zeros(101, dtype=np.int64)
    value[[0, 25, 75, 100]] = [1, 3, 4, 2]
    return HSVHistogram(hue, saturation, value, excluded_hue_count=0)


def test_histogram_panel_renders_labels_cutoff_and_numeric_overlays() -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _root(tkinter)
    root.geometry("960x640")
    try:
        panel = HSVHistogramPanel(root)
        panel.pack(fill="both", expand=True)
        panel.set_histogram(
            _histogram(),
            HSVThresholdSet(lower_h_deg=350, upper_h_deg=10, lower_s_pct=5, upper_s_pct=5),
        )
        root.update()

        assert panel.hue_note.startswith("Hue counts only S >= 5%")
        assert panel.overlay_segments("h") == ((350.0, 360.0), (0.0, 10.0))
        assert panel.threshold_text("h") == "350°–10° (wrap)"
        assert panel.overlay_segments("s") == ((5.0, 5.0),)
        hsv = np.array([[[20.0, 5.9, 50.0]]], dtype=np.float64)
        assert generate_mask(
            hsv,
            HSVThresholdSet(lower_s_pct=5, upper_s_pct=5),
        )[0, 0] == 0
        assert panel.overlay_segments("v") == ((0.0, 100.0),)
        assert panel.state_text == "Current source/frame"
        assert panel.canvases["h"].find_withtag("threshold-band")
        assert panel.canvases["h"].find_withtag("threshold-boundary")
        assert panel.canvases["h"].find_withtag("histogram-bar")

        panel.mark_invalid()
        assert "last valid" in panel.state_text.lower()
        panel.mark_pending(HSVThresholdSet(lower_h_deg=20, upper_h_deg=40))
        assert panel.overlay_segments("h") == ((20.0, 40.0),)
        assert panel.threshold_text("h") == "20°–40°"
        assert "pending" in panel.state_text.lower()
    finally:
        root.destroy()


def test_worker_reuses_histogram_for_threshold_only_requests(tmp_path) -> None:
    source = InputMedia(
        source_path=(tmp_path / "source.png").resolve(),
        source_sha256="c" * 64,
        source_format="PNG",
        rgb=np.array([[[255, 0, 0], [0, 255, 0]]], dtype=np.uint8),
    )
    worker = ProcessingWorker()
    try:
        results = []
        for revision, lower_hue in ((1, 0), (2, 60)):
            worker.submit(ProcessingRequest(
                source,
                HSVThresholdSet(lower_h_deg=lower_hue, parameter_revision=revision),
                revision,
            ))
            deadline = time.monotonic() + 3
            while not results or results[-1].request_revision != revision:
                results.extend(worker.poll())
                assert time.monotonic() < deadline
                time.sleep(0.005)

        first, second = results[-2].result, results[-1].result
        assert first.histogram is second.histogram
        assert first.histogram.pixel_count == 2
        assert first.thresholds != second.thresholds
    finally:
        worker.shutdown()


def test_worker_recomputes_histogram_for_source_and_frame_identity_changes(tmp_path) -> None:
    image = InputMedia(
        source_path=(tmp_path / "image.png").resolve(),
        source_sha256="a" * 64,
        source_format="PNG",
        rgb=np.array([[[255, 0, 0]]], dtype=np.uint8),
    )
    frame_zero = InputMedia(
        source_path=(tmp_path / "clip.avi").resolve(),
        source_sha256="b" * 64,
        source_format="AVI",
        rgb=np.array([[[0, 255, 0]]], dtype=np.uint8),
        media_kind="video",
        session_id="video-session",
        frame_index=0,
        backend="FFMPEG",
    )
    frame_one = InputMedia(
        source_path=frame_zero.source_path,
        source_sha256=frame_zero.source_sha256,
        source_format="AVI",
        rgb=np.array([[[0, 0, 255]]], dtype=np.uint8),
        media_kind="video",
        session_id=frame_zero.session_id,
        frame_index=1,
        backend="FFMPEG",
    )
    worker = ProcessingWorker()
    try:
        histograms = []
        for revision, source in enumerate((image, frame_zero, frame_one), start=1):
            worker.submit(ProcessingRequest(source, HSVThresholdSet(), revision))
            deadline = time.monotonic() + 3
            result = None
            while result is None:
                for completion in worker.poll():
                    if completion.request_revision == revision:
                        result = completion.result
                assert time.monotonic() < deadline
                time.sleep(0.005)
            histograms.append(result.histogram)

        assert all(item is not None for item in histograms)
        assert histograms[0] is not histograms[1]
        assert histograms[1] is not histograms[2]
        assert histograms[0].hue_counts[0] == 1
        assert histograms[1].hue_counts[120] == 1
        assert histograms[2].hue_counts[240] == 1
    finally:
        worker.shutdown()


def test_main_window_starts_with_histogram_and_four_usable_views() -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _root(tkinter)
    try:
        window = MainWindow(root)
        root.geometry("1100x720")
        window.histogram_panel.set_histogram(_histogram(), HSVThresholdSet())
        root.update()

        assert window.histogram_visible is True
        assert window.histogram_toggle_button.cget("text") == "Hide Histogram"
        assert len(window.views) == 4
        for view in window.views:
            assert view.canvas.winfo_width() >= 160
            assert view.canvas.winfo_height() >= 120

        window.set_histogram_visible(False)
        root.update()
        assert window.histogram_visible is False
        assert window.histogram_toggle_button.cget("text") == "Show Histogram"
        window.toggle_histogram()
        root.update()
        assert window.histogram_visible is True
    finally:
        root.destroy()


def test_histogram_panel_has_explicit_no_media_and_empty_hue_states() -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _root(tkinter)
    try:
        panel = HSVHistogramPanel(root)
        panel.pack(fill="both", expand=True)
        root.update()
        assert "no media" in panel.state_text.lower()

        empty = HSVHistogram(
            np.zeros(360, dtype=np.int64),
            np.array([2] + [0] * 100, dtype=np.int64),
            np.array([1, 1] + [0] * 99, dtype=np.int64),
            excluded_hue_count=2,
        )
        panel.set_histogram(empty, HSVThresholdSet())
        root.update()
        assert "2 excluded" in panel.hue_note.lower()
    finally:
        root.destroy()
