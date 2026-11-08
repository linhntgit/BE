# BE Phoenix, EMA/FDA, HVD và NTI — engine 0.3.1

Ngày kiểm tra nguồn: 30/10/2026. Kiểm thử số học không thay qualification phần mềm
hoặc đánh giá yêu cầu riêng của sản phẩm.

## Trạng thái đối chiếu bổ sung ngày 31/10/2026

Engine 0.3.1 đóng conventional ABE replicate chưa qualification: FDA replicate standard,
FDA NTI và nhánh HVD sWR <0.294 trả NOT EVALUABLE; I-contrast CI chỉ chẩn đoán.
[Gate, bằng chứng và version/snapshot](CONVENTIONAL_ABE_GATE.md).
Prototype full4 REML ở ngoài production; hai saved Phoenix cases có 60/60 số comparable khớp,
và ca giả lập 9/21 được kiểm tra bằng error-contrast REML độc lập. Chưa mở inference.

Đã xuất đầy đủ dependencies của ba project EMA ABEL/FDA HVD/FDA NTI qua Phoenix GUI.
[Báo cáo đối chiếu replicate](PHOENIX_REPLICATE_COMPARISON.md) ghi manifest, population,
settings và 28 so sánh: 23 khớp, 5 sai khác có nguyên nhân (hằng số NTI và conventional ABE khác mô hình).
Các project chứa output lưu từ build 8.3.2.116, không được chạy lại khi xuất bằng build 8.8.
Nhánh ABE của mẫu FDA NTI dùng covariance/df khác I contrast trong app; không xem các CI là tương đương.
Mẫu EMA có missing và mẫu HVD đã lưu chọn nhánh unscaled; chưa qualification missing replicate
hoặc nhánh HVD scaling bằng các mẫu này. Bảng phương pháp dưới đây mô tả mã đã triển khai,
không phải tuyên bố tất cả profile đã được qualification độc lập.

## Đối chiếu file người dùng

`Bioequivalence_Fasted.xlsx`, SHA256:
`7ff667b1c6adfa89d8ce8c8a7c142a9703faddc6df12c7ff0bd258b5b45c6098`.
Phoenix Build 8.8.0.20523; log tự nhiên; fixed Sequence + Treatment + Period,
random Subject(Sequence); REML và Satterthwaite.

| Endpoint | Subject | Quan sát dùng/thiếu | GMR (%) | CI90 (%) | ABE số học |
| --- | ---: | --- | ---: | --- | --- |
| Cmax | 24 | 48/0 | 74.950010 | 61.311131–91.622907 | FAIL |
| AUClast | 24 | 48/0 | 107.760585 | 93.053607–124.791978 | PASS |
| AUCINF_pred | 20 | 30/18 | 110.007904 | 94.321147–128.303559 | FAIL |

Chỉ Ln_Observed của Residuals được chuyển ngược về PK làm đầu vào. Không dùng
Predicted, LS means, phương sai hoặc CI Phoenix để fit. Chuỗi `-nan(ind)` được
ghi nhận là missing, không đổi thành zero. Kiểm thử thay các giá trị kỳ vọng chứng
minh chúng không ảnh hưởng kết quả engine.

**78/78 thống kê số trong Average Bioequivalence** khớp trong dung sai công bố:
CI theo %: absolute 0.0001 điểm phần trăm; thống kê khác: absolute 0.00001;
relative 1e-7. Sai khác lớn nhất khoảng 0.0000369651 ở CI95 upper của AUCINF_pred.
App dùng phân phối t của SciPy và số đầy đủ trước làm tròn. Dung sai benchmark
không dùng để nới giới hạn quyết định BE.

Hệ số, LS means, phương sai, DF, phần dư và SS của các endpoint đầy đủ cũng được
đối chiếu. Với endpoint thiếu, bảng SS OLS là chẩn đoán riêng, có thể khác pseudo-F
với DF xấp xỉ của Phoenix. App không giả lập Iteration History hoặc dùng lại số hội tụ.

## Phương pháp được triển khai

| Profile | Phương pháp và điều kiện |
| --- | --- |
| ABE 2×2 / parallel | CI90 và TOST; parallel pooled/Welch theo SAP; geometric means mô tả tách khỏi adjusted geometric LS means |
| EMA_REPLICATE_STANDARD | Method A: fixed subject(sequence), period, formulation; CI90 80–125% |
| EMA_HVDP_ABEL | Method A; reference-only ANOVA; chỉ Cmax CVwR >30% được scale, k=.760, cap CVwR=50%, không vượt 69.84–143.19%; thêm GMR 80–125%; AUC không scale |
| FDA_HVD_RSABE_2026 | Appendix G: I/D_R theo sequence, trọng số sequence bằng nhau; sWR <.294 cần conventional ABE hiện trả NOT EVALUABLE; ≥.294 giữ Howe UCB95 ≤0 và GMR 80–125% |
| EMA_NTI | AUC 90–111.11%; Cmax thu hẹp khi có yêu cầu và được cấu hình |
| FDA_NTI | Giữ Howe UCB95 và upper CI90(sWT/sWR); conventional ABE chưa qualification nên endpoint NOT EVALUABLE; chỉ full4 |
| FDA_REPLICATE_STANDARD | I-contrast diagnostics; conventional mixed ABE chưa qualification nên NOT EVALUABLE |

