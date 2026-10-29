# Video, xuất file và experiment

## Video

Ứng dụng đọc MP4/AVI bằng OpenCV. Người dùng có thể phát, tạm dừng, chuyển frame và chỉnh
ngưỡng trên frame hiện tại. Khi đánh giá bằng ground truth, hãy tạm dừng đúng frame; chuyển
frame sẽ xóa ground truth cũ để tránh so sánh sai.

## Xuất PNG

- **Save Mask…:** lưu mask nhị phân 0/255 đúng độ phân giải nguồn.
- **Save Result…:** lưu ảnh RGB chỉ giữ các pixel được mask chọn.

PNG là lossless nên phù hợp để kiểm tra lại hoặc dùng làm artifact trong báo cáo.

## Record Experiment

Experiment lưu cấu hình và bằng chứng cần thiết để tái lập một lần chạy, gồm nguồn/frame,
ngưỡng HSV, morphology, ghi chú, môi trường, SHA-256 và các artifact liên quan.

- Khi chỉ dùng baseline, record giữ schema 1 tương thích với dữ liệu cũ.
- Khi dùng analysis, Watershed hoặc evaluation, record dùng schema 2 và bổ sung thống kê,
  label, prediction, normalized ground truth và metric khi có.

Experiment phù hợp khi cần so sánh nhiều cấu hình hoặc chứng minh kết quả trong báo cáo. Nếu
chỉ cần ảnh để xem nhanh, xuất PNG là đủ.

Xem bộ bằng chứng hiện có tại [`experiments/README.md`](../../../experiments/README.md).
