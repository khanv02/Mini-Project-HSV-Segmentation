# Lấy mẫu màu và histogram

## Dùng để làm gì?

Nhóm công cụ này giúp tìm ngưỡng khởi đầu; nó không tự quyết định ngưỡng tối ưu.

- **Pick Color – Pixel:** lấy HSV tại một điểm ảnh.
- **Pick Color – Multi:** kết hợp từ 2 đến 4 điểm rời rạc trên cùng ảnh.
- **Pick Color – ROI:** lấy mẫu từ một vùng ảnh để đề xuất khoảng rộng hơn.
- **Histogram H/S/V:** hiển thị phân bố giá trị màu của frame hiện tại và vị trí các ngưỡng.

## Cách dùng

1. Mở ảnh hoặc dừng video tại frame cần xem.
2. Chọn **Pixel**, **Multi** hoặc **ROI**, sau đó nhấn **Pick Color**.
3. Với Pixel, nhấp một điểm. Với Multi, nhấp lần lượt 2–4 điểm; mỗi điểm có số thứ tự
   trên ảnh. Có thể nhấn **Finish Multi** sau 2–3 điểm hoặc để ứng dụng tự kết thúc ở điểm
   thứ tư. Dùng **Clear Points** để chọn lại. Với ROI, kéo một vùng chứa màu đại diện.
4. Histogram hiển thị mặc định; xem dải màu vàng để biết ngưỡng đang giữ phần nào của
   phân bố. Dùng **Hide Histogram** nếu cần thu gọn tạm thời.
5. Chỉnh lại H, S và V bằng mắt dựa trên Mask/Result.

## Lưu ý

Một pixel phù hợp khi màu rất đồng đều. Multi hữu ích khi cần lấy vài vị trí sáng/tối khác
nhau nhưng không muốn đưa toàn bộ nền trong hình chữ nhật vào mẫu. ROI phù hợp khi cả vùng
được kéo đều thuộc vật thể. Histogram chỉ mô tả số lượng pixel, không đo độ chính xác phân đoạn.
