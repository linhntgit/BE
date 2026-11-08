# ĐẶC TẢ TRIỂN KHAI CHO CODEX — ỨNG DỤNG PHÂN TÍCH TƯƠNG ĐƯƠNG SINH HỌC (BE)

> **Vai trò của Codex:** Hãy đóng vai kiến trúc sư phần mềm, chuyên gia dược động học (PK/NCA), chuyên gia thống kê tương đương sinh học (BE), kỹ sư kiểm thử và chuyên gia hồ sơ đăng ký thuốc. **Hãy triển khai ứng dụng thực sự, có kiểm thử và tài liệu, không chỉ dựng giao diện hoặc viết mã giả.** Khi một yêu cầu liên quan quy định chưa đủ rõ hoặc chưa được xác minh, áp dụng cách xử lý an toàn: đưa vào cấu hình có nguồn viện dẫn, cảnh báo rõ, và **không tự động kết luận đạt BE**.
>
> **Ngôn ngữ:** giao diện, hướng dẫn thao tác, thông báo và giải thích bằng **tiếng Việt**; thuật ngữ quốc tế (AUC, Cmax, TOST, ABEL, RSABE...) giữ nguyên khi cần. Báo cáo có lựa chọn **tiếng Anh theo văn phong hồ sơ CTD** và bản tiếng Việt nội bộ.
>
> **Mốc tài liệu để đối chiếu:** **29/10/2026**. Bắt buộc kiểm tra tình trạng văn bản gốc, phạm vi áp dụng, yêu cầu riêng của sản phẩm và cơ quan quản lý trước khi chốt thuật toán. Không giả định mọi phương pháp phù hợp cho mọi sản phẩm, dạng bào chế hoặc thiết kế.

---

## 1. Mục tiêu, phạm vi và nguyên tắc bắt buộc

Xây dựng một ứng dụng web nội bộ giúp nhóm nghiên cứu BE thực hiện quy trình khép kín:

1. Khởi tạo nghiên cứu, chọn **EMA / FDA**, thiết kế nghiên cứu, **tính cỡ mẫu/power**, lập danh sách ngẫu nhiên hóa và bảng **subject × sequence × period × treatment**.
2. Sau khi nghiên cứu thực tế được thực hiện, nhập **nồng độ thuốc trong huyết tương theo thời gian** cùng thời gian lấy mẫu thực tế, liều dùng, tình trạng hoàn thành, dữ liệu sai lệch và dữ liệu assay cần thiết.
3. Kiểm tra dữ liệu, tính **NCA**, phân tích **ABE/TOST**, **EMA reference-scaled acceptance limits (ABEL)**, **FDA reference-scaled average BE (RSABE)** theo đúng chỉ định; hỗ trợ phân tích nhạy cảm và truy xuất mọi quyết định.
4. Sinh báo cáo nghiên cứu BE, bảng biểu/dữ liệu nguồn và **gói nội dung phù hợp cấu trúc CTD** để chuyên gia lâm sàng, thống kê, QA và Regulatory Affairs rà soát trước khi nộp.
5. Lưu lại dự án có thể mở lại nguyên trạng: dữ liệu, phiên bản quy tắc, thiết kế, kết quả, biểu đồ, nguồn gốc, audit trail và bản xuất báo cáo.

**Ranh giới quan trọng:** Ứng dụng là công cụ xử lý dữ liệu/phát triển hồ sơ, **không tự khẳng định đã được EMA/FDA thẩm định, đủ điều kiện GxP, tuân thủ 21 CFR Part 11 hoặc sẵn sàng nộp eCTD** chỉ vì xuất được PDF/Word. Điều này cần bằng chứng xác nhận phần mềm, kiểm soát hệ thống, thẩm định QA và quy trình nộp theo từng khu vực.

### 1.1 Phân loại chức năng theo mức hoàn thiện

- **Giai đoạn 1 — Nền tảng có thể sử dụng:** thiết kế 2×2 và song song; tính cỡ mẫu TOST chuẩn; nhập/QC nồng độ; NCA liều đơn; ABE; báo cáo cơ bản; lưu/mở dự án; regression tests.
- **Giai đoạn 2 — Thiết kế lặp lại và tương đương mở rộng:** partial/full replicate; phân tích ABE với thiết kế replicate; **EMA ABEL**; **FDA RSABE** (bao gồm các phép kiểm định và đầu ra bổ trợ); mô phỏng power/cỡ mẫu; báo cáo so sánh EMA–FDA.
- **Giai đoạn 3 — Mở rộng theo nhu cầu và sau khi xác minh:** multiple-dose/steady-state, partial AUC, các thiết kế nhiều nhóm, nghiên cứu thích ứng có quy định trước, NTI/thuốc biên độ điều trị hẹp, multiple reference, dữ liệu chuẩn hóa SDTM/ADaM, API tích hợp LIMS và eCTD package assembly. Những mục chưa đủ bằng chứng phải **gắn nhãn Chưa hỗ trợ**, không hiển thị nút PASS.

## 2. Nguồn quy định và bộ quy tắc phiên bản hóa

**Không xây dựng duy nhất một “chế độ EMA/FDA” dùng chung ngưỡng.** Thiết kế `RegulatoryRuleSet` theo phiên bản: jurisdiction, guideline, ngày ban hành/hiệu lực, scope, design, endpoint, điều kiện, thuật toán, thresholds, nguồn URL, trạng thái được xác minh và phiên bản mã thực thi.

| Rule profile | Nguồn ưu tiên | Nguyên tắc áp dụng |
|---|---|---|
| **EMA / EU — IR, non-replicate** | ICH **M13A**, hiệu lực tại EU **25/01/2025** + tài liệu thực thi EMA | Ưu tiên các phần M13A đã thay thế EMA guideline cũ đối với nghiên cứu không lặp lại nằm trong phạm vi M13A. |
| **EMA / EU — replicate và HVDP** | EMA *Guideline on the Investigation of Bioequivalence*, Rev. 1, **các phần vẫn còn áp dụng**, kết hợp M13A ở nội dung thích hợp | Không suy diễn rằng M13A đã thay thế tất cả hướng dẫn EMA về replicate/ABEL. |
| **FDA — nghiên cứu PK/BE** | FDA **M13A** (final 10/2024), **Statistical Approaches to Establishing Bioequivalence** (**final 05/2026**), **Bioequivalence Studies With PK Endpoints for Drugs Submitted Under an ANDA** (**final 05/2026**) | FDA bản 05/2026 là mốc quan trọng: không dùng bản **Statistical Approaches 2001** hoặc bản **draft 2022** làm mặc định. |
| **FDA product-specific** | FDA **Product-Specific Guidances (PSG)** theo hoạt chất/sản phẩm, dạng bào chế, cơ chế giải phóng, đường dùng | Nếu PSG đòi endpoint, điều kiện hoặc phương pháp khác, phải kiểm tra và xử lý trước khi công bố kết luận. |
| **Bioanalytical** | ICH **M10** và câu hỏi–trả lời | Theo dõi assay, LLOQ, mẫu phân tích, ISR, độ tin cậy và tính toàn vẹn dữ liệu; app không thay thế thẩm định phương pháp phân tích. |
| **Báo cáo** | ICH **E3**, **M4E(R2)**; EMA Appendix IV cho Module 2.7.1 | CSR, bản tóm tắt sinh dược học và bảng chứng cứ ở đúng cấu trúc; tuân thủ CTD không đồng nghĩa tự động tạo được sequence eCTD hợp lệ. |

