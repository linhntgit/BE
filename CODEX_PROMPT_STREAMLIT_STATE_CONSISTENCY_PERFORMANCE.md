# PROMPT BẮT BUỘC CHO CODEX — STREAMLIT: KHÔNG MẤT DỮ LIỆU, KHÔNG LỆCH DỮ LIỆU TÍNH TOÁN, KHÔNG CHẬM

Bạn đang phát triển ứng dụng phân tích tương đương sinh học (BE) bằng Streamlit, gồm thiết kế nghiên cứu, nhập Cplasma, NCA, ABE/EMA ABEL/FDA RSABE và báo cáo CTD. Giao diện tiếng Việt. **Yêu cầu ưu tiên P0, áp dụng cho toàn bộ các tab/page, không chỉ một màn hình:** (1) dữ liệu người dùng vừa chỉnh sửa không bị mất khi rerun, chuyển tab, chuyển page, ẩn/hiện biểu mẫu hoặc lưu/mở dự án; (2) số liệu thực sự được dùng để tính toán phải trùng khớp với bộ dữ liệu đầu vào được thể hiện rõ ràng trên giao diện; (3) cơ chế đảm bảo tính đúng đắn không được làm ứng dụng chạy chậm vô lý.

## 1. Nguyên tắc kiến trúc bắt buộc

1. Áp dụng **single source of truth**: mỗi dự án có `ProjectState` (hoặc domain state tương đương) độc lập với vòng đời của widget. Dữ liệu nghiên cứu và dữ liệu tính toán chỉ lấy từ domain state đã xác nhận, không lấy trực tiếp từ biến mặc định trong hàm render, từ `st.data_editor` trong một lần rerun tùy ý, hoặc từ các widget key có thể bị Streamlit dọn dẹp.
2. Phân biệt rành mạch: **widget state** (trạng thái giao diện tạm thời), **draft/pending edits** (nếu có), **committed domain state** (dữ liệu đầu vào chính thức) và **result snapshot** (bộ đầu vào đã thực sự dùng để chạy phân tích). Đừng xây dựng các bản sao trạng thái không có quy tắc đồng bộ.
3. Tất cả thay đổi phải đi theo một luồng thống nhất: `UI edit -> validate -> commit/record pending -> increment affected revision -> invalidate dependent results -> calculate from immutable snapshot -> show/report result tagged with snapshot revision`. Chỉ được thay đổi đầu vào khi có thao tác có chủ đích của người dùng hoặc thao tác import/restore được kiểm tra.
4. `initialize_project_state()` **chỉ khởi tạo nếu dữ liệu chưa tồn tại**. Tuyệt đối không để mỗi lần render/rerun lại gán default, tự nạp lại file cũ hoặc đè dữ liệu đang chỉnh sửa. Key phải ổn định, duy nhất theo `project_id / study_id / entity_id / field`; không dựa vào vị trí widget hay index hàng có thể đổi.
5. Không coi `st.session_state` là lưu trữ bền vững khi người dùng reload browser, hết session hoặc đổi máy. Xây lớp lưu/mở dự án (ví dụ SQLite + file dữ liệu theo dự án, hoặc archive ZIP có manifest), ghi dữ liệu theo giao dịch/atomic save và có kiểm tra schema/version. Đừng ghi toàn bộ dataset lớn ra đĩa trên *mọi* rerun.

## 2. Chống mất dữ liệu khi chuyển tab/page

