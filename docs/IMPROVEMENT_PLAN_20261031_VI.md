# Kế hoạch cải tiến ứng dụng BE từ kiểm thử ngày 31 tháng 10 năm 2026

Ưu tiên đầu tiên là sửa liên kết giữa profile NTI và cỡ mẫu. Tiếp theo là làm rõ phạm vi FDA thực sự dùng được, hoàn tất qualification conventional replicate ABE, rồi cải thiện luồng sử dụng và báo cáo. Kế hoạch này dựa trên [báo cáo kiểm thử](USER_ACCEPTANCE_REVIEW_20261031_VI.md).

**Cập nhật triển khai 31/10/2026:** Đã có giới hạn cỡ mẫu theo profile, chặn planning EMA NTI khi chưa có oracle, capability theo profile, provenance và phân loại dữ liệu. Trang Tổng quan đã có bảng tám bước và gợi ý bước tiếp theo; trang BE tách bảng PK độc lập khỏi snapshot nghiên cứu, trình bày endpoint, giới hạn và UCB. Báo cáo song ngữ đã chuyển phần NCA/thống kê từ JSON sang diễn giải phương pháp, gắn nhãn QA riêng và giữ cấu hình trong manifest/exports. Kết quả cũ sau khi mở revision chưa khóa được nhận là STALE. Gate study chặn dữ liệu training/QA, unknown, method development hoặc không khai báo provenance; nhãn `is_demo` vẫn độc lập với mục đích QA.

**Tiến độ kiểm thử bổ sung:** Bộ kịch bản synthetic có 77/77 kiểm tra kỳ vọng đạt; browser CDP hoàn thành 13 thao tác smoke với 714px/1440px, từ tạo demo → freeze → NCA → BE bị chặn kết luận → trang báo cáo DRAFT. Browser smoke chưa bao phủ upload/download, cuộn hết từng trang hoặc UAT thủ công. Regression, kiểm tra kiểu và lint được cập nhật trong [nhật ký triển khai](PHOENIX_IMPLEMENTATION_STATUS.md); gói bằng chứng mới nằm ở `output/qa_20261031/improvement_evidence_20261031.json` và giữ manifest lịch sử trước sửa riêng biệt.

**Nghiệm thu bổ sung 31/10/2026:** Regression hiện hành **236/236 đạt**, Ruff và mypy đạt. Đã render và xem trực quan 7/7 trang PDF tiếng Việt cùng 7/7 trang tiếng Anh, không thấy tràn khung/cắt biên; các banner cảnh báo tiếng Anh được bản địa hóa, dữ liệu nghiên cứu gốc giữ nguyên. Tệp đối chiếu hash `output/qa_20261031/pdf_visual_review_20261031.json` được liên kết vào evidence manifest. Đây chỉ là nghiệm thu bố cục PDF; Word vi/en, UAT trình duyệt toàn diện, thẩm định khoa học và ký duyệt vẫn chưa hoàn tất.

**Chưa hoàn tất:** Qualification độc lập FDA conventional replicate ABE/RSABE nhánh thấp/NTI, oracle planning EMA NTI, browser UAT thủ công đầy đủ, duyệt bố cục Word từng trang vi/en và gói evidence có chữ ký reviewer. Các nhánh này vẫn ở trạng thái phát triển/NOT EVALUABLE theo phạm vi. Các cải tiến UI và pass bộ kiểm thử không đồng nghĩa đã thẩm định khoa học.

Ước lượng bên dưới là ngày công kỹ thuật, giả định một lập trình viên và một chuyên gia thống kê/BE có thể rà soát theo từng mốc. Không phải cam kết thời hạn; khối lượng qualification và việc có oracle độc lập sẽ quyết định lịch thực tế.

## Giai đoạn 1 Ngăn lập kế hoạch sai và làm rõ phạm vi

| Hạng mục | Việc làm cụ thể | Điều kiện nghiệm thu | Ước lượng |
|---|---|---|---|
| P1 Cỡ mẫu EMA NTI | Trước mắt khóa planning NTI nếu chưa đủ qualification. Sau đó đưa biên riêng AUC/Cmax vào bài toán power và bộ giải N; kiểm GMR có thuộc miền khả thi của endpoint; đường power phải dùng cùng biên. | Ca CV AUC 20%, GMR 0,95 không còn trả N=20/power 83,47% cho AUC NTI. Đối chiếu oracle độc lập; xác nhận endpoint Cmax tùy cờ sản phẩm. | 2–4 ngày |
| P1 Fingerprint kế hoạch | Bao gồm rule/version, design, endpoint roles, biên, alpha, cờ NTI Cmax, giả định và engine trong input/fingerprint của plan. Đổi profile cùng design phải làm plan cũ cần tính lại. | Đổi ABE→EMA NTI hoặc bật thu hẹp Cmax làm stale plan và không giữ đường power mang ý nghĩa cũ. | 1–2 ngày |
| P1 Ma trận capability | Tách “có tính toán”, “được kết luận endpoint”, “có planning” và “đã qualification”. Dùng cùng registry cho UI, báo cáo và docs. | Trước khi tạo FDA NTI/FDA replicate hoặc HVD có nhánh conventional, user nhìn thấy giới hạn cụ thể. Không gỡ gate bằng một cờ `supported`. | 1–2 ngày |
| P2 Chế độ dữ liệu | Thêm lựa chọn mục đích nghiên cứu và provenance rõ ràng; đào tạo/QA luôn có watermark và gate study phù hợp. Migration project cũ cần lưu căn cứ. | Dữ liệu QA tự tạo/import được gắn nhãn bền vững qua SQLite, archive, Excel, Word/PDF; không tự suy luận chỉ từ filename. | 1–2 ngày |

