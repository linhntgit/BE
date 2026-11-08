# Đối chiếu các workflow replicate Phoenix

Ngày xuất: 31/10/2026. Dùng menu **Workflow → Dependencies** của Phoenix 8.8.0.20523 để xuất input, settings, CSV kết quả và sơ đồ phụ thuộc. Không chạy lại workflow, không sửa hoặc lưu đè project nguồn. Các settings xuất ghi build tính kết quả đã lưu là **8.3.2.116**; build xuất không được xem là build đã tính lại kết quả.

525 file xuất nội bộ nằm trong `output/phoenix_replicate_reference` (được gitignore). Manifest SHA-256 từng file, danh tính/hash project nguồn và kết quả nằm trong `output/phoenix_replicate_comparison/summary.json`. Không đưa project thương mại hoặc bảng dữ liệu nguồn vào fixture công khai.

Chạy lại:

```powershell
.venv\Scripts\python.exe scripts/benchmark_replicate_phoenix.py
```

Script tách input khỏi expected: tính mô hình từ bảng dữ liệu trước khi đọc output tham chiếu. Dung sai tuyệt đối 1e-8, tương đối 1e-7; không nới dung sai để che khác biệt phương pháp. CSV giữ toàn bộ số xuất, không dùng bảng final đã làm tròn hai chữ số.

## Kết quả và giới hạn

**23/28 so sánh số khớp. Năm khác biệt có nguyên nhân được ghi riêng. Chưa qualification toàn bộ phương pháp.** Exit 0 của script chỉ xác nhận không có sai khác bất ngờ trong những thành phần cùng mô hình/population; trường `status` của summary vẫn là `NOT QUALIFIED`.

| Trường hợp | Kết quả trực tiếp | Ý nghĩa |
|---|---|---|
| EMA Method A | 298 quan sát/77 người, chỉ 69 người đủ 4 kỳ. Contrast 0.14547366694322245; SE 0.04650869112875911; df 217; GMR 115.658727770272%. Khớp output Method A. | Đối chiếu helper OLS trên toàn bộ input quan sát. Luồng kết luận replicate hiện hành vẫn trả NOT EVALUABLE cho missing; không tự bỏ 8 người để thay population. |
| EMA reference-only | 146 quan sát R/73 người; residual df 71; variance 0.19931355059019032; CVwR 46.9643071557706%; giới hạn toán học 71.2269768375454–140.396243726699%. | Khớp variance và phép tính giới hạn của bảng nguồn. Đây là kiểm chứng thành phần, chưa phê duyệt áp dụng scaling cho endpoint/sản phẩm. |
| FDA NTI I/D và variance | 18 người full replicate; I estimate −0.01499444444444446, SE 0.025058584058778408, df 16; sWR 0.12439276869166382; sWT 0.05572090920132419; upper CI90 SD ratio 0.6842667527522063. | Các thành phần này khớp output nguồn. |
| FDA NTI Howe constant | App exact 1/0.9 cho UCB −0.009828504008136512; mẫu dùng 1.11111 cho UCB −0.0098282889891327. | Sai khác 2.15e-7 vượt dung sai. Diagnostic replay với chính hằng số 1.11111 của settings khớp; giữ nguyên công thức app, không đổi hằng số để ép khớp. |
| FDA NTI conventional ABE | Phoenix SE 0.028365069523557, df 33.66075427, CI90 93.8970545053981–103.35322246778%. App I contrast SE 0.025058584058778408, df 16, CI90 94.29483052568196–102.91723426686168%. | Bốn giá trị không khớp vì Phoenix dùng repeated variance theo formulation + random formulation UN; app dùng subject contrasts. Cần đặc tả và independent validation riêng trước khi đổi estimator/df/decision. Không tuyên bố đã tái hiện nhánh ABE của mẫu NTI. |
| FDA HVD mẫu đã lưu | I dùng 69 người/df 67; D_R dùng 73 người/df 71; sWR 0.05747143361079134, thấp hơn 0.294. Các thành phần I/D và UCB tính thăm dò khớp. | Mẫu thực tế chọn **unscaled ABE**, không kiểm chứng nhánh HVD scaling. Không dùng population 69 người thay cho population R 73 người. |

## Phát hiện về thang đo trong mẫu HVD

File `Workflow.Prepare Dataset for Analysis.5_ Map your Data to Required Columns.Data (Dataset I Full Replicate).csv` có `logData≈7.73454135` và `Data=2285.96`. Worksheet mapping kế tiếp đưa `logData` vào cột `Data`; cấu hình `Trans_Flag=N`. Bảng `LOG_DATA_R1` sau đó chứa `≈2.04569619`, tức log tự nhiên của số đã log.

Đây là bằng chứng về **cấu hình và output đã lưu trong mẫu**, không phải căn cứ để log hai lần dữ liệu PK trong app. Script tái hiện đúng đầu vào của phép tính đã lưu để kiểm tra số học, không xác nhận cách biến đổi đó phù hợp nghiên cứu. Import wizard của app vẫn bắt buộc khai báo raw/Ln/log10 và chỉ chuyển ngược về PK gốc một lần.

## Công việc khoa học còn lại

1. Đặc tả conventional ABE cho FDA replicate/NTI: covariance, estimator, df, population, boundary/convergence và independent fixture trước khi mở thay đổi quyết định.
2. Đặc tả missing replicate theo từng thiết kế; kiểm tra riêng all-observation treatment contrast và population có hai R/T. Không bỏ chặn `prepare_replicate` chỉ vì helper OLS khớp mẫu EMA.
3. Có một reference HVD thực sự chọn scaled branch và dữ liệu/thang đo được xác nhận. Mẫu HVD vừa xuất không đáp ứng tiêu chí này.
4. Gắn adapter UI với manifest/cấu hình và phân loại same-model, different-model, scope-blocked; không dùng một nhãn “đã benchmark” chung.

PHX-02 vì vậy đã hoàn tất thu thập mẫu và một đợt đối chiếu có provenance; phần qualification/mở rộng mô hình vẫn chưa hoàn tất.
