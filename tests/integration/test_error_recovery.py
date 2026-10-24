"""Phase 6 recovery matrix for files, parameters, playback, and writes."""

from pathlib import Path
from threading import Event
import time

import numpy as np
import pytest
from PIL import Image

from hsv_segmentation.application.playback import PlaybackState
from hsv_segmentation.errors import (
    DecodeError,
    InputError,
    WriteError,
    format_recovery_message,
)
from hsv_segmentation.gui.controller import ApplicationController
from hsv_segmentation.models import InputMedia
from hsv_segmentation.io.video import AMBIGUOUS_TERMINATION_MESSAGE, VideoEnd


def _create_tk_root(tkinter):
    last_error = None
    for _attempt in range(3):
        try:
            return tkinter.Tk()
        except tkinter.TclError as error:
            last_error = error
            time.sleep(0.05)
    pytest.fail(f"Tk root could not be created after three attempts: {last_error}")


def _wait_for(root, predicate, timeout=4.0):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        root.update()
        time.sleep(0.005)
    assert predicate()


def _save_image(path: Path, value: int = 80) -> None:
    Image.fromarray(np.full((3, 4, 3), [value, 20, 10], dtype=np.uint8)).save(path)


def _open_valid(controller, root, path: Path, value: int = 80):
    _save_image(path, value)
    previous_session = controller.session.source.session_id if controller.session.source else None
    controller.open_image_path(str(path))
    _wait_for(
        root,
        lambda: controller.session.source is not None
        and controller.session.source.session_id != previous_session,
    )
    return controller.session.result


@pytest.mark.parametrize(
    ("error", "category", "action_fragment"),
    [
        (
            InputError("file was not found", path="C:/missing.png"),
            "missing input",
            "path",
        ),
        (
            InputError("permission denied", path="C:/private.png"),
            "unreadable input",
            "permission",
        ),
        (
            InputError("unsupported file type", path="C:/sample.gif"),
            "unsupported input",
            "PNG",
        ),
        (
            InputError("image exceeds the pixel limit", path="C:/huge.png"),
            "resource limit",
            "smaller",
        ),
        (
            DecodeError("image could not be decoded", path="C:/broken.png"),
            "decode failure",
            "supported",
        ),
        (
            WriteError("permission denied", path="C:/output.png"),
            "write failure",
            "destination",
        ),
    ],
)
def test_recovery_message_has_all_required_fields(error, category, action_fragment) -> None:
    message = format_recovery_message(
        error, preserved_state="Previous valid input, thresholds, and result were preserved."
    )

    assert f"Operation: {error.operation}." in message
    assert f"Affected: {error.path}." in message
    assert f"Cause: {category}." in message
    assert "Preserved:" in message
    assert "Action:" in message
    assert action_fragment.lower() in message.lower()


def test_failed_image_matrix_preserves_session_and_allows_next_valid_open(
    tmp_path, monkeypatch
) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    errors = []
    monkeypatch.setattr(
        "hsv_segmentation.gui.controller.messagebox.showerror",
        lambda title, message, **kwargs: errors.append(message),
    )
    from hsv_segmentation.application import processing_worker

    real_loader = processing_worker.load_image

    def matrix_loader(path):
        candidate = Path(path)
        if candidate.name == "unreadable.png":
            raise InputError("permission denied", path=candidate)
        if candidate.name == "oversized.png":
            raise InputError("image exceeds the 12,000,000-pixel limit", path=candidate)
        return real_loader(path)

    monkeypatch.setattr(processing_worker, "load_image", matrix_loader)
    controller = ApplicationController(root)
    try:
        first = _open_valid(controller, root, (tmp_path / "valid.png").resolve())
        corrupt = (tmp_path / "corrupt.png").resolve()
        corrupt.write_bytes(b"not an image")
        unsupported = (tmp_path / "unsupported.gif").resolve()
        unsupported.write_bytes(b"GIF89a")
        cases = [
            (tmp_path / "missing.png").resolve(),
            (tmp_path / "unreadable.png").resolve(),
            corrupt,
            unsupported,
            (tmp_path / "oversized.png").resolve(),
        ]

        for expected_count, candidate in enumerate(cases, start=1):
            controller.open_image_path(str(candidate))
            _wait_for(root, lambda: len(errors) == expected_count)
            assert controller.session.result is first
            message = errors[-1]
            assert all(
                label in message
                for label in ("Operation:", "Affected:", "Cause:", "Preserved:", "Action:")
            )
            assert str(candidate) in message

        recovered = _open_valid(
            controller, root, (tmp_path / "recovered.png").resolve(), value=180
        )
        assert recovered.session_id != first.session_id
        assert str(controller.window.save_result_button.cget("state")) == "normal"
    finally:
        controller.close()


