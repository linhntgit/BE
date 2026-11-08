# Phân tích dược động học độc lập từ bảng Cplasma

## Mục đích và phạm vi

Trang **Phân tích PK độc lập** được mở từ thanh điều hướng ngay cả khi chưa tạo nghiên cứu BE.
Kết quả chỉ phục vụ phân tích kỹ thuật, đánh giá và giảng dạy; chưa có qualification độc lập
cho quyết định nghiên cứu/quản lý. Các bảng PK đơn độc không được đưa vào pipeline thống kê BE.

Đầu vào là nồng độ huyết tương theo thời gian sau **một liều hoặc nhiều liều bằng nhau,
cách đều**. Chế độ nhiều liều có thể phân tích chu kỳ cuối và, khi được xác nhận bên ngoài,
các thông số ở trạng thái ổn định. Chưa hỗ trợ hiệu chỉnh baseline phức tạp, thay đổi liều,
lịch liều không đều hay mô hình phi tuyến. Một lượt phân tích áp dụng **chung đường dùng,
liều, lịch dùng thuốc và đơn vị** cho toàn bộ hồ sơ.

## Hướng dẫn sử dụng

1. Mở **Phân tích PK độc lập**, nhập tay hoặc tải CSV/XLSX. File có thể dạng **long**
   (cột hồ sơ, thời gian, nồng độ, BLQ tùy chọn) hoặc **wide** (cột thời gian và một cột
   nồng độ cho mỗi hồ sơ). Chọn sheet và ánh xạ cột. `BLQ`, `<LLOQ` và `<LOQ` được nhận
   như ký hiệu BLQ; dữ liệu trống và điểm thời gian trùng trong một hồ sơ bị chặn.
2. Sửa/kiểm tra bảng, chọn **Đường uống**, **IV bolus** hoặc **IV infusion**; điền liều
   và đơn vị nếu biết. Với truyền IV phải nhập thời gian truyền (giờ). Nồng độ đầu vào
   có thể chọn ng/mL, µg/mL, mg/L, mg/mL; kết quả chuẩn hóa ng/mL, CL L/giờ, V L.
3. Chọn NCA hoặc mô hình 1/2 ngăn, trọng số và quy tắc NCA. Nhấn **Chạy phân tích PK**;
   xem bảng, biểu đồ tuyến tính/bán log và phần dư. Thay đổi đầu vào sau khi chạy sẽ
   khiến kết quả hiện tại bị đánh dấu cần chạy lại.
4. Lưu lịch sử vào SQLite riêng `data/pk_analysis.sqlite` (có thể đổi qua biến môi trường
   `PK_ANALYSIS_DATABASE`) hoặc tải Excel, Word, PDF và JSON. Có thể mở lại phiên đã lưu
   từ đầu trang; mỗi phiên lưu bất biến với kiểm tra toàn vẹn SHA-256.

Các file CSV mẫu **mô phỏng** (đơn liều và chu kỳ cuối đa liều đường uống,
10 liều cách 12 giờ) được cấp trong giao diện; không dùng làm dữ liệu nghiên cứu.

## Báo cáo Word/PDF có mục lục và hình minh họa

Từ kết quả NCA/mô hình ngăn hoặc từ phiên lịch sử, chọn **Xuất Word** hay
**Xuất PDF** trên trang **Phân tích PK độc lập**. Báo cáo tiếng Việt gồm trang
bìa, mục lục, tóm tắt phân tích, cấu hình/lịch liều, phương pháp, bảng NCA,
bảng tham số và tiêu chí khớp mô hình, đồ thị, cảnh báo, phụ lục dữ liệu và
nguồn tham khảo/truy xuất SHA-256.

- **Word (.docx):** có style chuẩn **Heading 1** và **Heading 2** để dùng
  Navigation Pane và tạo mục lục tự động. Mục lục đã chèn trường TOC; sau khi
  mở trong Microsoft Word, nhấn **Ctrl+A, F9** (hoặc chuột phải lên mục lục,
  chọn **Update Field**) để cập nhật mục và số trang.
- **PDF:** có mục lục với số trang và bố cục A4, header/footer, bảng nhiều
  trang và đồ thị nhúng; PDF dùng font Unicode để hiển thị tiếng Việt.
- **Hình minh họa:** vẽ từ các giá trị quan sát và mô hình có trong bản ghi
  hiện tại: đường nồng độ tuyến tính, bán log và phần dư khi có mô hình. Điểm
  BLQ được ký hiệu trên trục thời gian, không nối như nồng độ định lượng.
  Mỗi báo cáo trình bày tối đa 6 hồ sơ trên biểu đồ; khi có hơn 40 dòng dữ liệu,
  phụ lục Word/PDF hiển thị 40 dòng đầu, còn dữ liệu đầy đủ nằm trong Excel/JSON.

