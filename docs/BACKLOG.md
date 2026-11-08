# Trạng thái và backlog chính xác

## Sprint 0

Đã đọc đầy đủ đặc tả, xác minh M13A/EMA và FDA Statistical Approaches final 05/2026,
định nghĩa engine tách UI, regulatory matrix, algorithm spec và validation plan.
Chưa có product cụ thể; scope/PSG do chuyên gia nghiên cứu ghi nhận khi tạo dự án.

## Sprint 1 đã triển khai

- Streamlit tiếng Việt 11 mục; nghiên cứu thật/demo tách nhãn; tạo/mở dự án SQLite.
- Randomization balanced block 2×2, parallel, partial3 và full4; seed/hash, Excel ID dạng text,
  planned schedule không gán actual time.
- Power TOST numerical joint integral và cỡ mẫu riêng 2×2/parallel, dropout,
  CV/GMR riêng AUC/Cmax, provenance, đường n–power Cmax.
- Nhập CSV/XLSX long, column mapping; actual timestamp có offset; unit conversion có xác nhận;
  QC theo dòng, duplicate, missing, BLQ/LLOQ, mismatch, predose; không tự loại outlier/subject.
- Raw bất biến, correction có lý do/người rà soát/bằng chứng, data/SAP freeze và revision.
- NCA single-dose: Cmax/Tmax, AUC last, lambda-z/t1/2/AUCinf khi đủ điều kiện, terminal diagnostics.
- ABE 2×2 đủ hai kỳ kể cả imbalance; parallel pooled/Welch; endpoint PASS/FAIL/NE,
  gate minimum N/scope, demo không tạo kết luận study thật.
- Biểu đồ actual linear/semilog, mean nominal ± SD, CI endpoint; snapshot và lịch sử.
- Word/PDF dự thảo song ngữ, PK listings Word; CTD mapping và analysis/audit/datasets exports.
- Archive JSON+manifest .beproject.zip giữ raw/history/config/runs/artifacts; giới hạn giải nén,
  checksum/schema/audit, SQLite append-only/conflict/backup API.

## Sprint 1 còn cần trước nghiệm thu nghiệp vụ

- Không hỗ trợ mất kỳ bằng mixed model: trả NE; cần model đã benchmark và population/exclusion workflow.
- Wide-to-long wizard, LIMS/reassay reconciliation, QC thời gian/lỗ hổng/outlier chuyên sâu.
- Chọn terminal thủ công từng profile qua UI và audit reviewer (engine có config có lý do).
- Mô hình có strata, covariates, cohort, nhiều site hoặc endogenous cần adapter riêng.
- Tổng hợp PK mô tả đầy đủ và đồ thị GMR–power, CV sensitivity/uncertainty; power đồng thời endpoint.
- Phần mềm NCA độc lập: đã đối chiếu public PKNCA AUC/Cmax/Tmax/Tlast/Clast và
  lambda-z/t1/2/AUCinf với policy terminal tương thích ví dụ gốc; cần mở rộng datasets phong phú hơn.
  Ví dụ PKNCA có adjusted R² thấp, nên engine mặc định chặn ngoại suy; chỉ cấu hình benchmark
  cho phép tái hiện kết quả này, không hạ ngưỡng QC mặc định để đạt kết quả mong muốn.
- ABE public R golden có imbalance; thêm fixtures SAS/Phoenix độc lập với dữ liệu balanced/extreme/outlier.
- DOCX/PDF có kiểm thử cấu trúc/Unicode; cần render DOCX trên môi trường có bundled renderer
  trước xác nhận chất lượng mọi trang. Chưa gắn nhãn report đã QA.
- UI phiên bản 0.1.0 là development; chưa thẩm định cho mục đích sử dụng thực tế có kiểm soát.

## Sprint 2 chưa phát hành

Từ 0.3.0 đã triển khai replicate đủ kỳ, EMA ABEL/NTI và FDA Appendix F/G với các kiểm thử độc lập.
Missing replicate, thiết kế khác, power Monte Carlo/Type I error và qualification phát hành vẫn còn trong backlog.
Cần adapter covariance/df theo thiết kế, sWR treatment-specific, independent results và chuyên gia rà soát.
Không dùng một MixedLM bất kỳ hoặc giới hạn EMA để gọi FDA RSABE.

## Sprint 3 chưa hoàn tất

CSR E3 đầy đủ, nội dung Module 2.7.1/5.3.1.2, EMA Appendix IV cần templates và dữ liệu thực tế;
bản hiện tại chỉ là khung tóm tắt và mapping, chưa phải gói nộp hồ sơ.
Authentication, RBAC, blinding, reviewer approval và audit external anchor chưa triển khai.
PostgreSQL adapter, encryption/key management, TLS/network deployment, validated backup SOP,
CSV URS/FRS/risk/IQ/OQ/PQ và chuyên gia phê duyệt là hạng mục bắt buộc trước sử dụng regulated.

## Sprint 4 chưa hỗ trợ

MR/product-specific model, multiple-dose/steady-state **BE** (PK độc lập có module xử lý riêng),
partial AUC/AUC72, adaptive/multiple groups,
multiple reference, SDTM/ADaM, LIMS và eCTD assembly/validation.

NTI đã có các nhánh tính toán EMA/FDA và kiểm tra điều kiện; FDA NTI vẫn khóa kết luận
vì conventional replicate ABE chưa qualification. Trạng thái chi tiết sinh từ registry:
[CAPABILITY_MATRIX.md](CAPABILITY_MATRIX.md).

Không có mục nào trong backlog được coi là đã hoàn thành chỉ vì UI có tên trang hoặc registry có profile.