1. Đọc và tuân thủ hành vi widget lifecycle của **phiên bản Streamlit thực tế được khóa trong dự án**. Widget có thể mất state khi không còn được render hoặc khi đổi page. Nếu phiên bản hỗ trợ `persist_state="session"`, có thể dùng cho widget thích hợp, nhưng **không dùng đây làm bảo đảm duy nhất**, đặc biệt vì `st.data_editor`, file upload và một số widget không hỗ trợ. Dữ liệu nguồn vẫn phải ở domain state độc lập.
2. Với input đơn giản (`number_input`, `selectbox`, `text_input`, v.v.), dùng key ổn định và callback `on_change`/adapter đồng bộ giá trị sang domain state ngay khi edit được xác nhận. Nếu dùng key tạm (ví dụ `_ui_*`), khởi tạo UI từ domain state khi widget được dựng lại và commit ngược đúng một chiều; không ghi đè widget bằng default trong mỗi rerun. Tránh cả vòng lặp callback lẫn lỗi ghi vào key sau khi widget đã tạo.
3. Với `st.data_editor` (đặc biệt bảng Cplasma hàng nghìn dòng), thiết kế adapter riêng: dùng định danh bất biến `record_id`/`sample_id`; xác nhận thứ tự hàng, thay đổi schema, thêm/xóa hàng và thay đổi kiểu dữ liệu; xử lý chính xác edit diff hay DataFrame trả về theo API/phiên bản đang dùng. **Không giả định `st.session_state[editor_key]` luôn là toàn bộ DataFrame đã sửa**. Không dựng lại editor từ DataFrame gốc làm mất edit. Kiểm thử nhiều lần edit liên tiếp rồi đổi tab ngay.
4. Không dùng `st.form` một cách khiến giá trị chưa submit trông như đã lưu. Nếu dùng nút **Áp dụng/Lưu thay đổi** cho một nhóm input, màn hình phải hiển thị rõ `Chưa áp dụng` và phải ngăn ngừa mất draft khi điều hướng (chặn/nhắc lưu hoặc có cơ chế giữ draft thực sự). Đối với sửa một giá trị đơn lẻ, ưu tiên tự commit sau khi widget xác nhận thay đổi, không cần người dùng bấm nút lưu từng ô.
5. Nhập file CSV/Excel phải đưa dữ liệu đã parse và xác nhận vào domain state. Object từ `st.file_uploader` chỉ là widget/input tạm, không phải kho lưu dự án. Sau khi import thành công, chuyển page hay rerun không được import lại hoặc mất dữ liệu. Ghi `source_file`, import timestamp, fingerprint và các cảnh báo làm sạch dữ liệu.
6. Với nhiều tab/conditional UI, chỉ khởi tạo UI từ canonical state khi thực sự cần; việc ẩn/hiện field, đổi lựa chọn nghiên cứu, chuyển tab NCA/ABE/ABEL/RSABE hoặc thay đổi cấu trúc trang không được reset những trường không liên quan. Không tính toán nặng vì `st.tabs` mặc định render nội dung tất cả tab.

## 3. Bảo đảm dữ liệu hiển thị = dữ liệu được tính toán

1. Viết các hàm thuần `run_nca(input_snapshot)`, `run_abe(input_snapshot)`, `run_ema_abel(input_snapshot)`, `run_fda_rsabe(input_snapshot)`; không đọc trực tiếp widget/session state bên trong lõi thống kê. Các phép tính luôn nhận **cùng một snapshot đã validate** từ domain state, có `input_revision`, `dataset_revision`, `config_revision`, `input_fingerprint`/hash và provenance.
2. Sau một thay đổi đã commit (ví dụ Cplasma, thời gian lấy mẫu, LLOQ/BLQ, treatment, period, sequence, dosing time, cách xử lý dữ liệu, ngưỡng chấp nhận), đánh dấu **chỉ những kết quả phụ thuộc là `STALE`**. Không được tiếp tục hiển thị kết luận BE `PASS`/`FAIL` cũ như thể phản ánh số liệu mới. Có thể giữ kết quả cũ để tham khảo, nhưng phải ghi rõ **Kết quả từ phiên bản dữ liệu trước** và vô hiệu hóa xuất báo cáo chính thức cho đến khi tính lại hoặc có chính sách snapshot được hiển thị minh bạch.
3. Màn hình kết quả phải chỉ ra phiên bản/fingerprint dữ liệu đầu vào đã dùng, thời điểm chạy, cấu hình NCA/statistical model, guideline/jurisdiction version. Ở màn hình nhập liệu, hiển thị trạng thái `Đã lưu/Chưa áp dụng/Cần tính lại`; có chức năng xem bảng đầu vào thực sự dùng để phân tích để đối chiếu 1:1, nhất là Cplasma.
4. Một thao tác tính toán phải “chốt” snapshot ngay lúc bắt đầu. Nếu người dùng sửa đầu vào trong lúc tác vụ đang chạy, kết quả cũ chỉ được gắn với revision cũ; không ghi đè nhầm thành kết quả mới. Việc load lại project, sửa dữ liệu rồi chạy lại không được tái sử dụng kết quả đã cache của revision khác.
5. Xuất Word/PDF/Excel/CTD phải dùng **chính result snapshot đã tính và kiểm tra**, không tự đọc một tập widget/default khác để tính lại âm thầm. Kèm manifest đầu vào, revision/hash, tham số và phiên bản thuật toán; bảo đảm con số trên báo cáo bằng màn hình kết quả của đúng snapshot đó.
6. Đặt assert/validation ở ranh giới UI → domain, domain → calculation, calculation → report. Với lỗi không khớp phiên bản dữ liệu, phải báo lỗi rõ ràng và từ chối công bố kết luận sai, không âm thầm fallback sang default.

