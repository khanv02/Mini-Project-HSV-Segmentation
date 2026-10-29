# Morphology

## Là gì?

Morphology làm sạch mask nhị phân sau bước ngưỡng HSV bằng một kernel vuông.

## Dùng để làm gì?

| Chế độ | Công dụng chính |
|---|---|
| Opening | Loại các đốm foreground nhỏ, rời rạc |
| Closing | Lấp lỗ hoặc khe background nhỏ bên trong vật thể |
| Opening + Closing | Thực hiện lần lượt cả hai thao tác |

## Cách dùng

1. Tạo mask HSV tương đối đúng trước.
2. Bật morphology và chọn thao tác.
3. Chọn kích thước kernel lẻ và số vòng lặp.
4. So sánh mask trước/sau để bảo đảm chi tiết thật không bị xóa hoặc nối nhầm.

## Khi nào không nên tăng mạnh?

Kernel lớn hoặc nhiều vòng lặp có thể làm mất vật thể nhỏ, thay đổi biên hoặc nối các vùng
gần nhau. Morphology chỉ sửa hình dạng cục bộ; nó không khắc phục được ngưỡng HSV chọn sai màu.
