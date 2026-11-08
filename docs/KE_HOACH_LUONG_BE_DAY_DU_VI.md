# Kế hoạch thiết kế lại luồng BE đầy đủ

Ngày lập: 05/11/2026. Phạm vi: luồng **BE đầy đủ** của BE Analysis Workbench. Luồng sáu chặng đã được triển khai. Tài liệu mô tả cách sử dụng và tiêu chí nghiệm thu.

## Quyết định thiết kế

**Sử dụng bản triển khai trong ứng dụng.** Chọn **BE đầy đủ**, rồi chọn chặng ở thanh bên. Chặng có hai công việc sẽ hiện thêm danh sách chọn. Có thể mở nhật ký từ bất kỳ chặng nào. Khi mở lại nghiên cứu đã lưu trên máy, ứng dụng đưa người dùng về công việc gần nhất.

Ở chặng 1, điền phiếu căn cứ theo sản phẩm và thị trường. Nếu cần đánh giá FDA và EMA cho cùng nghiên cứu, chọn **Đánh giá cùng nghiên cứu ở thị trường thứ hai**, ghi căn cứ dùng chung dữ liệu và tạo dự án liên kết. Mỗi nhánh có SAP, lần khóa dữ liệu, phân tích và kết luận riêng. Chặng 2 cho phép soạn rồi chốt nội dung đề cương vào phiên bản nghiên cứu. Với nghiên cứu thật, ứng dụng kiểm tra căn cứ đối chứng, nguồn hướng dẫn, kế hoạch lấy mẫu, định lượng và thống kê trước khi khóa.

Ở chặng 6, người rà soát nhập định danh, bằng chứng và kết quả xử lý. Báo cáo dự thảo ghi lại bản rà soát tương ứng với lần phân tích. Thay đổi sau khi khóa cần một phiên bản mới. Bảng PK do bên ngoài tính có đường dẫn đối chiếu riêng từ chặng 4 và được ghi rõ nguồn khi xuất bảng thống kê. Kết luận toàn nghiên cứu hiện dựa trên dữ liệu nồng độ của dự án đã khóa. Nghiệm thu với năm người dùng mới và xác nhận độc lập của PK, thống kê, QA cần được ghi nhận riêng.

Thay danh sách mười trang ngang cấp bằng sáu chặng theo công việc. Giữ các màn hình chuyên môn hiện có làm màn hình chi tiết. Đưa đồ thị đến cạnh quyết định cần đồ thị; cho mở lịch sử từ mọi chặng. Người dùng được xem trước, quay lại và lưu nháp; chỉ chặn hành động tạo kết quả hoặc phát hành khi điều kiện của hành động đó chưa đủ.

## Sáu chặng và điều kiện chuyển tiếp

