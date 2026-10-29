# HSV Color Segmentation

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Tkinter](https://img.shields.io/badge/GUI-Tkinter%20%2F%20ttk-2563EB)](https://docs.python.org/3/library/tkinter.html)
[![NumPy](https://img.shields.io/badge/NumPy-2.x-013243?logo=numpy&logoColor=white)](https://numpy.org/)
[![OpenCV](https://img.shields.io/badge/OpenCV-4.x-5C3EE8?logo=opencv&logoColor=white)](https://opencv.org/)
[![Tests](https://img.shields.io/badge/tests-283%20passed-16A34A)](docs/verification.md)
[![Feature 002](https://img.shields.io/badge/feature%20002-30%2F30%20tasks-16A34A)](specs/002-object-separation-evaluation/tasks.md)

Ứng dụng desktop chạy offline để học tập, trình diễn và đánh giá phân đoạn màu bằng
ngưỡng HSV. Ứng dụng hỗ trợ ảnh/video, morphology, phân tích vùng liên thông, Watershed,
đánh giá bằng ground truth và lưu thí nghiệm có thể tái lập.

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
2. Chỉnh khoảng Hue, Saturation và Value.
3. Quan sát đồng thời **Original**, **Mask** và **Result**.
4. Dùng **Save Mask…** hoặc **Save Result…** để xuất kết quả.

Nếu đây là lần đầu sử dụng, xem [hướng dẫn từng bước](docs/getting-started/README.md).

## Tính năng

| Nhóm | Dùng để làm gì? | Tài liệu |
|---|---|---|
| Ngưỡng HSV | Chọn pixel theo màu sắc, độ bão hòa và độ sáng | [Chi tiết](docs/features/hsv-thresholding/README.md) |
| Lấy mẫu và histogram | Tìm khoảng HSV khởi đầu và xem phân bố màu | [Chi tiết](docs/features/sampling-histogram/README.md) |
| Morphology | Loại đốm nhiễu nhỏ hoặc lấp lỗ trong mask | [Chi tiết](docs/features/morphology/README.md) |
| Phân tích vật thể | Đếm, lọc và đo các vùng liên thông | [Chi tiết](docs/features/object-analysis/README.md) |
| Watershed | Thử tách các vật thể đang chạm nhau | [Chi tiết](docs/features/watershed/README.md) |
| Ground-truth evaluation | Đo chất lượng mask bằng IoU, Dice và TP/FP/FN | [Chi tiết](docs/features/ground-truth-evaluation/README.md) |
| Video, xuất file và experiment | Xử lý frame, xuất PNG và lưu bằng chứng tái lập | [Chi tiết](docs/features/video-export-experiments/README.md) |

Xem [danh mục tính năng](docs/features/README.md) để chọn đúng công cụ cho từng nhu cầu.

## Tài liệu

| Nội dung | Dành cho |
|---|---|
| [Hướng dẫn bắt đầu](docs/getting-started/README.md) | Người sử dụng lần đầu |
| [Danh mục tính năng](docs/features/README.md) | Người muốn biết từng tính năng có tác dụng gì |
| [Pipeline và kiến trúc](docs/architecture/README.md) | Người muốn hiểu luồng xử lý và cấu trúc mã nguồn |
| [Thuật toán và quy ước số](docs/algorithm.md) | Người cần công thức và chi tiết kỹ thuật |
| [Hướng dẫn acceptance](docs/acceptance.md) | Người nghiệm thu ứng dụng |
| [Kết quả verification](docs/verification.md) | Người kiểm tra bằng chứng test/benchmark |
| [Báo cáo feature 002](experiments/feature-002/report.md) | Người xem kết quả object analysis, Watershed và evaluation |

## Kiểm thử

```powershell
uv run --locked --extra test pytest -q
```

Checkpoint gần nhất:

- **283/283** test tự động đạt trên Python 3.11/Tk 8.6;
- **30/30** task của feature 002 hoàn tất;
- baseline GUI Full HD đạt **99/100** cập nhật trong một giây;
- analysis và Watershed giữ UI responsive nhưng không cam kết xử lý thời gian thực.

## Giới hạn

HSV thresholding phân đoạn pixel theo màu; đây không phải object detection hay machine
learning. Bóng, vùng chói, phản xạ, cân bằng trắng, nén ảnh và màu có saturation thấp có thể
làm kết quả thay đổi. Accuracy chỉ có ý nghĩa khi người dùng cung cấp ground truth phù hợp.

Ứng dụng không bao gồm camera trực tiếp, object tracking, tự động chọn threshold, backend,
database hoặc dịch vụ mạng.

## Bản quyền

Mã nguồn được cấp phép theo [MIT License](LICENSE), bản quyền © 2026 Khang Pham.
License và provenance của dữ liệu thí nghiệm được ghi riêng trong
[`experiments/manifest.json`](experiments/manifest.json).
