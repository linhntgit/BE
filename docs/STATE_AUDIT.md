# Audit trạng thái trước thay đổi

Ngày 29/10/2026. Đã đọc toàn bộ CODEX_PROMPT_STREAMLIT_STATE_CONSISTENCY_PERFORMANCE.md.
Runtime khóa: Streamlit 1.66.1, Python 3.12.14. Công thức trong nca.py/statistics.py/design.py
được giữ nguyên trong đợt sửa state.

| Vị trí trước sửa | Cách tái hiện | Tác động |
|---|---|---|
| ui.py overview/create_study, revision | Nhập một trường, không submit, đổi trang rồi quay lại | Form chưa gửi không nằm trong domain; không có thông báo draft, mất nhập liệu |
| ui.py design_page/sample_size | CV AUC=24.7, GMR=.93, đổi trang trước submit | Trở về default 20/.95; domain chỉ giữ kết quả plan cũ, không giữ input đang sửa |
| ui.py randomization_page | Đổi seed/block/lịch planned, đổi trang | Các input dựng lại bằng default; xuất Excel tính lại mỗi rerun |
| ui.py import_page | Chọn file, đổi trang trước import | Uploader là kho duy nhất của bản xem trước; mapping và convert reset; parse lại mỗi rerun |
| ui.py qc_page | Truy cập QC hoặc thay field correction | parse/clean/QC toàn bộ dataset; correction định danh bằng row index; chưa có editor theo sample ID |
| ui.py nca_page | Có run, tạo revision/correction/config mới rồi quay lại NCA | Bảng cũ vẫn hiện thiếu nhãn STALE; cấu hình submit dựng NcaConfig từ vài field làm reset field không hiển thị |
| ui.py be_page | Xem run cũ sau sửa input | Có cảnh báo hash nhưng vẫn đặt kết luận cũ ở tiêu đề; hash lại toàn input mỗi render |
| ui.py plots_page | Sửa input sau một run | Đồ thị cũ thiếu nhãn revision; người dùng dễ hiểu nhầm là dữ liệu hiện hành |
| ui.py reports_page | Sửa input rồi xuất report | Không chặn stale; report/artifact/Excel/ZIP sinh trong render; toàn snapshot bị verify/hash lại |
| ui.py save_project | Mỗi thay đổi | Dump/validate/save toàn project + st.rerun; không có lightweight journal/checkpoint |
| persistence.py Project.record/input_hash/qc | Một sửa nhẹ khi project có dataset/runs lớn | Serialize/hash toàn state, reparse raw và QC; chưa có dependency revisions |
| pipeline.py run_analysis | So snapshot validated_data với số thực dùng bởi NCA | to_json(double_precision=15) mất bit số so với float64 được tính; thiếu revision chốt lúc bắt đầu |
| ui.py restore archive | Store.save lỗi/conflict sau import | Session bị thay project trước khi lưu thành công |
| Toàn bộ UI | Hai project có widget labels/form keys giống nhau | Key không namespace theo project/entity; chưa có regression isolation |

## Thiết kế sửa

Project vẫn là canonical domain. Bổ sung revisions, planning/preferences, draft bền vững và
fingerprint được cập nhật tại commit; ProjectState theo session giữ cache chỉ của project đó.
Adapter input lưu draft/commit có kiểm chứng, không lấy default làm dữ liệu tính toán.
Editor fixed rows dùng sample_id bất biến, diff được ràng buộc vào baseline/schema/row identity;
không hỗ trợ thêm/xóa hàng, không coi Session State diff là DataFrame. Correction theo batch
có review trước áp dụng; pending được giữ qua điều hướng, archive và reload.
SQLite journal ghi patch nhỏ theo transaction/optimistic revision; checkpoint đầy đủ theo thao tác chủ đích.
Calculation nhận immutable validated snapshot; cache profile chỉ trong session/project và kiểm tra đầy đủ key.
Mọi trang kết quả/report dùng một trạng thái CURRENT/STALE/LEGACY rõ ràng; stale bị chặn report.

## Tài liệu đã kiểm tra

- Streamlit package docs 1.66.1: session-state.md, data-display.md, performance.md.
- https://docs.streamlit.io/develop/concepts/architecture/widget-behavior
- https://docs.streamlit.io/develop/concepts/multipage-apps/widgets
- https://docs.streamlit.io/develop/api-reference/data/st.data_editor
- https://docs.streamlit.io/develop/concepts/architecture/session-state
- https://docs.streamlit.io/develop/concepts/architecture/caching

API data_editor của 1.66.1 không có persist_state; dùng adapter độc lập vòng đời widget.
Đo baseline và kết quả sau sửa bằng scripts/state_benchmark.py; không cam kết latency tuyệt đối trước khi đo.
