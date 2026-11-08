# Tiến độ triển khai kế hoạch audit BE Analysis Workbench

Ngày kiểm tra: 05/11/2026 (Australia/Perth). Phạm vi: `docs/AUDIT_IMPROVEMENT_PLAN_20261105_VI.md`, phiên bản khai báo `0.3.1`.

## Kết quả triển khai

Các sửa đổi mã nguồn A01–A11 dưới đây đã được thực hiện. Mức **đã sửa và có kiểm thử** chỉ áp dụng cho hành vi đã nêu; **không** đồng nghĩa với qualification của phương pháp BE, kiểm thử trình duyệt hoàn chỉnh, hoặc nghiệm thu phát hành.

| Mã | Thay đổi đã triển khai | Bằng chứng / giới hạn |
| --- | --- | --- |
| **A01** | Khóa cache bảng reviewer dùng hash toàn bộ giá trị kết quả, nội dung endpoint và thiết kế; BE nhanh truyền bảng endpoint cho reviewer. Chuẩn hóa dữ liệu NCA lưu dưới dạng `list[dict]` thành DataFrame trước khi sinh khóa và bảng. | Regression đổi Cmax khi quyết định vẫn PASS; khóa giống nhau cho danh sách NCA và DataFrame tương đương, nhưng đổi khi PK đổi. Hai ca AppTest BE/STALE trước đây lỗi nay đạt. Cần UAT click-through để đối chiếu bảng và Excel cùng snapshot. |
| **A02** | NCA truyền IV chỉ tính terminal lambda-z với ít nhất ba mẫu sau khi kết thúc truyền; thiếu dữ liệu thì giữ AUC quan sát, bỏ các thông số ngoại suy phụ thuộc terminal và cảnh báo. | Ba kịch bản trước/trùng/sau kết thúc truyền đạt. **Chờ chuyên gia PK thẩm định tiêu chí và đối chiếu oracle độc lập.** |
| **A03** | Archive trùng project ID được phục hồi thành dự án mới, lưu ID nguồn, thời điểm restore, SHA-256 archive; không thay thế draft/journal dự án đang mở. | Regression restore khi đang có draft chưa checkpoint đạt. |
| **A04** | BE nhanh kiểm tra tương thích rule/NTI/alpha/acceptance limits; nhãn CI lấy từ alpha thật. | Ma trận API kiểm tra cấu hình bị từ chối và nhãn CI 60% đạt. Chưa chạy toàn bộ ma trận UI thực tế. |
| **A05** | SQLite journal có trigger bất biến, kiểm liên tục revision của thay đổi và dấu mốc, phát hiện thiếu bản ghi; migration dấu mốc chỉ áp dụng một lần và theo transaction. | Kiểm thử can thiệp có chủ đích: xóa patch, xóa head giữa/cuối rồi mở lại, và nâng cấp journal cũ đều đạt. SQLite cục bộ không chống được người có toàn quyền sửa DB và toàn bộ metadata. |
| **A06** | Excel PK escape identifier dạng chuỗi bắt đầu `=`, `+`, `-`, `@`, giữ kiểu dữ liệu số hợp lệ. | Kiểm tra kiểu ô trong tất cả các sheet liên quan bằng openpyxl đạt. |
| **A07** | Xuất archive chọn lưu không nén cho phần nội dung có tỷ lệ nén bất thường, đồng bộ với giới hạn import. | Archive có 3 triệu ký tự lặp được xuất và import round-trip thành công. |
| **A08** | Fingerprint PK bảo toàn độ chính xác số thực, đưa danh tính nguồn và hash vào định danh snapshot. | Đổi số rất nhỏ hoặc tên/hash nguồn làm đổi fingerprint; sao chép nguyên dữ liệu cho fingerprint như cũ. |
| **A09** | Cập nhật script browser theo thao tác demo hiện hành và tách DB thử nghiệm. | `node --check` thành công cho hai script; **chưa chạy browser CI/Playwright và chưa có bằng chứng screenshot mới**. |
| **A10** | PK Excel/Word/PDF chỉ dựng sau yêu cầu, cache có TTL/giới hạn. BE nhanh cũng chỉ dựng Excel khi bấm chuẩn bị, cache gắn với identity nguồn+cấu hình. | Kiểm thử giả lập rendering/nhấn chuẩn bị và invalidation theo identity đạt. Đã đo benchmark Python tổng hợp 12/60/240 người cùng xuất Excel/Word/PDF 12/60 profile; **chưa đo first paint/rerun qua trình duyệt hay RSS toàn tiến trình**. |
| **A11** | Cờ BLQ kèm nồng độ dương được cảnh báo và ghi provenance từng mẫu ảnh hưởng, bảo toàn dữ liệu raw. | Regression xác nhận số mẫu, giá trị nguồn và cảnh báo. Cần hoàn thiện rà soát quy tắc BLQ theo LLOQ/SAP và các ca đỉnh/giữa/cuối profile. |

