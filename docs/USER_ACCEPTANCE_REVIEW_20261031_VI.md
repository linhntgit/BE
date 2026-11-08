# Đánh giá sử dụng và kiểm thử ứng dụng BE ngày 31 tháng 10 năm 2026

Ứng dụng 0.3.1 đã chạy được luồng ABE từ tạo nghiên cứu đến QC, khóa dữ liệu, NCA, BE, báo cáo và phục hồi archive. Các cơ chế giữ raw, gắn snapshot và khóa xuất khi kết quả STALE hoạt động trong các trường hợp đã thử. Tuy nhiên, **chưa nên dùng chức năng cỡ mẫu cho EMA NTI**: một lỗi đã tái hiện trên trình duyệt cho thấy phần lập kế hoạch vẫn dùng giới hạn ABE chuẩn. FDA NTI, FDA replicate conventional ABE và nhánh FDA HVD có sWR thấp vẫn có giới hạn phương pháp đã công bố, trả NOT EVALUABLE.

Đây là báo cáo kiểm thử phát triển bằng dữ liệu giả lập, không phải chứng nhận validation hoặc phê duyệt sử dụng pháp quy. Không chỉnh sửa thuật toán hay giao diện production trong đợt đánh giá này.

## Phạm vi và bằng chứng

Kiểm thử trực tiếp bằng trình duyệt nội bộ trên app trong workspace `D:\Sync\GDrive\AG\BE_app`. Đợt đầu dùng localhost:8501. Sau khi phiên làm việc bị ngắt, cổng đó phục vụ app khác; phần tiếp tục dùng `http://127.0.0.1:8502`, không dừng app kia.

| Lớp kiểm thử | Khối lượng và kết quả | Bằng chứng |
|---|---|---|
| Bộ test hiện hữu | 226 test đạt, 0 lỗi, 0 bỏ qua; 40,978 giây | `output/qa_20261031/pytest_host.xml` |
| Bộ tình huống tự tạo | 38 tình huống, 57 kết quả endpoint | `scenario_summary.csv`, `scenario_results.json` |
| Kiểm tra kỳ vọng bổ sung | 77 kiểm tra đạt; so quyết định, workbook UI, QC, archive, pipeline | `verification.json` |
| Pipeline nồng độ cho replicate và NTI | 6 nghiên cứu giả lập, 720 profile NCA | `PIPELINE_*.beproject.zip` |
| Luồng ABE thao tác từ đầu trên UI | 24 người, 2 kỳ, 14 mẫu/profile, tổng 672 mẫu | `SYNTHETIC_concentrations_ABE.csv` và archive ABE |
| Bảng PK thao tác trên UI | EMA ABEL full/partial, FDA RSABE full/partial, EMA NTI, NTI thu hẹp Cmax, FDA NTI | 7 file `UI_*.xlsx` và `browser_workbook_summary.csv` |
| Lỗi phát hiện ngoài bộ test | Cỡ mẫu EMA NTI sử dụng biên chuẩn | `finding_NTI_sample_size.json`, ảnh `04_NTI_sample_size_bug.jpg` |

Các con số trên có giao nhau; không cộng thành số ca kiểm thử độc lập. 77 kiểm tra đạt xác nhận các kỳ vọng đã viết, không bao gồm một khẳng định rằng lỗi cỡ mẫu NTI đã được sửa. Lần chạy test đầu trong sandbox gặp lỗi quyền thư mục tạm Windows; chạy lại ngoài sandbox đạt toàn bộ 226 test. Đây là khác biệt môi trường kiểm thử.

Seed dữ liệu là 20261031; seed phân nhóm cho project ABE thao tác trên UI là 241029, block 4. Bảng PK dùng 36 người. Dữ liệu có chủ đích đơn giản: các endpoint trong bảng PK cùng được nhân từ một mức phơi nhiễm giả lập. Điều này giúp kiểm tra nhánh phương pháp, nhưng không thay được bộ dữ liệu có tương quan PK thực tế phong phú.

## Trải nghiệm luồng ABE

Tạo mới `QA_20261031_ABE` với protocol/SAP giả lập; nhập hoạt chất và căn cứ scope; tính cỡ mẫu; tạo phân nhóm; xem trước CSV; nhập raw; QC; Data Freeze; phân tích; xem thống kê, đồ thị và xuất báo cáo. Không dùng nút demo thay cho thao tác tạo nghiên cứu này.

QC chấp nhận 672 mẫu hợp lệ. Sau khóa, UI không cho sửa raw trực tiếp. NCA tạo 48 profile và 41 thông số/profile. Workbook NCA tải được qua nút ứng dụng. Kết quả BE của snapshot đầu:

