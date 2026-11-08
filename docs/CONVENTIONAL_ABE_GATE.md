# Gate conventional ABE replicate ở engine 0.3.1

Thay đổi ngày 31/10/2026: các nhánh cần conventional replicate ABE trả **NOT EVALUABLE** đến khi mixed model được qualification. Không tích hợp prototype REML vào production và không thay công thức I/D, Howe, variance ratio hoặc threshold sWR.

## Sai khác đã xác nhận

Saved NTI Phoenix có SE conventional ABE 0.028365069523557 và df 33.6607542733802. Mô hình I contrast của app cho SE 0.025058584058778408 và df 16. Các GMR có thể giống nhau nhưng hai CI không cùng estimator. Dùng CI thứ hai để điền tiêu chí conventional ABE là không đúng với mô hình đã đối chiếu.

[FDA Statistical Approaches May 2026](https://www.fda.gov/media/163638/download), Appendix C trang in 32, minh họa mixed model với random treatment theo subject, residual theo treatment và Satterthwaite. Appendix F trang in 42 bước 3 đánh giá thêm unscaled ABE cho NTI. Nguồn được mở lại ngày 31/10/2026; đây là căn cứ xác định hai nhánh khác nhau, không phải tuyên bố app đã validated.

## Hành vi mới

| Nhánh | Kết luận endpoint | Các thành phần được giữ |
|---|---|---|
| FDA_REPLICATE_STANDARD, partial3/full4 | NOT EVALUABLE | I-contrast estimate/SE/df/CI chỉ chẩn đoán |
| FDA_NTI, full4 | NOT EVALUABLE | I/D, Howe UCB, sWR/sWT và CI SD ratio; ABE criterion chưa đánh giá |
| FDA_HVD_RSABE_2026, sWR <0.294 | NOT EVALUABLE | I/D chẩn đoán; không dùng CI này làm unscaled ABE |
| FDA_HVD_RSABE_2026, sWR ≥0.294 | Giữ hai tiêu chí RSABE hiện có | Howe UCB và ràng buộc point estimate; CI I chỉ bổ trợ |
| EMA replicate và nonreplicate | Không đổi estimator/tiêu chí | Kiểm tra cũ vẫn áp dụng |

Criterion conventional ABE ghi `passed=None`, value trống và lý do rõ ràng. `conventional_abe_ci90=None`; CI I được giữ ở `i_contrast_ci90` và các trường summary có nhãn phương pháp chẩn đoán. Reviewer/Excel ghi NOT EVALUABLE và lý do; forest dùng nền CI bổ trợ. Không biến tiêu chí chưa đánh giá thành FAIL hoặc PASS.

## Phiên bản và dữ liệu cũ

Engine/package chuyển 0.3.0→0.3.1; các rule FDA_NTI/FDA_HVD_RSABE_2026/FDA_REPLICATE_STANDARD chuyển 2.0.0→2.0.1. Rule implementation lấy từ engine version. Snapshot đã lưu không được ghi đè; state hiện có nhận engine cũ là LEGACY và yêu cầu tính lại để dùng output hiện hành. Không tự refit hoặc sửa dữ liệu nghiên cứu trong quá trình nâng mã.

Tests kiểm tra cả ba gate, bảng reviewer/Excel, màu forest bổ trợ, nhánh scaled HVD/EMA không đổi và snapshot engine 0.3.0 không còn CURRENT. Các số benchmark nonreplicate Fasted phải tiếp tục khớp. Kế hoạch mở mixed model nằm trong `FDA_REPLICATE_ABE_METHOD_SPEC.md`; gate này chỉ đóng việc suy luận chưa được kiểm chứng.
