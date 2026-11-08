# Audit và kế hoạch cải tiến BE Analysis Workbench

Ngày hoàn tất: 05/11/2026, Australia/Perth. Phiên bản khai báo: 0.3.1.

## 1. Kết luận và phạm vi

App có nền tảng tốt: engine tách khỏi Streamlit, fixtures đối chiếu độc lập, snapshot có checksum, raw bất biến, kiểm soát kết quả STALE và gate cho phương pháp replicate chưa qualification. Tuy nhiên, cần ưu tiên sửa tính nhất quán kết quả, phục hồi dự án và NCA truyền IV trước khi mở rộng tính năng.

Audit này kiểm tra mã nguồn của ba luồng PK độc lập, BE nhanh và BE đầy đủ; đọc kiểm thử, CI và tài liệu; chạy lint, type checking, benchmark và các tái hiện có kiểm soát. Không thay đổi mã nghiệp vụ hoặc cơ sở dữ liệu nghiên cứu. Chỉ tạo báo cáo và bằng chứng trong `output/audit_20261104/` (tên thư mục theo ngày bắt đầu).

Đây là audit kỹ thuật về hành vi phần mềm, không phải xác nhận tuân thủ hướng dẫn pháp quy hoặc qualification khoa học toàn bộ engine. Không thực hiện UAT trực quan bằng trình duyệt, render toàn bộ Word/PDF, kiểm toán dependency trực tuyến hay đo tải nhiều người dùng trong lần này. Các đề xuất UX là từ mã luồng và kiểm thử, chưa phải kết quả quan sát người dùng.

Mức ưu tiên: **P1** cần sửa trước mốc nghiệm thu tiếp theo do nguy cơ sai kết quả/nhầm dữ liệu; **P2** sửa trong vòng ổn định hóa kế tiếp; **P3** cải tiến bảo trì và trải nghiệm. Không gán P0 khi chưa có bằng chứng cho sự cố nghiêm trọng đang xảy ra.

## 2. Bằng chứng kiểm tra

| Kiểm tra | Kết quả | Giới hạn |
|---|---|---|
| Ruff | All checks passed | Không chứng minh tính đúng nghiệp vụ |
| Mypy | Không lỗi trong 43 source files | Theo cấu hình hiện tại, không phải strict toàn bộ |
| `scripts/benchmark.py` | 19/19 đạt | Chỉ những fixture và chỉ số trong script này |
| Pytest lần đầu | 350 passed, 3 failed, 37 errors; 390 test | Lỗi quyền truy cập thư mục tạm trong sandbox ảnh hưởng setup và AppTest; không quy các lỗi này thành lỗi app |
| Tái hiện cache BE nhanh | Khóa cache giống nhau khi Cmax và bảng CI thay đổi | Xác minh khóa và dữ liệu bảng bằng Python, chưa chạy click-through trình duyệt |
| Tái hiện truyền IV, cấu hình BE | Đã lưu số liệu | Xem `scientific_repro.json` |
| Tái hiện xuất Excel PK và fingerprint | Đã lưu kiểu ô công thức và va chạm fingerprint | Xem `integrity_repro.json` |

Bằng chứng: `output/audit_20261104/test-results.xml`, `benchmark_results.csv`, `cache_repro.json`, `scientific_repro.json`, `integrity_repro.json`. Các lần chạy lại với thư mục tạm trong workspace được ghi trạng thái ở mục 7; không được gọi toàn bộ suite là đạt khi chưa có kết quả kết thúc.

## 3. Các phát hiện và cách nghiệm thu

### A01 — P1: BE nhanh có thể dùng bảng chi tiết của bộ dữ liệu cũ

**Vị trí:** `be_app/quick_be_ui.py:267`; `be_app/ui.py:1502`.

