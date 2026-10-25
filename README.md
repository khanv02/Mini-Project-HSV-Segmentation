# HSV Color Segmentation

[![Python][Python-shield]][Python-url]
[![Tkinter][Tkinter-shield]][Tkinter-url]
[![NumPy][NumPy-shield]][NumPy-url]
[![Pillow][Pillow-shield]][Pillow-url]
[![OpenCV][OpenCV-shield]][OpenCV-url]
[![pytest][Pytest-shield]][Pytest-url]
[![uv][UV-shield]][UV-url]

Ứng dụng desktop phục vụ học tập và trình diễn phân đoạn màu bằng sáu ngưỡng HSV.
Người dùng có thể mở ảnh hoặc video, điều chỉnh khoảng H/S/V, quan sát đồng thời ảnh gốc,
mask nhị phân và kết quả tách màu, sau đó lưu ảnh hoặc ghi lại experiment có thể tái lập.

## Công nghệ

- **Python 3.11** — ngôn ngữ và môi trường chạy chính.
- **Tkinter / ttk** — giao diện desktop native, không cần web server.
- **NumPy** — chuyển đổi RGB → HSV và xử lý ma trận ảnh vector hóa.
- **Pillow** — đọc ảnh, dựng preview và xuất PNG lossless.
- **OpenCV** — giải mã tuần tự video MP4/AVI.
- **pytest** — kiểm thử unit, integration và tái lập experiment.
- **uv** — quản lý môi trường, dependency và lệnh chạy.

## Tính năng chính

- Đọc ảnh PNG, JPEG, BMP; chuẩn hóa ảnh xám, palette và ảnh có alpha về RGB.
- Đọc tuần tự video MP4/AVI, hỗ trợ phát, tạm dừng, kết thúc và phát lại.
- Sáu điều khiển HSV theo đơn vị độ/phần trăm, so sánh biên bao hàm và hỗ trợ hue vòng qua 0°.
- Hiển thị đồng bộ Original, Binary Mask và Segmented Result.
- Panel histogram HSV tùy chọn cho ảnh/frame hiện tại, có marker ngưỡng liên tục và thống kê
  riêng số pixel saturation dưới 5% bị loại khỏi biểu đồ hue.
- Xuất mask và ảnh kết quả PNG ở đúng độ phân giải nguồn.
- Ghi experiment theo UUID cùng threshold, mô tả ánh sáng, nhận xét và SHA-256.
- Xử lý nền có revision để loại bỏ kết quả cũ khi người dùng chỉnh nhanh.
- Hoạt động offline; không cần tài khoản, database, dịch vụ mạng hay project khác.

## Trạng thái

- **210/210** kiểm thử tự động đã đạt ở checkpoint gần nhất.
- Benchmark GUI Full HD khi hiện histogram đạt **99/100** lần cập nhật dưới một giây trên máy
  đã ghi nhận, vượt tiêu chí tối thiểu 95/100.
- Hoàn thành **54/56** task.
- Còn T049 (hai kiểm tra nghiệm thu độc lập với người thật) và T050 (rà soát cuối sau T049).

Chi tiết nằm trong [kết quả xác minh](docs/verification.md),
[thuật toán](docs/algorithm.md) và [kịch bản demo](docs/demo.md).

## Cấu trúc dự án

```text
HSV Segmentation/
├── src/hsv_segmentation/       # Mã nguồn ứng dụng
│   ├── processing/             # Thuật toán RGB/HSV thuần, không phụ thuộc GUI/I/O
│   ├── io/                     # Đọc ảnh/video, xuất file và experiment
│   ├── application/            # Session, playback và background worker
│   └── gui/                    # Cửa sổ, widget và controller Tk
├── tests/
│   ├── unit/                   # Kiểm thử thuật toán và model độc lập
│   ├── integration/            # Kiểm thử workflow ảnh/video/export/recovery
│   └── fixtures/               # Dữ liệu kiểm thử nhỏ, tái tạo được
├── scripts/                    # Công cụ sinh fixture, experiment và benchmark
├── experiments/                # Dataset demo đã tuyển chọn và bằng chứng thực nghiệm
├── docs/                       # Thuật toán, nghiệm thu, demo và kết quả xác minh
├── specs/                      # Specification, plan, contract và task ledger
├── pyproject.toml              # Metadata, dependency và entrypoint
└── uv.lock                     # Dependency lock chính thức
```

## Cài đặt

Yêu cầu Windows 10/11 x64, Python 3.11 có Tcl/Tk và `uv`.

```powershell
uv sync --locked --extra test
```

Lần đồng bộ đầu tiên cần Internet hoặc cache package. Sau khi cài đặt, toàn bộ workflow chạy
offline. `uv.lock` là lockfile chính; `requirements-lock.txt` được giữ làm bản ghi môi trường
lịch sử của giai đoạn thiết lập.

## Chạy ứng dụng

```powershell
uv run hsv
```

Alias tương thích dài hơn vẫn được giữ:

```powershell
uv run hsv-segmentation
```

## Cách sử dụng nhanh

