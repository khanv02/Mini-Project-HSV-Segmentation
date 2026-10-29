# Kiểm chứng Feature 003: Grayscale, Otsu và Save Overlay

## Môi trường

- Ngày kiểm chứng: 2026-10-30
- Lệnh cài đặt: `uv sync --extra test`

## Foundation và tương thích HSV

- `uv run pytest tests/unit/test_models.py -q`: **62 passed**.
- `uv run pytest tests/integration/test_playback.py tests/integration/test_image_session.py tests/integration/test_histogram_panel.py -q`: **26 passed**.
- Các constructor cũ vẫn mặc định `segmentation_mode=hsv`; worker/playback cũ không cần truyền tham số mới.

## US1 — Grayscale thủ công

- Exact eligibility, `I > T`, `I <= T`, biên 0/255 và complement được kiểm bằng fixture NumPy.
- Ảnh gần xám bị từ chối; HSV vẫn là mode mặc định.
- Histogram ghi rõ Hue unavailable và bốn preview vẫn giữ kích thước nghiệm thu.

## US2 — Otsu

- Histogram hai mức 20/220 trả ngưỡng 20 theo quy tắc `smallest_optimal_threshold`.
- Ảnh hằng trả `unavailable`; không tạo mask giả.
- Manual threshold được giữ khi chuyển qua lại Otsu.

## US3 — Save Overlay

- PNG decode lại khớp chính xác `OverlaySnapshot.rgb`.
- Receipt giữ variant và danh tính source/frame; Save Mask/Result vẫn qua regression cũ.
- Test tập trung Overlay/export/experiment: **31 passed**.

## US4 — Experiment schema 3

- Manual/Otsu hoặc Overlay dùng schema 3; HSV baseline/extended vẫn lần lượt là schema 1/2.
- Schema 3 giữ threshold source/value, polarity, tie rule, variant, file hash và pixel hash.
- Loader chấp nhận 1/2/3 và tiếp tục từ chối version không biết.

## Hiệu năng và regression

- `uv run pytest -q`: **319 passed** trong 46.36 giây sau refactor.
- Benchmark `grayscale-full-hd`, 100 edit: **98/100** trong một giây; median **450.85 ms**,
  p95 **586.08 ms**, maximum **1783.07 ms**.
- Heartbeat: **99** mẫu trong 250 ms; cả latency và heartbeat criterion đều đạt.
- Raw evidence: `experiments/grayscale_performance_results.json`; input được tạo tất định bởi script.

## Truy vết yêu cầu

| Nhóm | Bằng chứng |
|---|---|
| FR-001..FR-007 | Mode/model/core/session/UI tests; HSV mặc định và mask dùng chung downstream |
| FR-008..FR-012 | Otsu analytical/constant/tie/playback/UI tests |
| FR-013..FR-016 | Overlay composition/export/controller race tests |
| FR-017..FR-019 | Schema 3 và legacy schema 1/2 tests |
| FR-020..FR-021 | Tài liệu tiếng Việt; không có adaptive/auto conversion/ML |
| SC-001..SC-003 | Tutorial và exact fixture tests |
| SC-004..SC-005 | Pixel round-trip và experiment hash tests |
| SC-006 | Full regression 319 passed |
| SC-007 | Retained Full-HD benchmark đạt criterion |
| SC-008 | Tài liệu phân biệt input/mask/Result/Overlay và cảnh báo accuracy |
