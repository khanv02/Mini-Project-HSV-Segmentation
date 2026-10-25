# Công cụ bảo trì

Các script trong thư mục này chạy từ thư mục gốc repository bằng môi trường `uv`.

| Script | Mục đích | Đầu ra chính |
|---|---|---|
| `generate_acceptance_media.py` | Tạo bảy fixture ảnh/video nhỏ cho kiểm thử định dạng | `tests/fixtures/acceptance_media/` |
| `generate_experiment_evidence.py` | Tạo manifest, environment, report và 20 run thực nghiệm | `experiments/` |
| `benchmark_gui_performance.py` | Đo 100 cập nhật threshold qua controller/Tk thật | `experiments/performance_results.json` |

```powershell
uv run python scripts/generate_acceptance_media.py
uv run python scripts/generate_experiment_evidence.py
uv run python scripts/benchmark_gui_performance.py
```

Không chạy generator experiment nếu muốn giữ nguyên `experiments/runs/` hiện tại. Script chủ
động dừng khi thư mục run không rỗng để tránh ghi đè bằng chứng.