1. Chọn **Open Image…** hoặc **Open Video…**.
2. Điều chỉnh Lower/Upper H, S và V. H dùng độ; S/V dùng phần trăm.
3. Nếu Lower H lớn hơn Upper H, khoảng hue sẽ vòng qua 0° (ví dụ `350..10`).
4. So sánh ba khung Original, Binary Mask và Segmented Result.
5. Bật **Show Histogram** để xem phân bố H/S/V của ảnh hoặc frame hiện tại. Vùng đỏ biểu diễn
   đúng các ngưỡng đang dùng; biểu đồ chỉ hỗ trợ chọn thủ công, không tự tìm ngưỡng.
6. Dùng `−`, `Fit`, `+` hoặc con lăn chuột trên từng khung để thu/phóng; kéo thanh cuộn
   để xem vùng ảnh khi đã zoom và double-click để trở về Fit.
7. Dùng **Save Mask…** hoặc **Save Result…** để xuất PNG lossless.
8. Nhập mô tả ánh sáng/nhận xét rồi dùng **Record Experiment** khi cần lưu bằng chứng.

## Kiểm thử

Chạy toàn bộ test:

```powershell
uv run --locked --extra test pytest -q
```

Chạy riêng từng lớp:

```powershell
uv run --locked --extra test pytest tests/unit -q
uv run --locked --extra test pytest tests/integration -q
```

## Script hỗ trợ

```powershell
# Tạo lại bộ fixture định dạng nhỏ
uv run python scripts/generate_acceptance_media.py

# Tạo lại 20 experiment (chỉ chạy khi muốn thay bộ bằng chứng hiện tại)
uv run python scripts/generate_experiment_evidence.py

# Đo 100 lần cập nhật GUI trên ảnh 1920×1080
uv run python scripts/benchmark_gui_performance.py
```

Script experiment từ chối ghi đè thư mục `experiments/runs/` không rỗng nhằm bảo vệ bằng chứng
đang giữ. Xem [hướng dẫn experiment](experiments/README.md) trước khi tái tạo.

## Thuật toán và giới hạn

RGB được chuẩn hóa sang `float64`, chuyển sang H trong `[0,360)` và S/V trong `[0,100]`.
Mask dùng so sánh bao hàm, có giá trị đúng `0` hoặc `255`; pixel được chọn giữ nguyên RGB,
pixel còn lại chuyển thành đen. Công thức đầy đủ nằm tại [docs/algorithm.md](docs/algorithm.md).
Histogram dùng 360 bin H và 101 bin cho mỗi S/V. Biểu đồ H bỏ qua pixel có S dưới 5% vì hue
không ổn định ở vùng gần trung tính; quy tắc hiển thị này không thay đổi phép phân đoạn.

HSV thresholding không phải nhận dạng vật thể. Bóng, vùng chói, cân bằng trắng, nén ảnh,
phản xạ và màu có saturation thấp có thể làm kết quả thay đổi. Phạm vi hiện tại không gồm
tracking, audio, camera trực tiếp, tìm kiếm frame hay mã hóa toàn bộ video đầu ra.

## Dữ liệu và khả năng tái lập

`experiments/manifest.json` quản lý 10 ảnh có provenance và hash, gồm tám ảnh SimpleCube++
CC BY 4.0 và hai ảnh cùng một cảnh MIT dưới hai hướng chiếu sáng thật (CC-BY). Hai threshold
được lưu cho mỗi ảnh, tạo thành 20 run hoàn chỉnh. Không sử dụng các ảnh ngoài manifest làm
bằng chứng chính thức.

Việc nghiệm thu cuối cần một sinh viên thứ hai tái lập ba run và một sinh viên hoàn thành luồng
mở ảnh → chỉnh HSV → so sánh → lưu kết quả trong tối đa năm phút mà không được hỗ trợ.

[Python-shield]: https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python&logoColor=white
[Python-url]: https://docs.python.org/3.11/
[Tkinter-shield]: https://img.shields.io/badge/Tkinter-ttk-2C5F2D?style=for-the-badge&logo=python&logoColor=white
[Tkinter-url]: https://docs.python.org/3.11/library/tkinter.html
[NumPy-shield]: https://img.shields.io/badge/NumPy-2.x-013243?style=for-the-badge&logo=numpy&logoColor=white
[NumPy-url]: https://numpy.org/
[Pillow-shield]: https://img.shields.io/badge/Pillow-Imaging-8A2BE2?style=for-the-badge&logo=python&logoColor=white
[Pillow-url]: https://pillow.readthedocs.io/
[OpenCV-shield]: https://img.shields.io/badge/OpenCV-4.x-5C3EE8?style=for-the-badge&logo=opencv&logoColor=white
[OpenCV-url]: https://opencv.org/
[Pytest-shield]: https://img.shields.io/badge/pytest-Testing-0A9EDC?style=for-the-badge&logo=pytest&logoColor=white
[Pytest-url]: https://docs.pytest.org/
[UV-shield]: https://img.shields.io/badge/uv-Package%20Manager-DE5FE9?style=for-the-badge&logo=uv&logoColor=white
[UV-url]: https://docs.astral.sh/uv/