Các thay đổi nên nằm trong `be_app/design.py`, `be_app/ui.py`, `be_app/regulations.py`, contract state và tests liên quan. Không sửa `tost_power` chỉ để ép số benchmark; cần chứng minh công thức và đầu vào đúng.

## Giai đoạn 2 Hoàn thiện nhánh FDA còn bị khóa

1. Chốt specification conventional replicate ABE: full4/partial3, covariance, treatment-specific variance, fixed/random effects, cách fit, contrast, SE và denominator df. Ghi rõ thiết kế nào được hỗ trợ.
2. Thu thập oracle SAS/Phoenix/R phù hợp phương pháp với provenance: balanced, imbalance, variance thấp/cao, sát ngưỡng, GMR biên, missing theo phạm vi định trước, nghiệm biên và fit không hội tụ.
3. Đối chiếu từng thành phần trước khi so PASS/FAIL: estimate, variance, covariance, df, CI; giải thích mọi khác biệt. CI I contrasts không được dùng thay conventional ABE.
4. Sau qualification, tích hợp lần lượt FDA replicate chuẩn, nhánh HVD sWR<0,294, rồi FDA NTI. Quy tắc NTI phải đánh giá đủ conventional ABE, scaled criterion và variance comparison.
5. Bổ sung mô phỏng operating characteristics với seed, sai số Monte Carlo và scenario grid được thống kê viên phê duyệt; không gọi một bộ synthetic pass là qualification.

Ước lượng 8–15 ngày kỹ thuật cộng thời gian tạo oracle/rà soát chuyên gia; có thể tăng nếu mô hình độc lập cho kết quả khác. Gate hiện tại phải giữ cho mọi nhánh chưa nghiệm thu. Tiêu chuẩn gỡ gate là báo cáo đối chiếu được duyệt, tolerance định trước và regression tests, không phải hoàn thành UI.

## Giai đoạn 3 Làm luồng sử dụng rõ và gọn

| Nhu cầu | Thay đổi | Nghiệm thu |
|---|---|---|
| Biết bước tiếp theo | Hiển thị trạng thái tạo nghiên cứu, phân nhóm, import, QC, freeze, phân tích, review, export; nút disabled có lý do tại chỗ. | User mới hoàn thành ABE không cần đọc source hoặc đoán vì sao nút bị khóa. |
| Chọn phương pháp hợp lệ | Lọc/gợi ý design phù hợp rule; chỉ ra điều kiện scaling/NTI và nhánh chưa mở. | Không để user hiểu chọn menu đồng nghĩa phương pháp đã qualification. |
| Phân biệt hai phân tích | Tách bảng PK độc lập khỏi kết luận snapshot nghiên cứu; luôn hiện project, dataset, rule, purpose, timestamp và fingerprint ngắn. | Đổi bảng PK không làm user hiểu nhầm đã tính lại nghiên cứu chính thức. |
| Đọc kết quả nhanh | Một bảng tóm tắt endpoint chính, GMR, CI/tiêu chí thực dùng, giới hạn, trạng thái và lý do; chi tiết model đặt dưới. | AUC FAIL và Cmax PASS nhìn thấy cùng lúc; FDA RSABE không gợi kết luận bằng CI chuẩn. |
| Dùng trên khung hẹp | Sidebar gọn, đóng dễ; bố trí form theo nhóm; bảng rộng có lựa chọn cột và giá trị format vừa đọc. | Thử viewport khoảng 714px và 1440px; không có thao tác chính bị che khi điều hướng thông thường. |
| Cỡ mẫu dễ quyết định | Hiện N chọn, N đánh giá/tuyển, endpoint chi phối, biên và phạm vi power; sau này mới bổ sung replicate planning có qualification. | Số N được chọn và giả định không phải tự tổng hợp từ nhiều dòng; không gọi power riêng endpoint là power đồng thời. |

Ước lượng 4–6 ngày. Giữ cơ chế draft/commit hiện tại; kiểm tra rằng tối ưu UI không làm mất bản nháp hoặc làm phân tích tự chạy ngoài ý muốn.