`show_be_results()` nhận khóa chỉ gồm `settings_sha256`; cache bổ sung schema và tuple quyết định, nhưng không có hash dữ liệu hoặc giá trị kết quả. Đổi dữ liệu và chạy lại với cùng cấu hình, nếu PASS/FAIL giữ nguyên, bảng tổng hợp cập nhật nhưng bảng reviewer/CI/ANOVA có thể lấy từ cache trước.

**Tái hiện:** dùng fixture `tests.test_quick_be.pk_table()`, nhân Cmax của T với 1,01. GMR Cmax đổi từ 1,0693580849 thành 1,0800516657; hai endpoint vẫn PASS; khóa cache bằng nhau, bảng Confidence Intervals tính mới khác nhau. Excel được dựng từ kết quả mới nên có thể không khớp bảng chi tiết trên màn hình.

**Sửa:** khóa bằng danh tính snapshot hoặc hash gồm input, settings, engine và phiên bản bảng; dùng cùng nguồn kết quả cho bảng tổng hợp, bảng chi tiết và export.

**Nghiệm thu:** chạy hai dataset cùng cấu hình/cùng quyết định liên tiếp; mọi CI, ANOVA, tiêu chí và Excel đều tương ứng dataset thứ hai; cache chỉ tái dùng khi snapshot giống nhau.

### A02 — P1: NCA truyền IV có thể suy ra pha thải trừ khi chưa kết thúc truyền

**Vị trí:** `be_app/pk_analysis.py:141–175`, nhánh `analyze_nca()` dùng kết quả `_terminal()`.

Chọn điểm terminal dựa trên vị trí sau đỉnh quan sát, chưa ràng buộc thời điểm kết thúc truyền. Một đường cong giảm trong thời gian truyền vẫn được coi là pha cuối, dù cần rà soát lịch truyền hoặc dữ liệu.

**Tái hiện:** truyền 10 giờ, lấy mẫu tại 0–5 giờ, nồng độ `[0,10,8,6.4,5.12,4.096]`. App chọn điểm 2–5 giờ, trả lambda-z 0,22314355 h⁻¹, AUC∞ 49,8142 và CL 2007,4597 L/h khi liều nhập 100 mg. Cảnh báo hiện có về tỷ lệ ngoại suy không xử lý điều kiện truyền chưa kết thúc.

**Sửa:** điều kiện chọn terminal theo đường dùng và lịch truyền; thiếu đủ điểm sau kết thúc truyền thì giữ AUC quan sát, để trống các thông số phụ thuộc pha thải trừ và giải thích rõ.

**Nghiệm thu:** bộ fixture gồm mẫu trước/trùng/sau kết thúc truyền, đủ và thiếu điểm terminal; chuyên gia PK rà soát quy tắc và oracle trước nghiệm thu. Không chỉ kiểm tra độ khớp hồi quy.

### A03 — P1: Mở archive cũ có thể thay thế các chỉnh sửa đã lưu gần đây

**Vị trí:** `be_app/ui.py:421–425`.

Khi project ID trùng, UI lấy working revision hiện tại rồi dùng token đó để lưu payload từ archive mà chưa đọc/hòa giải các chỉnh sửa ở revision đó. Optimistic conflict thông thường vẫn tồn tại, nhưng thao tác restore đã tự nhận token mới nhất.

**Tái hiện được trong SQLite cô lập:** export dự án, lưu thêm draft qua journal, rồi thực hiện đường lưu archive cũ với cùng project ID. Checkout mới không chứa draft vừa lưu. Dòng journal cũ vẫn tồn tại: đây là rollback âm thầm của trạng thái hiện hành, không phải xóa vật lý lịch sử.

**Sửa:** mặc định phục hồi thành bản sao có ID mới và liên kết nguồn; nếu hỗ trợ restore cùng ID, hiển thị chênh lệch, ghi sự kiện restore và áp dụng kiểm tra revision trên checkout thực sự đã đọc.

**Nghiệm thu:** hai session, archive cũ/mới và pending draft; không bỏ qua thay đổi chưa được xử lý; luôn truy xuất được trạng thái trước restore.