**Bộ quy tắc phải hỗ trợ:** `EMA_IR_NONREPLICATE_M13A`, `EMA_REPLICATE_STANDARD`, `EMA_HVDP_ABEL`, `FDA_ABE_2026`, `FDA_HVD_RSABE_2026`. Bổ sung `FDA_NTI` sau khi đã xác minh, triển khai và đối chiếu reference independently. Không gộp FDA HVD với FDA NTI.

Mỗi kết quả phải hiển thị trong tab **Cơ sở pháp lý**: guideline/version, đoạn/điều liên quan (được nhập có kiểm chứng), điều kiện kích hoạt, tham số và lý do chọn đường phân tích. Không cho phép thay rule set sau khi khóa phân tích nếu không tạo **analysis revision** mới.

## 3. Công nghệ, kiến trúc và cấu trúc dự án

**Ưu tiên Python + Streamlit** để xây ứng dụng web khoa học nhanh, dễ triển khai tại máy nội bộ. Tách riêng UI khỏi engine để về sau chuyển sang FastAPI + React mà không sửa công thức. Thư viện dự kiến: `numpy`, `pandas`, `scipy`, `statsmodels` (chỉ ở nơi phù hợp và đã được kiểm chứng), `pydantic`, `plotly`, `openpyxl`, `python-docx`, thư viện PDF theo nhu cầu, `pytest`, `hypothesis`. Nếu một phương pháp hồi quy/phương sai không thể tái hiện chính xác bằng thư viện phổ thông, **viết adapter thống kê chuyên biệt và kiểm chứng bằng R/SAS/Phoenix/nguồn chuẩn độc lập**; tuyệt đối không thay ngầm bằng một `MixedLM` bất kỳ.

**Cấu trúc gợi ý:**

```text
be_app/
├─ app.py                         # entrypoint Streamlit
├─ ui/                            # các trang và thành phần giao diện tiếng Việt
├─ domain/                        # schema study, subject, dose, sample, assay, analysis
├─ regulations/                   # rule sets/version/scope/validation
├─ design/                        # randomization, power, sample size, schedules
├─ imports/                       # parsing, mapping, QC, reconciliations
├─ nca/                           # AUC, Cmax, Tmax, lambda_z, steady state
├─ statistics/                    # ABE, replicate, ABEL, RSABE
├─ reporting/                     # report templates, CTD mappings, manifest
├─ persistence/                   # SQLite/Postgres, archive and migration
├─ security/                      # role, event log, access controls
├─ tests/                          # fixtures, gold standards, unit/integration/E2E
├─ docs/                           # phương pháp tính, traceability, SOP, validation
├─ examples/                       # CHỈ dữ liệu giả lập, nhận diện rõ
├─ requirements.txt or pyproject.toml
└─ README.md
```

- Chọn **SQLite cho local single-user**, chuẩn hóa lớp persistence để hỗ trợ **PostgreSQL** trong môi trường nhiều người dùng.
- Không chứa dữ liệu cá nhân nhạy cảm trong log, exception hoặc repo; subject dùng pseudonymous ID.
- Pipeline bắt buộc **raw → validated → NCA → BE → report**; dữ liệu gốc bất biến, mỗi lần transform ghi lịch sử.
- Sử dụng snapshot phiên bản bất biến (`analysis_run_id`, `dataset_hash`, `rule_set_id`, `engine_version`, `config_hash`, `timestamp`, `operator`, `reviewer`).
- Ưu tiên deterministic build, dependency lockfile, timezone UTC nội bộ và thể hiện múi giờ địa phương trong UI; đơn vị định lượng luôn tường minh.
- Không cần kết nối internet để phân tích sau khi quy tắc đã được đóng gói và kiểm soát phiên bản.

## 4. Giao diện tiếng Việt và trải nghiệm

Thanh bên có các mục:

1. **Tổng quan / Quản lý nghiên cứu**
2. **Thiết kế và cỡ mẫu BE**
3. **Ngẫu nhiên hóa và lịch lấy mẫu**
4. **Nhập dữ liệu nồng độ**
5. **Kiểm soát chất lượng (QC)**
6. **Phân tích NCA**
7. **Thống kê BE — EMA / FDA**
8. **Đồ thị và chẩn đoán**
9. **Báo cáo CTD / Xuất dữ liệu**
10. **Nhật ký kiểm toán / Quản trị**
11. **Trợ giúp, công thức, nguồn quy định**

**Nguyên tắc UI:** bố cục rõ, wizard có bước hoàn thành, dùng tiếng Việt chuẩn và giải thích tooltip. Có trạng thái `Chưa nhập`, `Đang kiểm tra`, `Hợp lệ`, `Có cảnh báo`, `Lỗi chặn`, `Đã khóa`, `Chưa được thẩm định`.

- Tách rõ **Dữ liệu nghiên cứu thật** và **Dữ liệu giả lập phục vụ học thử**; dữ liệu demo không được tạo chứng nhận/report có nhãn “Dùng nộp cơ quan quản lý”.
- Nút **Phân tích** chỉ hoạt động nếu kiểm tra dữ liệu và thiết kế đạt điều kiện tối thiểu.
- Không lấy trạng thái `Power đạt` hoặc `p > 0.05` làm kết luận BE.
- Kết luận phải theo từng endpoint và từng chế độ pháp lý; không hiển thị chữ `PASS` cho toàn nghiên cứu khi endpoint bắt buộc nào đó `FAIL` hoặc `NOT EVALUABLE`.
- Đồ thị tương tác: concentration–time thang tuyến tính và bán log; từng subject, từng treatment, đường trung bình; thống kê endpoint và CI, so sánh giữa các period/sequence.

## 5. BƯỚC 1 — Thiết kế, cỡ mẫu, power và ngẫu nhiên hóa

### 5.1 Thông tin đầu vào

**Nghiên cứu:** study ID, tên nghiên cứu, protocol/SAP ID + phiên bản, đơn vị thực hiện, hoạt chất, dạng bào chế (**IR/MR**), hàm lượng, liều, điều kiện fed/fasted, đơn liều/đa liều, quốc gia/quy định đích, tên Test/Reference, batch/lot, route, washout dự kiến, cửa sổ lấy mẫu, primary endpoints, ngưỡng BE, giả định và nguồn.