Replicate hỗ trợ **TRR/RTR/RRT** và **TRTR/RTRT đủ kỳ**; thiết kế khác hoặc missing
replicate trả NOT EVALUABLE. Không chuyển ngầm về 2×2 hoặc tự xóa subject. Cần
tối thiểu hai subject/sequence để fit; pipeline áp minimum 12 subject crossover
hoặc 12 mỗi nhánh parallel cùng các điều kiện scope, QC, protocol/SAP và freeze.

EMA dùng ANOVA chỉ dữ liệu reference với subject và period để ước tính sWR.
Trong partial3, DF có thể khác mô hình D_R theo sequence của FDA. Không gộp hai
phương pháp. Các hệ số Method A xuất trên dữ liệu FDA được ghi nhãn bổ sung;
mô hình trung gian I/D mới là căn cứ Appendix F/G.

FDA: I=mean(log T)−mean(log R), D_R=log R1−log R2, sWR²=MSE(D_R)/2.
Howe: x=delta²−SE²; bound_x=max(abs(CI90_log))²; y=−theta*sWR²;
bound_y=y*df_R/chi2(.95,df_R); UCB=x+y+hypot(bound_x−x,bound_y−y).
HVD dùng theta=(ln(1.25)/.25)². NTI dùng theta=(ln(1/.9)/.1)², với hằng số
chính xác 1/.9; SAS minh họa của FDA làm tròn thành 1.11111. Output ghi rõ khác biệt.

CV gộp 2×2 không phải sWR để scale HVD. Cần định trước scaling và có clinical
justification cùng rà soát độ tin cậy biến thiên/outlier. NTI cần profile riêng;
không dùng ngưỡng HVD cho NTI. Phân loại NTI và yêu cầu Cmax dựa trên sản phẩm/PSG.

## Missing và cách diễn giải

Mặc định missing chặn suy luận endpoint. REML quan sát sẵn có cho 2×2 chỉ được
mở khi chọn phương pháp và nhập căn cứ SAP; engine liệt kê từng quan sát thiếu
và ghi nhận giả định missing-at-random, không chứng minh giả định đó. Với EMA
nonreplicate, nếu còn subject không có cả T/R thì giữ thống kê chẩn đoán nhưng
chặn kết luận để rà soát population. Cách xử lý missing trong Phoenix không tự
động được xem là phù hợp EMA/FDA.

Mặc định AUClast/Cmax là endpoint chính; AUCINF_pred là bổ sung. Kết luận study
chỉ tổng hợp endpoint chính. Power_TOST legacy, Power_80_20, Anderson–Hauck và
Pitman–Morgan được xuất để đối chiếu, không dùng quyết định BE. Power_TOST legacy
khác phương pháp tích phân power chính xác trong trang thiết kế.

## Sử dụng và kiểm chứng

Mở **Thống kê BE — EMA / FDA → Đối chiếu Excel BE Phoenix WinNonlin**, bấm tính
lại để dùng file sẵn có hoặc upload file khác đúng cấu trúc. Xem các tab ANOVA,
LS means, phương sai, scaling, phần dư, missing và tải Excel đầy đủ.

Mục **Phân tích bảng PK cho replicate, HVD và NTI** cho phép upload bảng PK hoặc
xem dữ liệu giả lập theo thiết kế/profile. Demo không có kết luận cho nghiên cứu
thật. Nghiên cứu thực cần khai báo NTI/scaling/clinical justification, hoàn thành QC
và freeze. Kết quả engine cũ cần tính lại. Excel là snapshot, không tự tính lại khi sửa ô.

```powershell
.venv\Scripts\python.exe scripts\benchmark_be.py
.venv\Scripts\python.exe -m pytest -q
```

Kiểm chứng gồm ma trận statsmodels độc lập cho Method A/reference-only variance,
mô hình I/D và công thức FDA, ca biên .294, constraint GMR, NTI failing riêng tiêu
chí biến thiên, invalid/missing, snapshot và UI. Chưa có qualification cho mọi
tình huống, các thiết kế replicate khác hoặc đối chiếu một bộ dữ liệu replicate
thực từ SAS/Phoenix do người dùng cung cấp. Các profile vẫn ở trạng thái phát triển.

## Nguồn chính thức

- [FDA final May 2026, II.C, III.B/C, Appendices F/G](https://www.fda.gov/media/163638/download)
- [Trang phát hành FDA](https://www.fda.gov/regulatory-information/search-fda-guidance-documents/statistical-approaches-establishing-bioequivalence)
- [EMA Rev.1, 4.1.9/4.1.10](https://www.ema.europa.eu/en/documents/scientific-guideline/guideline-investigation-bioequivalence-rev1_en.pdf)
- [EMA Q&A 3.1: Method A và reference-only variance](https://www.ema.europa.eu/en/scientific-guidelines/clinical-pharmacology-pharmacokinetics-questions-answers)
- [EMA: phần nonreplicate được M13A thay từ 25/01/2025](https://www.ema.europa.eu/en/scientific-guidelines/investigation-bioequivalence)
- [Certara: mô hình BE](https://onlinehelp.certara.com/phoenix/8.3/topics/Average_bioequivalence_study_designs.htm)
- [Certara: equal-variance tests](https://onlinehelp.certara.com/phoenix/8.3/topics/Tests_for_equal_variances.htm)