def test_invalid_parameters_preserve_old_result_disable_export_and_recover(tmp_path) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    controller = ApplicationController(root)
    try:
        original = _open_valid(controller, root, (tmp_path / "valid.png").resolve())

        controller.controls.fields["lower_h_deg"].set("not-a-number")
        assert controller.controls.validate_now() is None
        assert "whole number in 0..359" in controller.controls.error_text
        assert controller.session.result is original
        assert str(controller.window.save_result_button.cget("state")) == "disabled"
        controller.controls.fields["lower_h_deg"].set("0")
        restored = controller.controls.validate_now()
        _wait_for(root, lambda: controller.session.result is not original)

        before_range_error = controller.session.result
        controller.controls.fields["upper_h_deg"].set("361")
        assert controller.controls.validate_now() is None
        assert "0..360" in controller.controls.error_text
        assert controller.session.result is before_range_error
        controller.controls.fields["upper_h_deg"].set("360")
        controller.controls.validate_now()
        _wait_for(root, lambda: controller.session.result is not before_range_error)

        before_order_error = controller.session.result
        controller.controls.fields["lower_s_pct"].set("90")
        controller.controls.fields["upper_s_pct"].set("20")
        assert controller.controls.validate_now() is None

        assert controller.session.result is before_order_error
        assert "ordering rule" in controller.controls.error_text
        assert str(controller.window.save_result_button.cget("state")) == "disabled"

        controller.controls.fields["upper_s_pct"].set("100")
        corrected = controller.controls.validate_now()
        assert corrected is not None
        _wait_for(
            root,
            lambda: controller.session.result is not original
            and controller.session.result.parameter_revision == corrected.parameter_revision,
        )
        assert str(controller.window.save_result_button.cget("state")) == "normal"
    finally:
        controller.close()


class _FailingVideoReader:
    def __init__(self, path: Path):
        self.first_frame = InputMedia(
            source_path=path,
            source_sha256="a" * 64,
            source_format="AVI",
            rgb=np.full((2, 3, 3), [200, 20, 20], dtype=np.uint8),
            media_kind="video",
            frame_index=0,
            backend="TEST",
        )
        self.released = False

    def read_next(self):
        raise DecodeError("could not decode frame 1", path=self.first_frame.source_path)

    def restart(self):
        return self.first_frame

    def release(self):
        self.released = True


class _AmbiguousVideoReader(_FailingVideoReader):
    def read_next(self):
        raise VideoEnd(AMBIGUOUS_TERMINATION_MESSAGE, clean=False)


