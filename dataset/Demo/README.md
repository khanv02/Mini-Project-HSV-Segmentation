# Bộ ảnh demo HSV

Nguồn: `dataset/Fruits/test_zip/test` (dataset Fruits, split test). Ảnh được sao chép nguyên bản để dùng thử phân đoạn HSV.

## Ảnh đã chọn

- **Táo:** `apple_79`, `apple_83`, `apple_84`, `apple_86`, `apple_91`, `apple_94` — táo đỏ/xanh, đơn và nhiều quả, nền sáng/tối/tự nhiên.
- **Chuối:** `banana_81`, `banana_84`, `banana_87`, `banana_88`, `banana_89`, `banana_90` — vàng nổi, một quả và chùm quả, có nền trắng và nền hồng.
- **Cam:** `orange_78`, `orange_80`, `orange_83`, `orange_89`, `orange_90`, `orange_93` — cam đơn/nhiều quả, nguyên và cắt đôi, nhiều điều kiện nền.
- **Ảnh trộn:** `mixed_21`, `mixed_23` — kiểm tra nhiều màu/đối tượng cùng lúc.

## Gợi ý demo nhanh

Bắt đầu với `banana_81.jpg` hoặc `orange_83.jpg` để thấy mask gọn; sau đó thử `apple_84.jpg` hoặc `mixed_21.jpg` để minh họa nền phức tạp và nhiều màu. Ảnh có watermark/đồ họa hoặc nhiều vùng cùng màu có thể tạo mask không trọn vẹn, thích hợp để nói về giới hạn của ngưỡng HSV.

## BloodCell bổ sung

Nguồn: `dataset/BloodCell/dataset2-master/dataset2-master/images/TEST_SIMPLE` (bản test đơn giản). Đã thêm 8 ảnh JPEG, hai ảnh cho mỗi lớp, giữ nguyên nội dung và đặt tiền tố `bloodcell_` cùng tên lớp để phân biệt.

- **Eosinophil:** `bloodcell_eosinophil_7_2284.jpeg`, `bloodcell_eosinophil_2_1226.jpeg`
- **Lymphocyte:** `bloodcell_lymphocyte_4_2908.jpeg`, `bloodcell_lymphocyte_5_1558.jpeg`
- **Monocyte:** `bloodcell_monocyte_1_4511.jpeg`, `bloodcell_monocyte_3_9457.jpeg`
- **Neutrophil:** `bloodcell_neutrophil_11_1721.jpeg`, `bloodcell_neutrophil_25_8686.jpeg`

Ảnh tế bào minh họa nền kính hiển vi hồng nhạt với nhân tím; ngưỡng màu phù hợp sẽ làm nổi bật nhân, nhưng hồng cầu cũng có sắc độ hồng nên có thể lọt một phần vào mask. Đây là ví dụ tốt để minh họa giới hạn của phân đoạn theo HSV.
