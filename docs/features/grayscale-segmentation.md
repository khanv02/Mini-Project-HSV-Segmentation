# Phân đoạn ảnh xám

Ảnh xám có thể được lưu dưới dạng RGB, nhưng ba kênh phải bằng nhau tại mọi pixel. Ứng dụng không
tự coi ảnh “gần xám” là ảnh xám và luôn mở nguồn mới ở chế độ HSV.

- **Bright > T** chọn vùng sáng hơn ngưỡng.
- **Dark <= T** chọn vùng tối, kể cả pixel bằng ngưỡng.

Binary Mask chỉ gồm đen/trắng; nó không phải ảnh đầu vào màu xám. Mask tiếp tục dùng được với
morphology, phân tích vật thể, Watershed và ground truth như mask HSV.