## Kiểm thử và chất lượng mã

Chạy tại workspace Windows, với `TEMP/TMP` và `--basetemp` trong `.cache` để cách ly dữ liệu thử.

| Hạng mục | Kết quả đến cuối lần triển khai | Bằng chứng |
| --- | --- | --- |
| Kiểm thử hồi quy audit cùng hai luồng AppTest trước đây lỗi | **26 passed** | `.cache/pytest-a01-regression.xml`; bao gồm kiểm thử NCA `list[dict]`/DataFrame và hai ca AppTest toàn trang + trạng thái STALE. |
| Suite không chứa module sử dụng `streamlit.testing.v1.AppTest` | **244 passed** | `.cache/pytest-unit-20261105.xml`; loại 13 module có AppTest, không được gọi là full suite. |
| Bộ số liệu chuẩn/benchmark offline | **19/19 passed** | `output/implementation_20261105/benchmark_results.csv`. |
| Manifest và kiểm thử điều kiện chấp nhận bằng chứng | **9 passed** | `tests/test_implementation_manifest.py`: không đếm trùng JUnit lồng nhau, từ chối kiểm thử/benchmark không hoàn tất, kiểm hash evidence và nguồn. |
| Ruff và Mypy | **Pass** | `ruff check be_app tests scripts`; `mypy be_app` (43 source files theo cấu hình hiện hành). |
| Cú pháp/biên dịch | **Pass** | `python -m compileall -q be_app`; `node --check` với hai script browser. |
| Pytest toàn bộ gồm giao diện | **423 passed; 0 failed; 0 errors** | `.cache/pytest-all-final.xml`, tổng 80,41 giây; chạy với TEMP/TMP trong workspace, DB test riêng và quyền loopback phù hợp cho Streamlit AppTest. |
| Manifest truy xuất | **Đã tạo, 423 tests + 19/19 benchmark** | `output/implementation_20261105/verification_manifest.json`: SHA-256 của JUnit/benchmark và mã nguồn, test, fixture, script, cấu hình, dependency lock. Tài liệu này chỉ xác nhận bằng chứng kỹ thuật tại thời điểm tạo. |

Các lần chạy AppTest dưới sandbox mặc định từng dừng tại `asyncio` khi `socket.socketpair()` chờ `accept()` trên Windows. Khi chạy với quyền loopback mở rộng, suite hoàn tất và phát hiện hai lỗi `AttributeError: 'list' object has no attribute 'to_csv'` ở `show_be_results`; cả hai được sửa và kiểm thử lại. Đây là thông tin môi trường và lỗi đã được xác minh, không còn đánh dấu full suite là bị treo. Kiểm thử hồi quy dùng fixture tổng hợp và SQLite tại `tmp_path`, không sử dụng cơ sở dữ liệu nghiên cứu đang hoạt động. Bộ số liệu chuẩn là bằng chứng kiểm tra thuật toán ở các ca đã khai báo; không thay thế validation/qualification theo mục đích sử dụng.

## Hiệu năng và kiểm tra báo cáo tổng hợp

`scripts/performance_audit.py` đo trên dữ liệu mô phỏng cục bộ bằng wall-clock và `tracemalloc`. Đo bao gồm chuẩn bị state, QC có cache và tạo báo cáo qua API Python; **không bao gồm** tải trang đầu, rerun Streamlit thực, độ trễ truyền tải trình duyệt, RSS hệ điều hành hoặc phân trang trong Microsoft Word. Kết quả đầy đủ: `output/implementation_20261105/performance_audit.json`.

| Quy mô nghiên cứu | Dòng mẫu raw | Tạo dữ liệu tổng hợp | QC lần đầu | QC gọi lại sau cache | Bộ nhớ Python đỉnh khi QC |
| --- | ---: | ---: | ---: | ---: | ---: |
| 12 người | 336 | 0,78 s | 0,32 s | <0,001 s | 1,04 MiB |
| 60 người | 1.680 | 2,25 s | 1,96 s | <0,001 s | 2,96 MiB |
| 240 người | 6.720 | 11,34 s | 9,61 s | <0,001 s | 10,36 MiB |

Qua ba lần đọc lại QC ở mỗi quy mô, số lần tính QC vẫn là **1**. Đây là dấu hiệu cache hoạt động trong trường hợp thử; chi phí QC đầu tiên ở 240 người cần được theo dõi khi đo UI thực tế.

