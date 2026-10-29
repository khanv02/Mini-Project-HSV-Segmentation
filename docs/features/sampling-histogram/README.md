# Lấy mẫu màu và histogram

## Dùng để làm gì?

Nhóm công cụ này giúp tìm ngưỡng khởi đầu; nó không tự quyết định ngưỡng tối ưu.

- **Pick Color – Pixel:** lấy HSV tại một điểm ảnh.
- **Pick Color – Multi:** tạo 2–4 khoảng HSV độc lập rồi hợp chúng bằng phép OR.
- **Pick Color – ROI:** lấy mẫu từ một vùng ảnh để đề xuất khoảng rộng hơn.
- **Histogram H/S/V:** hiển thị phân bố giá trị màu của frame hiện tại và vị trí các ngưỡng.

## Cách dùng

1. Mở ảnh hoặc dừng video tại frame cần xem.
2. Chọn **Pixel**, **Multi** hoặc **ROI**, sau đó nhấn **Pick Color**.
3. Với Pixel, nhấp một điểm. Với Multi, nhấp lần lượt 2–4 điểm; mỗi điểm có số thứ tự
   trên ảnh. Sau khi có ít nhất 2 điểm, nhấn **Finish Multi** bất kỳ lúc nào. Kéo một marker
   đã chọn sang vị trí khác để thay màu tương ứng; điểm thứ tư là giới hạn tối đa, không phải
   số lượng bắt buộc. Dùng **Clear Points** để chọn lại. Với ROI, kéo một vùng chứa màu đại diện.
4. Histogram hiển thị mặc định; xem dải màu vàng để biết ngưỡng đang giữ phần nào của
   phân bố. Dùng **Hide Histogram** nếu cần thu gọn tạm thời.
5. Chỉnh lại H, S và V bằng mắt dựa trên Mask/Result.

## Lưu ý

Một pixel phù hợp khi màu rất đồng đều. Multi hữu ích khi cần lấy các màu tách biệt như đen và
vàng: mỗi điểm giữ một khoảng HSV riêng, mask cuối là `mask 1 OR mask 2 ...`, nên không tạo một
khoảng quá rộng nằm giữa các màu. Các thanh HSV và histogram biểu diễn khoảng đầu tiên; trạng
thái Multi cho biết tổng số khoảng đang được hợp. Chỉnh các thanh HSV khi đang ở Multi sẽ sửa
khoảng đầu tiên và giữ các khoảng còn lại. **Clear Points** bỏ các khoảng bổ sung nhưng giữ
khoảng đầu tiên. ROI phù hợp khi cả vùng được kéo đều thuộc
vật thể. Histogram chỉ mô tả số lượng pixel, không đo độ chính xác phân đoạn.
