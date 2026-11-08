# Đặc tả thuật toán và nguồn đối chiếu

Phiên bản engine 0.3.0. Toàn bộ phép so sánh BE dùng số đầy đủ trước định dạng.
CV đầu vào dạng tỷ lệ: 0.30 = 30%; UI nhận phần trăm có đơn vị.

## Power và cỡ mẫu

Nguồn: [PowerTOST tác giả](https://github.com/Detlew/PowerTOST), README mục Parallel/Crossover,
và [Schuirmann TOST trong SAS](https://support.sas.com/documentation/cdl/en/statug/66103/HTML/default/statug_ttest_details19.htm).
Không dùng chênh lệch hai power noncentral t như thể hai kiểm định độc lập.
Tích phân xác suất đồng thời hai TOST: conditional normal theo V ~ chi-square(df).
sigma²=log(1+CV²); df=n1+n2−2. SE thật crossover=sigma sqrt((1/nTR+1/nRT)/2),
parallel=sigma sqrt(1/nT+1/nR). CV crossover là CVw; parallel là CV total giữa người.
Với q=t(1−alpha,df), tích phân phần dương của
Phi((log(U)−delta)/SE−q sqrt(V/df))−Phi((log(L)−delta)/SE+q sqrt(V/df)).
Chỉ tích phân đến hai giới hạn chạm nhau; sai số tích phân phải ≤1e-7.
Giả định lognormal, phương sai bằng nhau, dữ liệu đầy đủ; không dùng cho Welch/replicate.
Cỡ mẫu tìm tăng dần từng cặp, tuyển thêm làm tròn theo từng nhóm sau chia (1−dropout).
Golden PowerTOST: CV=.20, GMR=.95, n=20 2×2 → .834680 (làm tròn 6 chữ số);
parallel CV=.35, GMR=.95, nT=52,nR=49 → .8011186.

## ABE

Nguồn: [Schütz Labes Fuglsang 2014](https://pmc.ncbi.nlm.nih.gov/articles/PMC4389751/),
DOI 10.1208/s12248-014-9661-0, phương trình 2 và datasets phụ lục.
2×2 dùng phép khử subject từ mô hình sequence + subject(sequence) + period + treatment:
d_i=ln(T_i)−ln(R_i); delta=(mean(d_TR)+mean(d_RT))/2.
Pooled variance của d trong từng sequence với df=N−2; MSE=variance(d)/2;
SE²=variance(d)/4 × (1/nTR+1/nRT). Có hiệu chỉnh period qua hai sequence.
Phép rút gọn tương đương fixed subject model khi mọi người đủ hai kỳ;
không suy diễn mixed model cho mất kỳ. Không tự xóa người có kỳ thiếu: trả NOT EVALUABLE.
Xuất intermediate sequence means, residuals, MSE, period contrast, df.
Parallel: independent log means, pooled variance hoặc Welch Satterthwaite theo SAP.
CI=exp(delta ± t(1−alpha,df)SE); TOST dùng cùng SE/df. Zero residual variance trả NE.
Geometric means mô tả và adjusted geometric LS means là hai nhóm kết quả riêng.
REML/Satterthwaite hỗ trợ quan sát sẵn có cho 2×2 khi SAP cho phép; không tự xóa subject.
Xem [phạm vi BE mở rộng và kiểm chứng](PHOENIX_BE_COMPARISON.md).

## NCA đơn liều

Nguồn: M13A 2.2.2.2; [PKNCA vignette](https://humanpred.github.io/pknca/articles/v05-auc-calculation-with-PKNCA.html).
AUC last kết thúc ở điểm cuối định lượng dương, không cộng đuôi BLQ thành AUCall.
Trapezoid tuyến tính: dt(C1+C2)/2; giảm dương: dt(C1−C2)/ln(C1/C2).
Nếu zero, bằng nhau hoặc đi lên: tuyến tính. Không lấy log zero.
Actual time phải có thật từ timestamp có offset; không thay nominal vào actual.
Baseline time=0 là bắt buộc trong bản hiện tại; mẫu predose âm phải được rà soát/correction,
không tự dịch thời điểm hay gán nồng độ zero.
MISSING/REJECTED/REASSAY chưa được xử lý: chặn profile; BLQ=0 nhưng giữ raw và cờ.
Cmax là quan sát, Tmax đồng mức chọn đầu/cuối theo cấu hình.
Lambda-z: suffix của các điểm định lượng sau Tmax cuối, ít nhất 3 điểm, sườn âm;
chọn adjusted R² cao nhất, ưu tiên suffix dài hơn nếu chênh ≤1e-4.
Ngưỡng adjusted R² và span/half-life là kiểm soát chất lượng theo cấu hình, không phải khẳng định guideline.
Chỉ xuất AUCinf khi thỏa các kiểm tra; Clast quan sát/lambda_z là đuôi ngoại suy;
hiển thị mọi candidate và lý do bị chặn. Manual terminal cần lý do và lưu trong config snapshot.
MRT đã có từ 0.2.0. Partial AUC/AUC72 và steady state chưa hỗ trợ.

## Tmax: so sánh phi tham số hỗ trợ trong nghiên cứu BE

- Dùng Tmax quan sát trên thang thời gian gốc (giờ), không log-transform,
  không tính geometric mean và không áp giới hạn tương đương 80–125%.
- Thiết kế crossover 2×2 đủ cặp T/R trên từng người: Wilcoxon signed-rank
  hai phía trên chênh lệch Tmax (T−R); thống kê trung vị chênh lệch ghép cặp.
  Đây là kiểm định thăm dò, **không hiệu chỉnh period/sequence**.
- Thiết kế song song: Mann–Whitney U hai phía trên hai nhóm độc lập T và R.
- Với mọi thiết kế: xuất N, trung vị, nhỏ nhất/lớn nhất theo T và R, thống kê,
  p hai phía, phương pháp, trạng thái và lý do nếu không đánh giá được.
- Profile NCA không đánh giá được, Tmax thiếu/âm/không hữu hạn, cặp T/R thiếu
  hoặc trùng làm kiểm định **NOT EVALUABLE**; không tự loại người hoặc kỳ để
  được p-value. Chỉ trình bày thống kê mô tả từ các giá trị hợp lệ và ghi rõ N.
- Với thiết kế replicate, kiểm định mặc định **NOT EVALUABLE** cho đến khi
  SAP quy định và triển khai phương pháp phù hợp cấu trúc lặp.
- Kết quả được lưu trong analysis snapshot, hiển thị trên luồng BE đầy đủ,
  xuất Excel/Word/PDF, nhưng **không tham gia** endpoint ABE hoặc tổng hợp
  PASS/FAIL/NOT EVALUABLE của nghiên cứu. Quy tắc áp dụng và diễn giải phải
  đối chiếu protocol/SAP và guideline/PSG tương ứng trước khi báo cáo chính thức.

## Kết luận và kiểm soát

Kết quả thống kê là PASS/FAIL/NOT EVALUABLE theo endpoint. Tổng hợp chỉ PASS nếu
tất cả endpoint bắt buộc có kết quả PASS và không có blockers. Không suy diễn từ power/p treatment.
Scope/PSG, minimum N, QC, protocol/SAP và data freeze là điều kiện của pipeline.
Demo giữ kết quả số để học thử nhưng kết luận study luôn NOT EVALUABLE và report ghi demo.
EMA ABEL dùng Method A và reference-only ANOVA; k=.760, cap sWR tại sqrt(log(1+.5²)), không vượt cặp giới hạn
được công bố 0.6984–1.4319 ở precision đầy đủ; AUC không mở rộng.
FDA Appendix G dùng I/D contrasts đúng thiết kế, theta=(ln(1.25)/.25)², UCB theo Howe và constraint GMR.
FDA Appendix F dùng sigma_w0=.1, theta=(ln(1/.9)/.1)², đồng thời kiểm tra ABE và upper CI90(sWT/sWR)≤2.5.
EMA NTI thu hẹp AUC về .9–1.1111, Cmax theo cấu hình yêu cầu sản phẩm.
Các nhánh replicate hiện yêu cầu đủ kỳ; không áp mô hình 2×2 cho missing replicate.

