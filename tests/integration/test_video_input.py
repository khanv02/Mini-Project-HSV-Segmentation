"""Video reader lifecycle tests using real tiny files and deterministic captures."""

from pathlib import Path

import cv2
import numpy as np
import pytest

from hsv_segmentation.errors import DecodeError, InputError
from hsv_segmentation.io.video import (
    AMBIGUOUS_TERMINATION_MESSAGE,
    VideoEnd,
    VideoReader,
)


def _write_video(path: Path, codec: str) -> list[np.ndarray]:
    frames_rgb = [
        np.full((8, 10, 3), [220, 20, 20], dtype=np.uint8),
        np.full((8, 10, 3), [20, 220, 20], dtype=np.uint8),
        np.full((8, 10, 3), [20, 20, 220], dtype=np.uint8),
    ]
    writer = cv2.VideoWriter(
        str(path), cv2.VideoWriter_fourcc(*codec), 5.0, (10, 8)
    )
    if not writer.isOpened():
        pytest.skip(f"OpenCV writer {codec} is unavailable")
    try:
        for rgb in frames_rgb:
            writer.write(cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR))
    finally:
        writer.release()
    return frames_rgb


@pytest.mark.parametrize(
    ("filename", "codec", "format_name"),
    [("tiny.avi", "MJPG", "AVI"), ("tiny.mp4", "mp4v", "MP4")],
)
def test_real_short_video_decodes_rgb_frames_and_known_eof(
    tmp_path, filename, codec, format_name
) -> None:
    path = (tmp_path / filename).resolve()
    expected = _write_video(path, codec)
    reader = VideoReader.open(path, trust_frame_count=True)
    try:
        assert reader.first_frame.source_format == format_name
        assert reader.first_frame.frame_index == 0
        assert reader.first_frame.backend
        assert reader.first_frame.media_kind == "video"
        assert reader.frame_count_hint == 3
        np.testing.assert_allclose(reader.first_frame.rgb, expected[0], atol=8, rtol=0)

        second = reader.read_next()
        third = reader.read_next()
        assert (second.frame_index, third.frame_index) == (1, 2)
        assert second.session_id == reader.first_frame.session_id == third.session_id
        np.testing.assert_allclose(third.rgb, expected[2], atol=8, rtol=0)
        with pytest.raises(VideoEnd) as ended:
            reader.read_next()
        assert ended.value.clean is True
    finally:
        reader.release()
    assert reader.closed is True


class FakeCapture:
    def __init__(self, outcomes, *, opened=True, frame_count=0, backend="FAKE"):
        self.outcomes = list(outcomes)
        self.opened = opened
        self.frame_count = frame_count
        self.backend = backend
        self.position = -1
        self.released = False

    def isOpened(self):
        return self.opened

    def grab(self):
        self.position += 1
        if self.position >= len(self.outcomes):
            return False
        return self.outcomes[self.position][0]

    def retrieve(self):
        if self.position >= len(self.outcomes):
            return False, None
        _grabbed, retrieved, frame = self.outcomes[self.position]
        return retrieved, frame

    def get(self, property_id):
        if property_id == cv2.CAP_PROP_FRAME_COUNT:
            return float(self.frame_count)
        return 0.0

    def getBackendName(self):
        return self.backend

    def release(self):
        self.released = True


def _bgr(color=(0, 0, 255)):
    return np.full((2, 3, 3), color, dtype=np.uint8)


def _path(tmp_path, name="fake.avi"):
    path = (tmp_path / name).resolve()
    path.write_bytes(b"fixture identity")
    return path


def test_empty_video_and_failed_open_release_capture(tmp_path) -> None:
    failed = FakeCapture([], opened=False)
    with pytest.raises(InputError, match="MP4 or AVI"):
        VideoReader.open(_path(tmp_path), capture_factory=lambda _path: failed)
    assert failed.released is True

    empty = FakeCapture([], frame_count=0)
    with pytest.raises(DecodeError, match="first frame"):
        VideoReader.open(_path(tmp_path, "empty.avi"), capture_factory=lambda _path: empty)
    assert empty.released is True


def test_retrieve_failure_is_explicit_decode_error(tmp_path) -> None:
    capture = FakeCapture(
        [(True, True, _bgr()), (True, False, None)], frame_count=2
    )
    reader = VideoReader.open(_path(tmp_path), capture_factory=lambda _path: capture)
    with pytest.raises(DecodeError, match="decode frame 1"):
        reader.read_next()
    reader.release()


def test_ambiguous_termination_uses_honest_message(tmp_path) -> None:
    capture = FakeCapture([(True, True, _bgr())], frame_count=0)
    reader = VideoReader.open(_path(tmp_path), capture_factory=lambda _path: capture)
    with pytest.raises(VideoEnd) as ended:
        reader.read_next()
    assert ended.value.clean is False
    assert str(ended.value) == AMBIGUOUS_TERMINATION_MESSAGE
    reader.release()


def test_untrusted_backend_frame_count_remains_only_a_hint(tmp_path) -> None:
    capture = FakeCapture([(True, True, _bgr())], frame_count=3)
    reader = VideoReader.open(_path(tmp_path), capture_factory=lambda _path: capture)
    with pytest.raises(VideoEnd) as ended:
        reader.read_next()
    assert ended.value.clean is False
    assert str(ended.value) == AMBIGUOUS_TERMINATION_MESSAGE
    reader.release()


def test_premature_termination_before_reported_count_is_failure(tmp_path) -> None:
    capture = FakeCapture([(True, True, _bgr())], frame_count=3)
    reader = VideoReader.open(
        _path(tmp_path), capture_factory=lambda _path: capture, trust_frame_count=True
    )
    with pytest.raises(DecodeError, match="before the reported frame count"):
        reader.read_next()
    reader.release()


def test_restart_reopens_frame_zero_and_releases_old_capture(tmp_path) -> None:
    captures = [
        FakeCapture([(True, True, _bgr((0, 0, 255)))], frame_count=1),
        FakeCapture([(True, True, _bgr((0, 255, 0)))], frame_count=1),
    ]

    def factory(_path):
        return captures.pop(0)

    reader = VideoReader.open(_path(tmp_path), capture_factory=factory)
    old_capture = reader.capture
    restarted = reader.restart()

    assert old_capture.released is True
    assert restarted.frame_index == 0
    assert restarted.session_id == reader.first_frame.session_id
    np.testing.assert_array_equal(restarted.rgb[0, 0], [0, 255, 0])
    reader.release()


def test_unsupported_extension_is_rejected_without_opening_capture(tmp_path) -> None:
    called = False

    def factory(_path):
        nonlocal called
        called = True
        return FakeCapture([])

    path = _path(tmp_path, "clip.mov")
    with pytest.raises(InputError, match="MP4 or AVI"):
        VideoReader.open(path, capture_factory=factory)
    assert called is False
