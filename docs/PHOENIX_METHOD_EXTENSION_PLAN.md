# Phạm vi các chương trình phương pháp tiếp theo

Ngày 31/10/2026. Tài liệu lập kế hoạch cho PHX-11/12 theo survey; không thêm phương pháp hoặc tiêu chí sản phẩm vào engine. Baseline là engine 0.3.1, complete supported replicate only; prototype mixed full4 vẫn ngoài production.

## PHX-11 missing replicate và thiết kế bổ sung

Đợt đầu chỉ xem TRTR/RTRT và TRR/RTR/RRT với quan sát thiếu. Thiết kế khác, nhiều nhóm/covariates hoặc endogenous correction cần đặc tả riêng. Không gỡ kiểm tra complete trong `prepare_replicate`, không tự chuyển sang 2×2, không tự chọn complete cases để tạo kết luận cho toàn nghiên cứu.

### Các estimator và population phải tách

| Nhánh | Dữ liệu cần mô tả | Câu hỏi cần giải quyết trước code |
|---|---|---|
| EMA Method A | Mọi quan sát PK đủ định danh/thang đo; fixed subject, period, treatment | Điều kiện estimability, population theo SAP, subject thiếu T hoặc R và missing mechanism |
| EMA reference-only variance | Các lần R của đúng population reference | Subject chỉ một R ảnh hưởng residual df thế nào; mapping period/sequence, mất kỳ và rank |
| FDA I contrasts | Các T/R cần để tính đúng subject contrast của thiết kế | Có cho phép subject không đủ repeated administrations không; công thức và trọng số không được suy từ dữ liệu còn lại |
| FDA D_R và D_T | Hai lần của đúng formulation trong subject | Population có thể khác I và khác nhau R/T; giữ subject IDs/df ở từng fit, không gộp thành một n |
| Conventional FDA mixed ABE | Các quan sát còn lại với covariance đã đặc tả | REML, nhận diện G/R, observed information/Satterthwaite, boundary và nonconvergence; không dùng CI I thay thế |

Trên đây là đối tượng cần đặc tả, chưa phải chính sách cho phép dùng available observations. Trước khi suy luận phải chốt handling missing/intercurrent events trong protocol/SAP và xác minh nguồn hướng dẫn của đúng thị trường/sản phẩm. App không thể chứng minh MAR từ dữ liệu quan sát.

### Bằng chứng hiện có và bộ test phải tạo

EMA template có 77 subject/298 observations/69 đủ bốn kỳ. HVD saved workflow có population I và R khác nhau, đồng thời mappings đã log lại logData. DS01 của basic replicate có cùng kích thước thiếu kỳ. Các file giữ dưới output và đã hash; không phát hành dữ liệu thương mại làm fixture công khai hoặc coi đó là đầu vào PK đúng khi transform chưa được xác nhận.

Qualification cần fixture độc lập có missing một T, một R, thiếu cả T/R của một subject, mất cả sequence hoặc period, unequal sequence counts, duplicate/conflicting IDs, và rank/nonconvergence. Expected phải có settings, populations I/R/T/mixed, full precision, SE/df/variance/UCB/CI; tính fit trước đọc expected. Trường hợp không nhận diện phải trả NE cùng nguyên nhân, không tự impute hoặc đổi estimator.

## PHX-12 các epic tách riêng

| Epic | Domain riêng cần có | Acceptance trước mở kết luận |
|---|---|---|
| MR và partial AUC | Endpoint ID, cửa sổ thời gian/đơn vị, actual/nominal basis, quy tắc nội suy tại hai biên, dose/fed/steady-state theo sản phẩm | Chốt cửa sổ theo SAP/PSG trước xem kết quả; fixture độc lập có đúng/thiếu biên, BLQ, khoảng lấy mẫu rộng và missing; không ngoại suy ngoài dữ liệu khi chưa đặc tả |
| IBE | Estimand, subject-by-formulation interaction, covariance và thuật toán riêng | Phạm vi nghiên cứu phương pháp lịch sử phải ghi rõ; không gọi IBE là ABE hoặc mở từ tên template; cần nguồn hiện hành và reference riêng |
| PBE / modified PBE | Total variance, giữa và trong container/batch, log/scale và hằng số đúng mô hình | Chọn loại PBE theo sản phẩm và thiết kế; oracle từng thành phần/df/UCB, near-threshold và singular cases; không tái dùng Howe RSABE/NTI |
| In vitro | batch, container/device, replicate, life-stage, actuation/measurement và đơn vị | Giữ hierarchy trong input, population và reports; không ép container/life-stage thành subject/period; independent fixture và tiêu chí sản phẩm định trước |

[FDA Statistical Approaches May 2026](https://www.fda.gov/media/163638/download) mô tả PBE/modified PBE ở Appendices D/E và nêu IBE hiện không dùng trong regulatory setting; đây không phải chỉ định áp dụng cho một sản phẩm cụ thể. Không suy ra yêu cầu methylphenidate hoặc cửa sổ pAUC từ tên project mẫu.

## Điều kiện hoàn thành từng epic

1. Đặc tả estimand, design, scale, populations và thuật toán có nguồn; ghi các lựa chọn theo sản phẩm còn thiếu.
2. Input schema/validator riêng, reject sai mapping/đơn vị và giữ nguyên source/provenance.
3. Independent oracle, fixtures boundary/imbalance/missing và tolerance chốt trước; mọi mismatch có giải thích kiểm chứng được.
4. Reviewer/Excel/Word/PDF hiển thị cùng snapshot và populations; không gán nhầm nhãn estimator.
5. Engine/rule version, migration/stale/freeze/audit và hồi quy benchmark cũ đạt trước khi mở UI cho kết luận.

PHX-12 ở survey là hướng lập kế hoạch theo nhu cầu sản phẩm, nên việc có roadmap này không đồng nghĩa đã triển khai hay qualification các epic. Các gate hiện hành tiếp tục áp dụng.
