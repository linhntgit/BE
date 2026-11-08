# Trạng thái và hiệu năng sau sửa

Nghiệm thu cục bộ ngày 30/10/2026, Australia/Perth. Xem STATE_AUDIT.md cho audit trước sửa.
Phạm vi là state, consistency và performance; không mở thêm ABEL/RSABE/replicate chưa benchmark.

## Kết quả

- 141 tests đạt, 0 failed, 0 skipped ở lượt nghiệm thu cuối (10.53 giây); bao gồm 29 ca mới (kể cả parametrization).
- 19/19 scientific golden comparisons vẫn đạt; công thức trong nca.py/statistics.py/design.py giữ nguyên.
- Ruff và mypy đạt. CI đã bổ sung job browser-state; chưa chạy CI từ xa hoặc push.
- Chrome/Playwright E2E đạt 6 checkpoint thực: CV=24.7 và T/R=.93 qua đổi trang;
  sửa 3 ô Cplasma S0001/kỳ 2 trong editor; áp dụng và chạy NCA/BE đúng số đã sửa;
  tải input_manifest.json khớp revision/fingerprint; STALE chặn Word/PDF;
  reload browser và mở lại dự án giữ chỉnh sửa pending.
- Bằng chứng máy đọc được: browser_state_evidence.json, state_performance_before.json,
  state_performance_after.json, benchmark_results.csv; JUnit trong output/state-test-results.xml.

## Hiệu năng đo trước và sau

Cùng dữ liệu synthetic, 3 lần đo mỗi đường truy cập; thời gian median.

| Dữ liệu | Trước: QC bị chạy lại trên một lượt truy cập | Sau: truy cập QC đã cache | QC tính lại sau 3 lượt warm | NCA/BE chạy khi điều hướng |
|---|---:|---:|---:|---:|
| 336 dòng, 12 người | 0.193 giây | Dưới 0.0001 giây ở phép đo cục bộ | 3 → 0 | 0 |
| 6.720 dòng, 240 người | 3.800 giây | Dưới 0.0001 giây ở phép đo cục bộ | 3 → 0 | 0 |

Đây là latency của lớp truy cập dữ liệu, không phải thời gian render toàn trang hoặc
cam kết phản hồi trình duyệt dưới một mili giây. Lần QC lạnh vẫn kiểm tra đầy đủ.
Ngưỡng regression cục bộ là đường warm <10% median baseline trên cùng máy, kèm invariant
không tính lại QC/NCA khi chỉ điều hướng. Script thoát !=0 khi vi phạm.
Kiểm thử còn cấm full input hash khi sửa field nhẹ và cấm DataFrame.copy trong callback editor.

Khi sửa một profile, phép tính sau dùng cache của các profile còn lại;
kiểm thử xác nhận 1 computed + N−1 reused. Đổi chỉ cấu hình BE tái dùng NCA;
đổi tích phân NCA làm tính lại tất cả profile. Tùy chọn report/đồ thị và giả định thiết kế
không làm kết quả Cplasma thành stale hoặc kích hoạt lại phân tích.

## Cách state vận hành

- Project là domain đã xác nhận; ProjectState chỉ thuộc một session/project, không cache mutable toàn cục.
- planning_inputs được validate và commit khi input xác nhận. drafts và pending_edits được journal bền vững,
  chưa dùng để tính. Widget keys có project/mount/section/entity; callback không gọi st.rerun.
- SQLite working_changes lưu patch nhỏ, checksum và optimistic revision trong transaction.
  Session chỉ đổi canonical state sau khi ghi thành công. Checkpoint đầy đủ theo thao tác chủ đích.
- Store.checkout đọc snapshot và journal trong cùng transaction, trả cả base/working revision;
  hai phiên không thể ghi đè patch chưa đọc. Phiên khác dự án không chia sẻ controller/cache.
- Editor giữ baseline/schema/sample_id, kiểm tra diff; Session State của editor là dict diff.
  Baseline không được ghi đè bởi DataFrame trả về. Khi unmount, dựng lại từ domain + pending đã giữ.
- InputSnapshot chứa bytes JSON bất biến, revision và fingerprint; NCA/ABE không đọc widget/session state.
  Các wrapper EMA/FDA scaled chưa hỗ trợ vẫn trả NOT EVALUABLE.
- Snapshot JSON dùng lossless float round-trip; sửa thêm parser tại biên nhập để tránh làm tròn qua
  pandas.to_numeric. Các phép tích phân/kiểm định không bị đổi để xử lý state.
- Mọi trang NCA/BE/đồ thị/report dùng cùng CURRENT/STALE/LEGACY. Pending config hoặc mẫu làm chặn report.
  Manifest chứa revisions, hashes, config, rule/version, software versions và source file.
- Đồ thị dùng fragment; power là cache_data thuần, bounded, không chứa Project hay dataset người dùng.
  Excel/Word/PDF/archive chỉ chuẩn bị theo nút, không tạo trong render mỗi lần gõ.

## Khôi phục và giới hạn được giữ rõ

- Schema 2 đọc archive/schema 1 có kiểm soát; dữ liệu cũ giữ nguyên, kết quả thiếu revision gắn LEGACY,
  cần tính lại trước khi coi là hiện hành. Schema chưa biết bị từ chối.
- Reload trình duyệt không được coi là lưu session; mở lại project từ SQLite sẽ replay journal.
  Archive chứa cả pending/drafts; dữ liệu gốc và lịch sử correction vẫn bất biến.
- Chưa xác nhận Enter/blur thì ký tự còn trong bộ gõ của trình duyệt chưa được server nhận;
  không hứa khôi phục các ký tự chưa gửi nếu trình duyệt bị đóng đột ngột.
- Editor không thêm/xóa hàng hoặc đổi sample_id. Cần thêm mẫu/thay schema: import có kiểm tra bằng revision.
  Đổi thiết kế khi có phân nhóm/dữ liệu bị từ chối và hướng dẫn tạo dự án riêng, không xóa dữ liệu ngầm.
- Correction cần lý do/reviewer/evidence trước Áp dụng; bản nháp vẫn được giữ nếu đổi trang.
- Vẫn là ứng dụng local single-user, chưa có authentication/RBAC/GxP validation; isolation kỹ thuật
  của session/cache không phải cơ chế phân quyền giữa người dùng có quyền mở cùng DB.
- Bố cục DOCX vẫn chưa được render bằng LibreOffice trên runtime này; không đổi trạng thái DRAFT/QA.

## Lệnh kiểm tra

```powershell
uv run --frozen pytest -q --junitxml=output/state-test-results.xml
uv run --frozen ruff check .
uv run --frozen mypy be_app
uv run --frozen python scripts/benchmark.py
uv run --frozen python scripts/state_benchmark.py --phase after
```

Browser test: Node + Playwright 1.62.1 và Chrome/Chromium, script scripts/browser_state_e2e.cjs.
Set NODE_PATH tới thư viện Playwright; BE_TEST_PYTHON tới Python của venv nếu cần.
BE_BROWSER_CHANNEL mặc định chrome; có thể đặt chromium sau khi cài browser tương ứng.
Script tự tạo DB synthetic riêng, tự chạy/dừng server; không ghi vào DB nghiên cứu đang dùng.

Các thay đổi chính: persistence.py, state.py, widgets.py, snapshots.py, pipeline.py,
imports.py, reporting.py, ui.py, tests/test_state_consistency.py, các benchmark/E2E scripts và CI.
Chưa commit/push; không có commit hash cho đợt sửa này.
