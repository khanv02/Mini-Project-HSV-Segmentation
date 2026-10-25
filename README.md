# HSV Color Segmentation

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter%20%2F%20ttk-2563EB)](https://docs.python.org/3/library/tkinter.html)
[![NumPy](https://img.shields.io/badge/NumPy-2.x-013243?logo=numpy&logoColor=white)](https://numpy.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-5C3EE8?logo=opencv&logoColor=white)](https://opencv.org/)
[![Tests](https://img.shields.io/badge/tests-248%20passed-16A34A)](docs/verification.md)
[![Status](https://img.shields.io/badge/status-62%2F64%20tasks-F59E0B)](specs/001-hsv-color-segmentation/tasks.md)

Ứng dụng desktop độc lập dùng để học tập, trình diễn và đánh giá phân đoạn màu bằng
ngưỡng HSV. Toàn bộ workflow hoạt động offline: mở ảnh hoặc video, điều chỉnh sáu ngưỡng,
so sánh ảnh gốc với mask và kết quả phân đoạn, sau đó xuất PNG hoặc lưu một experiment
có thể tái lập.

## Đây là gì?

HSV Color Segmentation là công cụ trực quan hóa thuật toán phân đoạn màu theo ba thành phần:

- **Hue (H)** — góc màu trong khoảng `[0°, 360°)`;
- **Saturation (S)** — độ bão hòa trong khoảng `[0%, 100%]`;
- **Value (V)** — độ sáng trong khoảng `[0%, 100%]`.

Ứng dụng dành cho sinh viên và giảng viên cần một công cụ dễ giải thích, có kết quả xác định,
không phụ thuộc dịch vụ mạng và có đủ bằng chứng kiểm thử cho báo cáo học thuật.

## Điểm nổi bật

- Mở ảnh **PNG, JPEG, BMP** và video **MP4, AVI** được decoder cục bộ hỗ trợ.
- Hiển thị đồng thời **Original**, **Binary Mask** và **Segmented Result**.
- Sáu ngưỡng HSV dạng số nguyên, cập nhật tự động và hỗ trợ hue vòng qua `0°`.
- Preset khởi đầu cho Red, Yellow, Green và Blue.
- Lấy mẫu trực tiếp từ một pixel hoặc vùng ROI để đề xuất khoảng HSV.
- Morphology tùy chọn với Opening, Closing hoặc Opening + Closing.
- Chế độ overlay, so sánh mask trước/sau morphology và thống kê tỷ lệ pixel được chọn.
- Histogram H/S/V cho frame hiện tại với marker ngưỡng liên tục.
- Zoom, Fit, cuộn và pan độc lập trên từng vùng preview.
- Xuất mask và kết quả dưới dạng PNG lossless ở đúng độ phân giải nguồn.
- Lưu experiment gồm UUID, nguồn, frame, threshold, ghi chú, SHA-256 và các artifact liên quan.
- Xử lý nền có revision để loại bỏ kết quả cũ khi người dùng chỉnh nhanh.
- Giao diện light-first theo kiểu scientific workspace, hỗ trợ bàn phím và hoạt động offline.

## Kiến trúc

```text
Local image / video
        │
        ▼
┌────────────────┐     ┌──────────────────────┐
│ I/O adapters   │ ──▶ │ Session + playback   │
│ Pillow/OpenCV  │     │ Revision coordination│
└────────────────┘     └──────────┬───────────┘
                                  │
                                  ▼
                       ┌──────────────────────┐
                       │ Pure processing      │
                       │ RGB→HSV, mask,       │
                       │ morphology, histogram│
                       └──────────┬───────────┘
                                  │
                    ┌─────────────┴─────────────┐
                    ▼                           ▼
             Tkinter workspace          PNG / experiment export
```

| Layer | Trách nhiệm |
|---|---|
| `processing/` | Thuật toán thuần trên mảng NumPy; không đọc file và không phụ thuộc GUI |
| `io/` | Đọc ảnh/video, xuất PNG và ghi experiment |
| `application/` | Session, playback, background worker và kiểm soát revision |
| `gui/` | Theme, controls, preview, histogram, dialog và controller Tk |

## Yêu cầu

- Windows 10/11 x64
- Python 3.11 có Tcl/Tk
- [uv](https://docs.astral.sh/uv/)

Ứng dụng không yêu cầu tài khoản, database, web server hoặc kết nối mạng khi chạy.

## Cài đặt và chạy

```powershell
git clone <repository-url>
cd "HSV Segmentation"
uv sync --locked --extra test
uv run hsv
```

Entrypoint tương đương:

```powershell
uv run hsv-segmentation
```

## Sử dụng nhanh

1. Chọn **Open Image…** hoặc **Open Video…**.
2. Điều chỉnh Lower/Upper của Hue, Saturation và Value trong inspector bên trái.
3. So sánh ba preview Original, Mask và Result.
4. Dùng **Pick Color** với chế độ Pixel hoặc ROI nếu cần một khoảng HSV khởi đầu.
5. Bật Morphology khi cần loại nhiễu nhỏ hoặc lấp các lỗ nhỏ trong mask.
6. Mở **Show Histogram** để đối chiếu phân bố màu với các ngưỡng đang dùng.
7. Dùng **Save Mask…**, **Save Result…** hoặc **Record Experiment…** để lưu kết quả.

Hue cho phép khoảng vòng qua gốc đỏ. Ví dụ `H = 350°..10°` chọn cả phần cuối và phần
đầu của vòng màu. Các khoảng S và V luôn phải có lower không lớn hơn upper.

### Phím tắt

| Phím | Hành động |
|---|---|
| `Ctrl+O` | Mở ảnh |
| `Ctrl+Shift+O` | Mở video |
| Con lăn chuột trên preview | Phóng to hoặc thu nhỏ |
| Double-click trên preview | Trở về Fit |

## Định dạng hỗ trợ

| Loại | Định dạng | Ghi chú |
|---|---|---|
| Ảnh | PNG, JPEG, BMP | Ảnh xám được nhân thành RGB; alpha được bỏ qua |
| Video | MP4, AVI | Codec thực tế phụ thuộc OpenCV backend trên máy chạy |
| Xuất ảnh | PNG | Mask chỉ chứa 0/255; result giữ nguyên pixel RGB được chọn |
| Experiment | JSON + PNG | Metadata, hash và đường dẫn artifact cục bộ |

Bộ acceptance hiện có fixture cho RGB PNG/JPEG/BMP, grayscale PNG, RGBA PNG, MJPG/AVI
và mp4v/MP4.

## Kiểm thử

Chạy toàn bộ test:

```powershell
uv run --locked --extra test pytest -q
```

Chạy theo lớp:

```powershell
uv run --locked --extra test pytest tests/unit -q
uv run --locked --extra test pytest tests/integration -q
```

Checkpoint gần nhất:

- **248/248** test tự động đạt;
- GUI Full HD với histogram đạt **99/100** cập nhật trong một giây;
- **62/64** task hoàn tất;
- T049 và T050 vẫn mở vì cần nghiệm thu độc lập với người tham gia thật.

Chi tiết lệnh, môi trường và kết quả nằm trong
[docs/verification.md](docs/verification.md).

## Experiment và khả năng tái lập

`experiments/manifest.json` quản lý 10 ảnh có provenance và SHA-256. Mỗi ảnh có hai
cấu hình threshold, tạo thành 20 run hoàn chỉnh. Bộ dữ liệu chính gồm tám ảnh
SimpleCube++ CC BY 4.0 và hai ảnh MIT của cùng một cảnh dưới hai hướng chiếu sáng.

```text
experiments/
├── inputs/                 # 10 ảnh được manifest quản lý
├── runs/<uuid>/            # mask.png, result.png, record.json
├── manifest.json           # provenance, hash và liên kết run
├── environment.json        # môi trường tái lập
├── performance_results.json
├── report.md
└── reproduction.md
```

Không chạy generator experiment nếu muốn giữ nguyên bộ bằng chứng hiện tại. Script chủ động
từ chối ghi đè thư mục `experiments/runs/` không rỗng.

## Công cụ bảo trì

```powershell
# Tạo lại fixture định dạng nhỏ
uv run python scripts/generate_acceptance_media.py

# Tạo bộ experiment mới có chủ đích
uv run python scripts/generate_experiment_evidence.py

# Benchmark 100 lần cập nhật GUI trên ảnh 1920×1080
uv run python scripts/benchmark_gui_performance.py
```

Xem thêm tại [scripts/README.md](scripts/README.md).

## Cấu trúc repository

```text
.
├── src/hsv_segmentation/   # Mã nguồn ứng dụng
├── tests/                  # Unit, integration và fixture
├── experiments/            # Dataset, benchmark và bằng chứng tái lập
├── scripts/                # Công cụ tạo fixture/evidence và benchmark
├── docs/                   # Thuật toán, demo, acceptance và verification
├── specs/                  # Specification, plan, contracts và task ledger
├── pyproject.toml          # Package metadata và entrypoint
└── uv.lock                 # Dependency lock chính thức
```

## Tài liệu

- [Thuật toán và quy ước số](docs/algorithm.md)
- [Hướng dẫn acceptance](docs/acceptance.md)
- [Kịch bản demo](docs/demo.md)
- [Kết quả verification](docs/verification.md)
- [Đặc tả tính năng](specs/001-hsv-color-segmentation/spec.md)
- [Implementation plan](specs/001-hsv-color-segmentation/plan.md)
- [Task ledger](specs/001-hsv-color-segmentation/tasks.md)

## Giới hạn phạm vi

HSV thresholding không phải nhận dạng vật thể. Bóng, vùng chói, phản xạ, cân bằng trắng,
nén ảnh và màu có saturation thấp có thể làm pixel dịch chuyển khỏi khoảng ngưỡng cố định.

Project hiện không bao gồm:

- object detection hoặc machine learning;
- object counting và tracking;
- camera trực tiếp, audio hoặc tìm kiếm frame;
- tự động chọn threshold;
- mã hóa toàn bộ video kết quả;
- backend, database hoặc dịch vụ mạng.

## Trạng thái bản quyền

Repository hiện chưa khai báo license cho mã nguồn ứng dụng. License và provenance của dữ liệu
thực nghiệm được ghi riêng trong `experiments/manifest.json` và tài liệu đi kèm.