| Chặng | Việc người dùng thực hiện | Đầu ra và điều kiện để sử dụng ở bước sau |
|---|---|---|
| 1. Xác định nghiên cứu | Tạo hoặc mở dự án; khai sản phẩm, dạng bào chế, hàm lượng, thuốc đối chứng và thị trường, mục đích, FDA/EMA hoặc cả hai. | Phiếu phạm vi cho từng thị trường: nguồn, phiên bản, tình trạng draft/final, lý do áp dụng. Nếu chưa xác định thuốc đối chứng, hướng dẫn riêng hoặc cơ sở dùng chung dữ liệu cho hai thị trường, cho lưu nháp và giao việc cho người phụ trách pháp quy. |
| 2. Chốt thiết kế và kế hoạch phân tích | Chọn điều kiện đói/no, quần thể, thiết kế, kỳ, washout, lịch lấy mẫu, ngẫu nhiên hóa; ghi nguồn CV, GMR, power, hao hụt và phân tích độ nhạy cỡ mẫu. Chốt analyte, endpoint, quần thể phân tích, mô hình, quy tắc BLQ, loại trừ và giới hạn theo endpoint. | Bản protocol/SAP có phiên bản và lý do lựa chọn. Chỉ cho dùng phương án cỡ mẫu tương thích quy tắc đã chọn. Sửa sau khi chốt phải tạo phiên bản mới, lưu thời điểm, lý do và ảnh hưởng đến kết quả. |
| 3. Nhập và kiểm tra dữ liệu | Xem trước ánh xạ cột, đơn vị, T/R, kỳ, trình tự, giờ dùng thuốc và lấy mẫu thực tế. Đối chiếu kế hoạch với thực tế; ghi nhận bằng chứng thẩm định phương pháp định lượng, LLOQ, vấn đề mẫu và sai lệch. | Bảng QC phân biệt lỗi phải sửa với cảnh báo cần giải trình. Giữ bản gốc; lưu mọi chuyển đổi và loại trừ. Người soát khóa bộ dữ liệu có mã phiên bản khi lỗi chặn đã hết. |
| 4. Duyệt thông số PK | Chạy NCA trên bộ đã khóa; xem đường cong theo người/kỳ, Cmax, AUC, vùng lấy mẫu và phần ngoại suy khi có liên quan. Mở trực tiếp profile bị cảnh báo. | Bảng endpoint dẫn về profile và nguồn; ghi cách xử lý thông số không ước lượng được. Nếu dùng bảng PK từ bên ngoài, đi qua nhánh nhập đã kiểm tra nguồn, đơn vị, khóa định danh và bằng chứng NCA; ghi rõ NCA bên ngoài. |
| 5. Đánh giá BE | Áp dụng mô hình đã chốt. Xem GMR, khoảng tin cậy, tiêu chí, số người phân tích và quyết định theo từng endpoint, điều kiện nghiên cứu và thị trường. | Phân biệt **đạt**, **không đạt**, **không thể đánh giá**. Chỉ tổng hợp đạt khi mọi tiêu chí bắt buộc của thị trường đó đều đạt. Dữ liệu hoặc phương pháp thiếu không được coi là bằng chứng thất bại hay thành công. |
| 6. Rà soát và xuất | Người rà soát đi từ kết luận về tiêu chí, dữ liệu và các quyết định loại trừ. Hiện sai lệch chưa đóng và người chịu trách nhiệm. | Xuất báo cáo, bảng kết quả và nhật ký từ cùng một snapshot. Cho xuất báo cáo rà soát có nhãn nêu giới hạn; không phát hành kết luận BE hiện hành từ kết quả cũ hoặc thiếu tiêu chí. |

Ví dụ thông báo: **“Chưa thể khóa dữ liệu: người 024, kỳ 2 có hai dòng cùng thời điểm lấy mẫu.”** Kèm nút **Xem 2 dòng**. Nếu sửa giờ lấy mẫu sau khi đã chạy BE, giữ kết quả trước để đối chiếu, đánh dấu kết quả phụ thuộc là cũ, dẫn về QC và chỉ cho xuất kết luận hiện hành sau khi khóa lại, tính lại và rà soát.

## Quy tắc theo thị trường