def test_decode_interruption_stops_video_preserves_frame_and_recovers(
    tmp_path, monkeypatch
) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    errors = []
    monkeypatch.setattr(
        "hsv_segmentation.gui.controller.messagebox.showerror",
        lambda title, message, **kwargs: errors.append(message),
    )
    controller = ApplicationController(root)
    video_path = (tmp_path / "interrupted.avi").resolve()
    reader = _FailingVideoReader(video_path)
    controller.playback._reader_factory = lambda path: reader
    try:
        controller.open_video_path(str(video_path))
        _wait_for(root, lambda: controller.playback.state is PlaybackState.PAUSED)
        retained = controller.session.result
        controller.play_video()
        _wait_for(root, lambda: controller.playback.state is PlaybackState.ERROR)

        assert controller.session.result is retained
        assert errors and "Cause: decode failure." in errors[-1]
        assert "last valid video frame" in errors[-1].lower()
        assert reader.released is False

        recovered = _open_valid(
            controller, root, (tmp_path / "after-video-error.png").resolve(), value=120
        )
        assert recovered.source.media_kind == "image"
        assert reader.released is True
    finally:
        controller.close()


def test_ambiguous_video_termination_is_honest_and_restartable(tmp_path) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    controller = ApplicationController(root)
    video_path = (tmp_path / "ambiguous.avi").resolve()
    reader = _AmbiguousVideoReader(video_path)
    controller.playback._reader_factory = lambda path: reader
    try:
        controller.open_video_path(str(video_path))
        _wait_for(root, lambda: controller.playback.state is PlaybackState.PAUSED)
        retained = controller.session.result
        controller.play_video()
        _wait_for(root, lambda: controller.playback.state is PlaybackState.ENDED)

        assert controller.session.result is retained
        message = controller.window.status_var.get()
        assert "Cause: uncertain decoder termination." in message
        assert "ended or the next frame could not be read" in message
        assert "Action:" in message and "supported MP4/AVI encoding" in message

        controller.restart_video()
        _wait_for(root, lambda: controller.playback.state is PlaybackState.PAUSED)
        assert controller.session.result.frame_index == 0
    finally:
        controller.close()


def test_cancelled_dialogs_emit_no_error_and_preserve_everything(tmp_path, monkeypatch) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    errors = []
    monkeypatch.setattr(
        "hsv_segmentation.gui.controller.messagebox.showerror",
        lambda *args, **kwargs: errors.append(args),
    )
    monkeypatch.setattr(
        "hsv_segmentation.gui.controller.filedialog.askopenfilename", lambda **kwargs: ""
    )
    monkeypatch.setattr(
        "hsv_segmentation.gui.controller.filedialog.asksaveasfilename", lambda **kwargs: ""
    )
    controller = ApplicationController(root)
    try:
        result = _open_valid(controller, root, (tmp_path / "valid.png").resolve())
        controller.choose_image()
        controller.choose_video()
        controller.choose_save_mask()
        controller.choose_save_result()
        root.update()

        assert controller.session.result is result
        assert errors == []
    finally:
        controller.close()


def test_oversized_failure_runs_off_gui_thread_and_preserves_responsiveness(
    tmp_path, monkeypatch
) -> None:
    tkinter = pytest.importorskip("tkinter")
    root = _create_tk_root(tkinter)
    root.withdraw()
    started = Event()
    release = Event()
    errors = []
    from hsv_segmentation.application import processing_worker

    real_loader = processing_worker.load_image

    def slow_loader(path):
        if Path(path).name == "oversized.png":
            started.set()
            assert release.wait(3)
            raise InputError("image exceeds the 12,000,000-pixel limit", path=path)
        return real_loader(path)

    monkeypatch.setattr(processing_worker, "load_image", slow_loader)
    monkeypatch.setattr(
        "hsv_segmentation.gui.controller.messagebox.showerror",
        lambda title, message, **kwargs: errors.append(message),
    )
    controller = ApplicationController(root)
    try:
        retained = _open_valid(controller, root, (tmp_path / "valid.png").resolve())
        controller.open_image_path(str((tmp_path / "oversized.png").resolve()))
        assert started.wait(2)
        serviced = []
        root.after(0, lambda: serviced.append(True))
        _wait_for(root, lambda: bool(serviced))
        release.set()
        _wait_for(root, lambda: bool(errors))

        assert controller.session.result is retained
        assert "Cause: resource limit." in errors[-1]
    finally:
        release.set()
        controller.close()
