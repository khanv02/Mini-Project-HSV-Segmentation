# Ngưỡng HSV

## Là gì?

HSV biểu diễn màu bằng ba thành phần: Hue (màu sắc), Saturation (độ bão hòa) và Value
(độ sáng). Ứng dụng tạo mask trắng/đen bằng cách kiểm tra từng pixel có nằm trong cả ba
khoảng ngưỡng hay không.

## Dùng để làm gì?

- Tách một màu hoặc nhóm màu khỏi nền.
- Quan sát ảnh hưởng của từng thành phần H, S và V.
- Tạo mask cơ sở cho morphology, phân tích vật thể và Watershed.

## Cách dùng

1. Mở ảnh hoặc video.
2. Chọn preset **Red**, **Yellow**, **Green** hoặc **Blue** làm điểm bắt đầu; chọn
   **Custom** nếu muốn nhập hoàn toàn thủ công.
3. Chỉnh Lower/Upper của H, S và V.
4. Theo dõi **Mask** và **Result** sau mỗi lần chỉnh.

Hue dùng đơn vị độ trong `[0°, 360°)` và hỗ trợ khoảng vòng qua gốc đỏ. Ví dụ
`350°..10°` chọn cả hai phía của màu đỏ. S và V dùng phần trăm `[0%, 100%]`.

## Khi nào không đủ?

HSV cố định dễ bị ảnh hưởng bởi ánh sáng, bóng, phản xạ và cân bằng trắng. Nếu vật thể và
nền có màu gần giống nhau, chỉ điều chỉnh HSV có thể không tạo được ranh giới chính xác.

Chi tiết công thức: [Thuật toán và quy ước số](../../algorithm.md).
