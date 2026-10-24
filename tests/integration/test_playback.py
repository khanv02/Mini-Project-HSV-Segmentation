"""Deterministic playback/session state and revision tests."""

from pathlib import Path
import time

import cv2
import numpy as np
import pytest

from hsv_segmentation.application.playback import PlaybackSession, PlaybackState
from hsv_segmentation.application.session import ImageSession
from hsv_segmentation.gui.controller import ApplicationController
from hsv_segmentation.io.video import VideoEnd
from hsv_segmentation.models import HSVThresholdSet, InputMedia


def _frame(path: Path, session_id: str, index: int, rgb) -> InputMedia:
    return InputMedia(
        source_path=path,
        source_sha256="b" * 64,
        source_format="AVI",
        rgb=np.asarray(rgb, dtype=np.uint8).reshape(1, 1, 3),
        media_kind="video",
        session_id=session_id,
        frame_index=index,
        backend="TEST",
    )


class StubReader:
    def __init__(self, path: Path, session_id: str, colors):
        self.path = path
        self.session_id = session_id
        self.colors = list(colors)
        self.first_frame = _frame(path, session_id, 0, self.colors[0])
        self.position = 0
        self.closed = False

    def read_next(self):
        next_position = self.position + 1
        if next_position >= len(self.colors):
            raise VideoEnd("Video ended.", clean=True)
        self.position = next_position
        return _frame(self.path, self.session_id, self.position, self.colors[self.position])

    def restart(self):
        self.position = 0
        return self.first_frame

    def release(self):
        self.closed = True


def _factory(readers):
    queue = list(readers)

    def create(_path):
        return queue.pop(0)

    return create


def test_open_is_paused_then_play_pause_and_end_retain_last_frame(tmp_path) -> None:
    path = (tmp_path / "one.avi").resolve()
    reader = StubReader(path, "session-one", [(255, 0, 0), (0, 255, 0)])
    media = ImageSession()
    playback = PlaybackSession(media, reader_factory=_factory([reader]))

    candidate = playback.prepare_open(path, media.thresholds, request_revision=1)
    playback.commit_open(candidate)
    assert playback.state is PlaybackState.PAUSED
    assert media.result.frame_index == 0

    playback.play()
    assert playback.state is PlaybackState.PLAYING
    advance = playback.prepare_next(media.thresholds, request_revision=2)
    assert playback.commit_advance(advance) is True
    assert media.result.frame_index == 1
    playback.pause()
    assert playback.state is PlaybackState.PAUSED

    playback.play()
    ended = playback.prepare_next(media.thresholds, request_revision=3)
    assert playback.commit_advance(ended) is False
    assert playback.state is PlaybackState.ENDED
    assert media.result.frame_index == 1
    assert playback.status_message == "Video ended."


def test_paused_threshold_change_reprocesses_retained_frame(tmp_path) -> None:
    path = (tmp_path / "paused.avi").resolve()
    reader = StubReader(path, "paused-session", [(255, 0, 0)])
    media = ImageSession()
    playback = PlaybackSession(media, reader_factory=_factory([reader]))
    playback.commit_open(playback.prepare_open(path, media.thresholds, 1))
    thresholds = HSVThresholdSet(
        lower_h_deg=120, upper_h_deg=120, parameter_revision=1
    )

    result = playback.reprocess_current(thresholds, request_revision=2)
    media.accept_thresholds(thresholds)
    assert media.commit_result(result) is True
    assert result.frame_index == 0
    np.testing.assert_array_equal(result.mask, [[0]])
    assert playback.state is PlaybackState.PAUSED


def test_restart_returns_frame_zero_paused(tmp_path) -> None:
    path = (tmp_path / "restart.avi").resolve()
    reader = StubReader(path, "restart-session", [(255, 0, 0), (0, 255, 0)])
    media = ImageSession()
    playback = PlaybackSession(media, reader_factory=_factory([reader]))
    playback.commit_open(playback.prepare_open(path, media.thresholds, 1))
    playback.play()
    playback.commit_advance(playback.prepare_next(media.thresholds, 2))

    restarted = playback.prepare_restart(media.thresholds, 3)
    playback.commit_restart(restarted)

    assert playback.state is PlaybackState.PAUSED
    assert media.result.frame_index == 0
    assert media.result.session_id == "restart-session"


def test_replacement_releases_old_reader_and_rejects_obsolete_frame(tmp_path) -> None:
    first_path = (tmp_path / "first.avi").resolve()
    second_path = (tmp_path / "second.avi").resolve()
    first = StubReader(first_path, "first-session", [(255, 0, 0), (0, 255, 0)])
    second = StubReader(second_path, "second-session", [(0, 0, 255)])
    media = ImageSession()
    playback = PlaybackSession(media, reader_factory=_factory([first, second]))
    playback.commit_open(playback.prepare_open(first_path, media.thresholds, 1))
    obsolete = playback.prepare_next(media.thresholds, 2)

    replacement = playback.prepare_open(second_path, media.thresholds, 3)
    playback.commit_open(replacement)

    assert first.closed is True
    assert media.result.session_id == "second-session"
    assert playback.commit_advance(obsolete) is False
    assert media.result.session_id == "second-session"


