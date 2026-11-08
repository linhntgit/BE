# Sửa lỗi persist_state khi khởi chạy ngoài môi trường dự án

Ngày kiểm tra: 30/10/2026, Australia/Perth.

Traceback thực tế dùng Python 3.10.11 tại Python310 và Streamlit 1.58.0.
Signature của radio/text_input ở môi trường này không có persist_state.
Môi trường .venv của dự án là Python 3.12.14, Streamlit 1.66.1 theo lockfile.

Đã bỏ persist_state khỏi navigation và widget adapters. Việc giữ input dùng ProjectState,
drafts và journal bền vững đã kiểm chứng, không phụ thuộc tham số tùy chọn của widget.
app.py kiểm tra runtime trước khi import UI; môi trường ngoài cấu hình được thông báo rõ
phiên bản đang chạy và lệnh khởi động đúng, không để lỗi API xuất thành traceback.

run_app.cmd luôn gọi .venv/Scripts/python.exe với UTF-8 và working directory của dự án.
Không nâng cấp thư viện Python toàn máy hoặc thay đổi dữ liệu nghiên cứu.

Kiểm chứng:

- 146 pytest tests đạt, 0 failed/skipped; Ruff và mypy đạt.
- 19/19 scientific golden comparisons đạt.
- 6 checkpoint E2E Chrome đạt sau khi bỏ persist_state: input/design, 3 ô editor,
  calculation snapshot, manifest, STALE và reload/reopen.
- AppTest bằng Python 3.10/Streamlit 1.58.0: 0 exceptions, hiển thị hướng dẫn runtime.
- run_app.cmd --help: exit code 0; launcher dùng interpreter .venv.

Dừng tiến trình Streamlit cũ bằng Ctrl+C, rồi chạy run_app.cmd hoặc
uv run --frozen streamlit run app.py. Không khởi động bằng streamlit toàn máy.
