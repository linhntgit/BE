# Ma trận quy định lịch sử phiên bản 0.1.0

**Bản hiện hành: engine 0.3.1; rule FDA replicate 2.0.1, rule khác 2.0.0; nguồn đối chiếu lại 31/10/2026.**
**Bảng trạng thái thực thi hiện tại** được sinh từ registry tại [CAPABILITY_MATRIX.md](CAPABILITY_MATRIX.md);
các dòng lịch sử bên dưới không dùng làm bảng khả năng phát hành hiện tại.
Xem [ma trận phương pháp, HVD/NTI, điều kiện và benchmark hiện hành](PHOENIX_BE_COMPARISON.md).
Các trạng thái “chưa hỗ trợ/khóa” bên dưới ghi lại baseline 0.1.0, không phải trạng thái 0.3.0.

[Gate engine 0.3.1](CONVENTIONAL_ABE_GATE.md) đóng conventional mixed ABE chưa qualification;
I-contrast CI không dùng thay ABE cho FDA NTI/replicate standard hoặc HVD nhánh unscaled.

Cập nhật kiểm chứng ngày 31/10/2026: xem [đối chiếu replicate thực tế](PHOENIX_REPLICATE_COMPARISON.md).
Phải phân biệt mã đã triển khai, thành phần đã đối chiếu và phương pháp đã qualification.
525 file dependencies mới cho thấy khác biệt population, hằng số và mô hình conventional ABE;
23/28 số khớp không đủ để tuyên bố cả EMA ABEL/FDA HVD/NTI đã qualification.

Mốc đối chiếu: 29/10/2026. Xác minh văn bản không đồng nghĩa thẩm định phần mềm.
Profile được lưu nguyên bản trong mỗi analysis revision; engine không truy cập mạng khi phân tích.

| Profile | Nguồn và phạm vi | Thuật toán phát hành | Trạng thái |
|---|---|---|---|
| EMA_IR_NONREPLICATE_M13A | [M13A Step 5](https://www.ema.europa.eu/en/scientific-guidelines/ich-guideline-m13a-bioequivalence-immediate-release-solid-oral-dosage-forms), EU hiệu lực 25/01/2025, IR oral systemic, nonreplicate | ABE 2×2 complete-case không mất kỳ; parallel pooled/Welch được SAP định trước | Nguồn đã mở; engine development |
| FDA_ABE_2026 | [Statistical Approaches final May 2026](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/statistical-approaches-establishing-bioequivalence), [PK endpoints ANDA](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/bioequivalence-studies-pharmacokinetic-endpoints-drugs-submitted-under-abbreviated-new-drug), M13A | ABE, giới hạn 0.8–1.25 trong phạm vi đã rà soát | Nguồn final đã xác nhận; PSG cần chuyên gia rà soát từng sản phẩm |
| EMA_REPLICATE_STANDARD | [EMA Rev 1](https://www.ema.europa.eu/en/scientific-guidelines/investigation-bioequivalence), 4.1.8 còn áp dụng replicate | Chưa hỗ trợ fit replicate | Khóa kết luận |
| EMA_HVDP_ABEL | EMA Rev 1, 4.1.10, Cmax và điều kiện định trước | Chỉ helper giới hạn; không kết luận từ helper | Khóa đến khi có model + benchmark độc lập |
| FDA_HVD_RSABE_2026 | [FDA PDF Appendix G](https://www.fda.gov/media/163638/download), AUC/Cmax, non-NTI, sWR <0.294: ABE; ≥0.294: UCB 95% + GMR | Chỉ helper điều kiện; không thay RSABE bằng CI EMA | Khóa đến khi có Appendix G adapter + benchmark |
| FDA_NTI | FDA Appendix F | Chưa hỗ trợ | Không dùng tham số HVD |

M13A: 2.1.3 và 2.2.3.1 quy định tối thiểu 12 crossover hoặc 12 mỗi nhánh parallel;
2.2.2.2 dùng actual time, BLQ = 0 cho PK, loại BLQ khỏi kel;
2.2.3.2–4 mô hình theo thiết kế; 2.2.4 giới hạn và endpoint.
Đặc tả dẫn mục 2.2.3.1 cho mốc 12 là đúng; thêm mục thiết kế 2.1.3.
Predose >5% Cmax: engine chặn để quyết định population có chứng cứ, không tự loại người/kỳ.

Trang EMA có thông báo M13B sẽ hiệu lực 17/03/2027: chưa áp dụng vào rule snapshot ngày 29/10/2026.
Các profile không áp dụng MR, multiple-dose, endogenous baseline correction, NTI,
multiple groups, strata/covariates hoặc các trường hợp đặc biệt chưa có model đã đối chiếu.
Không mặc định mọi IR đều phù hợp; cần protocol, SAP và ghi nhận scope/PSG review.