**Cỡ mẫu/power:**

- Design: **2×2 crossover** (`TR`, `RT`); **parallel** (`T`, `R`); **partial replicate 3 period** (`TRR`, `RTR`, `RRT`); **full replicate 4 period** (`TRTR`, `RTRT`); thiết kế replicate khác chỉ sau khi xác minh mô hình và tính khả thi.
- `CVw` / intra-subject **theo endpoint (AUC, Cmax)** và theo T/R nếu biết; `CVb` / inter-subject **tách biệt**; tránh sử dụng CVb cho công thức cỡ mẫu crossover như thể đó là CVw.
- T/R expected GMR (vd 0.95), **riêng AUC/Cmax nếu khác**.
- Power mục tiêu (vd 80%, 90%), alpha TOST (mặc định 0.05), acceptance limits từ rule set; dropout dự kiến, tỷ lệ phân nhóm, số đối tượng tối thiểu theo hướng dẫn có hiệu lực.
- Tùy chọn nguồn dữ liệu pilot cho CV, mức độ không chắc chắn, kịch bản bảo thủ và sensitivity analysis.

**Không cho nhập `CV = 30` mà không biết là 30% hay 0.30; UI lưu dạng số chuẩn có đơn vị.** Phải xác nhận rằng `CVw` có thể là ước tính từ within-subject variance log-scale và không nhầm với SD gốc.

### 5.2 Cỡ mẫu và power

- 2×2 chuẩn: dùng power **exact/numerical TOST** theo phân phối t không trung tâm với mô hình crossover phù hợp và bậc tự do đúng; không chỉ lấy công thức z xấp xỉ rồi hiển thị power giả chính xác.
- Parallel: mô hình hai nhóm độc lập, sử dụng đúng biến thiên/variance và phép kiểm định tương ứng; không reuse công thức crossover.
- Replicate/ABEL/RSABE: mô phỏng Monte Carlo trên đúng mô hình dữ liệu và **đúng phép thử BE của chế độ đó**; kết quả có CI Monte Carlo, seed, số lượt chạy, tham số/giả định, kiểm tra Type I error ở các tình huống biên. Chỉ chạy đánh giá power bằng thuật toán đã được benchmark.
- Kết quả: n phân tích cần thiết, n tuyển với dropout, n mỗi sequence/arm, power đạt được, design effect, nguồn CV, biểu đồ **n–power**, biểu đồ **GMR–power**, phân tích nhạy cảm CV (ví dụ 15–60%).
- Không dùng CV inter-subject làm nguồn biến thiên duy nhất của endpoint crossover; giải thích trong UI vai trò từng loại CV.
- Với M13A trong phạm vi IR nonreplicate, thực hiện kiểm tra số người có dữ liệu đánh giá theo quy định (ví dụ mốc tối thiểu **12 người có dữ liệu đánh giá cho crossover; 12 mỗi nhánh parallel** theo mục 2.2.3.1), nhưng không áp cứng mốc này cho mọi bối cảnh ngoài phạm vi.
- Kết quả design chưa phải danh sách phân nhóm, cũng chưa phải kết luận nghiên cứu.

### 5.3 Randomization

- Cân bằng sequence theo block, định nghĩa số block và kích thước; deterministic với seed lưu trong hồ sơ; cung cấp chế độ sinh seed bảo mật theo SOP.
- Tạo **subject screening ID**, **randomization ID**, sequence, period, treatment, cohort/group, planned dosing và **planned sample time**.
- Thêm actual dosing date/time và actual sample datetime **sau khi thực hiện**; không được tự chép nominal thành actual.
- Tách **danh sách phân nhóm (restricted access)** khỏi **bảng thiết kế cho phòng lấy mẫu**; mã hóa thuốc nếu nghiên cứu mù.
- Xuất Excel (bảo toàn leading-zero ID), CSV UTF-8 BOM khi dùng Excel, file protocol summary; tất cả có version/seed/hash.
- Chức năng kiểm tra phân nhóm: mỗi subject có số kỳ phù hợp thiết kế, đúng treatment/sequence, không có cặp ID trùng, không có một subject ở hai sequence.

**Ví dụ bảng thiết kế (chỉ minh họa):**

| Subject | Sequence | Period | Treatment | Status |
|---|---|---:|---|---|
| S001 | TR | 1 | Test | Planned |
| S001 | TR | 2 | Reference | Planned |
| S002 | RT | 1 | Reference | Planned |
| S002 | RT | 2 | Test | Planned |

## 6. BƯỚC 2 — Nhập và quản lý Cplasma thực tế

### 6.1 Định dạng dữ liệu

- Nhận `.xlsx`, `.csv` (long format chính; wide format qua mapping wizard), tùy chọn API LIMS khi mở rộng.
- **Long schema** tối thiểu:

```csv
study_id,subject_id,sequence,period,treatment,dose_datetime,sample_datetime,nominal_time_h,actual_time_h,concentration,concentration_unit,blq_flag,lloq,sample_id,analyte,source_batch
BE001,S001,TR,1,T,2026-09-01T08:00:00+07:00,2026-09-01T08:00:00+07:00,0,0,0,ng/mL,false,1,SM001,parent,B001
BE001,S001,TR,1,T,2026-09-01T08:00:00+07:00,2026-09-01T09:00:00+07:00,1,1,120,ng/mL,false,1,SM002,parent,B001
```

Ví dụ này là **synthetic/demo**, không phải dữ liệu nghiên cứu hoặc bộ chuẩn để xác nhận thuật toán.

- `actual_time_h` suy ra từ actual dose/sample datetime nếu đủ dữ liệu, hiển thị sai lệch giữa computed và imported để người dùng đối chiếu. Không thay actual time bằng nominal mặc định.
- Đơn vị chuẩn được cấu hình; chuyển đổi µg/L, ng/mL... phải có kiểm tra thứ nguyên, ghi đầy đủ dấu vết và không tự chuyển khi chưa xác định.
- Có thông tin **assay run/batch**, LLOQ, parent/metabolite, sample status (`VALID`, `BLQ`, `MISSING`, `REASSAY`, `REJECTED`...), định danh mẫu ban đầu và mẫu phân tích lại; raw vẫn giữ nguyên.

### 6.2 Quy tắc kiểm tra dữ liệu

Bắt lỗi hoặc cảnh báo:

- ID không tồn tại trong danh sách phân nhóm; period/sequence/treatment lệch randomization; thiếu dose datetime.
- Nhập trùng **sample ID**, trùng record hoặc nhiều mẫu ở cùng thời gian **trong cùng subject–period–analyte**; phân biệt thật sự được lấy mẫu nhiều lần và dữ liệu nhập lặp.
- Nồng độ âm, NaN, đơn vị không xác định, nồng độ bằng 0 không phân biệt được BLQ, mẫu trước liều, sai định dạng thời gian, actual time âm bất thường.
- Thiếu baseline hoặc thiếu vùng Cmax, ít điểm cuối pha, lỗ hổng thời gian, Tmax ở mẫu đầu tiên, ngoại lệ có thể là sample mislabel.
- Missingness/dropout: **không xóa subject hoặc period tự động**; ghi nguyên nhân, người phê duyệt, thời điểm quyết định so với thời điểm mở mẫu.
- Carryover/định lượng trước liều: dùng quy tắc cụ thể từ profile, có cảnh báo **predose > 5% Cmax** cho single-dose M13A trong phạm vi áp dụng; áp đúng logic loại period và quy định báo cáo, không tự áp quy tắc cho mọi nghiên cứu.
- Tự động đánh dấu outlier để **rà soát**, không tự xóa outlier vì kết quả không mong muốn hoặc để đạt BE.

### 6.3 Kiểm soát thay đổi

- Xem raw và cleaned song song, import preview, bảng lỗi theo dòng/cột, tải về QC report.
- Mọi sửa đổi raw tạo correction record: bản cũ, bản mới, lý do, người sửa, người duyệt, thời điểm, bằng chứng.
- Có `Data Freeze` và `Analysis Freeze`; chạy lại tạo revision riêng, không ghi đè lịch sử.
- Quản lý phiên bản protocol/SAP, prespecified exclusions, assumptions, BLQ policy **trước khi mở kết quả**.

## 7. BƯỚC 3A — NCA (Non-Compartmental Analysis)

### 7.1 Chỉ số bắt buộc

**Single dose:** `Cmax`, `Tmax`, `AUC0-last`, `AUC0-t` theo định nghĩa, `AUC0-inf`, `lambda_z` (kel), `t1/2`, phần trăm AUC ngoại suy, `AUC0-last / AUC0-inf`, `Clast`, `Tlast`, `MRT` khi phù hợp; `AUC0-72h` và **partial AUC** khi quy định/đặc tính thuốc yêu cầu.

**Steady state (giai đoạn sau):** `Cmax,ss`, `Cmin,ss`, `Ctau,ss`, `AUC0-tau,ss`, `Cavg,ss`, fluctuation, swing, Tmax,ss và bằng chứng steady state. Không hiển thị các chỉ số này là “đã tính” trong MVP nếu chưa hỗ trợ thật.

### 7.2 Thuật toán NCA

- **Cmax/Tmax:** giá trị quan sát thực (không lấy từ đường spline làm chính); nếu đồng mức Cmax ở nhiều thời gian, quy tắc xử lý Tmax được cấu hình, ghi trong phương pháp.
- **AUC:** hỗ trợ `linear trapezoidal`, `linear-up/log-down` và cấu hình phù hợp; quy tắc tích phân cho C=0, C không dương, BLQ, khoảng cuối phải explicit; tuyệt đối không lấy log của 0 hoặc nội suy lén khi thiếu dữ liệu.
- **Lambda-z:** chọn các điểm cuối pha bằng hồi quy log-concentration vs time, kiểm soát tối thiểu số điểm thích hợp (thông thường ≥3), độ phù hợp (adjusted R²), sườn âm và cách chọn terminal segment; hiển thị đồ thị và cho phép chọn thủ công có **lý do + audit**. Không tự khẳng định lambda-z hợp lệ vì adjusted R² cao đơn thuần.
- `t1/2 = ln(2)/lambda_z`; `AUC0-inf = AUC0-last + Clast/lambda_z` khi có thể tính hợp lệ; `AUC extrapolated (%) = (AUCinf − AUClast)/AUCinf × 100`.
- **BLQ:** chiến lược phụ thuộc guideline/SAP. Với M13A, các nồng độ dưới LLOQ trong tính PK được xử lý như quy định của tài liệu; không được biến giá trị `MISSING` thành 0 và không dùng BLQ trong hồi quy terminal. Giữ raw BLQ và cờ trong toàn bộ quá trình.
- Dùng **actual sampling time** cho NCA cá thể, nominal chỉ dành tổng hợp/đồ thị mean theo hướng dẫn có liên quan.
- Mỗi profile cần có `NcaResult`: đủ endpoint, cảnh báo, phương pháp, số điểm lambda-z, thời gian/data terminal dùng, lý do không tính được, phiên bản algorithm.

### 7.3 Bảng và biểu đồ

- Individual C–t theo **actual time** (linear/semi-log); mean profile theo **nominal time**, hỗ trợ SD/SE/CV/N kèm thời điểm thực tế không đồng đều.
- Bảng NCA subject × period × treatment, bảng summary theo treatment: n, arithmetic/geometric mean, median, SD, CV%, min/max; phân biệt **CV mô tả**, `CVw` phân tích BE, `CVwR` từ replicate.
- Report nêu rõ nguồn, công thức, phương pháp tích phân, chính sách terminal, BLQ và bất cứ can thiệp thủ công nào.

## 8. BƯỚC 3B — Phân tích thống kê BE

### 8.1 ABE/TOST thông thường

- Endpoint chính thường là **AUC0-t** và **Cmax** cho single dose IR; endpoint bổ sung theo form/regulatory/PSG.
- Phân tích PK endpoint trên **log tự nhiên**: `y = ln(PK)`; không dùng phép kiểm định tương đương trên giá trị thô hoặc CI tỷ lệ số học thay cho GMR log-scale.
- **GMR = exp(ước lượng tương phản T − R)**; **90% CI** = `exp(estimate ± t(0.95, df) × SE)` khi phù hợp với mô hình đã pre-specify; TOST với alpha mỗi phía 0.05.
- Trong trường hợp giới hạn chuẩn **80.00–125.00%**, chỉ `PASS` khi **toàn bộ CI 90%** của từng endpoint phải nằm trong giới hạn tương ứng, với quy tắc so sánh/rounding theo jurisdiction và SOP; kiểm tra bằng precision đầy đủ trước format hiển thị.
- **2×2:** mô hình có formulation, period, sequence, subject nested within sequence với fixed/random effects đúng profile và thiết kế, xuất effect estimates và ANOVA/mixed-model diagnostics. Không dùng 2-sample independent t-test cho crossover.
- **Parallel:** 2 nhánh độc lập, điều chỉnh covariate/strata khi được quy định trước; variance model/df và CI phù hợp.
- **Replicate:** effect structure, subject correlation, within-subject treatment-specific variance, covariance, df, GMR phải được xử lý đúng; không dùng ANOVA 2×2 trên dữ liệu 3–4 period.
- Không dựa vào `p-value` của hiệu ứng treatment hoặc sequence để kết luận đạt BE. Với ABE, xuất **TOST p-values** nếu mô hình cung cấp có kiểm chứng.
- Với nghiên cứu nhiều nhóm, nhiều trung tâm, mất kỳ hoặc imbalance, áp mô hình đúng theo văn bản/SAP và phát hiện model failure, singular covariance, không đủ df, convergence, rank deficiency.