### A04 — P2: Kiểm tra khoa học không đồng nhất giữa API BE nhanh và pipeline đầy đủ

**Vị trí:** `be_app/quick_be.py:248–266`, `be_app/replicate.py:569`, đối chiếu `be_app/regulations.py:192` và `be_app/pipeline.py:53`.

API BE nhanh cho phép `nti=True` với rule chuẩn, trong khi workflow đầy đủ kiểm tra tính tương thích hai chiều. API cũng nhận biên và alpha tùy chỉnh dưới tên rule chuẩn. UI hiện suy ra cờ NTI từ rule: không mô tả đây là lỗi có thể kích hoạt bằng mọi thao tác UI hiện tại.

**Tái hiện:** nhân Cmax/AUC của T trong fixture với 1,06: rule chuẩn với `nti=True` trả PASS, `EMA_NTI` trả FAIL (GMR khoảng 1,13352). Nhân với 1,3: mặc định FAIL, biên 0,5–2,0 trả PASS. Với alpha 0,2, CI thực tính 60% vẫn mang nhãn “CI 90% within acceptance limits” tại `statistics.py:44`.

**Sửa:** dùng validator chung cho tính tương thích design/rule/NTI/config; nếu hỗ trợ custom analysis, tách tên/phạm vi và hiển thị đúng mức tin cậy. Giữ khác biệt có chủ đích giữa kết luận endpoint ở chế độ thăm dò và kết luận nghiên cứu đầy đủ.

**Nghiệm thu:** ma trận API và UI cho NTI/rule/alpha/biên; không xuất tiêu chí gắn nhãn sai; cấu hình ngoài phạm vi bị chặn hoặc được gắn nhãn custom rõ ràng.

### A05 — P2: Journal chưa phát hiện đầy đủ mất bản ghi

**Vị trí:** `be_app/persistence.py:363`, `436–445`.

Checkout kiểm hash từng patch còn tồn tại nhưng bỏ qua tính liên tục của working revision. Journal chưa có trigger UPDATE/DELETE như snapshots.

**Tái hiện trong DB thử nghiệm:** journal lần 1 thay CV, lần 2 thay preference; xóa patch 1 bằng truy cập DB trực tiếp. Checkout vẫn thành công, thiếu thay đổi CV nhưng audit còn ghi sự kiện tương ứng. Cần truy cập/sửa DB ngoài luồng app để kích hoạt ví dụ này; README đã nói checksum không bảo vệ chống người có quyền sửa file DB.

**Sửa:** kiểm revision liên tục, liên kết predecessor/state hash, bổ sung bảo vệ journal và expected head để phát hiện cả mất patch cuối. Trình bày rõ giới hạn của audit cục bộ.

**Nghiệm thu:** xóa/sửa/đổi thứ tự patch trong DB fixture phải báo lỗi toàn vẹn; restore không âm thầm tạo một trạng thái khác.

### A06 — P2: Export Excel PK diễn giải mã hồ sơ thành công thức

**Vị trí:** `be_app/pk_records.py:158–168`; BE exporter đã có bảo vệ tại `be_app/be_reporting.py:289`.

Mã hồ sơ nhập `=1+1` được xuất ở `Du_lieu!A2` với kiểu ô `f`. Excel diễn giải dữ liệu text thành công thức; không cần mở Excel để xác minh lỗi kiểu ô.

**Sửa:** policy text-cell dùng chung cho mọi exporter; kiểm dữ liệu, metadata, cảnh báo và header. Giữ kiểu số thật cho cột số.

**Nghiệm thu:** chuỗi thử bắt đầu bằng `=`, `+`, `-`, `@` vẫn là text theo policy; không làm số âm hợp lệ thành text ngoài ý muốn; không chạy công thức để kiểm thử.

### A07 — P2: Archive export thành công nhưng import của app từ chối

**Vị trí:** `be_app/persistence.py:315` và `336`.