Tham khảo tổ chức báo cáo từ **ICH E3: Structure and Content of Clinical Study
Reports** (FDA/EMA) và ví dụ báo cáo lâm sàng/dược động học công khai từ
**FDA Clinical Pharmacology Review NDA 208215** và **EMA Apixaban Accord EPAR**.
Đây là mẫu trình bày tham khảo, không phải mẫu được FDA/EMA phê duyệt và
không thay thế báo cáo nghiên cứu đầy đủ hoặc thẩm định phân tích.

## Chế độ đa liều và trạng thái ổn định

1. Trong **Chế độ dùng thuốc**, chọn **Đa liều** hoặc **Trạng thái ổn định**. Điền
   khoảng cách đều `τ` (giờ), **tổng số liều thực dùng** từ liều đầu và đường dùng.
   Có thể bỏ chọn **Có thông tin liều mỗi lần** để chỉ tính NCA quan sát; độ thanh thải
   và khớp mô hình ngăn cần biết liều mỗi lần. Truyền IV
   yêu cầu thời gian truyền >0, không dài hơn `τ`. Liều đầu xảy ra tại giờ 0.
2. Chọn **Mốc thời gian của bảng Cplasma**: **Giờ sau liều cuối** khi chỉ có dữ liệu của
   chu kỳ cuối, từ `0` đến `τ`; hoặc **Giờ từ liều đầu** nếu có cả toàn bộ lịch dùng thuốc.
   Chế độ dùng giờ từ liều đầu sẽ lấy chu kỳ cuối là từ `(n−1)τ` đến `nτ`. Các hồ sơ phải
   cùng lịch liều. Không ghép các thời gian tương đối của các liều khác nhau vào một cột.
3. Với **IV bolus**, mẫu ở giờ 0 (hoặc đúng thời điểm liều cuối nếu tính từ liều đầu)
   được hiểu là **ngay sau tiêm (C0+)**. Mẫu tại cuối khoảng liều `τ` được hiểu là
   **trước liều kế tiếp**. Không nhập mẫu predose ngay trước liều cuối với cùng mốc giờ 0;
   phần mềm chặn AUC nếu C0 không phù hợp và loại mẫu 0 tại thời điểm bolus khỏi fit.
4. NCA tính **Cmax,τ, Tmax,τ, Cmin,τ quan sát**, trough đo tại `τ` nếu có,
   **AUCτ**, `Cavg,τ = AUCτ/τ`, **dao động (%) = (Cmax,τ − Cmin,τ)/Cavg,τ × 100**.
   AUCτ chỉ được tính nếu có **mẫu định lượng tại cả hai biên** và không có BLQ trong
   khoảng cuối. Không tự thêm mẫu, ngoại suy biên hoặc thay BLQ bằng 0 ở đa liều.
5. Trong chế độ **Trạng thái ổn định**, phải chủ động chọn xác nhận bằng chứng
   steady-state ngoài ứng dụng trước khi tính **CLss = Dose/AUCτ** đối với IV hoặc
   **CL/Fss = Dose/AUCτ** đối với uống. Chỉ thời gian dùng nhiều liều hoặc một chu kỳ
   dữ liệu không chứng minh đạt trạng thái ổn định. Chế độ **Đa liều** chỉ báo cáo kết quả
   quan sát trên chu kỳ cuối, không gọi đó là các thông số steady-state.
6. **Tỷ số tích lũy AUCτ,cuối/AUCτ,đầu** chỉ tính khi trạng thái ổn định được xác nhận,
   có cả hai khoảng đo hoàn chỉnh tính từ liều đầu; không tính đối với IV bolus khi
   C(τ−) và C(τ+) ở ranh giới liều đầu không thể phân biệt từ một mẫu đơn.
7. Mô hình 1/2 ngăn dùng **phép chồng chất tuyến tính hữu hạn**:
   `C(t) = Σ C_đơn_liều(t − iτ)` cho `i = 0…n−1`, bao gồm uống, IV bolus, IV infusion.
   Chúng khớp dữ liệu theo lịch đã khai báo, không tự thay thế bằng một trạng thái ổn định
   vô hạn liều; các tham số mô hình có thể thiếu định danh khi chỉ lấy mẫu một chu kỳ.

Kết quả và báo cáo nhiều liều lưu **snapshot phiên bản 2** cùng lịch liều; bản ghi
đơn liều phiên bản 1 vẫn được đọc. Cần so sánh các chu kỳ quan sát, trough qua các liều,
hoặc đánh giá độc lập khác để có bằng chứng đạt steady-state. Các kết quả này chỉ là
phân tích kỹ thuật, chưa thẩm định GxP.