### 8.2 EMA ABEL — Highly variable drug products

**Chỉ cho phép ở trường hợp đủ điều kiện, được định trước trong protocol, có dữ liệu replicate đủ để ước tính biến thiên trong-cá-thể của Reference (`sWR`) tin cậy.** Không chọn ABEL bằng một nút khi chỉ có 2×2.

- Mặc định **có thể scale Cmax khi đúng tiêu chí EMA**, không tự mở rộng AUC; AUC vẫn theo 80–125% trong quy tắc tương ứng.
- `CVwR = sqrt(exp(sWR²) − 1) × 100%`.
- Khi đáp ứng điều kiện dùng ABEL (mốc biến thiên Reference >30% theo EMA guideline, cùng các điều kiện khoa học/pháp lý khác):
  - `L = exp(−0.760 × sWR)`, `U = exp(+0.760 × sWR)`.
  - Giới hạn tối đa được mở rộng là **69.84–143.19%**; không được rộng hơn.
  - **GMR T/R phải nằm trong 80.00–125.00%** đồng thời **CI 90% nằm trọn trong [L, U]**.
  - Lưu CVwR, sWR, nguồn ước lượng, valid design, expanded limits, GMR/CI, các kiểm tra ngoại lệ và sự phê duyệt.
- Khi không thỏa điều kiện ABEL, dùng phương pháp ABE chuẩn và không nói “ABEL failed” nếu thực chất là **not eligible**.
- Phải kiểm tra các điều kiện về tính phù hợp lâm sàng của mở rộng Cmax và prespecification, cùng tính bền vững của ước lượng sWR đối với outlier.

### 8.3 FDA RSABE — Highly variable drugs

**FDA RSABE khác EMA ABEL về bản chất phép thử; cấm dùng giới hạn CI mở rộng kiểu EMA để gọi là FDA RSABE.**

- Với **highly variable, non-NTI** và thiết kế **partial/full replicate phù hợp**, tính `sWR` trên log-PK riêng **theo từng endpoint**.
- Theo FDA Statistical Approaches final **05/2026**: nếu `sWR < 0.294`, xét **ABE/TOST**; nếu `sWR ≥ 0.294`, thực hiện **RSABE** với **95% upper confidence bound** của tiêu chí chuẩn hóa, kèm ràng buộc **point estimate GMR T/R ∈ [0.8000, 1.2500]**.
- Tiêu chí tuyến tính hóa cơ sở (trình bày để audit):

  `eta = (mu_T − mu_R)^2 − theta × sigma_WR^2`, với `theta = [ln(1.25) / 0.25]^2`.

  Kết luận khi **95% upper confidence bound(eta) ≤ 0** **và** thỏa GMR point-estimate constraint theo hướng dẫn.
- **Điều kiện pass phải dựa trên upper confidence bound chứ không dùng giá trị eta ước lượng điểm đơn thuần.**
- Triển khai các bước theo **Appendix G** của FDA hướng dẫn 05/2026 cho **partial replicate** và **fully replicate**, gồm cách tính variance, df, upper bound/Howe approximation hoặc phương pháp được guideline chấp nhận. Xuất các thành phần trung gian để reviewer tái tính.
- FDA 05/2026 mô tả phương pháp này đối với **AUC và Cmax theo từng endpoint**, không được tự mặc định “FDA scale duy nhất Cmax” như EMA.
- Phân biệt rõ **FDA NTI RSABE** có tham số/ngưỡng/điều kiện khác và thêm kiểm soát biến thiên T so với R; không reuse `theta=.../0.25²` cho NTI. Chỉ mở chức năng NTI sau khi validation hoàn tất.

### 8.4 Bảng kết quả BE tối thiểu

| Endpoint | Method | N analyzed | T geometric mean | R geometric mean | GMR (%) | 90% CI (%) | CVw / CVwR (%) | Regulatory limits / scaled test | Decision |
|---|---|---:|---:|---:|---:|---|---:|---|---|
| AUC0-t | ABE | ... | ... | ... | ... | ... | ... | 80.00–125.00 | PASS/FAIL/NE |
| Cmax | EMA ABEL | ... | ... | ... | ... | ... | ... | giới hạn tính từ sWR | PASS/FAIL/NE |
| Cmax | FDA RSABE | ... | ... | ... | ... | **báo cáo CI ABE bổ trợ nếu phù hợp** | ... | 95% upper bound + GMR | PASS/FAIL/NE |

- Bảng chuẩn hóa phải hiển thị **phương pháp thật đang sử dụng**; đối với RSABE, thêm `RSABE upper bound`, `GMR constraint`, lý do chọn nhánh và các biến trung gian.
- Nên tạo **2 bản phân tích EMA và FDA song song** từ cùng snapshot dữ liệu (khi phù hợp), giữ lịch sử từng bản; kết quả EMA có thể khác FDA và điều đó không tự động là lỗi tính toán.
- Không so sánh pass rate mô phỏng với BE một nghiên cứu thật. Nếu sau này có module VBE/power: ghi tách biệt `Simulation`, `Observed BE`, `Regulatory decision`.

### 8.5 Quy tắc loại trừ, sensitivity và xử lý bất thường

- SAP/protocol phải quy định population (`randomized`, `dosed`, `PK evaluable`, `BE analysis`), deviations, BLQ, missing values, rules và phân tích bổ trợ **trước khi biết kết quả nghiên cứu**.
- Những subject thiếu một period không được tự động điền giá trị hoặc xóa toàn bộ; phân tích theo eligibility/model và mô tả tình trạng, consistent theo guideline.
- Outlier có thể được phát hiện bằng visual/statistical diagnostics nhưng **không tự động xóa để biến FAIL thành PASS**. Xuất cả primary và sensitivity khi có căn cứ hợp lệ.
- Carryover: phân tích theo predose và guideline, tránh dùng carryover significance test để quyết định phân tích period 1 như một mẹo cứu BE.
- Có analysis history đầy đủ để tái hiện mọi thay đổi selection/method.

## 9. BƯỚC 4 — Báo cáo và hồ sơ CTD

### 9.1 Loại file xuất

1. **Clinical BE Study Report (CSR) draft** tiếng Anh theo cấu trúc liên quan **ICH E3**, `.docx` và `.pdf`; có lựa chọn bản tiếng Việt để soát nội bộ.
2. **CTD Module 2.7.1 Biopharmaceutic Studies and Associated Analytical Methods**: phần tổng hợp, các bảng theo ICH M4E(R2) và **EMA Appendix IV** khi nộp EU.
3. **CTD Module 5.3.1.2**: phần báo cáo nghiên cứu comparative BA/BE và phụ lục dữ liệu; thông tin hỗ trợ bioanalytical method và study sample analysis được sắp đúng mục CTD liên quan.
4. **Statistical Analysis Report (SAR)**: chi tiết mô hình, đầu vào, output, design, model matrix/covariance nếu cần, ANOVA, BE estimates, residual diagnostics, deviations, sensitivity, software versions.
5. **Raw/analysis datasets** ở CSV/XLSX, có metadata/data dictionary, actual dosing/sampling time, concentrations, individual PK, PK summaries, randomization, audit trail và references.
6. **Evidence/traceability package**: `manifest.json`, hashes, file inventory, rule-set versions, algorithm versions, validation records, người tạo/người rà soát/trạng thái phê duyệt.

