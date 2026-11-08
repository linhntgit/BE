# Đối chiếu NCA với Phoenix WinNonlin

Nguồn người dùng cung cấp: `NCA_Fasted.xlsx`.
SHA256: `0b4d2554b73bfad13907e89d685df2d692a733151748ed94a4785594372b7bc1`.
Settings ghi Phoenix Build 8.8.0.20523; nghiên cứu diclofenac fasted,
24 subject, 2 treatment, 48 profile, 15 mẫu/profile (720 mẫu), liều 50 mg.

## Cách tính và phạm vi

- NCA đơn liều extravascular, tích phân linear trapezoidal cho cả AUC và AUMC.
- Tmax lấy lần đầu đạt Cmax. Tlag là thời điểm ngay trước nồng độ dương đầu tiên.
- AUClast dừng tại nồng độ dương cuối; AUCall bao gồm phần về zero sau đó.
- Hồi quy ln(C) theo thời gian, uniform weighting, tối thiểu 3 điểm sau Tmax.
  Xét các suffix kết thúc ở nồng độ dương cuối; ưu tiên nhiều điểm khi adjusted R²
  nằm trong khoảng 0.0001. Không dùng điểm zero trong hồi quy.
- Preset theo file mẫu đặt ngưỡng adjusted R² và span bằng 0, giữ cấu hình mặc định
  nghiêm ngặt hiện có cho các nghiên cứu chưa chọn preset. Đây là lựa chọn phương pháp,
  không phải tiêu chí đánh giá chất lượng một nghiên cứu.
- Bổ sung 41 thông số có trong bảng Phoenix, gồm AUMC, MRT, dose-normalized,
  Clast_pred, các thông số ngoại suy obs/pred, CL/F và Vz/F.
  Đổi liều về ng để tính CL/F (mL/h), Vz/F (mL); không đổi giá trị Dose gốc.
- Nếu không chọn được pha cuối, giữ các thông số phụ thuộc lambda-z trống.
  Không suy ra chúng từ kết quả Phoenix và không tự loại subject.

Các công thức được kiểm tra với tài liệu Certara:

- [NCA parameter formulas](https://onlinehelp.certara.com/phoenix/8.4/Phoenix_UserDocs/NCA_Object/NCA_parameter_formulas.htm)
- [WinNonlin Guide: calculation rules, AUC/AUMC, terminal regression](https://onlinehelp.certara.com/phoenix/8.4/responsive_html5_%21MasterPage%21/WinNonlin_Guide.pdf)

## Bằng chứng đối chiếu

Chỉ Time/Concentration của Summary Table và liều của Dosing Used được đưa vào
engine. Final Parameters, Predicted, Residual, AUC, AUMC và Slopes Settings của
Phoenix là dữ liệu kỳ vọng để kiểm tra. Không dùng chúng để chọn điểm hay tính PK.

| Kiểm tra | Kết quả |
| --- | --- |
| Profile | 48/48 |
| Thông số | 41/profile, 1.968 phép đối chiếu |
| Khớp trong dung sai | 1.968/1.968 |
| Ô số khớp | 1.500 |
| Ô cùng để trống | 468 |
| Profile có lambda-z | 30 |
| Profile không ước tính được lambda-z | 18, giống Phoenix |
| Sai khác tuyệt đối lớn nhất | 3,710738383233547 × 10⁻¹⁰ |
| Dung sai | relative 10⁻⁹ hoặc absolute 10⁻⁸ |

Kiểm thử còn đối chiếu từng mẫu: điểm được chọn hồi quy, predicted concentration,
residual, cumulative AUC và cumulative AUMC. Fixture JSON lưu riêng nồng độ đo và
giá trị kỳ vọng, có SHA256 nguồn. Kiểm thử thay toàn bộ Estimate của Phoenix chứng
minh giá trị kỳ vọng không ảnh hưởng đến kết quả engine.

Đây là benchmark với workbook cụ thể, không phải xác nhận tương đương mọi chức
năng hoặc mọi dữ liệu của Phoenix. File xuất không có thông tin BLQ/LLOQ ban đầu
hay thời gian lấy mẫu có timestamp; zero được giữ như file xuất. Luồng đối chiếu
không tạo kết luận BE hoặc giả lập metadata còn thiếu. Nghiên cứu thật vẫn dùng
luồng nhập dữ liệu, QC, Data Freeze và SAP của app.

## Sử dụng

1. Mở **Phân tích NCA → Đối chiếu với Excel Phoenix WinNonlin**.
2. Bấm **Tính lại và đối chiếu Phoenix** để dùng file NCA_Fasted.xlsx sẵn có,
   hoặc tải lên file khác có cấu trúc và phương pháp được hỗ trợ.
3. Xem 41 thông số, các khoảng hồi quy, đồ thị tuyến tính/bán log, từng mẫu và cảnh báo.
4. Tải Excel kết quả và bảng đối chiếu. Các bảng là snapshot đã tính, không phải
   workbook công thức có thể sửa nồng độ để tự cập nhật. Thay dữ liệu trong app rồi tính lại.

Để áp dụng phương pháp cho nghiên cứu đang mở: trước Data Freeze, chọn
**Áp dụng cấu hình như NCA_Fasted (Phoenix)**; khai báo đúng liều tại thông tin
nghiên cứu, hoàn thành QC, khóa đầu vào và phân tích. Kết quả engine cũ được đánh
dấu LEGACY; cần tính lại trước khi xuất báo cáo. Kết quả nghiên cứu mới xuất thêm
`nca.xlsx`, giữ các định danh snapshot và hash đầu vào.

Lệnh chạy lại benchmark:

```powershell
.venv\Scripts\python.exe scripts\benchmark_phoenix.py
```

Kết quả ở `output/phoenix_nca/NCA_Fasted_App_vs_Phoenix.xlsx` và summary JSON.
