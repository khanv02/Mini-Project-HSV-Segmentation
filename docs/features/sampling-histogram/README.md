# Lấy mẫu màu và histogram

## Dùng để làm gì?

Nhóm công cụ này giúp tìm ngưỡng khởi đầu; nó không tự quyết định ngưỡng tối ưu.

- **Pick Color – Pixel:** lấy HSV tại một điểm ảnh.
- **Pick Color – ROI:** lấy mẫu từ một vùng ảnh để đề xuất khoảng rộng hơn.
- **Histogram H/S/V:** hiển thị phân bố giá trị màu của frame hiện tại và vị trí các ngưỡng.

## Cách dùng

1. Mở ảnh hoặc dừng video tại frame cần xem.
2. Chọn **Pick Color**, sau đó chọn Pixel hoặc ROI.
3. Nhấp vào vật thể hoặc kéo vùng chứa màu đại diện.
4. Histogram hiển thị mặc định; xem dải màu vàng để biết ngưỡng đang giữ phần nào của
   phân bố. Dùng **Hide Histogram** nếu cần thu gọn tạm thời.
5. Chỉnh lại H, S và V bằng mắt dựa trên Mask/Result.

## Lưu ý

Một pixel có thể không đại diện cho toàn bộ vật thể. ROI thường ổn định hơn khi vật thể có
bóng hoặc nhiều sắc độ. Histogram chỉ mô tả số lượng pixel, không đo độ chính xác phân đoạn.
