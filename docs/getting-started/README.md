# Hướng dẫn bắt đầu

Hướng dẫn này tập trung vào workflow cơ bản nhất. Chưa cần bật Watershed hoặc ground truth.

## 1. Mở một ảnh

Chạy `uv run hsv`, nhấn **Open Image…** và chọn PNG/JPEG/BMP. Bốn vùng preview có ý nghĩa:

- **Original:** ảnh đầu vào.
- **Binary Mask:** vùng trắng là pixel được chọn; vùng đen là pixel bị loại.
- **Segmented Result:** ảnh màu chỉ giữ các pixel được chọn.
- **Overlay:** đặt mask, contour, Watershed hoặc TP/FP/FN lên ảnh gốc để dễ kiểm tra.

Histogram H/S/V nằm ngay dưới bốn preview và hiển thị mặc định. Nhấn **Hide Histogram**
khi cần thêm chiều cao cho ảnh.

## 2. Chọn màu cần tách

Nếu muốn tách vật thể đỏ, chọn preset **Red**. Với màu khác, chọn preset gần nhất hoặc
**Custom** trong tab **HSV Thresholds**. Sau đó chỉnh từng nhóm:

- **Hue:** chọn đúng màu.
- **Saturation:** tăng lower để loại vùng xám/trắng ít màu.
- **Value:** điều chỉnh khi vùng quá tối hoặc quá sáng bị chọn sai.

Mục tiêu ban đầu là để vật thể cần tìm màu trắng trên Mask và phần lớn nền màu đen.
Nếu cần lấy nhiều màu ở nhiều vị trí, chọn **Multi** và bấm 2–4 điểm. Mỗi điểm tạo một khoảng
HSV riêng; ứng dụng hợp các mask bằng OR. Có thể kết thúc ngay sau điểm thứ hai hoặc thứ ba,
và có thể kéo marker sang pixel khác để đổi mẫu. Chế độ **Pixel** một điểm vẫn hoạt động như cũ.

## 3. Làm sạch nếu cần

Mở tab **Refine & Separate** và chỉ bật morphology khi mask đã tương đối đúng:

- có nhiều chấm trắng nhỏ → thử **Opening**;
- có lỗ đen nhỏ bên trong vật thể → thử **Closing**.

Dùng kernel nhỏ trước. Nếu chỉnh quá mạnh, chi tiết hoặc vật thể nhỏ có thể biến mất.

## 4. Lưu kết quả

- **Save Mask…** khi cần mask trắng/đen.
- **Save Result…** khi cần ảnh đã tách nền.
- **Record Experiment…** khi cần lưu cả tham số và bằng chứng để chạy lại.

## 5. Chọn tính năng tiếp theo

| Vấn đề đang gặp | Tài liệu tiếp theo |
|---|---|
| Không biết đặt ngưỡng | [Lấy mẫu và histogram](../features/sampling-histogram/README.md) |
| Cần đếm hoặc lọc vùng nhỏ | [Phân tích vật thể](../features/object-analysis/README.md) |
| Các vật thể đang chạm nhau | [Watershed](../features/watershed/README.md) |
| Cần đo kết quả đúng đến đâu | [Ground-truth evaluation](../features/ground-truth-evaluation/README.md) |

Toàn bộ danh mục nằm tại [Tính năng](../features/README.md).
