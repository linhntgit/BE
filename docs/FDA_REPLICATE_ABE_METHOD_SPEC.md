# Đặc tả nhánh conventional ABE cho full replicate FDA

Trạng thái: **DRAFT — chưa mở kết luận bằng mô hình mới**. Đặc tả này được tạo từ sai khác quan sát trong `PHOENIX_REPLICATE_COMPARISON.md`, không thay estimator hiện hành chỉ để làm khớp một bảng số.

## Căn cứ và phạm vi đợt đầu

[FDA Statistical Approaches, May 2026](https://www.fda.gov/media/163638/download), Appendix C (trang in 32), mô tả ABE replicate với fixed sequence/period/treatment, covariance ngẫu nhiên theo treatment trong subject, residual riêng theo treatment và Satterthwaite. Appendix F (trang in 42, bước 3) yêu cầu đánh giá ABE không scaling cùng các tiêu chí NTI khác. Đã mở văn bản nguồn ngày 31/10/2026. Đây là căn cứ chọn mô hình cần kiểm chứng; qualification phần mềm vẫn là công việc riêng.

Đợt đầu chỉ xét TRTR/RTRT **đủ bốn kỳ**, endpoint dương/hữu hạn và ít nhất hai người mỗi sequence. Missing replicate, partial3, nhiều nhóm/covariates, baseline/endogenous và các thiết kế khác vẫn nằm ngoài gate. Không tự loại người hoặc đổi thang đo để đạt điều kiện này.

## Mô hình đề xuất để kiểm chứng

Với một subject, đặt response là log tự nhiên PK, ma trận X gồm intercept, sequence, period và treatment. Ma trận Z có hai cột indicator T và R. Covariance quan sát:

`V_i = Z_i G Z_i' + diag(sWT² nếu T, sWR² nếu R)`

G là covariance 2×2 giữa random treatment effects trong subject, đối xứng và positive semidefinite. Residual giữa các lần dùng thuốc độc lập có điều kiện theo random effects. Đây là diễn giải ma trận của mô hình cần thử; phải kiểm tra đối chiếu với settings/output Phoenix trước khi công nhận tương đương.

- Ước lượng variance bằng REML; beta bằng GLS. Cố định cách mã hóa factor/reference; kiểm tra rank của X.
- Không thay covariance này bằng random-intercept 2×2 hiện có hoặc OLS subject contrasts.
- Dùng parameterization bảo đảm covariance hợp lệ; thử nhiều điểm khởi đầu, ghi log-likelihood, gradient, Hessian, trạng thái hội tụ và boundary. Không coi optimizer trả success là đủ.
- Contrast treatment T−R lấy từ cùng GLS fit. Không dùng I contrast cho SE/df của nhánh conventional ABE.
- Tính Satterthwaite bằng độ nhạy variance contrast và covariance của variance estimates. Phải ghi rõ lựa chọn observed/expected information và cách xử lý boundary; chưa được chọn theo việc cấu hình nào làm CI thuận lợi.
- Nếu covariance/df không nhận diện được hoặc không có nghiệm ổn định đã qualification, trả NOT EVALUABLE và giữ diagnostics.

## Hợp đồng đầu ra và snapshot

### Quy ước prototype 0.1 (31/10/2026, trước khi fit)

- Thứ tự covariance là R,T; đặt `L=[[a,0],[b,c]]`, `G=L L'`, residual `rR=exp(qR)`, `rT=exp(qT)`. Fit các tham số `(a,b,c,qR,qT)` bằng REML với gradient giải tích và nhiều điểm khởi đầu cố định. Không lấy initial values từ kết quả Phoenix.
- Dùng Hessian **observed** của negative REML log-likelihood, có cả số hạng đạo hàm bậc hai của covariance theo factor/log-variance; không chỉ biến đổi Hessian của các variance components tuyến tính. Dùng inverse Hessian này cho sensitivity của variance contrast.
- [SAS PROC MIXED](https://support.sas.com/documentation/cdl/en/statug/67523/HTML/default/statug_mixed_syntax01.htm) mô tả observed information là mặc định; [RANDOM statement](https://support.sas.com/documentation/cdl/en/statug/63962/HTML/default/statug_mixed_sect019.htm) ghi FA0(2) ràng buộc covariance nonnegative definite. Các tài liệu được kiểm tra ngày 31/10/2026.
- G gần rank deficient phải được báo `boundary`; các số SE/df lúc đó chỉ là chẩn đoán thử nghiệm. Gate `inference_allowed=False` cho **mọi** fit trong prototype; module không trả PASS/FAIL, không được import từ pipeline hoặc UI.
- Bảo vệ khối lượng: prototype đợt đầu giới hạn 600 quan sát, đủ kiểm tra các bộ tham chiếu hiện có; không diễn giải đây là giới hạn khoa học của mô hình.

Đầu ra thử nghiệm phải ghi delta, SE, df, critical t, GMR/CI90, fixed effects, G/R covariance, log-likelihood, convergence/boundary, model ID/version và population dùng. Kết quả RSABE I/D, conventional ABE và variance comparison được giữ thành ba nhánh riêng. Không ghi đè các snapshot hoặc expected Phoenix.

Prototype đầu tiên phải nằm ngoài luồng `analyze_regulatory_be`; không thay đổi PASS/FAIL đang phát hành. Chỉ tích hợp sau khi hoàn tất các điều kiện dưới đây, kèm cập nhật engine/config version để snapshot cũ trở thành stale theo chính sách hiện có.

## Tiêu chí kiểm chứng trước tích hợp

1. Tái hiện input đủ kỳ 18 người của mẫu NTI đã xuất; kiểm tra G/R covariance, fixed effects, contrast SE/df và CI, không chỉ GMR hoặc quyết định.
2. Expected values phải đọc từ output độc lập đã lưu và có SHA-256; thay expected không thay fitted estimates. Hằng số Howe chính xác/làm tròn được kiểm tra riêng, không điều chỉnh dung sai chung.
3. Ít nhất một bộ độc lập thứ hai với imbalance sequence và variance T/R khác nhau; một bộ near-boundary với giới hạn CI và một bộ singular/nonconvergent phải trả NE đúng lý do.
4. Kiểm tra hoán vị nhãn subject/thứ tự hàng, rescaling PK và dấu T/R. Đối chiếu gradient/Hessian bằng một phép tính độc lập, không chỉ test lặp lại implementation.
5. Tolerance cho variance/SE/df được định trước và giải thích theo độ chính xác xuất/optimizer. Không dùng tolerance để nới ngưỡng BE.
6. Xác định ảnh hưởng tới `FDA_REPLICATE_STANDARD`, nhánh HVD sWR thấp và conventional ABE NTI. Các nhánh khác giữ estimator đã định trước.
7. Sau khi đạt: tests engine → population/reviewer → Excel/Word/PDF → freeze/stale/version → benchmark cũ. Chỉ lúc đó mở lựa chọn mới trong UI và cập nhật hồ sơ qualification.

## Các chương trình tách riêng

### Tolerance audit prototype trước bộ tham chiếu thứ hai

Chốt ngày 31/10/2026 sau kiểm tra NTI và trước fit bộ `Bioequivalence_replicated`: delta/fixed effects/SE/GMR/CI dùng absolute 1e-7, relative 1e-6; covariance dùng absolute 1e-7, relative 1e-5; df dùng absolute 1e-4, relative 1e-5. Đây là tolerance chẩn đoán số của optimizer, không thay ngưỡng BE hay tự cho phép kết luận. Mọi sai khác vượt tolerance phải giữ trong bảng audit, không tăng tolerance sau khi nhìn kết quả. Boundary và Hessian phải ghi riêng.

Log-likelihood dùng hằng số chính xác `log(2*pi)` và normalization `+0.5 logdet(X'X)`. NTI có sai khác 3.08e-5; replay riêng với hằng số 1.837878 tái hiện output lưu. Đây là suy luận từ đồng nhất số, chưa phải xác nhận cách Phoenix triển khai. Không thay công thức estimator bằng hằng số làm tròn; ghi cả sai khác nguyên bản và replay chẩn đoán.

### Kiểm chứng nội miền / imbalance bằng error contrasts

Trước khi fit bổ sung: tạo fixture giả lập cố định seed 20261031, 30 người (9 TRTR, 21 RTRT), covariance sinh dữ liệu R,T `[[0.15,0.025],[0.025,0.25]]`, residual SD 0.16/0.28. Không tìm seed theo kết quả và không dùng số sinh dữ liệu làm expected estimates. Reference số được tính bằng chương trình độc lập chỉ trong test: null space trực chuẩn Q của X', response `Q'y`, covariance `Q'VQ`; tối ưu negative log density trong tọa độ năm variance/covariance tuyến tính bằng Nelder-Mead, khác FA/log-residual L-BFGS của prototype. Chỉ xét nghiệm G positive definite của fixture này; Hessian/sensitivity/df dùng finite differences ở nghiệm reference, không gọi projection/score/Hessian của prototype.

Ngưỡng test chốt trước chạy: covariance/SE/estimate/CI absolute 2e-6, relative 2e-5; df absolute 0.01, relative 2e-4, do Hessian số bậc hai. G phải nội miền và Hessian positive definite; khi thiếu điều kiện test phải thất bại, không thay seed hoặc tự bỏ test. Dữ liệu giả lập này kiểm chứng implementation độc lập, không thay bộ Phoenix imbalance còn thiếu hoặc cho phép mở kết luận ở boundary.

PHX-11 cần đặc tả missing và population riêng cho I/D_R/D_T/mixed fit, với fixtures missing/imbalance độc lập. PHX-12 tách MR/pAUC, IBE, PBE và in vitro thành các epic; khảo sát tên template không đủ căn cứ mở các phương pháp đó. Chưa có thay đổi kết luận nào thuộc các chương trình này.