Export và import không dùng cùng điều kiện chấp nhận: import thêm giới hạn tỷ lệ nén >500 cho entry lớn, trong khi export chỉ kiểm kích thước. Export cũng chưa cộng manifest vào giới hạn tổng giải nén.

**Tái hiện:** trường draft reason chứa 3 triệu ký tự `A` tạo ZIP khoảng 4,9 KB, tỷ lệ nén khoảng 678:1; import lại bị từ chối. Đây là trường hợp biên, không chứng minh mọi backup thông thường đều lỗi.

**Sửa:** dùng validator archive chung; dùng ZIP_STORED khi thích hợp hoặc từ chối ngay lúc export. Không bỏ bảo vệ ZIP bomb để làm round-trip đạt.

**Nghiệm thu:** mọi archive mà exporter chấp nhận đều import được; kiểm sát ngưỡng kích thước, manifest và dữ liệu nén mạnh.

### A08 — P2: Fingerprint PK mất độ chính xác và thiếu danh tính nguồn

**Vị trí:** `be_app/pk_ui.py:61–66`, `429`.

`DataFrame.to_json()` mặc định làm tròn số trong chuỗi băm. Giá trị 1,00000000001 và 1,00000000002 cho cùng fingerprint. Ngoài ra, thay file bằng file khác có cùng dữ liệu chuẩn hóa không làm đổi fingerprint, trong khi snapshot giữ provenance của nguồn cũ. Ví dụ số rất gần nhau chủ yếu chứng minh lỗ hổng định danh; không tự suy ra chênh lệch PK có ý nghĩa lâm sàng.

**Sửa:** chuẩn hóa số không mất thông tin, kèm source hash và phiên bản engine/schema; phân biệt hash nội dung tính toán với hash provenance nếu cần cache có chủ đích.

**Nghiệm thu:** thay dữ liệu dù nhỏ hoặc thay nguồn phải có trạng thái/provenance đúng; file khác tên nhưng cùng dữ liệu không được hiển thị sai nguồn.

### A09 — P2: Browser regression chưa cập nhật theo luồng demo mới

**Vị trí:** `scripts/browser_state_e2e.cjs:53`, `.github/workflows/` job `browser-state`; cùng selector cũ trong `scripts/browser_smoke_cdp.cjs`.

Script tìm nút `Nạp dữ liệu giả lập học thử`, không còn trong mã UI. UI hiện có `Điền dữ liệu mẫu vào biểu mẫu nghiên cứu` rồi `Tạo nghiên cứu` (`ui.py:307`, `335`). Vì thế kịch bản sẽ không qua bước này với UI hiện tại; đây là kết luận đối chiếu tĩnh, chưa báo rằng đã thực thi Playwright và thấy timeout.

**Sửa:** dựng fixture qua workflow công khai mới, cập nhật selector và hoàn thiện allocation/import/QC theo hành vi hiện tại; DB riêng cho cả `BE_PROJECT_DATABASE` và `PK_ANALYSIS_DATABASE`.

**Nghiệm thu:** browser CI hoàn tất ba luồng, upload, edit, stale, download và restore; có proof/screenshots gắn phiên bản, không chỉ kiểm rằng trang tải được.

### A10 — P2: PK tạo tất cả báo cáo ngay cả khi chưa mở tab export

**Vị trí:** `be_app/pk_ui.py:308–333`.

Tab ẩn vẫn thực thi; `_render_snapshot()` gọi cả Excel/Word/PDF ngay khi hiển thị snapshot mới. `_export` có cache nhưng chưa giới hạn số entry hoặc TTL. Luồng BE nhanh cũng dựng workbook ở mỗi rerun khi còn kết quả.

**Sửa:** tạo artifact theo nút yêu cầu, cache có giới hạn theo snapshot và định dạng; tách render đồ thị/bảng nặng khi cần. Không cache bằng khóa thiếu dữ liệu như A01.

**Nghiệm thu:** xem bảng không gọi renderer báo cáo; tải đúng định dạng mới tạo artifact; đo lần đầu và rerun ở bộ dữ liệu 12/60/240 người. Đặt SLO sau baseline đo thực, không tuyên bố tốc độ từ suy đoán.