| Endpoint | N | GMR phần trăm | CI 90 phần trăm | Kết quả toán học |
|---|---:|---:|---|---|
| AUClast | 24 | 104,1341 | 98,1265–110,5095 | PASS |
| Cmax | 24 | 104,2831 | 98,0404–110,9233 | PASS |
| AUCINF_pred bổ sung | 24 | 104,1325 | 98,1241–110,5088 | PASS |

Đây hoàn toàn là dữ liệu tự tạo. Project tạo thủ công có `is_demo=False` mặc định, nên UI hiển thị “Đạt tiêu chí thống kê” ở cấp nghiên cứu sau khi đủ các khai báo. Điều đó không làm dữ liệu thành bằng chứng BE thật; đây cũng là lý do cần một khai báo mục đích dữ liệu rõ ràng khi tạo/import project.

Với CV AUC 20%, CV Cmax 30%, GMR 0,95, target 80%, dropout 10%, kế hoạch ABE chuẩn trả AUC 20 người đánh giá được/tuyển 24 và Cmax 40/tuyển 46. Bảng trình bày riêng hai endpoint; nên bổ sung một kết luận nổi bật về N được chọn và nhắc rằng đây chưa phải power đồng thời. Project phân tích 24 người ở trên là bộ kiểm thử riêng; không tuyên bố đã thực hiện nghiên cứu theo cỡ mẫu kế hoạch 46 người.

## Kết quả theo phương pháp

| Trường hợp đã thử | Quan sát |
|---|---|
| ABE EMA và FDA 2×2 | Dữ liệu gần T/R=1 cho PASS; dữ liệu lệch lớn cho FAIL. CI/GMR trong workbook UI nhất quán với engine ở các đối chiếu đã thực hiện. |
| Parallel | Bộ giả lập 36 người cho PASS; bộ test hiện hữu bao phủ pooled/Welch. Không thao tác lại toàn bộ luồng nhập nồng độ parallel trên trình duyệt. |
| EMA replicate chuẩn | Full4 đủ kỳ cho PASS; kiểm tra engine và bộ test. |
| EMA ABEL full4 | Cmax GMR 91,4061%, CI90 80,8767–103,3064%; biên áp dụng 72,3883–138,1438%; PASS. AUC vẫn dùng 80–125%. |
| EMA ABEL partial3 | Cmax GMR 82,4808%, CI90 70,9199–95,9264%; PASS với biên 69,84–143,19%. AUC cùng dữ liệu FAIL vì không được nới biên. Đã xác nhận bằng workbook tải qua UI. |
| EMA ABEL CV cao | Biên Cmax dừng ở 69,84–143,19%; không tiếp tục nới theo CV. GMR ngoài 80–125% bị FAIL dù điều kiện khác có thể đạt. |
| FDA RSABE full4 | GMR 91,4061%; Howe UCB95 âm; endpoint PASS. CI90 từ I contrasts là bổ trợ, không được dùng thay tiêu chí RSABE. |
| FDA RSABE partial3 | GMR 82,4808%; CI90 bổ trợ 71,7188–94,8578%; endpoint PASS theo RSABE. Khác EMA AUC là hệ quả phương pháp, không phải lỗi chỉ vì CI ra ngoài 80–125%. |
| FDA sWR thấp | Khi sWR dưới 0,294, nhánh conventional ABE chưa qualified nên NOT EVALUABLE. Không tạo PASS bằng CI I contrasts. |
| FDA ngưỡng sWR | Đã thử 0,293999; 0,294; 0,294001. Hai giá trị từ ngưỡng trở lên chọn nhánh scaled. |
| EMA NTI | Dữ liệu kiểm tra GMR 115,5289%, CI90 111,7186–119,4691%: AUC FAIL, Cmax PASS nếu chưa yêu cầu thu hẹp. Bật thu hẹp Cmax thì Cmax cũng FAIL. |
| FDA NTI | Tính được các thành phần scaled/variance, nhưng kết luận endpoint NOT EVALUABLE do conventional replicate ABE chưa qualified. UI nghiên cứu đã xác nhận “Không thể kết luận”. |
| Thiết kế sai và dữ liệu lỗi | RSABE với 2×2, thiếu kỳ replicate, trùng subject–period, endpoint âm/0/thiếu, sai treatment đều không tạo PASS. Thiếu prespecification/căn cứ HVD và cờ NTI sai cũng bị chặn ở các ca engine đã thử. |

