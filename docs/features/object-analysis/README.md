# Phân tích vật thể

## Là gì?

Tính năng này xem mỗi vùng foreground liên thông trên mask là một vùng độc lập. Đây là phân
tích vùng theo pixel, không phải nhận dạng danh tính vật thể.

## Dùng để làm gì?

- Đếm số vùng trên mask.
- Lọc bỏ vùng có diện tích nhỏ hơn **Minimum area**.
- Xem diện tích, tâm (centroid) và bounding box.
- Hiển thị contour hoặc box để kiểm tra trực quan.

## Cách dùng

1. Tạo và làm sạch mask cơ sở.
2. Bật **Object Analysis**.
3. Chọn connectivity 4 hoặc 8.
4. Đặt **Minimum area (px)** để bỏ vùng nhiễu nhỏ.
5. Xem bảng thống kê; bật **Contours** hoặc **Boxes** nếu cần overlay.

## Hiểu đúng kết quả

Hai vật thể chạm nhau có thể bị tính là một vùng. Một vật thể bị đứt mask có thể thành nhiều
vùng. ID của vùng chỉ có ý nghĩa trên frame hiện tại và không phải object tracking.
