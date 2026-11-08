# Hướng dẫn học thử BE và PK bằng dữ liệu tổng hợp

## Nguyên tắc

Mọi nút **Điền dữ liệu mẫu** chỉ đưa dữ liệu tổng hợp vào các ô/bảng nhập liệu thông thường.
Nút không tự lưu dự án, không tự nhập dữ liệu raw, không tự chạy QC/phân tích hay đưa ra kết luận.
Người học có thể thay đổi từng ô, dán từ Excel, sửa hoặc thêm/xóa dòng tại các bảng có editor,
rồi bấm **Áp dụng chỉnh sửa bảng** trước khi kiểm tra/đánh giá. Cách nhập và các nút thao tác
sau đó giống với khi sử dụng dữ liệu thật.

Đối với dữ liệu tổng hợp, mục đích là `training_qa`, provenance ghi rõ synthetic; kết quả BE
ở cấp nghiên cứu luôn **NOT EVALUABLE** dù phép tính thống kê endpoint có thể hiển thị.
Các tình huống NTI/HVD chỉ là bài tập, người học vẫn phải xem guideline/PSG, SAP, điều kiện
scaling và bằng chứng cần thiết.

## Bài 1 — Toàn quy trình BE

1. Vào **Tổng quan / Quản lý nghiên cứu**, chọn một trong sáu tình huống **Crossover 2×2**,
   **Song song**, **Replicate 3 kỳ**, **Replicate 4 kỳ**, **NTI** hoặc **HVD**.
2. Bấm **Điền dữ liệu mẫu vào biểu mẫu nghiên cứu**, đọc và có thể sửa các trường. Bấm
   **Tạo nghiên cứu** khi đã sẵn sàng. Nếu muốn chuyển lại nhập nghiên cứu thực, bấm
   **Làm trống biểu mẫu nghiên cứu** trước khi tạo.
3. Sang **Thiết kế và cỡ mẫu BE** để kiểm tra giả định; sang **Ngẫu nhiên hóa và lịch lấy mẫu**,
   lập và lưu danh sách phân nhóm.
4. Sang **Nhập dữ liệu nồng độ**. Chọn tình huống bên dưới, bấm **Điền dữ liệu mẫu vào bảng
   nồng độ**. Chỉnh sửa và bấm **Áp dụng chỉnh sửa bảng** nếu cần, kiểm tra mapping/đơn vị;
   bấm **Kiểm tra cấu trúc và QC**, đọc báo cáo rồi quyết định **Nhập và lưu raw bất biến**.
5. Tiếp tục **QC → Data Freeze → NCA → Thống kê BE → Báo cáo DRAFT** qua các nút thông thường.
   Không bỏ qua lỗi chặn, xác nhận phạm vi, yêu cầu duyệt và kiểm tra dữ liệu.

**Chọn tình huống nồng độ theo mục tiêu học:**

| Tình huống | Nội dung thực hành |
| --- | --- |
| Bảng hợp lệ | Kiểm tra 16 cột, preflight, QC và nhập raw. |
| Khác biệt T/R lớn | Quan sát ước lượng và khoảng tin cậy khi T/R lệch nhiều. |
| Các mẫu BLQ | Xem đánh dấu BLQ, LLOQ, phân tích NCA. |
| Thiếu một mẫu / thiếu một kỳ | Phát hiện thiếu dữ liệu, không tự điền giá trị. |
| Mẫu trùng | Đọc lỗi QC, sửa trong editor, áp dụng rồi QC lại. |
| Đơn vị µg/mL | Kiểm tra phép đổi sang ng/mL và dấu vết xác nhận. |
| NTI / HVD | Rà soát rule, độ biến thiên, điều kiện giới hạn hẹp hoặc scaling. |

Nút nạp nồng độ được khóa khi chưa có phân nhóm hoặc đang mở nghiên cứu thật. Để thực hành,
hãy tạo một nghiên cứu demo theo Bước 1 và lập phân nhóm trước.

## Bài 2 — BE nhanh

Chọn luồng **BE nhanh — phân tích độc lập**. Có chín tình huống: **nồng độ → NCA → BE**,
**bảng Cmax/AUClast**, **T/R lệch nhiều**, **replicate 3 kỳ**, **replicate 4 kỳ**,
**NTI**, **HVD**, **thiếu một endpoint** và **tên cột không chuẩn**.
Sau khi bấm **Điền dữ liệu mẫu vào bảng BE nhanh**, dữ liệu xuất hiện tại vùng dán CSV/TSV
và editor. Xem/tự sửa bảng, bấm **Áp dụng chỉnh sửa bảng**, kiểm tra mapping tên cột,
nhãn T/R, sequence, thiết kế và rule, sau đó chủ động chạy phân tích BE.

Đặc biệt với bài **tên cột không chuẩn**, chọn mapping `Peak → Cmax` và
`Exposure → AUClast`. Với bài **thiếu endpoint**, xem cờ cảnh báo và điều kiện đánh giá.

## Bài 3 — Bảng PK cho thống kê BE độc lập

Mở **Thống kê BE — EMA / FDA**, phần **Phân tích bảng PK cho replicate, HVD và NTI**.
Chọn một trong bảy bài: **Cmax/AUClast**, **T/R lệch nhiều**, **replicate 3 kỳ**,
**replicate 4 kỳ**, **NTI**, **HVD**, **thiếu endpoint**. Bấm **Điền dữ liệu mẫu vào bảng PK**;
dữ liệu được đưa vào cùng nguồn bảng PK như khi tải CSV/XLSX thật. Người học có thể sửa
bảng nguồn, bấm **Áp dụng chỉnh sửa bảng**, chọn sheet/thang đo/mapping và xác nhận đơn vị.
Sau đó bấm **Xem trước mapping bảng PK** và **Phân tích bảng PK đã tải** khi sẵn sàng.

Đây là phiên thống kê độc lập để đối chiếu; không ghi đè raw hoặc kết luận của nghiên cứu chính.

## Bài 4 — Phân tích PK độc lập

Mở **Phân tích PK độc lập**, chọn một trong bảy tình huống: **đơn liều uống**, **IV bolus**,
**đa liều 10 liều / τ=12h**, **steady-state giả định**, **BLQ**, **thiếu điểm pha cuối**,
**trùng thời điểm**. Bấm **Điền dữ liệu mẫu vào bảng PK**; kiểm tra bảng, chỉnh sửa,
áp dụng và rà soát đường dùng, chế độ liều, khoảng cách liều và thời điểm.
Bấm **Chạy phân tích PK** theo cách thông thường. Với bài trùng thời điểm, nút chạy
phải bị khóa đến khi người học sửa lỗi và áp dụng lại bảng. Với steady-state,
không tự xác nhận đã đạt trạng thái ổn định chỉ vì nguồn là demo.

## Kiểm tra kết quả học tập

Sau mỗi bài, người học nên giải thích: dữ liệu nguồn gồm những cột gì, những chỉnh sửa nào
đã được áp dụng, tại sao một cảnh báo/lỗi chặn xuất hiện, cần xác nhận những giả định nào,
và khi nào kết luận thống kê không đồng nghĩa với kết luận BE cho nghiên cứu thực.
Giữ tệp dự án demo/tệp xuất tách biệt khỏi dữ liệu nghiên cứu thực.