### A11 — P2: Xử lý BLQ ở BE nhanh cần giải thích và rà soát rõ hơn

**Vị trí:** `be_app/quick_be.py:141`, `be_app/nca.py:186`.

BE nhanh nhận nồng độ dương kèm cờ BLQ và engine quy về 0. Tái hiện độc lập đánh dấu các đỉnh trong fixture là BLQ làm đổi Cmax/AUC nhưng vẫn PASS mà không có cảnh báo tương ứng. Nồng độ dương có thể là số ước lượng dưới LLOQ; không nên mặc định mọi cặp dương/BLQ là sai.

**Sửa:** ghi rõ chính sách BLQ, số mẫu bị thay thế, giá trị nguồn và tác động; yêu cầu xử lý mâu thuẫn dựa trên LLOQ/metadata khi có. Cảnh báo khi cờ BLQ làm mất đỉnh hoặc tạo đoạn bất thường.

**Nghiệm thu:** test BLQ trước đỉnh/giữa các mẫu định lượng/cuối profile; báo cáo tái dựng được các bước xử lý và không sửa raw âm thầm.

## 4. Cải tiến cấu trúc, trải nghiệm và tài liệu

- **Tách UI theo trách nhiệm:** `ui.py` khoảng 2.392 dòng, gồm study, import, QC, NCA, BE, reports và điều hướng. Tách từng page và application service sau khi có regression test cho các lỗi trên; tránh refactor lớn cùng lúc sửa thuật toán.
- **Một quy ước trạng thái chung:** ba luồng dùng nhãn input hợp lệ, chưa áp dụng, đã tính, stale, đã lưu và draft nhất quán; chỉ rõ kết quả endpoint khác kết luận cấp nghiên cứu. Hiển thị hành động tiếp theo và lý do bị chặn ngay cạnh nút.
- **Provenance chung cho export:** cùng snapshot ID, source hash, config hash, engine version, phạm vi tính và cảnh báo giữa màn hình/Excel/Word/PDF/JSON.
- **QA report:** render các báo cáo Việt/Anh với bảng dài, cảnh báo dài, dấu tiếng Việt và đồ thị; lưu ảnh kiểm tra. Unit test cấu trúc DOCX không thay thế kiểm tra phân trang.
- **Tài liệu capability:** backlog còn ghi NTI và multiple-dose chưa hỗ trợ trong khi README đã mô tả phạm vi hỗ trợ mới. Sinh bảng capability từ registry kết hợp trạng thái qualification; tách “có tính toán”, “được kết luận”, “đã benchmark” và “ngoài phạm vi”.
- **Quản lý phiên bản:** tại thời điểm audit, `git ls-files` trả 0 và toàn bộ nguồn hiện là untracked. Cần rà soát dữ liệu nhạy cảm, lập baseline commit/release và gắn bằng chứng test với commit/hash; audit này không tự stage hoặc commit các tệp đó.
- **Triển khai:** localhost và chưa có RBAC là giới hạn đã công bố, không phải lỗ hổng mới phát hiện. Chỉ đưa authentication, phân quyền, TLS, backup/restore SOP và logging vận hành vào nhánh kế hoạch nếu cần triển khai nhiều người dùng.

## 5. Lộ trình đề xuất

Ước lượng dưới đây là ngày công cho một lập trình viên quen codebase, thêm QA và chuyên gia PK/BE ở các mốc nghiệm thu; không phải cam kết lịch hoặc thời gian qualification pháp quy.

