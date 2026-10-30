# Watershed

> **Giới hạn an toàn:** với ảnh lớn, ứng dụng kiểm tra nhanh các vùng mẫu trước. Nếu mask quá
> nhiều chi tiết hoặc nhiễu, Watershed dừng trước bước phân vùng nặng và báo `not applied`.
> Kết quả HSV gốc vẫn được giữ nguyên.
> Hãy siết lại ngưỡng phân đoạn hoặc dùng morphology để dọn chấm nhiễu rồi thử lại; tách hàng
> nghìn cực đại cục bộ vừa không có ý nghĩa, vừa có thể tiêu tốn rất nhiều bộ nhớ.

Watershed gộp các cực đại gần nhau theo độ dày cục bộ của vật thể và chỉ chấp nhận tối đa 16
marker có ý nghĩa. Nhiều hơn mức này được xem là over-segmentation và trả về `not applied`.
Nếu mục tiêu là thống kê nhiều vật thể vốn đã rời nhau, hãy dùng **Analyze Objects**. Các tùy
chọn Contours/Boxes của Analyze không được vẽ lên Overlay Watershed.

## Là gì?

Watershed là bước hậu xử lý thử tách các vùng foreground đang chạm nhau. Nó dùng mask từ
HSV hoặc Grayscale làm miền xử lý và ảnh nguồn làm thông tin biên.

## Dùng để làm gì?

Ví dụ hai quả cùng màu chạm nhau tạo thành một vùng liên thông. Ứng dụng tìm các cực đại cục bộ
của distance map làm marker riêng, sau đó Watershed tạo đường ranh giới giữa chúng. Cách này
không để vật thể lớn áp ngưỡng seed lên vật thể nhỏ.

## Cách dùng

1. Tạo mask bao phủ đúng các vật thể.
2. Mở tab **Refine & Separate** và bật **Separate touching objects (Watershed)**.
3. Chỉnh **Seed core** bằng slider. Giá trị cao làm lõi seed nhỏ hơn; giá trị thấp làm lõi rộng
   hơn. Kéo đến giá trị mong muốn rồi thả chuột để xử lý một lần; khi dùng bàn phím, nhấn Enter
   hoặc rời khỏi slider. Ô nhập số chỉ áp dụng khi nhấn Enter hoặc rời khỏi ô.
4. Xem `Overlay · Watershed`: mỗi vùng được tô màu riêng và đường phân cách có màu đỏ. Binary
   Mask và Segmented Result vẫn là mask nền, nên không dùng hai khung đó để nhận biết số vùng.
5. Dòng trạng thái hiển thị số marker, số vùng sau tách và số seed pixel. Có thể kết hợp
   **Minimum area** trong Analyze để loại vùng quá nhỏ. Trạng thái luôn giữ trên một dòng để
   layout không dịch chuyển; rê chuột lên dòng này để xem đầy đủ lý do khi có `not applied`.

## Trạng thái cần biết

- `applied`: có ít nhất hai marker; trạng thái ghi rõ `markers`, `regions` và `seed pixels`.
- `empty`: mask đầu vào rỗng.
- `not_applied`: không đủ marker hoặc điều kiện tách; ứng dụng vẫn giữ mask cơ sở.

Một seed hợp lệ chỉ là số trong khoảng `(0, 1)`; trạng thái `applied` mới xác nhận thuật toán đã
chạy. Nếu mask không có ít nhất hai cực đại cục bộ—ví dụ một hình chữ nhật đặc hoàn toàn—không
có đủ bằng chứng hình học để suy ra hai vật thể. Watershed không thay thế HSV và không nên bật
khi các vật thể vốn đã tách rời rõ ràng.
