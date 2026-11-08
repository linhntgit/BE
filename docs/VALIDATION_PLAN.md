# Kế hoạch kiểm chứng

## Phạm vi phát hành

Development build, local single-user. Không dùng như phần mềm đã thẩm định GxP.
Sprint 0–1 là mục tiêu bản 0.1.0; Sprint 2–4 có cổng đóng theo bằng chứng.

## Nguồn chuẩn

1. PowerTOST README: power 2×2 và parallel, dung sai bằng độ chính xác số công bố.
2. PKNCA 0.12.1.9002 vignette: AUClast 12.9965842, Tmax=2, Clast=1.1, Tlast=8.
   Lambda=.1075592, t1/2=6.4443313, AUCinf.obs=23.2235095 được đối chiếu thêm khi
   dùng policy tương thích ví dụ nguồn (không áp ngưỡng R²/span nghiêm hơn của mặc định engine).
3. Schütz 2014 datasets A–H: GMR/CI công bố hai số thập phân phần trăm,
   dung sai 0.0051 điểm phần trăm (0.000051 dạng tỷ lệ). Kiểm tra balanced và unbalanced.
4. Parallel đối chiếu independently statsmodels ttost_ind cho pooled và unequal.
5. NCA exponential có nghiệm đóng, trapezoid tính tay; property tests bảo toàn đơn vị,
   bất biến thứ tự và monotonicity power trong điều kiện đã xác định.

Golden fixtures phải kèm source, expected, precision và hash. Không sửa fixture để khớp implementation.
scripts/benchmark.py tạo bảng expected/actual/difference/tolerance/source và exit !=0 nếu sai.

## Ranh giới cần kiểm tra

Import timestamp có offset, leading-zero ID, actual vs nominal, BLQ, unknown units,
duplicate cùng time/sample, missing, invalid number, randomization mismatch, predose >5%.
NCA không có terminal hợp lệ, Tmax tie, zero terminal, missing baseline và negative time.
ABE có PASS/FAIL/NE, missing period, thiếu sequence, sai treatment, zero variance,
rounding boundary, endpoint tổng hợp và demo không thể tạo PASS study.
Archive checksum/schema, zip traversal/bomb/symlink/duplicate, freeze/revision,
SQLite audit chain và reload không refit. Report DRAFT/status, CTD mappings, Unicode,
Word/PDF cấu trúc và kiểm tra render với sample report khi runtime cho phép.
Streamlit AppTest thực hiện workflow synthetic và mọi trang.

## Cổng nghiệm thu

pytest, lint, mypy, benchmark phải xanh. CI tự động chạy lại trên máy sạch.
pip-audit kiểm tra dependency lock; nếu unavailable cần ghi nhận riêng, không coi là pass.
Khóa release regulatory cho đến khi có review độc lập biostatistics/PK/QA/RA,
validation protocols và bằng chứng IQ/OQ/PQ theo hệ thống chất lượng đơn vị.
Từ 0.3.0: Method A và reference-only variance được đối chiếu bằng ma trận statsmodels độc lập;
Appendix F/G kiểm tra theo mô hình I/D độc lập, công thức và các ca biên có số liệu biết trước.
Đối chiếu workbook Phoenix riêng cho 2×2, bao gồm endpoint missing.
Replicate missing, thiết kế khác và qualification cho nộp hồ sơ vẫn chưa hoàn tất.