### 9.2 Nội dung báo cáo

- Cover: study ID, title, API/formulation, design, fed/fasted, protocol/SAP, sponsor, sites, dates, version/status, chữ ký/ô xác nhận theo quy trình thực tế.
- Synopsis, objective, reference/test product information, batch numbers, strength, dose, crossover/parallel design, randomization, washout, conduct, deviations, population.
- Sampling/assay overview, validated bioanalytical methodology reference, LLOQ, data QC, handling BLQ/missing/reassay, analytical deviations.
- Individual/mean C–t plots (linear/semilog), PK tables, NCA method, descriptive stats, observed/nominal sampling differences.
- Statistical methods, rule-set sources, GMR, 90% CI, model details, CVw, ABEL/RSABE components, endpoint decisions; uncertainty, sensitivity, data exclusions, limitations.
- References, annexes, individual listings, source/traceability.

### 9.3 Chống báo cáo sai

- Không có dữ liệu thật hoặc phân tích chưa được đánh giá → chỉ xuất bản **DRAFT / NOT REGULATORY-READY** với watermark/status trong report và manifest.
- Đã có kết quả thống kê **chưa có QA/Regulatory review** → chỉ gắn `Pending independent review`, không tự gắn `Submission Ready`.
- Không sinh chữ ký điện tử giả, không ghép approval date giả, không tạo ``eCTD validated`` nếu chưa có validator độc lập và metadata sequence hợp lệ.
- Kiểm soát page breaks, bảng nhiều cột, font hỗ trợ tiếng Việt, đồ thị vector/độ phân giải cao, header/footer, numbering, TOC, references và hyperlink.
- `render`/export được kiểm thử để tránh hình bị cắt, tables bị rớt cột, nhầm tên treatment hoặc lệch đơn vị.

## 10. Dữ liệu, API nội bộ và persistence

### 10.1 Các thực thể cốt lõi

`Study`, `RegulatoryRuleSet`, `Product`, `ProtocolVersion`, `SAPVersion`, `StudyDesign`, `Subject`, `RandomizationAssignment`, `TreatmentPeriod`, `DoseEvent`, `Sample`, `BioanalyticalAssayRun`, `ConcentrationMeasurement`, `QCFlag`, `DataCorrection`, `AnalysisPopulation`, `NcaConfig`, `NcaResult`, `BeAnalysisConfig`, `BeAnalysisResult`, `ReportArtifact`, `AuditEvent`.

**Khóa tham chiếu quan trọng:** `study_id + subject_id + period + treatment + analyte + sample_id`; không giả sử một bản ghi duy nhất cho mỗi thời điểm nếu có duplicate sample/reassay; không gộp mẫu theo trung bình mà không có quy tắc pre-specified.

### 10.2 Dữ liệu bất biến và lưu/mở

- Có tính năng **Tải xuống dự án** / **Mở dự án** bằng một file `.beproject.zip` gồm metadata + database hoặc JSON snapshots + raw files + QC + NCA + BE + report config + charts + audit/history, kèm checksums, schema version, manifest.
- Reopen phải hiện lại tất cả thiết kế, randomization, dữ liệu và kết quả **không cần fit/phân tích lại**, nhưng có nút Recalculate có kiểm soát.
- Khi import `.beproject.zip`: chống path traversal, zip bombs, file độc hại; validate checksum và schema, có migration version cũ; không dùng `pickle` để deserialize dữ liệu không tin cậy.
- Export kèm `requirements/lockfile`, engine version và phương pháp; project không bao gồm khóa bí mật/token.

## 11. Bảo mật, audit, GxP readiness

- Hỗ trợ role-based access: `Admin`, `Study Designer`, `Data Manager`, `Statistician`, `QA/Reviewer`, `Read-only`.
- Authentication và session controls thích hợp; TLS cho môi trường mạng; mã hóa lưu trữ/backups theo chính sách đơn vị; hạn chế dữ liệu cá nhân tối đa.
- **Audit trail không thể sửa bằng UI**: actor, datetime, action, object, trước/sau, lý do, reference; thêm export và review.
- Separate access cho randomization/blinding khi thiết kế yêu cầu.
- Documented computerized system validation: URS, FRS, risk assessment, traceability matrix, IQ/OQ/PQ hoặc cách tiếp cận tương đương theo hệ thống chất lượng áp dụng; change control, backup/restore và kiểm chứng dữ liệu.
- Đánh giá khả năng áp dụng **21 CFR Part 11** và các yêu cầu EU/local có liên quan, nhưng **không tự công bố compliant** khi thiếu các bằng chứng/process cần thiết.

## 12. Kiểm thử khoa học và thống kê — BẮT BUỘC

**Không được nghiệm thu dựa vào app chạy không lỗi hoặc dashboard hiển thị con số hợp lý.** Mỗi phương pháp phải có golden reference được tính từ nguồn độc lập, kiểm thử các trường hợp có kết quả PASS, FAIL và không thể đánh giá.

### 12.1 Kiểm thử thiết kế và cỡ mẫu

- Randomization 2×2, parallel, TRR/RTR/RRT, TRTR/RTRT không trùng, cân bằng/seed reproducibility.
- Power chính xác ở các giá trị CV, GMR, n, alpha; kiểm tra các vùng sát ngưỡng 80/125 và các mức biến thiên cao; Monte Carlo có CI và seed; kiểm tra Type I error theo kịch bản biên.
- Mỗi thông số đầu vào đều có provenance và phạm vi hợp lệ; sai đơn vị CV không cho chạy.

### 12.2 Kiểm thử NCA

- Profile lý tưởng có AUC tính bằng tay; profile tuyến tính lên/xuống log; mẫu BLQ/zero; lambda-z không đủ 3 điểm; số liệu actual vs nominal; duplicate exact same time; Tmax nhiều điểm; partial AUC; AUC72; ngoại suy không hợp lệ.
- Đối chiếu với **ít nhất một phần mềm độc lập có dữ liệu tham chiếu** (ví dụ Phoenix WinNonlin, R `PKNCA`/`NonCompart` nếu model/method tương thích); ghi version, tham số lựa chọn, tolerance.

### 12.3 Kiểm thử thống kê

