# Phân tích dược động học và tương đương sinh học

Ứng dụng **độc lập**, xử lý NCA và BE bằng Python/Streamlit, hoạt động offline sau khi cài môi trường.
Người dùng nhập dữ liệu nồng độ hoặc bảng PK, khai báo protocol/SAP, kiểm tra QC và Data Freeze,
chạy phân tích rồi xuất Excel/Word/PDF. Không cần cài đặt, kết nối hoặc nhập file kết quả từ
phần mềm dược động học thương mại. Các nhánh đánh giá theo FDA/EMA vẫn phụ thuộc phạm vi
phương pháp đã kiểm chứng và hồ sơ nghiên cứu; phần mềm chưa được thẩm định pháp quy.

**Điều hướng bên trái:** Chọn một trong ba luồng **Phân tích PK độc lập**
(phân tích dược động học không cần dự án BE), **BE nhanh** (dán/tải dữ liệu
để tính NCA và BE trực tiếp), hoặc **BE đầy đủ** (quy trình nghiên cứu có
quản lý dự án và kiểm soát dữ liệu). Khi chọn **BE đầy đủ**, mục **Các bước BE đầy đủ**
hiển thị 10 bước từ **Tổng quan / Quản lý nghiên cứu** đến
**Nhật ký kiểm toán / Quản trị**. Bước BE đang chọn được lưu khi chuyển sang
PK độc lập hoặc BE nhanh và quay lại.

Phạm vi tính toán, mức kiểm chứng và các giới hạn được tổng hợp trong
[ma trận capability](docs/CAPABILITY_MATRIX.md). Các sửa đổi từ audit ngày 05/11/2026,
kiểm thử hồi quy và hạng mục chờ nghiệm thu được ghi tại
[tiến độ cải tiến](docs/IMPLEMENTATION_PROGRESS_20261105_VI.md).

**BE nhanh — phân tích độc lập (02/11/2026):** Chọn **BE nhanh — phân tích độc lập**
trên thanh điều hướng khi đã có dữ liệu PK và muốn kiểm tra BE ngay, không cần tạo
dự án, phân nhóm ngẫu nhiên, QC, freeze hoặc đi hết các bước nghiên cứu.
Tải CSV/XLSX hoặc dán bảng từ Excel, kiểm tra mapping Subject/Sequence/Period/Treatment,
nhãn T/R và chuỗi Sequence, chọn thiết kế/quy tắc rồi bấm **Chạy phân tích BE nhanh**.
Nếu có **Cplasma**, bảng phải có thêm **Time (giờ)** để tính NCA trước khi đánh giá BE;
nếu đã tính PK, dùng **Cmax/AUClast/AUCinf** (thang raw/ln/log10 được khai báo).
Hỗ trợ 2×2, song song, partial/full replicate theo phạm vi engine hiện có.
Kết quả hiển thị GMR, CI90%, CV, cảnh báo, và có thể tải Excel kèm dữ liệu nguồn,
NCA và cấu hình/hàm băm SHA-256. Thiếu kỳ, thiếu thời điểm 0 hoặc endpoint không hợp lệ
sẽ bị chặn đánh giá, không tự bù dữ liệu hoặc bỏ subject. Kết quả chỉ ở trạng thái
**DRAFT / REVIEW**, chưa được thẩm định để sử dụng làm kết luận pháp quy.

**Phân hệ mới — Phân tích PK độc lập:** Trên thanh điều hướng chọn **Phân tích PK độc lập**
để tải hoặc nhập trực tiếp bảng Cplasma, chạy NCA và khớp mô hình 1–2 ngăn cho
đường uống, IV bolus hoặc IV infusion, kể cả khi chưa có dự án BE. Có chế độ đơn liều,
đa liều cách đều và tính thông số khoảng liều tại steady-state khi được xác nhận. Giao diện tiếng Việt,
có đồ thị tuyến tính/bán log, phần dư, xuất Excel/Word/PDF/JSON và lưu lịch sử SQLite
riêng; thông số phụ thuộc liều chỉ tính khi đủ metadata và AUC thích hợp theo chế độ. Xem
[hướng dẫn, công thức và giới hạn](docs/PK_STANDALONE_VI.md).