| Giai đoạn | Công việc | Ước lượng | Điều kiện hoàn tất |
|---|---|---:|---|
| 0 — Chốt baseline | Baseline nguồn; làm rõ test environment; sửa browser fixture A09; lưu manifest bằng chứng | 1–2 ngày | Test chạy kết thúc, lỗi môi trường tách khỏi lỗi sản phẩm; browser đi qua luồng mới |
| 1 — Sửa lỗi tác động kết quả/dữ liệu | A01 cache, A02 truyền IV, A03 restore; A04 rule/config/CI label; A06 text-cell | 4–6 ngày | Mỗi lỗi có regression trước/sau; không còn P1 mở; review PK cho A02 |
| 2 — Củng cố tính toàn vẹn | A05 journal, A07 archive round-trip, A08 fingerprint, A11 BLQ/provenance | 3–5 ngày | Negative tests có kiểm soát; restore/round-trip không mất trạng thái; export truy xuất được nguồn |
| 3 — Hiệu năng và UX | A10 on-demand export; trạng thái thống nhất; điều hướng và help; đo dataset nhỏ/lớn | 3–5 ngày | Không dựng báo cáo khi chỉ xem bảng; baseline latency/memory; UAT ba luồng |
| 4 — Dễ bảo trì và sẵn sàng phát hành | Tách UI/service; capability/docs; render report; CI artifacts và release checklist | 3–5 ngày | Clean test/CI, report đã visual QA, capability khớp implementation, release gắn version |

Tổng sơ bộ **14–23 ngày công**, chưa gồm qualification phương pháp mới, triển khai nhiều người dùng hoặc tích hợp LIMS/CTD. Có thể giao sửa A06 và cập nhật browser độc lập; A05/A07 cần thống nhất chiến lược restore với A03; tách UI nên làm sau các regression quan trọng.

## 6. Các cổng nghiệm thu

1. **Đúng kết quả:** cache không trả bảng cũ; CI label đúng alpha; rule/NTI/config nhất quán; truyền IV có gate dữ liệu thích hợp. Oracle độc lập cho nhánh thay đổi, không chỉ so cùng engine với chính nó.
2. **Đúng trạng thái:** thay input/mapping/config/source phải invalidation đúng; save/reload/switch project/restore giữ đúng snapshot và draft; test xung đột hai session.
3. **Đúng artifact:** màn hình và các file dùng cùng snapshot; Excel không chuyển ID thành công thức; archive xuất ra phải mở lại được; DOCX/PDF được render và đọc kiểm tra.
4. **CI tái lập:** lint/type/test/benchmark/browser đều có kết quả kết thúc; lưu versions, fixture hashes và artifacts. Không dùng số lượng test pass để thay thế coverage theo rủi ro.
5. **Phạm vi rõ:** phương pháp chưa qualified vẫn bị chặn theo thiết kế; kết quả đào tạo/thăm dò không biến thành phê duyệt nghiên cứu; các giới hạn chưa làm được hiển thị đúng.

## 7. Theo dõi chạy lại test

Hai lần chạy lại chuyển TEMP/TMP và pytest basetemp vào workspace không hoàn tất và đã được dừng. Lần cuối in 19 dấu test đạt rồi không có tiến triển quan sát được trong thời gian kiểm tra. Không suy ra nguyên nhân treo là lỗi app khi chưa điều tra thêm. JUnit của lần đầu là bằng chứng kết thúc duy nhất của toàn suite: **350 passed, 3 failed, 37 errors**. Vì vậy audit **không xác nhận toàn bộ suite đạt**. Cần điều tra test UI đầu tiên và môi trường AppTest trong giai đoạn 0.

`output/audit_20261104/audit_manifest.json` ghi phiên bản runtime, trạng thái kiểm tra, SHA-256 của các bằng chứng và mã nguồn `be_app/*.py`. Hash giúp xác định đúng nội dung được audit, không thay thế một baseline Git có kiểm soát.

## 8. Việc ngoài phạm vi triển khai trong audit này

Chưa sửa các lỗi nêu trên, chưa commit/release/deploy, chưa bật engine replicate experimental và chưa tuyên bố các benchmark cũ là qualification toàn diện. Đầu ra của lần làm việc này là audit có bằng chứng và backlog đủ cụ thể để triển khai, đúng yêu cầu lập kế hoạch cải tiến.