- 2×2 cân bằng và không cân bằng, missing period; parallel với variance unequal khi mô hình quy định; replicate 3/4 period; model convergence failure.
- ABE: tự tính từ ma trận contrast/SE/df + đối chiếu R/SAS/Phoenix; kiểm tra endpoint log transform, 90% CI, TOST, boundary rounding.
- EMA ABEL: CVwR = 29.9%, 30%, 35%, 40%, ≥50%; Cmax giới hạn tính; GMR constraint; AUC không mở rộng; outlier/sWR sensitivity.
- FDA RSABE: `sWR` sát biên 0.294, 2 nhánh switching, 95% upper bound âm/dương/sát 0, GMR trong/ngoài 80–125, partial/full replicate, các cấu phần Appendix G, khác biệt với EMA ABEL.
- **FDA NTI không được tự động áp RSABE HVD**; nếu chưa xác nhận NTI thì trạng thái `Not supported`.
- Từng endpoint `PASS / FAIL / NOT EVALUABLE`; kết luận cấp-study là tổng hợp chính xác các endpoint bắt buộc.

### 12.4 Kiểm thử tích hợp / báo cáo / lưu trữ

- Import → QC → NCA → BE → report → export → reload → so sánh hashes và outputs (tất cả giữ nguyên).
- Dữ liệu thiếu/không hợp lệ không được xuất báo cáo với trạng thái PASS.
- Report mapping tự động đúng CTD section và đúng subject/period; tables DOCX không mất cột; PDF đủ trang, hình/đồ thị hiển thị chuẩn.
- Regression test cho mỗi lỗi sửa, fixtures tự chứa trong `tests/fixtures`, **không phụ thuộc đường dẫn trên máy nhà phát triển**.
- CI: `ruff`/lint, type check, `pytest`, security checks và report reproducibility.

**Điều kiện nghiệm thu thuật toán:** có bảng benchmark ghi `fixture | design | jurisdiction | endpoint | expected | actual | absolute/relative difference | tolerance | source | pass`; sai khác ngoài tolerance sẽ **block release**. Không tùy tiện chọn tolerance quá rộng để hợp thức hóa khác biệt mô hình.

## 13. Các ý tưởng nâng cao (ưu tiên theo giá trị)

1. **Design Advisor:** đưa đề xuất crossover/parallel/partial/full replicate và lý do khoa học: half-life/washout, CVw, high variability, NTI, số period, burden cho volunteer; không thay quyết định của bác sĩ/biostatistician.
2. **Regulatory Comparison:** một dataset, hai bản phân tích EMA/FDA với rule citations + differences; chỉ so sánh khi đúng phạm vi.
3. **Sampling Schedule Optimizer:** gợi ý mật độ lấy mẫu gần Tmax, terminal sampling, khả năng đo AUC; bắt buộc người phụ trách duyệt.
4. **Sensitivity Dashboard:** GMR, CI, CVw, PK anomalies, missingness, outlier, terminal selection; luôn phân biệt primary vs exploratory.
5. **Pre-analysis SAP Lock:** lưu/khóa phương pháp và các lựa chọn data handling trước unblinding/analysis.
6. **Automated Data Reconciliation:** so sánh randomization ↔ dosing ↔ sample collection ↔ lab result ↔ analysis dataset.
7. **BE Quality Risk Score:** checklist về thiếu mẫu, predose carryover, incomplete AUC, first-point Cmax, ABEL eligibility, model failures; score chỉ hỗ trợ QC, không thay kết luận.
8. **Regulatory Update Registry:** hiển thị lịch sử bản hướng dẫn và kiểm tra cập nhật qua quy trình kiểm soát thay đổi; không tự động đổi rules cho nghiên cứu đã khóa.
9. **Import templates for Phoenix/LIMS**, dữ liệu `PKNCA`, các CSV/Excel kiểu CRO thông dụng; không áp dụng map tự động nếu có cột mơ hồ.
10. **Structured export (giai đoạn 3):** hỗ trợ dataset metadata, SDTM/ADaM mappings theo yêu cầu áp dụng, thay vì tuyên bố một file CSV là hồ sơ eCTD hợp lệ.

## 14. Kế hoạch thi công bắt buộc cho Codex

### Sprint 0 — Khảo sát và khóa đặc tả

- Nếu repository tồn tại: **khảo sát đầy đủ** trước khi sửa; không đập bỏ code/dữ liệu còn dùng. Nếu chưa có: tạo repo mới theo cấu trúc trên.
- Soạn `docs/REGULATORY_MATRIX.md`: từng profile → guideline → scope → endpoint → design → logic → acceptance → citations → tình trạng xác minh.
- Soạn `docs/ALGORITHM_SPEC.md`: công thức, variants, input assumptions, data handling, statistical model, output, lý do loại trừ.
- Soạn `docs/VALIDATION_PLAN.md`: golden references, fixtures, tolerances, CI, release criteria.
- Nhận diện mọi chỗ **chưa có quy định/benchmark đủ chắc chắn** và đánh dấu chưa hỗ trợ thay vì tự làm đại.

### Sprint 1 — MVP có thể kiểm tra được

- Database, project lifecycle, giao diện tiếng Việt, tạo thiết kế 2×2 & parallel, randomization, ABE power/cỡ mẫu.
- Nhập Excel/CSV + mapping + QC + data correction + snapshot.
- NCA single dose, ABE đúng thiết kế, đồ thị, report draft Word/PDF, archive reload.
- Đầy đủ unit/integration tests và fixture gold references cho phần đã phát hành.

### Sprint 2 — EMA ABEL và FDA RSABE

- Partial/full replicate data/model, power simulation, CVwR, criteria theo EMA và FDA 2026, test từng nhánh.
- Nhận diện `HVDP` đủ điều kiện, enforce prespecification và guideline scope.
- Benchmark với code kết quả tham chiếu độc lập, thêm audit trung gian để biostatistician rà soát.
- Report EMA/FDA comparison và validation evidence.

### Sprint 3 — Hồ sơ CTD và vận hành tin cậy

- Mẫu CSR E3, Module 2.7.1, Module 5.3.1.2, template EMA Appendix IV, manifest/hashes, print checks.
- Roles/audit, reviewer workflow, backups/restore, hệ thống chỉ báo chưa được thẩm định, traceability matrix, tài liệu triển khai.
- Chỉ sau khi đủ validation và chuyên gia phê duyệt mới bật `Submission package draft approved by reviewer`; eCTD assembly độc lập thuộc phạm vi khác.

### Sprint 4 — Tính năng tùy chọn

- Steady-state, NTI, MR/product-specific, partial AUC theo sản phẩm, multi-group, data standards, LIMS API, advanced sensitivity. Mỗi hạng mục phải có rule/spec/benchmark trước khi mở.

## 15. Definition of Done — không được bỏ qua

