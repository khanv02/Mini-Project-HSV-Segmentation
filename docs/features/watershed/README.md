# Watershed

## Là gì?

Watershed là bước hậu xử lý thử tách các vùng foreground đang chạm nhau. Nó dùng mask từ
HSV hoặc Grayscale làm miền xử lý và ảnh nguồn làm thông tin biên.

## Dùng để làm gì?

Ví dụ hai quả cùng màu chạm nhau tạo thành một vùng liên thông. Watershed có thể tìm các seed
riêng và tạo đường ranh giới giữa chúng.

## Cách dùng

1. Tạo mask bao phủ đúng các vật thể.
2. Mở tab **Refine & Separate** và bật **Separate touching objects (Watershed)**.
3. Chỉnh **Seed fraction** nếu số vùng tách chưa phù hợp.
4. Quan sát vùng màu và đường biên; có thể kết hợp **Minimum area** để loại vùng quá nhỏ.

## Trạng thái cần biết

- `applied`: đã đủ marker và bước tách được áp dụng.
- `empty`: mask đầu vào rỗng.
- `not_applied`: không đủ marker hoặc điều kiện tách; ứng dụng vẫn giữ mask cơ sở.

Watershed phụ thuộc hình dạng và seed, nên không bảo đảm tách được mọi trường hợp. Nó không
thay thế HSV và không nên bật khi các vật thể vốn đã tách rời rõ ràng.