Engine BE cung cấp mô hình REML/Satterthwaite, EMA Method A/ABEL/NTI và FDA Appendix F/G
trong phạm vi thiết kế đã hỗ trợ. Giao diện gồm bảng reviewer/population, chẩn đoán phần dư,
rà soát pha terminal, mapping PK raw/Ln/log10 và báo cáo Word/PDF. Xem
[ma trận phương pháp và mức xác nhận](docs/CAPABILITY_MATRIX.md).

Ở 0.3.1, FDA replicate standard, FDA NTI và HVD sWR <0.294 trả **NOT EVALUABLE**
khi conventional mixed ABE chưa được qualification; CI từ I contrasts giữ để chẩn đoán.
[Chi tiết gate và ảnh hưởng snapshot cũ](docs/CONVENTIONAL_ABE_GATE.md).
Mô hình REML full4 thử nghiệm có [audit độc lập](docs/REPLICATE_ABE_EXPERIMENTAL_VALIDATION.md),
chưa được nối vào quyết định. Gỡ file PK khỏi uploader làm kết quả cũ STALE và khóa tải.

Kết quả NCA có 41 thông số, đồ thị hồi quy pha terminal và tệp Excel nhiều bảng.
Công thức và giả định được mô tả tại [đặc tả thuật toán](docs/ALGORITHM_SPEC.md).

**Kiểm thử hồi quy nội bộ:** Các bộ dữ liệu đối chiếu với kết quả phần mềm khác
được lưu trong `tests/fixtures` và `tests/legacy_benchmarks`
và các tài liệu kiểm chứng lịch sử để phục vụ nghiên cứu QA. Chúng không thuộc
giao diện ứng dụng và không phải điều kiện để chạy NCA/BE.

Bản phát triển 0.3.1 từ `CODEX_SPEC_BE_EMA_FDA_VI.md`. Engine khoa học độc lập với
Streamlit, phân tích offline. Đã triển khai nền tảng Sprint 0–1; chưa hoàn thành toàn bộ đặc tả.
Ưu tiên tính đúng và khả năng tái lập: phương pháp chưa benchmark bị khóa, không tự tạo PASS.

**Cập nhật cải tiến và QA ngày 31/10/2026:** Planning bị ràng buộc bởi rule, design, endpoint, biên, NTI-Cmax và fingerprint; planning EMA NTI chưa có oracle độc lập được khóa rõ ràng. Capability phân biệt tính toán, kết luận, planning và qualification. Dự án có mục đích dữ liệu (`real_study`, `training_qa`, `unknown`...) và provenance, dữ liệu synthetic/QA luôn bị chặn kết luận cấp nghiên cứu. Tổng quan có tiến độ tám bước; BE phân biệt phân tích PK độc lập với snapshot nghiên cứu; báo cáo Word/PDF song ngữ diễn giải phương pháp và ghi rõ trạng thái DRAFT. Xem [kế hoạch và trạng thái](docs/IMPROVEMENT_PLAN_20261031_VI.md), [báo cáo UAT baseline](docs/USER_ACCEPTANCE_REVIEW_20261031_VI.md).