| Báo cáo PK tổng hợp | Excel | Word | PDF | Kiểm tra cấu trúc |
| --- | ---: | ---: | ---: | --- |
| 12 profile / 168 dòng | 0,15 s | 2,39 s | 7,49 s | XLSX 6 sheet; DOCX 17 bảng; PDF 25 trang |
| 60 profile / 840 dòng | 0,31 s | 5,54 s | 14,89 s | XLSX 6 sheet; DOCX 65 bảng; PDF 80 trang |

Đã dùng `openpyxl`, `python-docx` và PyMuPDF để mở, kiểm tra cấu trúc các file; PDF có text trích xuất được và bộ ảnh kiểm tra trang 1, 3, 25 tại `output/implementation_20261105/synthetic_artifact_qa/`. Bộ file mẫu 12 profile được giữ trong cùng thư mục. Kết quả này chưa thay thế bước xem trực quan toàn bộ trang và kiểm tra file DOCX trong Microsoft Word. Không đặt SLO phát hành chỉ từ một lượt đo tổng hợp.

## Việc còn phải hoàn tất trước nghiệm thu

1. **P1 — Cổng đúng kết quả:** chuyên gia PK/BE xác nhận quy tắc chọn terminal truyền IV và chính sách BLQ/LLOQ theo SAP; đối chiếu oracle độc lập với các nhánh mới.
2. **P1 — Cổng giao diện:** AppTest và full suite đã khôi phục. Còn cần chạy Playwright/browser CI cho luồng dự án, BE nhanh, PK độc lập, restore/export và lưu ảnh bằng chứng; Playwright chưa có trong môi trường Node cục bộ được kiểm tra.
3. **P2 — Cổng artifact/hiệu năng:** benchmark Python và xác nhận cấu trúc Excel/Word/PDF tổng hợp đã có. Còn cần kiểm tra Word/PDF/Excel bằng ứng dụng thực, phân trang và tiếng Việt trên nhiều trang; đo first paint/rerun/RSS trong browser với quy mô 12/60/240 người, rồi đặt ngưỡng nghiệm thu dựa trên baseline đo được.
4. **P2 — Trạng thái và cấu trúc:** bảng capability đã được sinh từ registry (`scripts/generate_capability_matrix.py` → `docs/CAPABILITY_MATRIX.md`) và backlog cũ đã được chỉnh; còn cần thống nhất nhãn trạng thái ba luồng, tách dần `ui.py` thành module theo trách nhiệm sau khi UI regression ổn định.
5. **P2 — Phát hành có truy xuất:** rà soát toàn bộ file untracked, kiểm dữ liệu nhạy cảm, chuẩn bị baseline Git, ghim mã nguồn/fixture/manifest vào kết quả CI; chưa stage/commit/release/deploy trong đợt sửa này.

## Lệnh tái kiểm tra

```powershell
$env:TEMP = (Resolve-Path .cache\tmp).Path
$env:TMP = $env:TEMP
.venv\Scripts\python.exe -m pytest -q tests/test_audit_regressions.py tests/test_quick_be.py tests/test_persistence_pipeline.py tests/test_pk_standalone.py --basetemp=.cache\pytest-audit-focused
.venv\Scripts\python.exe -m pytest -q --basetemp=.cache\pytest-all-final --junitxml=.cache\pytest-all-final.xml
.venv\Scripts\ruff.exe check be_app tests scripts
.venv\Scripts\mypy.exe be_app
.venv\Scripts\python.exe scripts/benchmark.py --output output\implementation_20261105\benchmark_results.csv
.venv\Scripts\python.exe scripts/performance_audit.py --sizes 12,60,240 --report-sizes 12,60 --output output\implementation_20261105\performance_audit.json --sample-dir output\implementation_20261105\synthetic_artifact_qa
.venv\Scripts\python.exe scripts/implementation_manifest.py --junit .cache\pytest-all-final.xml --benchmark output\implementation_20261105\benchmark_results.csv --output output\implementation_20261105\verification_manifest.json
node --check scripts/browser_state_e2e.cjs
node --check scripts/browser_smoke_cdp.cjs
```

Trên Windows, AppTest dùng `asyncio` loopback; nếu môi trường sandbox chặn `socket.socketpair()`, cần chạy pytest trong môi trường cho phép loopback hoặc dùng CI tương ứng. Không suy diễn việc chờ socket thành lỗi thuật toán BE.

Lưu ý: toàn bộ cây làm việc được Git hiển thị là *untracked* tại thời điểm audit/triển khai; không thực hiện `git add`, `git commit`, thao tác dữ liệu nghiên cứu hoặc ghi đè báo cáo audit gốc.
