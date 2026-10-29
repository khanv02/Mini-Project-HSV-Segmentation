# Morphology

## Là gì?

Morphology làm sạch mask nhị phân sau bước chọn HSV hoặc Grayscale bằng một kernel vuông.

## Dùng để làm gì?

| Chế độ | Công dụng chính |
|---|---|
| Opening | Loại các đốm foreground nhỏ, rời rạc |
| Closing | Lấp lỗ hoặc khe background nhỏ bên trong vật thể |
| Opening → Closing | Loại nhiễu trước, sau đó lấp lỗ trên phần foreground còn lại |

## Cách dùng

1. Tạo mask HSV tương đối đúng trước.
2. Bật morphology và chọn thao tác.
3. Chọn kích thước kernel vuông 3×3, 5×5, 7×7 hoặc 9×9. Mỗi thay đổi chạy một lần.
4. So sánh mask trước/sau để bảo đảm chi tiết thật không bị xóa hoặc nối nhầm.

## Khi nào không nên tăng mạnh?

Kernel lớn có thể làm mất vật thể nhỏ, thay đổi biên hoặc nối các vùng gần nhau. Với
**Opening → Closing**, vùng bị Opening xóa sẽ không được Closing khôi phục. Morphology chỉ sửa
hình dạng cục bộ; nó không khắc phục được mask đầu vào chọn sai vùng.