**Mẫu báo cáo BE chi tiết (01/11/2026):** Trang **Báo cáo** có nút **Tải mẫu Word đầy đủ (chưa cần phân tích)**, chọn tiếng Việt hoặc tiếng Anh. Mẫu có 11 chương, heading nhiều cấp, sáu bảng phụ lục để điền, các mục lâm sàng, dược động học, phân tích mẫu sinh học, Data Integrity/ALCOA+, SAP, QA, nguồn tài liệu, truy xuất và chữ ký. Phần thống kê phân biệt ABE/TOST, EMA HVDP (ABEL), FDA HVD (RSABE), EMA NTI, FDA NTI và ABE thiết kế replicate. Khi đã chạy phân tích, tải **Word/PDF báo cáo** để nhận đề mục cùng kết quả theo snapshot và các bảng reviewer. Cấu trúc dựa trên `Bioequivalence_Study_Reporting_Format.pdf` do người dùng cung cấp (ASEAN ACCSQ PPWG, tài liệu lịch sử); cần đối chiếu guideline hiện hành, quy định riêng theo sản phẩm và hồ sơ nguồn trước khi sử dụng chính thức. Các ô chưa có bằng chứng hiển thị **CHƯA CUNG CẤP / NOT PROVIDED**; đây là **bản nháp giảng dạy và biên soạn**, chưa phải báo cáo nghiên cứu đã được thẩm định hoặc ký duyệt.

**Xuất đề cương nghiên cứu (01/11/2026):** Trong trang **Báo cáo**, mở **Đề cương nghiên cứu BE · Xuất Word / PDF**. Điền 11 nhóm thông tin: cơ sở khoa học, đối tượng, cỡ mẫu, washout, lấy mẫu, sử dụng thuốc, phân tích mẫu sinh học, an toàn, đạo đức, SAP và quản lý dữ liệu; chọn **Tạo đề cương Word và PDF**, sau đó tải `.docx` hoặc `.pdf`. Có thể thực hiện trước khi nhập nồng độ hoặc phân tích NCA/BE. Phần mềm lấy thiết kế, sản phẩm thử/đối chứng, lịch nghiên cứu từ **Tổng quan** và chỉ điền cỡ mẫu tính toán khi giả định còn hiệu lực. Đề cương tiếng Việt có 15 chương, hướng dẫn riêng cho ABE/EMA ABEL/FDA RSABE/NTI/replicate, ghi rõ nơi thiếu thông tin và trạng thái **DỰ THẢO — CHƯA ĐƯỢC PHÊ DUYỆT**. Khi sửa ghi chú, phải tạo lại tệp; ghi chú lưu cùng dự án, tệp đề cương chỉ được chuẩn bị để tải theo yêu cầu.

**Mẫu báo cáo PK độc lập nâng cấp (02/11/2026):** Word/PDF từ trang **Phân tích PK độc lập** nay có 9 chương tiếng Việt, bảng tóm tắt NCA và mô hình ngăn, đồ thị thực từ nồng độ–thời gian (tuyến tính/bán log/phần dư), thông tin BLQ, cảnh báo và SHA-256. Word dùng **Heading 1/2**, trường mục lục TOC (mở Word, **Ctrl+A, F9** để cập nhật); PDF có mục lục dàn trang tự động. Bố cục tham khảo ICH E3 và báo cáo đánh giá công khai FDA/EMA, không hàm ý đã được cơ quan quản lý thẩm định. Xem [hướng dẫn PK độc lập](docs/PK_STANDALONE_VI.md).

Bằng chứng synthetic QA được tạo bởi `scripts/qa_user_scenarios_20261031.py` và kiểm tra bởi `scripts/qa_verify_20261031.py`. Browser smoke `scripts/browser_smoke_cdp.cjs` dùng DB/cổng QA riêng. [Manifest triển khai mới](output/qa_20261031/improvement_evidence_20261031.json) liên kết lockfile, scenario expected/actual, kết quả pytest, ảnh browser và báo cáo draft vi/en với SHA-256; reviewer vẫn đang chờ ký và đây **không phải** regulatory validation. Manifest gốc `evidence_manifest.json` là quan sát lịch sử trước khi chặn lỗi planning NTI, được giữ nguyên để truy vết. Visual QA của DOCX và kiểm thử browser upload/download đầy đủ còn mở.

## Cài đặt và chạy

