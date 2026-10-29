# Experiment schema 3

Schema 1/2 cũ vẫn giữ nguyên cho HSV. Schema 3 được dùng khi kết quả là Grayscale hoặc experiment
giữ Overlay. Trường `segmentation` ghi mode, manual/Otsu, ngưỡng đã áp dụng, polarity và quy tắc
tie. Trường `overlay` ghi variant, thiết lập hiển thị, SHA-256 file PNG và hash pixel đã decode.

Để tái lập: kiểm tra hash nguồn, tính lại Otsu nếu cần, áp dụng đúng `> T` hoặc `<= T`, rồi so hash
mask/Overlay. Mismatch phải được báo là evidence drift, không được bỏ qua.
