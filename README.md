# HSV Color Segmentation

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter%20%2F%20ttk-2563EB)](https://docs.python.org/3/library/tkinter.html)
[![NumPy](https://img.shields.io/badge/NumPy-2.x-013243?logo=numpy&logoColor=white)](https://numpy.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-5C3EE8?logo=opencv&logoColor=white)](https://opencv.org/)
[![Tests](https://img.shields.io/badge/tests-319%20passed-16A34A)](docs/verification/feature-003-grayscale-otsu-overlay.md)

Ứng dụng desktop chạy offline để học tập, trình diễn và đánh giá phân đoạn ảnh. HSV là chế độ
mặc định cho ảnh màu; ảnh xám chính xác có thể dùng ngưỡng cường độ thủ công hoặc Otsu toàn cục.
Ứng dụng hỗ trợ ảnh/video, morphology, phân tích vùng liên thông, Watershed, đánh giá bằng ground
truth, xuất Overlay và lưu thí nghiệm có thể tái lập.

## Bắt đầu nhanh

Yêu cầu: Windows 10/11 x64, Python 3.11 có Tcl/Tk và
[uv](https://docs.astral.sh/uv/).

```powershell
git clone https://github.com/khanv02/hsv-segmentation.git
cd hsv-segmentation
uv sync --locked --extra test
uv run hsv
```

Sau khi mở ứng dụng:

1. Chọn **Open Image…** hoặc **Open Video…**.
2. Giữ **HSV** để chọn theo màu, hoặc chọn **Grayscale** cho ảnh có ba kênh RGB bằng nhau.
3. Chỉnh khoảng HSV; với Grayscale, chọn ngưỡng Manual/Otsu và vùng sáng hoặc tối.
4. Quan sát đồng thời **Original**, **Binary Mask**, **Segmented Result** và **Overlay**.
5. Dùng **Save Mask…**, **Save Result…** hoặc **Save Overlay…** để xuất đúng loại bằng chứng cần dùng.

Nếu đây là lần đầu sử dụng, xem [hướng dẫn bắt đầu](docs/getting-started/README.md) hoặc
[chọn tutorial theo nhu cầu](docs/tutorials/README.md).

## Giao diện

- Bốn preview đồng bộ luôn tách riêng ảnh gốc, mask, kết quả và lớp overlay.
- Histogram H/S/V hiển thị mặc định bên dưới preview và có thể thu gọn.
- Chế độ phân đoạn, ngưỡng Grayscale/Otsu và polarity nằm trên thanh trên cùng; Hue được đánh dấu
  không có ý nghĩa khi Grayscale đang hoạt động.
- Các chức năng được gom vào ba tab phía trên: **HSV Thresholds**, **Refine & Separate** và
  **Analyze**, giúp dành toàn bộ chiều rộng cho vùng ảnh.
- Mỗi preview có Fit, zoom và pan độc lập.

## Tính năng

| Nhóm | Dùng để làm gì? | Tài liệu |
|---|---|---|
| Ngưỡng HSV | Chọn pixel theo màu sắc, độ bão hòa và độ sáng | [Chi tiết](docs/features/hsv-thresholding/README.md) |
| Grayscale và Otsu | Chọn vùng sáng/tối của ảnh xám bằng ngưỡng thủ công hoặc Otsu toàn cục | [Ảnh xám](docs/features/grayscale-segmentation.md) · [Otsu](docs/features/otsu-threshold.md) |
| Lấy mẫu và histogram | Lấy 1 pixel, kết hợp 2–4 pixel hoặc một ROI để tìm khoảng HSV khởi đầu | [Chi tiết](docs/features/sampling-histogram/README.md) |
| Morphology | Loại đốm nhiễu nhỏ hoặc lấp lỗ trong mask | [Chi tiết](docs/features/morphology/README.md) |
| Phân tích vật thể | Đếm, lọc và đo các vùng liên thông | [Chi tiết](docs/features/object-analysis/README.md) |
| Watershed | Thử tách các vật thể đang chạm nhau | [Chi tiết](docs/features/watershed/README.md) |
| Ground-truth evaluation | Đo chất lượng mask bằng IoU, Dice và TP/FP/FN | [Chi tiết](docs/features/ground-truth-evaluation/README.md) |
| Video, xuất file và experiment | Xử lý frame, xuất PNG và lưu bằng chứng tái lập | [Chi tiết](docs/features/video-export-experiments/README.md) |
| Save Overlay | Lưu chính xác tint, contour/box, Watershed hoặc TP/FP/FN đang hiển thị | [Chi tiết](docs/features/overlay-export.md) |
| Experiment tái lập | Ghi mode, nguồn threshold, polarity và hash artifact | [Chi tiết](docs/features/experiments.md) |

Xem [danh mục tính năng](docs/features/README.md) để chọn đúng công cụ cho từng nhu cầu.

## Tutorial

| Bạn muốn… | Hướng dẫn |
|---|---|
| Làm quen với toàn bộ giao diện | [Bắt đầu sử dụng](docs/getting-started/README.md) |
| Phân đoạn ảnh xám bằng Manual hoặc Otsu | [Ảnh xám và Otsu](docs/tutorials/grayscale-manual.md) |
| Lưu lớp minh họa đang hiển thị | [Save Overlay](docs/tutorials/save-overlay.md) |

Xem [toàn bộ tutorial](docs/tutorials/README.md) để chọn luồng thực hành phù hợp.

## Tài liệu

| Nội dung | Dành cho |
|---|---|
| [Hướng dẫn bắt đầu](docs/getting-started/README.md) | Người sử dụng lần đầu |
| [Danh mục tính năng](docs/features/README.md) | Người muốn biết từng tính năng có tác dụng gì |
| [Danh mục tutorial](docs/tutorials/README.md) | Người muốn thực hành theo từng mục tiêu |
| [Pipeline và kiến trúc](docs/architecture/README.md) | Người muốn hiểu luồng xử lý và cấu trúc mã nguồn |
| [Thuật toán và quy ước số](docs/algorithm.md) | Người cần công thức và chi tiết kỹ thuật |
| [Hướng dẫn acceptance](docs/acceptance.md) | Người nghiệm thu ứng dụng |
| [Kết quả verification](docs/verification.md) | Người kiểm tra bằng chứng test/benchmark |
| [Kiểm chứng Grayscale, Otsu và Overlay](docs/verification/feature-003-grayscale-otsu-overlay.md) | Người kiểm tra test và benchmark của các chức năng này |

## Kiểm thử

```powershell
uv run --locked --extra test pytest -q
```

Checkpoint gần nhất:

- **319** test tự động đạt;
- baseline GUI Full HD đạt **99/100** cập nhật trong một giây;
- Grayscale Full HD đạt **98/100** cập nhật trong một giây, p95 **586,08 ms**;
- analysis và Watershed giữ UI responsive nhưng không cam kết xử lý thời gian thực.

## Giới hạn

HSV và Grayscale thresholding phân đoạn pixel theo màu hoặc cường độ; đây không phải object
detection hay machine learning. Bóng, vùng chói, phản xạ, cân bằng trắng, nén ảnh và ánh sáng
không đều có thể làm kết quả thay đổi. Otsu là một ngưỡng toàn cục, phù hợp nhất với histogram
gần hai đỉnh. Accuracy chỉ có ý nghĩa khi người dùng cung cấp ground truth phù hợp.

Ứng dụng không bao gồm camera trực tiếp, object tracking, adaptive/local thresholding, tự động
chuyển ảnh màu sang xám, backend, database hoặc dịch vụ mạng.

## Bản quyền

Mã nguồn được cấp phép theo [MIT License](LICENSE), bản quyền © 2026 Khang Pham.
License và provenance của dữ liệu thí nghiệm được ghi riêng trong
[`experiments/manifest.json`](experiments/manifest.json).