## 4. Hiệu năng bắt buộc

1. **Không chạy NCA/ANOVA/ABEL/RSABE hay tạo CTD trên mỗi lần người dùng gõ phím hoặc chuyển tab.** Chỉ tính khi bấm `Phân tích/Tính lại`, hoặc cập nhật có chọn lọc phần đủ nhẹ và được kiểm soát. Rerun UI được phép nhưng không được kéo theo tính toán nặng không liên quan.
2. Tách logic tính toán ra khỏi render; dùng `st.fragment` khi tương thích để cô lập phần rerun cần thiết; dùng `st.form` cho chỉnh sửa theo lô khi có quy trình submit/draft rõ ràng. Tránh `st.rerun()` lặp, gọi lại rerun trong callback không cần thiết và ghi đè state hai chiều.
3. Dùng `st.cache_data` cho hàm thuần, xác định và có cache key gồm mọi đầu vào ảnh hưởng kết quả (dataset revision/fingerprint, option, version thuật toán, guideline). Cần cân nhắc chi phí hash/serialize/copy DataFrame; **không full hash hoặc deepcopy tập Cplasma lớn ở mỗi lần rerun**. Tạo fingerprint tại ranh giới commit/import/calculate hoặc dùng revision đáng tin cậy, rồi tái sử dụng. Không dùng cache toàn cục chứa mutable project state giữa các user.
4. Tách dependency graph: sửa một mẫu chỉ invalidates NCA profile liên quan, rồi các phân tích aggregate phụ thuộc; sửa tuỳ chọn báo cáo không phải tính lại NCA; sửa tỷ lệ dự kiến T/R ở thiết kế không phải chạy lại phân tích Cplasma thực nghiệm nếu không phụ thuộc. Tối ưu theo profile/study và đo số lần tính lại.
5. Với bảng lớn: lưu dữ liệu theo cấu trúc ổn định, tính delta/patch nếu phù hợp, phân trang/virtualization nếu cần. Chỉ copy snapshot tại ranh giới thực sự cần để bảo vệ tính nhất quán, không copy toàn bộ data trên mỗi render. Không ghi đồng bộ toàn bộ archive sau từng ô sửa; checkpoint có chủ đích hoặc cơ chế autosave giới hạn tần suất nhưng không đánh đổi khả năng khôi phục dữ liệu.
6. Dùng `st.cache_resource` chỉ cho đối tượng tài nguyên dùng chung và an toàn đồng thời (nếu thật sự cần), **không** cho mutable dữ liệu dự án người dùng. Lập bảng benchmark trước/sau để chứng minh cải thiện latency và số phép tính lại.

## 5. Kiểm thử hồi quy bắt buộc

Tạo unit + integration + E2E (ưu tiên Playwright/Streamlit AppTest nếu phù hợp), có fixtures tự chứa trong repository, độc lập mạng và kiểm thử ít nhất các trường hợp sau:

- [ ] Nhập `CVintra=24.7`, `T/R=0.93`, đổi tab/page rồi quay lại: giá trị vẫn đúng trong widget và domain state; thiết kế dùng chính các giá trị đó.
- [ ] Sửa một ô `Cplasma` của subject A, period 2; chuyển ngay sang tab NCA và trở lại: ô hiển thị đúng, tính toán NCA nhận đúng giá trị; AUC/Cmax và kết quả tổng hợp bị invalidated phù hợp.
- [ ] Sửa liên tiếp 3 ô trong `st.data_editor`, thêm/xóa/sắp xếp hàng (nếu tính năng cho phép), đổi tab và lưu/mở project: không mất, lệch hàng hay ghi sai mẫu.
- [ ] Đổi thiết kế từ `2×2` sang `replicate` rồi quay lại (nếu được phép): dữ liệu tương thích được giữ; dữ liệu không tương thích phải được cảnh báo và yêu cầu xác nhận trước khi chuyển, không âm thầm xóa.
- [ ] Import CSV, chỉnh sửa dữ liệu đã import, đổi page, chạy NCA, xuất báo cáo: các giá trị đầu vào thực sự dùng và số liệu ở báo cáo khớp với dữ liệu đã sửa.
- [ ] Khi đổi một input làm đổi kết quả, trạng thái cũ phải thành `STALE`, không được hiển thị `PASS` cũ như kết luận hiện hành; chỉ bản tính mới có quyền kết luận hiện hành.
- [ ] Hai user/session và hai project độc lập không bị rò/cross-contaminate state hoặc cache; project reload không làm kết quả cũ được nhận nhầm là hiện hành.
- [ ] So sánh **UI current committed state**, **calculation snapshot**, **saved project**, **report manifest**: các biến/hàng liên quan phải khớp revision/hash hoặc có cảnh báo draft/STALE rõ ràng.
- [ ] Test benchmark: sửa 1 trường nhẹ/đổi tab không được gọi lại full NCA + thống kê; đếm số lần rerun, tính lại và thời gian phản hồi cho dataset nhỏ và lớn. Thiết lập ngưỡng latency dựa trên baseline đo thực tế, tránh cam kết số mili giây vô căn cứ.
- [ ] Test lỗi/khôi phục: input invalid, callback exception, điều hướng trước submit, reload session, lưu mở archive, phiên bản schema cũ; không ghi nửa dữ liệu hoặc báo kết quả chưa xác thực.

## 6. Quy trình triển khai Codex và tiêu chí nghiệm thu

1. **Trước khi sửa**, audit luồng dữ liệu thực tế ở tất cả tab/page: nơi khởi tạo state, nơi gán default, callback, `st.data_editor`, forms, import, load/save, điều kiện tính toán, cache, report. Liệt kê bug/rủi ro theo vị trí file + chức năng, có cách tái hiện và impact.
2. Đề xuất thiết kế state tối giản, ưu tiên tái sử dụng module hiện có và **không thay đổi thuật toán BE/NCA đã được xác nhận chỉ để sửa state**. Sửa theo từng lớp UI adapter → canonical state → calculation snapshot → report, kèm regression test đúng ranh giới.
3. Viết code triển khai thực sự, không chỉ nêu nguyên tắc. Có module quản lý ProjectState, công cụ mutation/revision/invalidation và adapters cho widget + editor; bổ sung hiển thị trạng thái dữ liệu/kết quả bằng tiếng Việt.
4. Chạy test tự động và benchmark thực tế; ghi lại lệnh chạy, kết quả pass/fail, số lỗi còn tồn tại, performance before/after và các giới hạn chưa xử lý. Không tuyên bố “đã fix” nếu chưa kiểm chứng tình huống đổi tab và tính toán bằng dữ liệu sửa mới.
5. **Definition of Done:** (a) không mất dữ liệu đã commit khi chuyển tab/page hoặc rerun; (b) không có mismatch âm thầm giữa input hiển thị và input thực tính; (c) không có kết luận BE hiện hành từ dữ liệu cũ; (d) các sửa đổi nhẹ không kích hoạt lại tính toán nặng; (e) lưu/mở project và báo cáo giữ được provenance; (f) E2E và regression tests pass.

**Ưu tiên giải pháp đúng, đơn giản, ít overhead. Không giải quyết bằng cách `deepcopy` tất cả state hoặc `st.rerun()`/ghi file mỗi khi tương tác. Nếu Streamlit có giới hạn kỹ thuật với một widget, phải trình bày giới hạn và xây adapter/UX đúng thay vì phỏng đoán state đã được lưu.**

### Tài liệu chính thức cần kiểm tra đúng theo phiên bản được khóa

- Widget lifecycle và persistence: https://docs.streamlit.io/develop/concepts/architecture/widget-behavior
- Multipage widget state: https://docs.streamlit.io/develop/concepts/multipage-apps/widgets
- `st.data_editor`: https://docs.streamlit.io/develop/api-reference/data/st.data_editor
- Session State: https://docs.streamlit.io/develop/concepts/architecture/session-state
- Caching: https://docs.streamlit.io/develop/concepts/architecture/caching