Về chuẩn đối chiếu, EMA cho phép nới Cmax trong điều kiện HVD phù hợp, giữ ràng buộc GMR và không nới AUC; NTI có biên hẹp theo endpoint. Xem [EMA Rev.1, mục 4.1.9 và 4.1.10](https://www.ema.europa.eu/en/documents/scientific-guideline/guideline-investigation-bioequivalence-rev1_en.pdf). FDA Appendix F/G quy định các nhánh NTI/HVD riêng; kiểm tra ngưỡng và tiêu chí dựa trên [FDA Statistical Approaches final tháng 5 năm 2026](https://www.fda.gov/media/163638/download). Các nhận xét ở đây là đánh giá triển khai, không phải quyết định của cơ quan quản lý.

## QC và tính toàn vẹn kết quả

Đã tạo thêm sáu bản dữ liệu nồng độ lỗi: nồng độ âm, trùng mẫu, timestamp thiếu timezone, đơn vị không hợp lệ, treatment không khớp phân nhóm, thiếu cột bắt buộc. QC engine đều trả không hợp lệ. Trên trình duyệt, nhập bảng PK có Cmax bằng 0 được từ chối bằng thông báo “PK phải dương; không tự coi zero/âm là missing”, không tạo kết quả mới. Bộ test hiện hữu kiểm tra correction, pending edits, raw bất biến, journal và conflict giữa phiên. Trong đợt này chưa trực tiếp gõ correction nhiều ô vào grid bằng trình duyệt; không coi kiểm tra tự động đó là bằng chứng đã làm thao tác tay tương đương.

Trên UI đã xác nhận đổi phương pháp PK hoặc gỡ file nguồn làm kết quả STALE và vô hiệu hóa tải workbook. Đổi SAP trong revision của project ABE từ v1 sang v2 làm báo cáo snapshot cũ STALE, khóa Word/PDF và datasets. Tạo revision nhưng chưa thay dữ liệu/phương pháp có thể vẫn xem kết quả cùng đầu vào; khi SAP đã đổi, gate hoạt động đúng.

Đã tải archive và mở lại qua UI. Raw byte, analysis_run_id, input_fingerprint, snapshot_hash và hai báo cáo được bảo toàn; mở lại không tạo lần fit mới. Manifest tải từ UI thống nhất với archive. Snapshot ABE đầu có analysis_run_id `b8e2d9fb-990e-40f3-b46b-64523b8d3553`.

## Phát hiện cần xử lý

### F01 Lỗi cỡ mẫu EMA NTI mức ưu tiên P1

**Tái hiện:** mở project `SYN_QA_EMA_NTI`; trang Thiết kế và cỡ mẫu BE; CV AUC=20%, GMR=0,95, power=80%, dropout=10%; nhập nguồn giả định; bấm tính. UI trả AUC N=20, power 0,8347, tuyển 24. Đây là kết quả theo biên 80–125%, không phù hợp AUC của profile NTI đã chọn.

Tính lại bằng **cùng hàm `tost_power` của app**, nhưng truyền đúng biên 0,9–1,1111: N=168 đạt power khoảng 0,80153; N=20 chỉ đạt khoảng 0,05712. Theo cùng cách làm tròn dropout/cân bằng của app, N=168 tương ứng tuyển 188. Các số này minh họa lỗi nối cấu hình; chưa phải một công cụ cỡ mẫu NTI đã được qualification độc lập.

Nguyên nhân đã xác định: `ui.power_plan` chỉ nhận inputs, design, engine_version; gọi `sample_size` không truyền rule hoặc biên theo endpoint. Fingerprint kế hoạch cũng không có rule/NTI-Cmax. `sample_size` chỉ triển khai miền GMR/biên ABE chuẩn. Vì vậy thay tên profile không thay được kế hoạch tương ứng.

Hành động trước mắt: chặn hoặc cảnh báo rõ tính cỡ mẫu NTI cho đến khi bộ giải, đường power, fingerprint và tests dùng đúng profile. Không chỉ thay nhãn UI.

### F02 Phạm vi FDA đang bị giới hạn mức ưu tiên P1 về phát hành

Đây là **giới hạn đã biết, không phải phát hiện false PASS mới**. FDA NTI, FDA replicate chuẩn và FDA HVD sWR thấp chưa thể kết luận. Registry vẫn có `supported=True`, menu cho chọn đầy đủ; người dùng có thể hiểu nhầm là toàn bộ phương pháp đã dùng được. Cần trạng thái capability riêng cho planning, numerical analysis, decision và qualification. Giữ nguyên gate hiện hành cho đến khi conventional mixed ABE được benchmark độc lập.

### F03 Mục đích dữ liệu giả lập chưa được khai báo đầy đủ mức ưu tiên P2

Nút demo có gate cấp study tốt. Dữ liệu giả lập do người dùng tự import trong project mới không có cách bật cờ tương đương ở form khởi tạo đã kiểm tra. Cần khai báo “nghiên cứu thật / đào tạo / kiểm thử”, lưu trong archive, workbook và báo cáo. Không suy đoán mục đích chỉ từ tên file.

### F04 Cỡ mẫu replicate và khả năng diễn giải mức ưu tiên P2

Planning full4/partial3 chưa hỗ trợ ABEL/RSABE và có cảnh báo. Cần thông báo điều này ngay lúc chọn phương pháp, trước khi người dùng xây project. Bảng PK độc lập và snapshot nghiên cứu xuất hiện trên cùng trang dài; hai nguồn kết quả cần ngữ cảnh nổi bật hơn, nhất là khi phương pháp hoặc dữ liệu khác nhau.

### F05 Giao diện và báo cáo mức ưu tiên P2

Trong viewport hẹp khoảng 714px, sidebar mở có thể che nội dung; thao tác thuận tiện hơn ở 1440px. Đây là nhận xét khả dụng, chưa phải kết luận mọi nút bị lỗi. Bảng Reviewer Criteria hiện chuỗi CI nhiều chữ số và cần cuộn ngang; các bảng dùng tỷ lệ và phần trăm khác nhau dù đã có chú thích. Nên chuẩn hóa cách nhìn, giữ số đầy đủ trong export.

PDF tiếng Việt xuất được, có 7 trang, font/dấu/bảng đọc được trong ảnh render đã kiểm tra. Trang đầu còn JSON cấu hình, các trang sau dành nhiều chỗ cho population listing. Nên dùng diễn giải phương pháp, phần tóm tắt và phụ lục tách riêng. File DOCX tạo và tải được; chưa hoàn tất QA layout Word vì renderer thiếu LibreOffice `soffice.exe`. Không gọi DOCX đã được nghiệm thu bố cục.

### F06 Biên rất sát CV 30 phần trăm mức ưu tiên P2 cần rà soát

Tại CVwR mục tiêu 30,0001%, phép thử kiểm soát cho biên 0,800029561–1,249953813, trong khi nhãn method vẫn là “EMA replicate ABE”. Đây là sai khác rất nhỏ gần ngưỡng do hệ số/cách chọn nhánh; cần chuyên gia xác nhận cách làm tròn và xử lý biên, rồi thống nhất nhãn, tiêu chí và export. Không kết luận từ quan sát này rằng các ca ABEL thông thường sai.

### F07 Tài liệu và qualification mức ưu tiên P2

Một số phần backlog còn mô tả NTI hoặc terminal UI là chưa hỗ trợ, trong khi code hiện có một phần các chức năng này. Cần một capability matrix làm nguồn chung cho UI, README và tài liệu. 226 test đạt không phát hiện F01; cần bổ sung kiểm tra luồng nghiệp vụ nối profile→planning→analysis, thay vì chỉ kiểm các hàm riêng lẻ.

## Giới hạn đợt kiểm thử

Chưa làm validation pháp quy, nghiên cứu Monte Carlo type I error/power, thử tải lớn, đo hiệu năng có kiểm soát, thẩm định đầy đủ missing replicate, MR/steady-state/partial AUC, authentication hoặc chữ ký điện tử. Chưa có đối chiếu mới chạy trực tiếp SAS/Phoenix; các benchmark hiện hữu nằm trong bộ test của repo. Kiểm tra workbook UI so với engine xác nhận đường truyền dữ liệu/kết quả, không tự tạo một oracle thống kê độc lập.

Các sửa đổi sản phẩm được đề xuất trong [kế hoạch cải tiến](IMPROVEMENT_PLAN_20261031_VI.md). Các script tái tạo bổ sung là `scripts/qa_user_scenarios_20261031.py` và `scripts/qa_verify_20261031.py`; chúng đã qua Ruff. Toàn bộ evidence của đợt này nằm trong `output/qa_20261031`.

## Phụ lục sau khi thực hiện cải tiến (31/10/2026)

Các phát hiện F01–F07 ở trên được giữ nguyên như **bằng chứng baseline trước sửa**. Trong phiên bản cải tiến, planning EMA NTI được khóa đến khi có oracle độc lập, fingerprint gắn rule/giới hạn/endpoint; capability và provenance được lưu và thể hiện trên UI; kết quả synthetic vẫn NOT EVALUABLE cấp nghiên cứu. Browser smoke sau sửa có 13 bước đạt trên dữ liệu demo riêng và hai viewport 714px/1440px; 77 kiểm tra synthetic scenario đã đạt, nhưng không phải kiểm định thống kê độc lập. Báo cáo hiện hành Word/PDF được phát hành lại ở thư mục `output/qa_20261031/improved_report_current`, tách với bản PDF/DOCX tạo trước sửa. Chi tiết hash và trạng thái reviewer nằm tại `output/qa_20261031/improvement_evidence_20261031.json`. Chưa có qualification FDA conventional replicate/FDA NTI, oracle cỡ mẫu EMA NTI hay visual QA đầy đủ Word.
