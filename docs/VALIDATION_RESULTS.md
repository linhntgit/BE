# Kết quả kiểm chứng bản phát triển 0.1.0

Ngày kiểm tra: 29/10/2026, Australia/Perth. Không phải báo cáo thẩm định GxP.

Đây là bằng chứng giai đoạn đầu. Đợt cập nhật state ngày 30/10/2026 có **141 tests đạt**,
19 golden comparisons và browser E2E; xem [STATE_CONSISTENCY_RESULTS.md](STATE_CONSISTENCY_RESULTS.md).

## Kết quả cuối

| Kiểm tra | Kết quả |
|---|---|
| pytest trong môi trường Python 3.12 sạch, từ lockfile | 112 passed, 0 failed, 0 skipped, 19.90 giây |
| Public golden benchmark | 19/19 passed; expected/actual trong benchmark_results.csv |
| Ruff lint và quy tắc security chọn lọc | Đạt |
| Mypy engine và UI | Đạt |
| Dependency audit requirements lock có hash | Không phát hiện lỗ hổng đã biết tại thời điểm kiểm tra |
| Giao diện Streamlit AppTest | Toàn bộ 11 trang, demo → QC → freeze → NCA/BE đạt |
| PDF | Render bằng Poppler; kiểm tra ảnh trang mẫu tiếng Việt, không thấy cắt bảng/lỗi dấu |
| DOCX | Kiểm tra OOXML/tables/Unicode đạt; chưa render được vì thiếu LibreOffice trong runtime |
| CI từ xa | Chưa chạy; chỉ tạo workflow tự động và chạy các bước tương ứng cục bộ |

Runtime kiểm chứng cuối: Python 3.12.14, NumPy 2.2.6, pandas 2.3.3, SciPy 1.15.3,
Streamlit 1.66.1. Toàn bộ phụ thuộc transitive và hashes trong uv.lock/requirements.lock.
Audit kiểm tra 83 dependencies, 0 skipped, không có vulnerability được báo cáo.
Đã nâng Pillow lên 13.0.0 và filelock lên 4.2.4 để xử lý findings của audit ban đầu.
Không bỏ qua CVE bằng ignore list. Kết quả security không chứng minh không tồn tại lỗ hổng chưa biết.

## Lệnh đã thực hiện

```powershell
uv sync --locked --extra dev --python <Python 3.12>
.venv/Scripts/python.exe -m pytest -q --basetemp=.cache/pytest-release --junitxml=output/test-results.xml
.venv-clean/Scripts/ruff.exe check .
.venv-clean/Scripts/mypy.exe be_app --no-error-summary
.venv-clean/Scripts/python.exe scripts/benchmark.py
.venv-clean/Scripts/python.exe -m pip_audit -r requirements.lock --require-hashes --disable-pip --cache-dir .cache/pip-audit -f json -o output/security-audit.json
```

Đường dẫn Python/runtime đầy đủ chỉ được dùng khi thiết lập máy hiện tại;
tests và fixtures không phụ thuộc các đường dẫn này. Trên máy khác dùng uv và README.
Sandbox Windows với Python 3.12 chặn tạo thư mục TEMP mặc định ở một lượt chạy;
kiểm thử cuối dùng thư mục tạm trong workspace. Đây là lỗi thiết lập môi trường,
không bị bỏ qua hoặc đánh dấu skip trong kết quả cuối.

## Bằng chứng độc lập và dung sai

Bảng expected/actual/difference/tolerance/source nằm trong `benchmark_results.csv`.
Nguồn và precision của fixture nằm trong `tests/fixtures/golden.json` và provenance JSON.
Power đối chiếu PowerTOST, NCA AUC/Cmax/Tmax/Tlast/Clast đối chiếu PKNCA public vignette;
ABE 2×2 đối chiếu R BE với N=33 và sequence 16/17, kiểm tra thêm OLS full matrix
trên nhiều mức imbalance; parallel đối chiếu statsmodels pooled và Welch TOST.
Lambda-z/extrapolation đối chiếu thêm với public PKNCA khi chọn policy giống nguồn.
Ví dụ này có adjusted R² thấp nên không được dùng để hạ ngưỡng QC mặc định của engine.
Analysis snapshot lưu phiên bản thư viện và nội dung/hash uv.lock để archive có thể truy xuất môi trường.

## Tình trạng bàn giao

Đã khởi tạo Git repository; chưa tạo commit, không push remote. Chưa có commit hash.
File đặc tả đầu vào được giữ nguyên. Mã nguồn mới gồm app.py, be_app/*.py, tests/*,
scripts/*, cấu hình CI/Streamlit, lockfiles và tài liệu docs/*; dữ liệu examples/* có nhãn SYNTHETIC.
Các file DB, môi trường ảo và artifact QA không được đưa vào Git.
SHA256 đặc tả đầu vào: `11fe2591679a25076f1fde2510de474b1918cca2beb4e5e4f29bbf3a8e9488ae`.

Sprint 0 và nền tảng Sprint 1 đã triển khai có thể chạy/kiểm tra. Các điều kiện nghiệm thu
còn thiếu của Sprint 1 và phần Sprint 2–4 được liệt kê cụ thể trong BACKLOG.md.
Không tuyên bố hoàn tất Definition of Done toàn đặc tả hoặc sẵn sàng dùng nộp hồ sơ.