def test_failed_candidate_preserves_current_reader_and_state(tmp_path) -> None:
    path = (tmp_path / "current.avi").resolve()
    current = StubReader(path, "current-session", [(255, 0, 0)])

    def factory(candidate_path):
        if Path(candidate_path).name == "broken.avi":
            raise RuntimeError("decode failed")
        return current

    media = ImageSession()
    playback = PlaybackSession(media, reader_factory=factory)
    playback.commit_open(playback.prepare_open(path, media.thresholds, 1))
    playback.play()

    try:
        playback.prepare_open((tmp_path / "broken.avi").resolve(), media.thresholds, 2)
    except RuntimeError:
        pass

    assert current.closed is False
    assert playback.state is PlaybackState.PLAYING
    assert media.result.session_id == "current-session"


def test_close_releases_reader_and_rejects_more_playback(tmp_path) -> None:
    path = (tmp_path / "close.avi").resolve()
    reader = StubReader(path, "close-session", [(255, 0, 0)])
    media = ImageSession()
    playback = PlaybackSession(media, reader_factory=_factory([reader]))
    playback.commit_open(playback.prepare_open(path, media.thresholds, 1))

    playback.close()

    assert reader.closed is True
    assert playback.state is PlaybackState.CLOSED
    assert playback.play() is False


def _write_gui_fixture(path: Path, frame_count: int, offset: int = 0) -> None:
    writer = cv2.VideoWriter(
        str(path), cv2.VideoWriter_fourcc(*"MJPG"), 12.0, (12, 8)
    )
    if not writer.isOpened():
        pytest.skip("MJPG AVI writer is unavailable")
    try:
        for index in range(frame_count):
            rgb = np.full(
                (8, 12, 3),
                [(index * 17 + offset) % 256, (index * 31) % 256, (index * 47) % 256],
                dtype=np.uint8,
            )
            writer.write(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    finally:
        writer.release()


def _wait_for(root, predicate, timeout=4.0):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        root.update()
        time.sleep(0.005)
    assert predicate()


def test_real_video_controller_open_play_pause_edit_end_restart_and_replace(tmp_path) -> None:
    tkinter = pytest.importorskip("tkinter")
    last_error = None
    root = None
    for _attempt in range(3):
        try:
            root = tkinter.Tk()
            break
        except tkinter.TclError as error:
            last_error = error
            time.sleep(0.05)
    if root is None:
        pytest.fail(f"Tk root could not be created after three attempts: {last_error}")
    root.withdraw()
    first_path = (tmp_path / "workflow.avi").resolve()
    second_path = (tmp_path / "replacement.avi").resolve()
    _write_gui_fixture(first_path, frame_count=12)
    _write_gui_fixture(second_path, frame_count=3, offset=90)
    controller = ApplicationController(root)
    try:
        assert controller.window.open_video_button.cget("text") == "Open Video…"
        controller.open_video_path(str(first_path))
        _wait_for(root, lambda: controller.playback.state is PlaybackState.PAUSED)
        assert controller.session.result.frame_index == 0
        first_session_id = controller.session.result.session_id

        controller.play_video()
        _wait_for(root, lambda: controller.session.result.frame_index >= 2)
        controller.pause_video()
        _wait_for(root, lambda: controller.playback.state is PlaybackState.PAUSED)
        paused_index = controller.session.result.frame_index
        for _ in range(10):
            root.update()
            time.sleep(0.005)
        assert controller.session.result.frame_index >= paused_index
        stopped_index = controller.session.result.frame_index
        for _ in range(10):
            root.update()
            time.sleep(0.005)
        assert controller.session.result.frame_index == stopped_index

        thresholds = HSVThresholdSet(
            lower_h_deg=100, upper_h_deg=140, parameter_revision=1
        )
        controller._on_thresholds(thresholds)
        _wait_for(
            root,
            lambda: controller.session.result.parameter_revision == 1,
        )
        assert controller.session.result.frame_index == stopped_index

        controller.play_video()
        _wait_for(root, lambda: controller.playback.state is PlaybackState.ENDED)
        assert controller.session.result.frame_index == 11

        controller.restart_video()
        _wait_for(
            root,
            lambda: controller.playback.state is PlaybackState.PAUSED
            and controller.session.result.frame_index == 0,
        )
        assert controller.session.result.session_id == first_session_id

        controller.open_video_path(str(second_path))
        _wait_for(
            root,
            lambda: controller.playback.state is PlaybackState.PAUSED
            and controller.session.source.source_path == second_path,
        )
        assert controller.session.result.session_id != first_session_id
        assert controller.window.frame_var.get() == "Frame: 0"
        np.testing.assert_array_equal(
            controller.window.original_view.source_array,
            controller.session.result.original_rgb,
        )
        np.testing.assert_array_equal(
            controller.window.mask_view.source_array,
            controller.session.result.mask,
        )
        np.testing.assert_array_equal(
            controller.window.result_view.source_array,
            controller.session.result.segmented_rgb,
        )
    finally:
        controller.close()