## Công thức và lựa chọn phân tích

- AUC/AUMC tính theo hình thang tuyến tính hoặc tuyến tính tăng–log giảm. Lambda-z lấy từ
  đoạn cuối sau Cmax, ít nhất 3 điểm định lượng dương, adjusted R² ≥ ngưỡng chọn.
  AUC0–∞ = AUC0–last + Clast/lambda-z;
  AUMC0–∞ = AUMC0–last + Clast·(tlast/lambda-z + 1/lambda-z²).
- **IV bolus:** CL = Dose/AUC∞, Vz = CL/lambda-z, MRT = AUMC∞/AUC∞,
  Vss = CL·MRT. Nếu không có mẫu thời điểm 0, mặc định **không tính** AUC0–∞/CL;
  có tùy chọn tường minh ngoại suy C0 bằng hồi quy log tuyến tính của 3 điểm dương đầu.
  Nếu C0 tại t=0 bằng 0/BLQ, điểm đó không được xem là giá trị sau tiêm hợp lệ:
  phần mềm chỉ tính AUC0/CL khi người dùng chọn ngoại suy C0. Ngoại suy một hàm mũ
  ở thời điểm sớm có thể sai trong mô hình nhiều ngăn.
- **IV infusion:** CL = Dose/AUC∞, Vz = CL/lambda-z,
  MRT sau bolus tương đương = AUMC∞/AUC∞ − thời gian truyền/2 và Vss = CL·MRT đã hiệu chỉnh.
  Nếu thiếu mẫu t=0, người dùng có thể tường minh chọn giả định C(0)=0 khi bắt đầu truyền.
- **Uống:** CL/F = Dose/AUC∞, Vz/F = (CL/F)/lambda-z. Không suy ra F tuyệt đối,
  không áp công thức CL IV cho đường uống. Nếu thiếu mẫu t=0, tùy chọn C(0)=0
  chỉ được áp dụng sau khi chọn tường minh. Nồng độ predose >5% Cmax chặn tính
  thông số theo liều.
- BLQ trước mẫu định lượng đầu tiên hoặc sau mẫu định lượng cuối cùng được xem là 0
  trong tích phân NCA và được thông báo rõ; **BLQ xen giữa các mẫu định lượng bị chặn**
  khỏi NCA để tránh làm sai AUC. BLQ bị loại khỏi bình phương tối thiểu khi khớp mô hình.
- Mô hình **1 ngăn**: IV bolus đơn hàm mũ; IV infusion là tích chập đầu vào truyền
  đều; uống theo Bateman với hấp thu bậc một. **2 ngăn**: hàm đáp ứng hai mũ theo
  CL, Vc, Q, Vp (uống dùng CL/F, V/F, Q/F, Vp/F, ka).
  Tất cả tham số dương, giải `scipy.optimize.least_squares` trong miền log với
  nhiều điểm khởi tạo cố định; báo cáo RMSE, AIC/AICc/BIC và điều kiện Jacobian.
  AIC có trọng số chỉ dùng tham khảo giữa cùng tập quan sát/trọng số; nếu dữ liệu ít
  hoặc thiếu định danh thì cảnh báo, không tuyên bố mô hình được xác nhận.
- **Flip-flop:** mô hình uống 1 ngăn có nghiệm hoán đổi ka/k cho cùng nồng độ.
  Phần mềm hiển thị nhánh ka≥k theo quy ước và ghi cảnh báo; dữ liệu nồng độ
  đường uống đơn độc không chứng minh hằng số nào là hấp thu/thải trừ.

## Phạm vi kiểm chứng

`tests/test_pk_standalone.py` đối chiếu NCA với hàm mũ IV truyền/ngắt truyền,
khớp lại các thông số mô phỏng 1–2 ngăn cho IV bolus, infusion và oral,
kiểm tra nhập long/wide, BLQ, thiếu t0, lưu SQLite và sinh báo cáo Excel/Word/PDF.
`tests/test_pk_multiple.py` đối chiếu nghiệm IV bolus trạng thái ổn định, phép chồng
chất 1/2 ngăn trên ba đường dùng, khớp lại thông số mô phỏng, kiểm tra thiếu biên/BLQ,
điều kiện xác nhận steady-state, tích lũy và lịch sử báo cáo.
Đây là kiểm thử phần mềm và benchmark mô phỏng; chưa phải thẩm định độc lập theo
quy trình GxP hay kiểm tra toàn diện với dữ liệu lâm sàng thực tế.