- Với dạng rắn uống giải phóng ngay thuộc phạm vi M13A, dùng M13A làm cơ sở chung. Kiểm tra hướng dẫn theo sản phẩm, điều kiện dùng thuốc và từng endpoint trước khi đề xuất thiết kế. MR, miễn thử in vivo, hoặc thiết kế ngoài phạm vi engine đi vào nhánh đánh giá riêng; không tự chuyển sang crossover 2×2. [FDA M13A](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/m13a-bioequivalence-immediate-release-solid-oral-dosage-forms).
- FDA: đối chiếu hướng dẫn PK cho ANDA, hướng dẫn thống kê cuối cùng tháng 5/2026 và PSG tương ứng. Đính căn cứ đến từng tiêu chí. Theo giới hạn engine 0.3.1, giữ **không thể đánh giá** cho conventional replicate ABE, FDA NTI và nhánh FDA HVD có sWR < 0,294 cần conventional ABE. Không lấy CI chẩn đoán điền vào tiêu chí còn thiếu. [FDA – PK cho ANDA](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/bioequivalence-studies-pharmacokinetic-endpoints-drugs-submitted-under-abbreviated-new-drug), [FDA – thống kê BE](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/statistical-approaches-establishing-bioequivalence).
- EMA: M13A thay các phần liên quan đến thiết kế không lặp từ 25/01/2025. Với replicate, HVD, NTI hoặc thiết kế phức tạp, đối chiếu phần hướng dẫn EMA còn áp dụng và hướng dẫn riêng của sản phẩm. Tách quy tắc theo endpoint; không sao chép phương pháp scaled của FDA sang EMA. [EMA – triển khai M13A](https://www.ema.europa.eu/en/documents/scientific-guideline/considerations-regarding-implementation-ich-m13a-bioequivalence-immediate-release-solid-oral-dosage-forms_en.pdf).
- Các tài liệu trên là hướng dẫn khoa học. Phiếu phạm vi cần tách hướng dẫn, yêu cầu pháp lý bắt buộc và lựa chọn trong SAP. Người phụ trách pháp quy xác nhận căn cứ theo sản phẩm trước khi chốt; chuyên gia thống kê xác nhận mô hình và bằng chứng kiểm chứng. Không gắn nhãn “FDA/EMA approved” cho kết quả ứng dụng.

## Triển khai và nghiệm thu

| Đợt | Chủ trì và sản phẩm bàn giao | Điều kiện kết thúc |
|---|---|---|
| 1. Chốt ma trận và thử nguyên mẫu | Pháp quy + thống kê + UX: ma trận thị trường × thiết kế × endpoint × khả năng engine; nguyên mẫu luồng ABE 2×2, nhánh bị chặn và dự án mở lại. | Người phân tích và người soát tìm được bước tiếp theo, nguồn áp dụng và lý do bị chặn. Đối chiếu lại ca cỡ mẫu EMA NTI từng phát hiện trong UAT. |
| 2. Lắp luồng vào ứng dụng | Kỹ sư Streamlit: ánh xạ sáu chặng vào trang hiện có; một trạng thái tiến độ chung, lưu nháp, mở lại đúng việc đang làm; giữ archive cũ và tách dữ liệu demo. | Chuyển trang không mất bản sửa đã lưu; phục hồi archive không ghi đè dự án; mở snapshot cũ vẫn thấy phiên bản cũ. Thay đổi dữ liệu làm hết hiệu lực đúng các kết quả phụ thuộc. |
| 3. Đối chiếu chuyên môn | PK + thống kê: chạy dữ liệu đối chứng độc lập cho nhánh được hỗ trợ, ca sát biên, endpoint thiếu, replicate, HVD và NTI theo từng thị trường. | So cả ước lượng, SE/df/CI hoặc tiêu chí scaled thích hợp và quyết định theo dung sai định trước; mọi nhánh chưa đủ bằng chứng vẫn bị chặn. |
| 4. UAT và phát hành có giới hạn | QA + người dùng: chạy trọn luồng trên trình duyệt, sửa dữ liệu sau khóa, chuyển FDA/EMA, xuất và khôi phục. | Mục tiêu UX đề xuất: ≥4/5 người dùng mới hoàn tất ca 2×2 không cần trợ giúp; 5/5 nhận biết đúng trạng thái không thể đánh giá. Không còn lỗi nghiêm trọng; UI và file xuất cùng snapshot, cùng số liệu và nhãn. Chỉ mở các nhánh đã nghiệm thu. |

Đối chiếu nội bộ: [điều hướng](../be_app/ui.py), [giới hạn replicate ABE](CONVENTIONAL_ABE_GATE.md), [UAT tháng 10](USER_ACCEPTANCE_REVIEW_20261031_VI.md), [tiến độ audit tháng 11](IMPLEMENTATION_PROGRESS_20261105_VI.md). Ưu tiên bản đầu là ca 2×2 đi hết sáu chặng và ca FDA NTI dừng đúng lý do; đây là hai phép thử cho cả tính dễ dùng và tính trung thực của kết luận.