## Giai đoạn 4 Báo cáo và gói bằng chứng

Thay JSON cấu hình trong nội dung báo cáo bằng bảng/diễn giải phương pháp; giữ JSON đầy đủ trong phụ lục kỹ thuật hoặc manifest. Trang tóm tắt cần có primary/secondary endpoints, rule/version, giới hạn, model thực dùng, gate/lý do NOT EVALUABLE và trạng thái review. Đưa population listing dài sang phụ lục có tiêu đề lặp; thêm các đồ thị được chọn và cross-reference khi có giá trị cho người đọc.

Cấu hình môi trường render DOCX có LibreOffice hoặc công cụ được kiểm soát. Render rồi xem từng trang tiếng Việt/Anh; kiểm Unicode, bảng nhiều trang, số liệu, watermark, footer, nội dung sát biên. Chỉ gắn nhãn đã QA layout sau khi gate này đạt. File tải được không đủ làm tiêu chuẩn nghiệm thu.

Tạo manifest evidence gồm version engine, lock dependency, scenario, seed, input hash, expected/actual, tolerance, test result, artifact hash và người review. Giữ kiểm tra archive schema/checksum/path traversal, journal/conflict và raw bất biến. Ước lượng 3–5 ngày cho report UX và môi trường QA, chưa gồm CSR/E3/eCTD đầy đủ.

## Giai đoạn 5 Bộ kiểm thử để tránh lặp lại lỗi

| Nhóm | Ca cần thêm hoặc nâng cấp |
|---|---|
| Planning nối với profile | ABE và EMA NTI cùng CV/GMR cho biên và N khác nhau; bật/tắt NTI Cmax; đổi rule cùng design làm plan cũ stale; GMR ngoài biên hẹp không báo N khả thi theo ABE chuẩn. |
| ABEL sát ngưỡng | CVwR dưới/bằng/trên 30%, sát 50%, trên cap; quy ước làm tròn và nhãn nhánh được thống kê viên chốt. Không đặt kỳ vọng bằng cách sao chép logic đang có. |
| FDA RSABE | sWR=0,293999/0,294/0,294001; UCB sát 0; GMR sát 0,8/1,25; từng tiêu chí đạt và không đạt độc lập. |
| NTI | Giới hạn từng endpoint, variance ratio, low variability và trường hợp conventional ABE chưa qualified; không phát PASS khi thiếu một thành phần bắt buộc. |
| NCA/QC | Chọn terminal từng profile, actual/nominal mismatch, BLQ, thiếu mẫu, predose, extrapolation cao, dữ liệu lỗi và unit conversion có audit; dữ liệu giàu cấu trúc hơn cùng một scale cho mọi endpoint. |
| Trạng thái UI | Tạo mới, nhập, correction nhiều ô, đổi trang/reload, freeze/revision, STALE trên cả NCA/BE/plot/report; owner PK không rò sang project khác. |
| Export/restore | Report hai ngôn ngữ; Excel dùng đúng snapshot; archive mở lại không refit, giữ raw/artifact/hash; file lỗi không ghi đè project đang mở. |

Dùng unit tests cho toán học; AppTest cho widget/state; một tập browser end-to-end nhỏ cho file upload/download, rendering và thao tác người dùng. Regression sau sửa đã bổ sung kiểm tra nối planning với profile (ABE/NTI) và dấu vân tay khi đổi rule/Cmax; browser smoke có phạm vi giới hạn như trên. Số test cuối cùng được đọc từ `improvement_pytest.xml` trong manifest mới, tách khỏi 77 kiểm tra nghiệp vụ scenario; không lấy số 226 của baseline làm số test hiện hành.

## Điều kiện bàn giao phiên bản cải tiến

- F01 được sửa hoặc planning NTI được chặn minh bạch; regression tests và oracle độc lập đạt.
- Không gỡ các gate FDA khi qualification chưa hoàn tất; ma trận capability phản ánh đúng trạng thái từng nhánh.
- ABE, EMA ABEL và NTI được thử lại với input đạt, không đạt và không hợp lệ, qua pipeline và các luồng UI chính.
- Không có kết quả cũ xuất như hiện hành sau thay đổi đầu vào; raw/audit/snapshot được bảo toàn qua restore.
- Báo cáo tiếng Việt/Anh qua render QA; nêu rõ purpose, giới hạn và trạng thái review.
- Tài liệu cập nhật theo capability matrix; các hạng mục MR/steady-state/partial AUC, multi-user/RBAC và eCTD chỉ đưa vào release khi có phạm vi và qualification riêng.

Mốc đầu tiên nên là một bản sửa hẹp cho F01 và capability badges. Sau đó mới mở rộng FDA và replicate planning để mỗi thay đổi khoa học có bằng chứng đánh giá riêng.
