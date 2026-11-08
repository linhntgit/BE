# Full4 FA0 REML: audit prototype 0.1

Ngày 31/10/2026. **CHƯA QUALIFIED. Không nối vào production; không cho phép kết luận.** Đặc tả tại `FDA_REPLICATE_ABE_METHOD_SPEC.md`. Mọi fit trả `inference_allowed=False`, không có PASS/FAIL. Engine hiện hành 0.3.1 chỉ đóng suy luận conventional ABE chưa qualification; không tích hợp prototype. Xem `CONVENTIONAL_ABE_GATE.md`.

## Nguồn độc lập và cách tái chạy

Đã xuất Workflow → Dependencies qua GUI Phoenix 8.8.0.20523, không execute workflow hoặc save project nguồn. Hai nguồn audit: FDA NTI (saved build 8.3.2.116) và Bioequivalence_replicated (saved build 8.3.4.295). Hash cả hai project còn trùng survey. CSV/XML/settings và dữ liệu thương mại chỉ giữ trong `output/phoenix_replicate_reference`, không đóng gói thành fixture công khai.

Chạy `.venv/Scripts/python.exe -m scripts.benchmark_replicate_abe_experimental`. Script đọc settings/mapping rồi fit từ input; chỉ sau khi fit xong mới đọc bảng expected. Kết quả, population và các lần tối ưu nằm ở `output/replicate_abe_experimental/fits.json`; từng phép so sánh ở `comparisons.csv`; SHA-256 input/output/settings/project và tolerance nằm trong `summary.json`. Không dùng số Phoenix làm initial values.

## Kết quả và giới hạn

| Bộ | Population | SE prototype | df prototype | CI90 prototype | Covariance G |
|---|---|---:|---:|---|---|
| FDA NTI | 18 người, 72 quan sát | 0.028365072 | 33.660746 | 0.938970542–1.033532228 | Gần rank 1 |
| Basic replicate | 20 người, 80 quan sát | 0.094726312 | 55.583100 | 0.916122311–1.257717190 | Gần rank 1 |

**60/60** đại lượng có thể so sánh đạt tolerance định trước: treatment contrast/SE/df/GMR/CI; G và residual variance riêng T/R; fixed effects cùng SE sau đổi coding về đúng baseline của output; năm eigenvalues Hessian observed trong tọa độ factor/raw-residual; population; likelihood replay. Không dùng tiêu chí PASS/FAIL làm bằng chứng mô hình tương đương.

Hai log-likelihood nguyên bản vẫn giữ sai khác: khoảng 3.08e-5 (NTI) và 3.45e-5 (basic). Replay với hằng số 1.837878 thay `log(2*pi)` tái hiện cả hai output trong tolerance. Đây là suy luận từ tính đồng nhất số; chưa xác nhận chi tiết triển khai Phoenix. Estimator giữ hằng số chính xác; replay được ghi thành dòng chẩn đoán riêng. Có 62 dòng tổng cộng, hai dòng likelihood nguyên bản được đánh dấu không cùng normalization; không loại sai khác khỏi artifact.

Input basic là AUClast raw, Ln(x); Capsule→R, Tablet→T, CTCT→RTRT, TCTC→TRTR. Input NTI đã Ln, được exp đúng một lần trước API raw của prototype; Sequence 1→TRTR, 2→RTRT. Đọc settings trước fit để chặn nhầm transformation/reference/model. Không lấy residual variance của mixed fit thay sWR/sWT từ D contrasts của nhánh RSABE.

Dataset thứ hai `DS01` trong project basic có 77 người, 298 quan sát, 69 đủ kỳ. Nó còn khai báo Ln(logPK). Không đưa vào prototype đủ kỳ hoặc âm thầm cắt còn 69 người. Nó chỉ được lưu làm bằng chứng cho chương trình missing/transform riêng.

## Kiểm tra implementation

Sáu tests riêng đạt: objective GLS theo từng block subject được viết độc lập; gradient/Hessian bằng finite differences cả nghiệm nội miền và factor c=0 ở biên; hoán vị hàng/định danh, đổi đơn vị PK; đảo T/R và covariance; dữ liệu thiếu/trùng/ID rỗng, response suy biến và không hội tụ đều fail closed; AST chặn import prototype vào pipeline/UI/replicate/statistics.

Hai bộ Phoenix hiện có sequence cân bằng và G ở biên. Chưa đạt điều kiện independent interior/imbalanced, chính sách boundary, qualification end-to-end và version/snapshot theo đặc tả. Missing, partial3, MR/pAUC, IBE/PBE/in vitro vẫn đóng. Không được suy diễn rằng audit này hoàn tất PHX-02 hoặc mở kết luận FDA mới.

## Kiểm chứng error contrasts bổ sung

Ngày 31/10/2026: chốt thiết kế fixture/tolerance trong đặc tả trước khi fit. Chạy ca giả lập 30 người, 9 TRTR và 21 RTRT, residual SD sinh dữ liệu T/R khác nhau. Oracle riêng `tests/replicate_error_contrast_oracle.py` không import be_app, dùng null space trực chuẩn của X', covariance tuyến tính, Nelder-Mead và Hessian/sensitivity finite differences. Coding sequence/period/treatment khác prototype; không dùng estimate của bên nào làm initial values cho bên kia.

| Đại lượng | Oracle độc lập | Prototype |
|---|---:|---:|
| T−R log contrast | 0.140577299827 | 0.140577299827 |
| SE | 0.119539886697 | 0.119539889365 |
| df | 28.000312751878 | 27.999999986816 |
| CI90 lower | 0.939154175933 | 0.939154098712 |
| CI90 upper | 1.410480210575 | 1.410480326550 |

Các covariance cũng đạt tolerance định trước. Eigenvalues G của oracle là 0.06661048 và 0.22233440; prototype báo `boundary=False`. Gradient số infinity norm 5.58e-5, Hessian positive definite. Bảy tests prototype đạt, bao gồm ca này. Artifact chi tiết ở `output/replicate_abe_experimental/interior_imbalanced.json`.

Đây là kiểm chứng implementation độc lập cho trường hợp nội miền lệch nhóm, chưa phải output Phoenix mới hoặc qualification cho ca boundary. Vẫn cần policy boundary và kiểm tra tích hợp/version/snapshot trước khi thay estimator production. Mọi fit tiếp tục trả `inference_allowed=False`.
