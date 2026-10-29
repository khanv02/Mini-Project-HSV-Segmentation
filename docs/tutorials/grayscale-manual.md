# Tutorial: ảnh xám và Otsu

1. Mở ảnh có ba kênh RGB bằng nhau; ứng dụng vẫn bắt đầu ở **HSV**.
2. Đổi mode thành **Grayscale**.
3. Chọn **Manual**, nhập `T`, rồi chọn **Bright > T** hoặc **Dark <= T**.
4. Chọn **Otsu** để so sánh ngưỡng tự động; chọn lại **Manual** để chỉnh giá trị cũ.

Mode bị từ chối nghĩa là có pixel không thật sự xám. Otsu unavailable nghĩa là ảnh không có hai
lớp cường độ có ý nghĩa; kết quả hợp lệ trước đó vẫn được giữ.
