# Đánh giá bằng ground truth

## Ground truth là gì?

Ground truth là mask chuẩn do con người gán nhãn hoặc lấy từ nguồn đáng tin cậy. Pixel trắng
biểu diễn foreground đúng; pixel đen biểu diễn background đúng. Ứng dụng không tự tạo mask này.

## Dùng để làm gì?

- Đo mask dự đoán giống đáp án chuẩn đến đâu.
- Phân biệt vùng đúng, vùng chọn thừa và vùng bị bỏ sót.
- So sánh `baseline`, `components` và `watershed` trên cùng một ảnh.
- Lưu bằng chứng định lượng cho báo cáo hoặc thí nghiệm.

Nếu không có ground truth, **Selected pixels** chỉ là tỷ lệ diện tích mask (coverage), không
phải accuracy.

## Các chỉ số

| Chỉ số | Ý nghĩa |
|---|---|
| TP | Pixel foreground được chọn đúng |
| FP | Pixel background bị chọn nhầm |
| FN | Pixel foreground bị bỏ sót |
| IoU | `TP / (TP + FP + FN)` |
| Dice | `2TP / (2TP + FP + FN)` |

IoU và Dice nằm trong `[0, 1]`; càng gần `1` càng tốt. Hai mask cùng rỗng nhận `1` với trạng
thái `both_empty`; chỉ một mask rỗng nhận `0`.

## Cách dùng

1. Mở ảnh hoặc dừng video đúng frame cần đánh giá.
2. Chọn target: `baseline`, `components` hoặc `watershed`.
3. Đặt threshold chuyển ảnh ground truth thành nhị phân theo quy tắc `gray > threshold`.
4. Nhấn **Load** và chọn PNG/BMP lossless có cùng kích thước với nguồn.
5. Đọc IoU/Dice; bật **TP/FP/FN** để xem overlay lỗi.

Overlay dùng xanh lá cho TP, đỏ cho FP và xanh dương cho FN. Ground truth được giữ khi chỉnh
tham số trên cùng frame để metric tính lại, nhưng bị xóa khi đổi nguồn, chuyển frame hoặc
restart video.

## Yêu cầu file

- Chỉ nhận PNG/BMP lossless.
- Kích thước phải trùng ảnh nguồn.
- Ảnh RGB phải là grayscale với ba kênh bằng nhau.
- Alpha bị bỏ qua; ứng dụng không resize hoặc xoay ảnh.

Ground-truth evaluation chỉ đo kết quả; nó không tự sửa mask và không biến HSV thresholding
thành object detection.