- [ ] Giao diện **hoàn toàn bằng tiếng Việt** và không còn text tiếng Anh lẫn lộn ngoài thuật ngữ kỹ thuật cần thiết.
- [ ] Có workflow 4 bước chính và các bước QC/approval ở giữa; dữ liệu thật và demo tách biệt.
- [ ] Thiết kế 2×2, parallel, partial/full replicate tạo randomization đúng và có metadata tái lập.
- [ ] Tính sample size/power mô tả rõ CVw/CVb, expected GMR, alpha, endpoint, assumptions và mức độ kiểm chứng.
- [ ] Import concentration có actual sampling time, BLQ, LLOQ, đơn vị, provenance và không tự trung bình dữ liệu trùng.
- [ ] NCA đủ thông số, biểu đồ và chẩn đoán, test gold standard.
- [ ] ABE theo mô hình nghiên cứu; EMA ABEL và FDA RSABE **không dùng sai phép thử của nhau**; mỗi endpoint có quyết định độc lập.
- [ ] Phân tích thất bại/không đủ dữ liệu được trả `NOT EVALUABLE`, không tạo PASS mặc định.
- [ ] Report Word/PDF chuẩn trình bày, CTD **draft** có danh mục dữ liệu phụ trợ, citation, audit và rõ trạng thái phê duyệt.
- [ ] 1 file `.beproject.zip` lưu được toàn bộ dữ liệu, thiết kế, config, kết quả, provenance và mở lại không cần chạy lại.
- [ ] Tests chạy độc lập trên máy sạch, fixtures trong repo, CI xanh; benchmark thống kê đối chiếu nguồn độc lập đạt.
- [ ] README gồm hướng dẫn cài, chạy, backup, nạp ví dụ synthetic, luồng làm việc, giới hạn, cách đóng gói; tài liệu algorithm và regulatory matrix có links.
- [ ] Không có seed/demo/example mặc định tạo báo cáo PASS chắc chắn; không tuyên bố regulatory/GxP compliance khi chưa có validation.

## 16. Cách Codex phải thực hiện và phản hồi

1. **Bắt đầu triển khai** theo sprint và ưu tiên tính đúng đắn của NCA/BE hơn giao diện bắt mắt. Nếu không thể hoàn tất tất cả trong một lượt, giao phần **thực sự chạy được, có kiểm thử**, và đưa backlog chính xác; không giả báo cáo hoàn thành.
2. Trước mỗi phương pháp mới, lập `source-to-algorithm` traceability và tìm/kiểm tra golden result. Không viết phép kiểm định RSABE/ABEL trên suy đoán.
3. Mỗi thay đổi có test ở đúng boundary (import, NCA, statistical engine, archive, UI, report). Không sửa số liệu đầu vào để ép test pass.
4. Chạy test suite, cung cấp kết quả lệnh, số test pass/fail/skip, lỗi còn lại, commit hash nếu có và file changed. Không tự động push remote khi chưa có quyền/ủy quyền rõ.
5. Khi hoàn thành một sprint, trình bày: **đã làm**, **đã kiểm chứng**, **giới hạn**, **rủi ro regulatory**, **bước tiếp theo**.

---

## 17. Nguồn văn bản chính thức để Codex mở và xác minh

> **Lưu ý:** đây là các nguồn chính được kiểm tra khi soạn đặc tả (29/10/2026), không phải toàn bộ văn bản cần dùng; hãy tiếp tục kiểm tra product-specific guidances và quy định theo từng nghiên cứu. Nếu nguồn thay đổi, khóa bản áp dụng và nêu thay đổi bằng `RegulatoryRuleSet` mới.

1. **ICH M13A — EMA, current effective 25/01/2025:** https://www.ema.europa.eu/en/scientific-guidelines/ich-guideline-m13a-bioequivalence-immediate-release-solid-oral-dosage-forms
2. **ICH M13A — FDA final October 2024:** https://www.fda.gov/regulatory-information/search-fda-guidance-documents/m13a-bioequivalence-immediate-release-solid-oral-dosage-forms
3. **EMA Guideline on the Investigation of Bioequivalence — phần còn áp dụng, replicate/ABEL:** https://www.ema.europa.eu/en/scientific-guidelines/investigation-bioequivalence
4. **EMA — Considerations regarding implementation of ICH M13A (2025):** https://www.ema.europa.eu/en/documents/scientific-guideline/considerations-regarding-implementation-ich-m13a-bioequivalence-immediate-release-solid-oral-dosage-forms_en.pdf
5. **FDA — Statistical Approaches to Establishing Bioequivalence, FINAL May 2026:** https://www.fda.gov/regulatory-information/search-fda-guidance-documents/statistical-approaches-establishing-bioequivalence
6. **FDA — Statistical Approaches full PDF, Appendix F (NTI) & G (HVD):** https://www.fda.gov/media/163638/download
7. **FDA — Bioequivalence Studies With PK Endpoints for Drugs Submitted Under an ANDA, FINAL May 2026:** https://www.fda.gov/regulatory-information/search-fda-guidance-documents/bioequivalence-studies-pharmacokinetic-endpoints-drugs-submitted-under-abbreviated-new-drug
8. **FDA — PK Endpoint full PDF (May 2026):** https://www.fda.gov/media/192774/download
9. **FDA Product-Specific Guidances:** https://www.fda.gov/drugs/guidances-drugs/product-specific-guidances-generic-drug-development
10. **ICH M10 — bioanalytical method validation, EMA:** https://www.ema.europa.eu/en/scientific-guidelines/ich-m10-bioanalytical-method-validation
11. **ICH E3 — Clinical Study Reports:** https://www.ema.europa.eu/en/scientific-guidelines/ich-e3-structure-content-clinical-study-reports
12. **ICH M4E(R2) — Common Technical Document (Efficacy):** https://database.ich.org/sites/default/files/M4E_R2__Guideline.pdf
13. **EMA Appendix IV — Module 2.7.1 presentation tables:** https://www.ema.europa.eu/en/scientific-guidelines/appendix-iv-guideline-investigation-bioequivalence-presentation-biopharmaceutical-bioanalytical-data-module-271
14. **FDA eCTD và thông số kỹ thuật hiện hành:** https://www.fda.gov/drugs/electronic-regulatory-submission-and-review/electronic-common-technical-document-ectd
15. **FDA eCTD v4.0 standards:** https://www.fda.gov/drugs/electronic-regulatory-submission-and-review/ectd-submission-standards-ectd-v40-and-regional-m1
16. **FDA Data Integrity for In Vivo BA/BE Studies (draft April 2024; không trích như final):** https://www.fda.gov/regulatory-information/search-fda-guidance-documents/data-integrity-in-vivo-bioavailability-and-bioequivalence-studies

**Chỉ thị kết thúc:** Hãy viết phần mềm dựa trên đặc tả này với các phép tính có thể tái lập, có bằng chứng đối chiếu và có nguồn quy định rõ ràng. Mục tiêu là công cụ phân tích BE nghiêm túc phục vụ phát triển hồ sơ, **không phải giao diện tạo kết luận PASS từ dữ liệu giả hoặc kết luận tự suy diễn**.
