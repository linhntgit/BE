# Nghiệm thu UI cải tiến Phoenix

Ngày 31/10/2026. Database riêng: `output/phoenix_ui_qa.sqlite`; workbook tự sinh: `output/phoenix_ui_inputs/SYNTHETIC_full4_ln.xlsx`. Không dùng dữ liệu nghiên cứu thật; không coi dữ liệu QA là oracle qualification phương pháp.

## Terminal theo profile

Đã thao tác trên browser: nạp demo, mở NCA → rà soát từng profile, chọn S0001 kỳ 1 R; manual chọn 16.009093820277776, 23.997325107777776, 35.991015986111115 h; nhập reason/reviewer, preview rồi apply. Bảng so sánh giữ Automatic và Draft selection, terminal times, lambda_z, half-life, AUCinf và extrapolation. Biểu đồ semilog có observed >0, marker tròn tự động, marker hình thoi manual và hai đường fit/chú giải rõ ràng.

Đã đọc lại dự án QA từ đĩa: đúng một override với identity/data hash/reason/reviewer, raw_base64 giống revision trước, không có analysis run hoặc freeze được tự tạo. AppTest tương ứng cũng đạt. Nghiệm thu này không bao gồm mọi tổ hợp browser/độ phân giải.

## Import PK

Đã upload workbook giả lập, chọn sheet PK thứ hai thay Readme; thang Ln(PK), mapping participant/seq/visit/product/lnPeak/lnAUC; Capsule→R, Tablet→T; ABAB→TRTR, BABA→RTRT; xác nhận đơn vị. App cảnh báo khi lựa chọn sheet cũ 0 không còn tương thích và yêu cầu chọn lại, không tự thay dữ liệu.

Preview hiển thị subject 001/002 giữ số 0 đầu, sequence/treatment đúng mapping, PK được inverse Ln một lần. Đã chạy panel PK độc lập bằng EMA_HVDP_ABEL/full4, mở residual tab và checkbox plots. Bảng diagnostics mới ghi Units natural-log model scale cùng Source_PK_Units. Đã thấy lựa chọn mô hình EMA Method A; chưa xem đủ ba biểu đồ hoặc EMA reference-only trước gián đoạn.

## Hồi quy thao tác gỡ file

Khi rà callback phát hiện uploader None chưa xóa file đã stage. Đã sửa `stage_upload`: lưu None vào draft khi người dùng gỡ file, giữ mapping và canonical raw; không đổi dữ liệu hoặc xóa snapshot. AppTest tính PK trước rồi gọi đúng callback removal: source draft trống, phân tích mới disabled, cached results chuyển STALE, download disabled, giá trị cached không bị ghi đè. Chưa nghiệm thu browser cho removal sau sửa.

## Preset

AppTest chạy overview và nút Tạo dự án mới từ preset với database tạm: dự án mới giữ sheet/log/mapping nhưng không có raw/results/freeze/manual overrides/protocol/SAP/scope approval; yêu cầu xác nhận lại đơn vị; nguồn vẫn nguyên dữ liệu. AppTest seed upload draft vì không hỗ trợ file chooser; không ghi nhận đây là kiểm tra browser upload preset.

## Phần còn lại

- Browser hiện báo local browser use disabled trong Work settings. Cổng 8511 còn một server hiện hữu; không tạo trùng hoặc dừng tiến trình không xác nhận quyền sở hữu.
- Tiếp tục xem đầy đủ residual-fitted/QQ/box của EMA reference-only và supplementary Method A; preset upload/new project và stale/removal sau sửa.
- Word layout còn thiếu bundled soffice.exe; chưa render PNG và chưa xác nhận layout. PDF vi/en đã được kiểm tra riêng như checkpoint trước.

## Word đọc bổ sung

Sau khi người dùng cho phép tiếp tục mọi bước cần thiết, đã mở được Word và file QA reviewer_vi.docx có sẵn. Xem một phần trang 1/4 phát hiện Title thừa đường viền xanh và theme font override trong OOXML; generator đã bỏ border/theme để giữ font Arial tường minh. Sáu tests report/structure đạt. Đây chưa phải kiểm tra đầy đủ mọi trang hoặc render bản mới; không ghi nhận DOCX đã visual-qualified. File QA cũ không được lưu thay đổi.

## Nghiệm thu browser tiếp nối 31/10/2026

Browser đã hoạt động sau restart ứng dụng. Trên viewport 714px, thu sidebar để tránh overlay che nội dung. Đã xem đủ sáu plots residual-fitted/QQ/box cho EMA Method A và EMA reference-only R; nhãn/model-scale và dữ liệu R-only đúng. Đã gắn lại workbook qua file chooser thật rồi Remove: source draft trở thành null, cached result STALE, preview/calculation/download disabled. Đọc lại SQLite QA xác nhận raw nguyên vẹn, một terminal override, không có run mới, mapping Ln giữ lại. Chưa nghiệm thu preset hoặc latest Word layout trong mốc này.

## Preset qua browser thật

Đã chuẩn bị và tải preset từ dự án QA có một terminal override; file browser trả về C:/Users/linhn/Downloads/BE_method_preset.json. Đọc/validate file xác nhận schema/checksum hợp lệ, canonical design 2x2 và rule EMA_IR_NONREPLICATE_M13A (không lấy rule/design tạm của panel PK), giữ sheet PK/Ln/mapping, không raw hoặc manual slopes. Upload lại đúng file bằng file chooser rồi tạo dự án mới d7e2e95b-e6e1-4a25-8e45-09996ae70754. Đọc lại SQLite: không raw/results/freeze/protocol/SAP/scope approval/demo/manual override/staged input, chỉ event create_from_preset; units_confirmed false. Nguồn không đổi raw và vẫn giữ một override. Vòng download/upload/new-project đã nghiệm thu trên browser; không phải qualification khoa học.
