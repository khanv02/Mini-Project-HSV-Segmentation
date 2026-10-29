# Danh mục tính năng

Trang này giúp chọn đúng tính năng trước khi đi vào hướng dẫn chi tiết.

| Khi bạn muốn… | Nên dùng |
|---|---|
| Chọn một màu hoặc dải màu trong ảnh | [Ngưỡng HSV](hsv-thresholding/README.md) |
| Chưa biết nên đặt ngưỡng bao nhiêu | [Lấy mẫu và histogram](sampling-histogram/README.md) |
| Mask có chấm nhiễu hoặc lỗ nhỏ | [Morphology](morphology/README.md) |
| Đếm vật thể và loại vùng quá nhỏ | [Phân tích vật thể](object-analysis/README.md) |
| Hai vật thể chạm nhau thành một vùng | [Watershed](watershed/README.md) |
| Biết kết quả đúng đến đâu | [Ground-truth evaluation](ground-truth-evaluation/README.md) |
| Làm việc với video hoặc lưu kết quả nghiên cứu | [Video, xuất file và experiment](video-export-experiments/README.md) |

## Thứ tự sử dụng thường gặp

1. Tạo mask bằng ngưỡng HSV.
2. Dùng morphology nếu mask cần làm sạch.
3. Bật phân tích vật thể hoặc Watershed khi có nhu cầu tương ứng.
4. Nạp ground truth nếu cần đo độ chính xác.
5. Xuất PNG hoặc ghi experiment.

Các bước 2–4 đều tùy chọn. Ứng dụng luôn giữ mask HSV cơ sở để người dùng có thể quay lại
kết quả đơn giản và dễ giải thích nhất.
