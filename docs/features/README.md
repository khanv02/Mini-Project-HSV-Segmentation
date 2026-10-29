# Danh mục tính năng

Trang này giúp chọn đúng tính năng trước khi đi vào hướng dẫn chi tiết.

| Khi bạn muốn… | Nên dùng |
|---|---|
| Chọn một màu hoặc dải màu trong ảnh | [Ngưỡng HSV](hsv-thresholding/README.md) |
| Chọn vùng sáng hoặc tối trong ảnh xám | [Phân đoạn ảnh xám](grayscale-segmentation.md) và [Otsu](otsu-threshold.md) |
| Chưa biết nên đặt ngưỡng bao nhiêu | [Lấy mẫu và histogram](sampling-histogram/README.md) |
| Mask có chấm nhiễu hoặc lỗ nhỏ | [Morphology](morphology/README.md) |
| Đếm vật thể và loại vùng quá nhỏ | [Phân tích vật thể](object-analysis/README.md) |
| Hai vật thể chạm nhau thành một vùng | [Watershed](watershed/README.md) |
| Biết kết quả đúng đến đâu | [Ground-truth evaluation](ground-truth-evaluation/README.md) |
| Làm việc với video hoặc lưu kết quả nghiên cứu | [Video, xuất file và experiment](video-export-experiments/README.md) |
| Lưu đúng lớp minh họa đang hiển thị | [Save Overlay](overlay-export.md) |
| Hiểu dữ liệu tái lập của Grayscale/Overlay | [Experiment schema 3](experiments.md) |

## Thứ tự sử dụng thường gặp

1. Tạo mask bằng ngưỡng HSV, hoặc chọn Grayscale thủ công/Otsu cho ảnh xám hợp lệ.
2. Dùng morphology nếu mask cần làm sạch.
3. Bật phân tích vật thể hoặc Watershed khi có nhu cầu tương ứng.
4. Nạp ground truth nếu cần đo độ chính xác.
5. Xuất Mask, Result, Overlay hoặc ghi experiment.

Các bước 2–4 đều tùy chọn. Ứng dụng giữ mask cơ sở của mode đang chọn để các bước phía sau dùng
chung một đầu vào nhị phân rõ ràng và có thể kiểm chứng.

## Tutorial liên quan

Các trang trên giải thích từng chức năng và giới hạn của nó. Nếu muốn thực hành theo từng bước,
xem [danh mục tutorial](../tutorials/README.md).