Python 3.11–3.13 (mặc định 3.12); khuyến nghị dùng [uv](https://docs.astral.sh/uv/).
Từ thư mục dự án:

```powershell
uv sync --locked --extra dev
uv run --frozen streamlit run app.py
```

Trên Windows, có thể chạy trực tiếp `run_app.cmd` (hoặc `.\run_app.cmd` trong PowerShell).
File này luôn dùng `.venv\Scripts\python.exe`, tránh vô tình gọi Streamlit từ Python 3.10 toàn máy.
Nếu đã có lỗi ở cửa sổ chạy cũ, dừng bằng Ctrl+C rồi khởi chạy lại qua file này.
Ứng dụng sẽ hiển thị hướng dẫn chọn đúng môi trường nếu Python/Streamlit không khớp bản đã khóa.

Trình duyệt mở địa chỉ local `http://localhost:8501`. Cấu hình chỉ bind `127.0.0.1`.
Không triển khai qua mạng nhiều người khi chưa có authentication và kiểm soát hệ thống.
Nếu không có uv, dùng venv và `python -m pip install -e ".[dev]"`; cách này không khóa
dependency transitive như `uv.lock`. Không cần internet để phân tích sau khi đã cài.

PDF tiếng Việt cần Arial trên Windows hoặc DejaVuSans trên Linux. Word dùng Arial.

## Luồng thao tác

**Trợ giúp phục vụ giảng dạy:** Bật hoặc tắt công tắc **Trợ giúp bên phải**
ở phía trên nội dung để mở/ẩn khung hướng dẫn theo trang đang làm việc.
Mỗi trang có giải thích các thành phần giao diện, thao tác, lý thuyết và công thức,
thuật ngữ, nguồn quy định chính thức và câu hỏi tự kiểm tra. Phần **Tìm hiểu profile**
tự theo bộ quy tắc đang chọn hoặc cho phép xem riêng các phương pháp ABE, replicate,
EMA ABEL, FDA RSABE và NTI. Chọn profile trong Trợ giúp chỉ thay nội dung học,
không sửa dữ liệu hoặc kết quả phân tích.

**Thông tin giảng dạy:** Ở đầu vùng làm việc bên trái có nhóm ô nhập có thể thu gọn
gồm **Tên trường** (mặc định Trường Đại học Dược Hà Nội), **Tên Khoa**
(Bào chế và Công nghệ dược phẩm), **Tên giảng viên** (Nguyễn Trần Linh),
**Tên Học viên**, **Tên lớp** và **Khoá** (ba ô cuối để trống).
Các giá trị giữ nguyên khi đổi trang hoặc bật/tắt Trợ giúp trong cùng phiên học;
chưa lưu vào dự án hay xuất ra báo cáo.

1. **Tổng quan**: tạo nghiên cứu, protocol/SAP có phiên bản, phạm vi guideline/PSG và bằng chứng.
   Chọn tình huống học thử và bấm **Điền dữ liệu mẫu vào biểu mẫu nghiên cứu** để điền các ô hiện có;
   rà soát/chỉnh sửa rồi tự bấm **Tạo nghiên cứu**. Có nút **Làm trống biểu mẫu nghiên cứu** để quay lại nhập dữ liệu thật.
2. **Thiết kế**: nhập CV theo phần trăm rõ đơn vị, GMR riêng AUC/Cmax, power/dropout và nguồn giả định.
   2×2 dùng CVw, parallel dùng CV total giữa người. Chọn n lớn nhất trong các endpoint;
   đây chưa phải power đồng thời của nghiên cứu.
3. **Ngẫu nhiên hóa**: cân bằng sequence theo block, seed lưu trong project. Xuất Excel và lịch planned.
   Actual dose/sample time luôn do nghiên cứu thực tế cung cấp.
4. **Nhập dữ liệu**: CSV UTF-8/XLSX dạng long theo file mẫu; mapping đổi tên cột;
   timestamps phải có offset, ví dụ `2026-09-01T08:00:00+08:00`.
   Sau khi chọn tệp, bấm **Kiểm tra cấu trúc và QC** để xem 16 cột bắt buộc,
   cột thiếu/trùng, lỗi theo dòng và cảnh báo. Chỉ có thể **Nhập và lưu raw bất biến**
   khi có phân nhóm và kiểm tra không còn lỗi chặn. Nếu đổi tệp, mapping hoặc xác nhận
   chuyển đơn vị, phải kiểm tra lại. Bảng trước và sau nhập hiển thị đủ dòng,
   có bộ lọc theo người tình nguyện/kỳ và xuất CSV phần đang xem.
5. **QC**: xử lý lỗi chặn bằng correction có bằng chứng và người rà soát; raw giữ nguyên.
   Missing/reassay/predose không được tự xóa để đạt BE. Khóa dữ liệu và SAP sau rà soát.
6. **NCA**: cấu hình trước khóa; chạy **Phân tích NCA và BE**. Xem terminal diagnostics và warnings.
7. **Thống kê BE**: xem từng endpoint, TOST, df/SE/MSE, rule snapshot và lịch sử revision.
   GMR/CI hiển thị dạng tỷ lệ. Không diễn giải p treatment hoặc power là BE.
8. **Báo cáo**: Word/PDF tiếng Việt/Anh ở trạng thái DRAFT; datasets/audit và `.bewf.zip`.
   Báo cáo đã tạo được lưu cùng dự án và có trong archive tải xuống sau đó.

### Học thử bằng dữ liệu tổng hợp

Năm vị trí có nút điền dữ liệu mẫu: **Tổng quan** (6 thiết kế/ngữ cảnh nghiên cứu),
**Nhập dữ liệu nồng độ** (9 tình huống QC), **BE nhanh** (9 tình huống),
**Thống kê BE → bảng PK độc lập** (7 tình huống) và **Phân tích PK độc lập**
(7 tình huống). Nút demo chỉ nạp nguồn vào **chính các ô nhập hoặc bảng đang dùng cho dữ liệu thật**;
người học có thể sửa ô, áp dụng bảng, xác nhận mapping/đơn vị rồi chủ động chạy các bước tiếp theo.
Không tự tạo nghiên cứu, nhập raw, chạy QC, phân tích hoặc lưu kết quả khi bấm nạp demo.

Với luồng **BE đầy đủ**, tạo nghiên cứu có đánh dấu mục đích `training_qa`, lập và lưu phân nhóm,
rồi đến trang nhập nồng độ chọn tình huống. Nút nạp nồng độ chỉ hoạt động trong nghiên cứu demo đã có
phân nhóm; dữ liệu giả lập không được nạp nhầm vào dự án thực. Sau khi sửa/áp dụng bảng, bấm
**Kiểm tra cấu trúc và QC**, xử lý lỗi nếu cần rồi **Nhập và lưu raw bất biến** theo quy trình chuẩn.
BE nhanh và PK độc lập có thể thực hành trực tiếp mà không cần tạo nghiên cứu.
Tất cả kết quả tổng hợp chỉ dùng cho đào tạo/QA; cấp nghiên cứu không được kết luận PASS từ demo.

Xem [hướng dẫn học thử theo tình huống](docs/DEMO_LEARNING_GUIDE_VI.md) để chọn bài tập
BE chuẩn, replicate/HVD/NTI, dữ liệu thiếu, BLQ, mẫu trùng và chuyển đơn vị.

## Thuật toán và kiểm chứng

- Exact numerical **joint TOST power** bằng tích phân conditional normal/chi-square;
  đối chiếu PowerTOST 2×2 và parallel. Không dùng z approximation làm power chính xác.
- NCA actual time, linear hoặc linear-up/log-down, BLQ=0 theo M13A,
  AUC last kết thúc ở mẫu cuối định lượng. Lambda-z yêu cầu ≥3 điểm sau Tmax và QC cấu hình.
- ABE 2×2 đủ kỳ: subject/sequence/period/treatment qua within-subject contrast đã khử subject,
  đúng SE/df cho imbalance. Đối chiếu gói R BE và mô hình OLS đầy đủ độc lập.
- Parallel: pooled hoặc Welch theo SAP, đối chiếu statsmodels TOST độc lập.
- Study PASS cần tất cả primary endpoints PASS, minimum N và phạm vi hợp lệ.
  Dữ liệu demo luôn NOT EVALUABLE cấp study; kết quả toán học endpoint vẫn hiện để học thử.

```powershell
uv run --frozen pytest -q
uv run --frozen ruff check .
uv run --frozen mypy be_app
uv run --frozen python scripts/benchmark.py
uv run --frozen pip-audit -r requirements.lock --require-hashes
```

Golden fixtures tự chứa trong `tests/fixtures`; không cần R, pyreadr hoặc mạng khi test.
File `BE_NCAResult4BE.csv` là dữ liệu tham chiếu công khai, **không phải demo hoặc dữ liệu nghiên cứu của người dùng**;
nguồn và hash binary gốc trong provenance JSON. Script fetch chỉ phục vụ tái thu thập fixture,
cần requests/pyreadr, không thuộc pipeline phân tích.

## Lưu và phục hồi

SQLite: `data/projects.sqlite`; mỗi thao tác lưu snapshot mới có checksum, triggers chặn UPDATE/DELETE
qua ứng dụng. Truy cập file DB trực tiếp không được bảo vệ bằng các triggers; hash không phải chữ ký số.
Không lưu tên/ngày sinh hoặc thông tin định danh cá nhân trong dữ liệu nhập.

Mỗi luồng dùng một kiểu file project ZIP: PK độc lập (`.pk.zip`), BE nhanh (`.be.zip`),
BE đầy đủ (`.bewf.zip`). Khi mở project, ứng dụng kiểm tra đuôi file và định dạng nội dung.

Tải `.bewf.zip` sau các thay đổi quan trọng và lưu ở vị trí backup được kiểm soát. File chứa
raw base64 bất biến, correction, phân nhóm, cấu hình, kết quả, rule snapshot, audit và các báo cáo đã tạo.
Mở lại không refit. Import kiểm tra schema/checksum, file lạ, giới hạn nén và path traversal;
không deserialize pickle. Checksum phát hiện lỗi, không chứng minh nguồn đáng tin cậy.
API `ProjectStore.backup(path)` dùng SQLite backup API khi DB đang mở.

Để phục hồi DB, dừng app, bảo quản bản hiện tại và dùng bản backup đã kiểm chứng;
hoặc mở archive trong trang Tổng quan. Không chỉnh DB trực tiếp để sửa dữ liệu.

## Giới hạn

Replicate hiện hỗ trợ TRR/RTR/RRT và TRTR/RTRT đủ kỳ; missing replicate chưa được mở.
REML quan sát sẵn có trong 2×2 cần căn cứ SAP và kiểm tra population riêng theo cơ quan quản lý.
Phân hệ BE chưa hỗ trợ MR/steady-state/partial AUC; phân hệ PK độc lập đã hỗ trợ
phân tích đa liều và các thông số khoảng liều ở trạng thái ổn định khi được xác nhận.
Chưa có authentication/RBAC hoặc gói CTD hoàn chỉnh. Reports chỉ là khung tóm tắt DRAFT, không có chữ ký giả,
không là sequence eCTD và chưa xác nhận đã QA layout DOCX.
Không tuyên bố EMA/FDA validated, GxP hoặc 21 CFR Part 11 compliant.

Chi tiết: [thuật toán](docs/ALGORITHM_SPEC.md), [quy định](docs/REGULATORY_MATRIX.md),
[validation](docs/VALIDATION_PLAN.md), [backlog](docs/BACKLOG.md).

## Trạng thái dữ liệu và hiệu năng cập nhật ngày 30/10/2026

Các ô số/text được giữ độc lập với widget khi xác nhận bằng Enter hoặc rời ô.
CV/GMR thiết kế tự lưu vào domain; chỉ bấm **Tính cỡ mẫu và power** mới tính lại.
Các nhóm cấu hình có nhãn bản nháp: cần bấm Áp dụng/Lưu trước khi đổi đầu vào phân tích.
Bản nháp vẫn được giữ khi đổi trang, lưu project, hoặc mở lại từ SQLite/archive.

Trang QC có editor theo subject/kỳ và `sample_id` cố định. Sửa nhiều ô tạo **Chưa áp dụng**;
điền lý do, người rà soát, bằng chứng rồi chọn **Áp dụng các sửa đổi**. Không tự lấy trung bình,
thêm/xóa hàng hoặc sửa raw. Dữ liệu đã khóa cần **Tạo revision để sửa dữ liệu** trước correction.
Kiểm tra QC theo nút; kết quả QC được tái dùng, không quét toàn dữ liệu khi sửa field/đổi trang.

Trang NCA/BE/đồ thị và báo cáo hiển thị revision/fingerprint của snapshot thực tính.
Có input hoặc pending ảnh hưởng kết quả thì nhãn **STALE** xuất hiện và Word/PDF/datasets bị chặn
cho đến khi xử lý bản nháp và tính lại. Có thể xem bảng đầu vào thực sự dùng để đối chiếu.
Word/PDF, datasets và archive chỉ chuẩn bị khi chọn nút tương ứng.

Các thay đổi nhỏ ghi journal SQLite theo transaction, không ghi toàn dataset mỗi lần gõ.
**Lưu checkpoint dự án** lưu snapshot đầy đủ; mở lại dự án sẽ replay journal chưa checkpoint.
Khởi tạo chưa hoàn tất cũng có dự án DRAFT với mã phục hồi để mở lại sau reload.
Đừng đóng browser khi chữ còn trong bộ gõ chưa được Enter/blur gửi lên server.

Archive schema 1 được chuyển có kiểm soát sang schema 2; kết quả cũ thiếu revision được đánh dấu
LEGACY và cần tính lại. Schema chưa biết bị từ chối. Hai session sửa cùng dự án có optimistic conflict,
không ghi đè ngầm; bản local vẫn chưa có authentication/RBAC.

Xem [audit trước sửa](docs/STATE_AUDIT.md) và [nghiệm thu state/hiệu năng](docs/STATE_CONSISTENCY_RESULTS.md).

## Audit và bằng chứng triển khai 05/11/2026

Các sửa đổi A01–A11, kết quả kiểm thử, benchmark Python và giới hạn nghiệm thu được ghi tại
[báo cáo tiến độ](docs/IMPLEMENTATION_PROGRESS_20261105_VI.md). Ma trận hỗ trợ tính toán
được sinh từ registry tại [CAPABILITY_MATRIX](docs/CAPABILITY_MATRIX.md).

Chạy kiểm tra trong môi trường phát triển bằng `.venv\Scripts\python.exe -m pytest -q`,
`.venv\Scripts\ruff.exe check be_app tests scripts`, `.venv\Scripts\mypy.exe be_app`
và `.venv\Scripts\python.exe scripts/benchmark.py`. Công cụ benchmark tải tổng hợp:

```powershell
.venv\Scripts\python.exe scripts/performance_audit.py --sizes 12,60,240 --report-sizes 12,60 --output output\implementation_20261105\performance_audit.json
```

Benchmark chỉ đo phần Python và tạo artifact trên dữ liệu mô phỏng; kiểm thử giao diện qua browser,
đối chiếu PK/BE độc lập và nghiệm thu nội dung/bố cục báo cáo vẫn là các cổng riêng.
