"""Concise, read-only explanations of input labels and result-table headers."""

from dataclasses import dataclass


@dataclass(frozen=True)
class HelpGroup:
    title: str
    entries: tuple[tuple[str, str], ...]


RAW_COLUMNS = (
    ("study_id", "Mã nghiên cứu (Study ID); liên kết duy nhất mọi dòng dữ liệu phân tích với đề cương thử nghiệm."),
    ("subject_id / Subject", "Mã định danh đối tượng nghiên cứu (người tình nguyện); bảo toàn cấu trúc kể cả số 0 ở đầu."),
    ("sequence / Sequence", "Trình tự dùng thuốc (ví dụ TR, RT, TRTR, RTRT) được phân bổ ngẫu nhiên theo kế hoạch ban đầu."),
    ("period / Period", "Kỳ điều trị (Period) trong thiết kế chéo; mỗi kỳ cách nhau khoảng thời gian đào thải (washout)."),
    ("treatment / Treatment", "Thuốc nghiên cứu dùng trong kỳ: Thuốc thử (T - Test) hoặc Thuốc đối chứng (R - Reference)."),
    ("dose_datetime", "Thời điểm dùng thuốc thực tế (ngày, giờ, phút và múi giờ ISO 8601) theo hồ sơ nghiên cứu lâm sàng."),
    ("sample_datetime", "Thời điểm lấy mẫu máu thực tế (ngày, giờ, phút) ghi nhận tại trung tâm nghiên cứu lâm sàng."),
    ("nominal_time_h", "Thời điểm lấy mẫu dự kiến theo đề cương (nominal time), tính từ lúc bắt đầu dùng thuốc."),
    ("actual_time_h / Time (h)", "Thời điểm lấy mẫu thực tế sau liều (actual time); dữ liệu bắt buộc để tính toán NCA chính xác."),
    ("concentration / Cplasma", "Nồng độ hoạt chất (hoặc chất chuyển hóa) trong huyết tương định lượng bằng LC-MS/MS hoặc HPLC."),
    ("concentration_unit", "Đơn vị nồng độ chuẩn hóa của dữ liệu đầu vào (ví dụ: ng/mL, µg/L, pg/mL)."),
    ("blq_flag / BLQ", "Cờ đánh dấu nồng độ dưới giới hạn định lượng (Below Limit of Quantification) xử lý theo SAP."),
    ("lloq / LLOQ", "Giới hạn định lượng dưới (Lower Limit of Quantification) của quy trình phân tích sinh học."),
    ("sample_id", "Mã định danh duy nhất của mẫu sinh học; dùng đối chiếu chuỗi lưu giữ (chain of custody) và audit."),
    ("analyte", "Tên hoạt chất mẹ hoặc chất chuyển hóa có hoạt tính cần xác định nồng độ theo đề cương."),
    ("source_batch", "Mã lô phân tích sinh học (Bioanalytical Batch Run) phục vụ truy vết tính hợp lệ phân tích."),
    ("sample_status", "Trạng thái mẫu (hợp lệ, pha loãng lại, phân tích lại theo SOP bioanalytical) phục vụ rà soát QC."),
)


NCA_PARAMETERS = (
    ("N_Samples", "Tổng số mẫu nồng độ định lượng được đưa vào phân tích dược động học không phân ngăn (NCA)."),
    ("Dose", "Liều dùng danh định (mg hoặc µg) của thuốc thử hoặc đối chứng cho đối tượng tương ứng."),
    ("Rsq", "Hệ số xác định R² của đường hồi quy log-tuyến tính các điểm nồng độ thuộc pha thải trừ cuối."),
    ("Rsq_adjusted", "Hệ số xác định hiệu chỉnh (Adjusted R²) theo số điểm lấy mẫu pha cuối; tiêu chuẩn chọn pha λz."),
    ("Corr_XY", "Hệ số tương quan Pearson giữa thời gian và ln(nồng độ) ở pha thải trừ cuối (giá trị âm)."),
    ("No_points_lambda_z", "Số điểm nồng độ pha cuối được giải thuật tối ưu (hoặc kiểm định viên) chọn để ước tính λz."),
    ("Lambda_z", "Hằng số tốc độ đào thải pha cuối (terminal elimination rate constant, λz, đơn vị 1/h)."),
    ("Lambda_z_intercept", "Hệ số chặn (ln y-intercept) của phương trình hồi quy tuyến tính pha đào thải cuối."),
    ("Lambda_z_lower / Lambda_z_upper", "Thời điểm bắt đầu và kết thúc của khoảng nồng độ được chọn để hồi quy xác định λz."),
    ("HL_Lambda_z / t1/2", "Thời gian bán thải pha cuối (terminal elimination half-life), tính bằng ln(2)/λz."),
    ("Span", "Độ dài khoảng hồi quy pha cuối tính theo số lần chu kỳ bán thải (khuyến cáo Span ≥ 2×t1/2)."),
    ("Tlag", "Thời gian trễ hấp thu (Absorption lag time), điểm lấy mẫu cuối cùng có nồng độ 0 trước khi tăng."),
    ("Tmax / tmax", "Thời điểm nồng độ đỉnh huyết tương quan sát được (Tmax); phản ánh tốc độ hấp thu của thuốc."),
    ("Cmax / cmax", "Nồng độ đỉnh huyết tương quan sát được (Cmax); chỉ tiêu chính đánh giá tốc độ và mức độ hấp thu."),
    ("Cmax_D", "Nồng độ đỉnh huyết tương hiệu chỉnh theo liều (Cmax/Dose), dùng so sánh giữa các mức liều."),
    ("Tlast", "Thời điểm lấy mẫu cuối cùng có nồng độ định lượng được (Clast ≥ LLOQ)."),
    ("Clast", "Nồng độ huyết tương đo được tại thời điểm định lượng cuối cùng (Tlast)."),
    ("Clast_pred", "Nồng độ tại Tlast dự đoán từ phương trình hồi quy log-tuyến tính pha thải trừ cuối."),
    ("AUClast / auc_last", "Diện tích dưới đường cong nồng độ–thời gian từ 0 đến Tlast (Linear-up/Log-down hoặc Linear)."),
    ("AUClast_D", "Diện tích dưới đường cong AUC0-tlast chia cho liều dùng đã khai báo (AUClast/Dose)."),
    ("AUCall", "Diện tích dưới đường cong tính đến điểm lấy mẫu cuối cùng (kể cả điểm BLQ sau Clast)."),
    ("AUCall_D", "Diện tích AUCall chuẩn hóa theo liều dùng đã khai báo (AUCall/Dose)."),
    ("AUCINF_obs / auc_inf", "AUC ngoại suy đến vô cùng dựa trên Clast quan sát: AUC0-∞ = AUClast + Clast/λz."),
    ("AUCINF_D_obs", "AUC ngoại suy đến vô cùng (AUC0-∞,obs) chuẩn hóa theo liều dùng (AUCinf/Dose)."),
    ("AUC_%Extrap_obs", "Tỷ lệ phần trăm AUC ngoại suy ngoài Tlast: (AUC∞ - AUClast)/AUC∞ × 100% (khuyến cáo ≤ 20%)."),
    ("AUCINF_pred", "AUC ngoại suy đến vô cùng dùng nồng độ dự đoán tại Tlast: AUClast + Clast,pred/λz."),
    ("AUCINF_D_pred", "AUC vô cùng dự đoán (AUC0-∞,pred) chia cho liều dùng (AUCinf,pred/Dose)."),
    ("AUC_%Extrap_pred", "Tỷ lệ phần trăm AUC ngoại suy tính theo nồng độ dự đoán Clast,pred (khuyến cáo ≤ 20%)."),
    ("Vz_F_obs / Vz_F_pred", "Thể tích phân bố biểu kiến ở pha đào thải (Vz/F) tính theo Clast quan sát hoặc dự đoán."),
    ("Cl_F_obs / Cl_F_pred", "Độ thanh thải biểu kiến toàn thân (CL/F) tính theo Clast quan sát hoặc dự đoán (Dose/AUC∞)."),
    ("AUMClast", "Diện tích dưới đường cong thời gian nhân nồng độ từ 0 đến Tlast (tích phân mô men bậc một)."),
    ("AUMCINF_obs", "Diện tích tích số thời gian-nồng độ ngoại suy đến vô cùng theo Clast quan sát."),
    ("AUMC_%Extrap_obs", "Phần trăm AUMC ngoại suy ngoài khoảng quan sát dựa trên Clast quan sát."),
    ("AUMCINF_pred", "Diện tích tích số thời gian-nồng độ ngoại suy đến vô cùng theo Clast dự đoán."),
    ("AUMC_%Extrap_pred", "Phần trăm AUMC ngoại suy ngoài khoảng quan sát dựa trên Clast dự đoán."),
    ("MRTlast", "Thời gian lưu trung bình trong cơ thể đến thời điểm Tlast, MRTlast = AUMClast/AUClast."),
    ("MRTINF_obs / MRTINF_pred", "Thời gian lưu trung bình (MRT) ngoại suy đến vô cùng theo Clast quan sát hoặc dự đoán."),
)


NCA_DETAIL_COLUMNS = (
    ("Subject / Treatment / Sequence / Period", "Bộ bốn định danh then chốt: Đối tượng, Thuốc (T/R), Trình tự (Sequence) và Kỳ (Period)."),
    ("Parameter / Units / Estimate", "Tên thông số PK, đơn vị đo chuẩn và giá trị ước tính từ giải thuật NCA không phân ngăn."),
    ("Time / Concentration", "Thời điểm lấy mẫu thực tế (giờ) và nồng độ huyết tương đo được tại mẫu tương ứng."),
    ("lambda_z_Incl / terminal", "Cờ nhị phân (1/0) đánh dấu điểm nồng độ được chọn vào hồi quy pha đào thải cuối λz."),
    ("Predicted / predicted", "Nồng độ huyết tương dự đoán từ phương trình hồi quy log-tuyến tính pha cuối."),
    ("Residual / residual", "Phần dư (nồng độ quan sát trừ nồng độ dự đoán) dùng đánh giá độ phù hợp pha cuối."),
    ("AUC / AUMC", "Diện tích dưới đường cong nồng độ tích lũy và diện tích mô men bậc một tích lũy theo thời gian."),
    ("Start Time / End Time", "Khoảng thời gian (giờ bắt đầu và kết thúc) của các điểm nồng độ hồi quy ước tính λz."),
    ("Fit Method / Selection", "Phương pháp chọn pha cuối (tối ưu hóa R²adj tự động hay hiệu chỉnh thủ công có kiểm soát)."),
    ("Review Reason / Reviewer", "Căn cứ khoa học và định danh người thẩm định khi có điều chỉnh lựa chọn pha cuối λz."),
    ("Message / Warnings and Errors", "Thông điệp chẩn đoán, cảnh báo (ví dụ ngoại suy AUC > 20%) hoặc lỗi phân tích NCA."),
)


BE_RESULTS = (
    ("Endpoint / Dependent", "Thông số PK đánh giá tương đương sinh học (thường phân tích trên thang ln(Cmax), ln(AUC))."),
    ("Vai trò / Endpoint_Role", "Vai trò của chỉ tiêu theo đề cương/SAP: Tiêu chí chính (Primary) hoặc Tiêu chí phụ (Secondary)."),
    ("Phương pháp / Method", "Mô hình thống kê áp dụng: ANOVA (ABE chuẩn), Mô hình hỗn hợp tuyến tính, hoặc RSABE/ABEL."),
    ("N / N_subjects", "Số lượng đối tượng nghiên cứu hoàn tất và có đủ dữ liệu đưa vào mô hình phân tích BE."),
    ("N_observations", "Tổng số lượt quan sát PK trong mô hình; lớn hơn số đối tượng trong thiết kế lặp lại."),
    ("N_missing", "Số lượng giá trị hoặc lượt quan sát bị khuyết thiếu (missing data) được thống kê theo SAP."),
    ("GMR / GMR_% / Ratio_%Ref_", "Tỷ số trung bình nhân (Geometric Mean Ratio) của Test so với Reference: exp(LSM_T - LSM_R)."),
    ("CI 90% / Lower_% / Upper_%", "Khoảng tin cậy 90% cho GMR (tương đương 2 kiểm định một phía TOST ở mức ý nghĩa α = 0,05)."),
    ("Giới hạn / Applicable_Lower_Percent / Applicable_Upper_Percent", "Khoảng chấp nhận BE áp dụng: 80,00–125,00% (chuẩn), 90,00–111,11% (NTI), hoặc mở rộng (RSABE/ABEL)."),
    ("UCB scaling / scaled_ucb", "Cận trên của tiêu chuẩn tương đương co giãn theo FDA (95% Upper Confidence Bound ≤ 0)."),
    ("Trạng thái / Decision", "Kết luận tương đương sinh học: ĐẠT (PASS), KHÔNG ĐẠT (FAIL) hoặc CHƯA ĐỦ ĐIỀU KIỆN ĐÁNH GIÁ."),
    ("Lý do / Reason", "Căn cứ thống kê chi tiết dẫn đến kết luận hoặc giải trình nguyên nhân không thể đánh giá."),
    ("RefLSM / TestLSM", "Trung bình bình phương tối thiểu (Least Squares Means) trên thang log tự nhiên của R và T."),
    ("RefGeoLSM / TestGeoLSM", "Trung bình hình học hiệu chỉnh của R và T sau khi biến đổi hàm mũ ngược exp(LSM)."),
    ("Difference / Estimate", "Ước lượng độ chênh lệch trên thang log (LSM_T - LSM_R) từ mô hình phân tích ANOVA."),
    ("StdError / Diff_SE", "Sai số chuẩn của độ chênh lệch (Standard Error of Difference) dùng tính khoảng tin cậy."),
    ("Denom_DF / Diff_DF", "Bậc tự do của phần dư (Residual Degrees of Freedom) dùng tra cứu phân vị phân phối Student."),
    ("T_stat / P_value", "Giá trị thống kê t và mức ý nghĩa p-value của hai kiểm định một phía (TOST)."),
    ("Conf_Level / T_critical", "Độ tin cậy thống kê (mặc định 90%) và giá trị ngưỡng t tới hạn tương ứng với bậc tự do."),
    ("CI_80_Lower / CI_80_Upper", "Giới hạn dưới và trên của khoảng tin cậy 80% (thường dùng thăm dò hoặc theo quy định riêng)."),
    ("CI_90_Lower / CI_90_Upper", "Giới hạn dưới và trên của khoảng tin cậy 90% (tiêu chuẩn vàng đánh giá ABE theo ICH M13A)."),
    ("CI_95_Lower / CI_95_Upper", "Giới hạn dưới và trên của khoảng tin cậy 95% (thường áp dụng cho chỉ tiêu an toàn lâm sàng)."),
    ("sWR / sWT", "Độ lệch chuẩn trong cá thể trên thang log (s_wR, s_wT) ước tính từ thiết kế lặp lại."),
    ("CVwR / CVwT", "Hệ số biến thiên trong cá thể (CV_w = sqrt(exp(s_w^2)-1)) của thuốc R và T; căn cứ phân loại HVD."),
    ("MSE", "Trung bình bình phương phần dư (Mean Squared Error) của mô hình; đo lường phương sai trong cá thể s²_intra."),
    ("LSM / Geometric_LSM", "Trung bình bình phương tối thiểu trên thang log và giá trị trung bình hình học sau biến đổi ngược."),
    ("Residuals / Studentized Residual", "Phần dư mô hình và phần dư chuẩn hóa theo Student dùng phát hiện đối tượng ngoại lai (outlier)."),
    ("Power_TOST / Power_80_20", "Lực kiểm định thống kê hậu nghiệm (post-hoc power); chỉ số tham khảo, không dùng bác bỏ kết luận BE."),
    ("Sequential SS / Partial SS", "Tổng bình phương loại I (tuần tự) và loại III (riêng phần) phân rã trong phân tích ANOVA."),
    ("Population Matrix / Used", "Ma trận theo dõi tình trạng mẫu từng kỳ và cờ xác nhận dữ liệu có đưa vào mô hình hay không."),
)


TMAX_RESULTS = (
    ("Tmax / tmax", "Thời điểm đạt nồng độ đỉnh (Tmax); chỉ tiêu PK đánh giá tốc độ hấp thu (phân tích phi tham số)."),
    ("Nhóm / N", "Nhóm thuốc (T hoặc R) và số lượng đối tượng có giá trị Tmax hợp lệ được phân tích."),
    ("Trung vị (giờ)", "Giá trị trung vị (Median) của thời điểm Tmax (giờ) kèm khoảng tứ phân vị hoặc cực trị."),
    ("Nhỏ nhất / Lớn nhất (giờ)", "Giá trị Tmax cực tiểu và cực đại quan sát được trong từng nhóm nghiên cứu."),
    ("p hai phía", "Giá trị p của kiểm định Wilcoxon signed-rank hai phía; tham khảo hỗ trợ lâm sàng."),
    ("N cặp / Trung vị (T−R)", "Số cặp đối tượng ghép đôi và trung vị độ chênh lệch Tmax (T - R) theo ước lượng Hodges-Lehmann."),
)


PAGE_HELP = (
    (
        HelpGroup("Ô nhập / thiết lập nghiên cứu", (
            ("Mã nghiên cứu / Tên nghiên cứu", "Mã định danh duy nhất (Study Code) và tên đầy đủ của nghiên cứu tương đương sinh học."),
            ("Thiết kế nghiên cứu", "Cấu trúc thử nghiệm: Chéo 2×2 (Crossover), Song song (Parallel) hoặc Lặp lại (Replicate)."),
            ("Bộ quy tắc pháp lý", "Khung hướng dẫn pháp lý (ICH M13A/EMA, US FDA, NTI, HVD) quyết định phương pháp thống kê."),
            ("Protocol / SAP và phiên bản", "Mã số đề cương và kế hoạch phân tích thống kê (SAP) kèm phiên bản phê duyệt trước thử nghiệm."),
            ("Mục đích sử dụng dữ liệu / provenance", "Mục tiêu phân tích (đăng ký lưu hành, đào tạo sau đại học) và nguồn gốc dữ liệu thử nghiệm."),
            ("Hoạt chất / Liều dùng (mg)", "Tên hoạt chất (INN) và liều dùng danh định trong thử nghiệm tương đương sinh học."),
            ("Dạng giải phóng IR / MR", "Dạng bào chế giải phóng: Giải phóng tức thời (IR) hoặc Giải phóng biến đổi (MR/XR/ER)."),
            ("Trạng thái khi dùng thuốc", "Điều kiện dùng thuốc theo protocol: Uống lúc đói (Fasted) hoặc sau bữa ăn chuẩn (Fed)."),
            ("T / R", "Khai báo định danh thuốc thử (T - Test) và thuốc đối chứng/biệt dược gốc (R - Reference)."),
            ("Hàm lượng / Nồng độ / Số lô / Hạn dùng", "Thông tin bào chế: Hàm lượng công bố, số lô sản xuất và hạn dùng của hai chế phẩm."),
            ("Bắt đầu / Kết thúc / Data Lock", "Tiến độ lâm sàng: Ngày thu nhận mẫu đầu, ngày hoàn tất phân tích và mốc khóa dữ liệu."),
            ("NTI / HVD / Scaling", "Phân loại thuốc có khoảng trị liệu hẹp (NTI), biến thiên cao (HVD) và phương pháp co giãn."),
            ("Guideline / PSG / Bằng chứng rà soát phạm vi", "Căn cứ khoa học: Guideline cụ thể hoặc Product-Specific Guidance (PSG) được áp dụng."),
        )),
        HelpGroup("Trạng thái dự án", (
            ("CURRENT / STALE / LEGACY", "Trạng thái kết quả: Khớp hoàn toàn với dữ liệu / Đã lỗi thời do sửa đổi / Lưu từ bản cũ."),
            ("Revision / Snapshot", "Chỉ số phiên bản dữ liệu hiện hành / Bản chụp trạng thái (Snapshot) tại thời điểm phân tích."),
        )),
    ),
    (
        HelpGroup("Ô nhập tính cỡ mẫu", (
            ("CV AUC / CV Cmax", "Hệ số biến thiên trong cá thể (intra-subject CV) giả định của AUC và Cmax từ y văn."),
            ("GMR", "Tỷ số trung bình nhân Test/Reference dự kiến (thường chọn 0,95 để có cỡ mẫu an toàn)."),
            ("Power mục tiêu", "Lực kiểm định thống kê mong muốn (thường chọn 80% hoặc 90% theo quy chuẩn quốc tế)."),
            ("Dropout", "Tỷ lệ dự kiến đối tượng bỏ cuộc hoặc loại khỏi nghiên cứu để bù trừ vào số tuyển sinh."),
            ("Nguồn CV", "Trích dẫn tài liệu y văn, dữ liệu pilot hoặc báo cáo phê duyệt làm căn cứ ước tính CV."),
        )),
        HelpGroup("Bảng kết quả planning", (
            ("N đánh giá / N tuyển", "Số đối tượng cần phân tích hoàn tất / Tổng số đối tượng cần tuyển sinh sau khi bù dropout."),
            ("Power đạt được", "Lực kiểm định tính toán thực tế tại cỡ mẫu đã làm tròn theo số chuỗi ngẫu nhiên."),
            ("Endpoint chi phối", "Chỉ tiêu PK (AUC hoặc Cmax) đòi hỏi cỡ mẫu lớn hơn và quyết định quy mô nghiên cứu."),
            ("TOST", "Thủ tục hai kiểm định một phía đồng thời (Two One-Sided Tests) ở mức ý nghĩa α = 0,05."),
        )),
    ),
    (
        HelpGroup("Ô nhập phân nhóm", (
            ("Số người tuyển", "Tổng số người tình nguyện cần phân bổ đều vào các trình tự điều trị (Sequence)."),
            ("Seed", "Giá trị khởi tạo bộ sinh số giả ngẫu nhiên; bắt buộc ghi nhận để tái lập danh sách phân nhóm."),
            ("Kích thước block", "Quy mô khối hoán vị (Block Size) đảm bảo cân bằng tỷ lệ đối tượng giữa các nhánh thử nghiệm."),
            ("Lịch lấy mẫu dự kiến (giờ)", "Các thời điểm lấy mẫu máu sau liều theo đề cương, ngăn cách bằng dấu phẩy."),
        )),
        HelpGroup("Cột bảng phân nhóm / lịch", (
            ("randomization_id", "Mã số thứ tự ngẫu nhiên hóa (Randomization ID) cấp phát cho từng đối tượng."),
            ("screening_id / subject_id", "Mã sàng lọc lâm sàng (Screening ID) / Mã đối tượng nghiên cứu (Subject ID)."),
            ("sequence / period / treatment", "Trình tự điều trị phân bổ (Sequence) / Kỳ thử nghiệm (Period) / Thuốc dùng (T hoặc R)."),
            ("nominal_time_h / actual_time_h", "Giờ lấy mẫu dự kiến theo protocol / Giờ lấy mẫu thực tế được ghi nhận lâm sàng."),
        )),
    ),
    (
        HelpGroup("Ô nhập và xử lý tệp", (
            ("CSV / XLSX", "Tệp nồng độ thô: Cấu trúc mỗi hàng ứng với một mẫu máu; Excel cần chọn đúng sheet."),
            ("Mapping JSON", "Bảng ánh xạ tên cột từ tệp dữ liệu phòng thí nghiệm sang tên biến chuẩn của phần mềm."),
            ("Xác nhận đơn vị", "Kiểm tra và xác nhận đơn vị nồng độ, thời gian trước khi lưu vết vào hệ thống."),
        )),
        HelpGroup("Cột dữ liệu nồng độ (16 cột bắt buộc + tùy chọn)", RAW_COLUMNS),
    ),
    (
        HelpGroup("Ô nhập QC / correction", (
            ("Đối tượng cần sửa / Kỳ cần sửa", "Chọn chính xác đối tượng nghiên cứu và kỳ điều trị cần thực hiện hiệu chỉnh dữ liệu."),
            ("Lý do correction", "Giải trình lý do khoa học của việc sửa đổi theo quy trình kiểm soát chất lượng (SOP)."),
            ("Người rà soát độc lập", "Định danh cán bộ kiểm tra chất lượng (QA/QC) độc lập phê duyệt thao tác chỉnh sửa."),
            ("Tham chiếu bằng chứng correction", "Số phiếu kiểm tra (QC Ticket), biên bản độ lệch (Deviation Report) hoặc số trang labbook."),
            ("Data Freeze và khóa SAP", "Thao tác chốt dữ liệu (Data Freeze) ngăn chặn chỉnh sửa trái phép trước khi phân tích thống kê."),
        )),
        HelpGroup("Cột bảng QC", (
            ("severity", "Mức độ sai sót: ERROR (chặn tiến trình phân tích) hoặc WARNING (cảnh báo cần rà soát)."),
            ("row / column", "Vị trí hàng và tên cột trong tệp dữ liệu phát hiện bất thường cần hiệu chỉnh."),
            ("code / message", "Mã định danh lỗi quy chuẩn và thông điệp giải thích chi tiết sai sót kiểm tra dữ liệu."),
            *RAW_COLUMNS,
        )),
    ),
    (
        HelpGroup("Ô nhập cấu hình NCA", (
            ("Quy tắc tích phân AUC", "Thuật toán tính AUC: Tuyến tính tăng – log giảm (linear_up_log_down) hoặc Hình thang tuyến tính (linear)."),
            ("Số điểm pha cuối", "Số lượng điểm nồng độ tối thiểu ở pha thải trừ cuối tham gia hồi quy ước tính λz (≥ 3)."),
            ("Adjusted R²", "Ngưỡng hệ số xác định hiệu chỉnh tối thiểu để chấp nhận độ dốc pha thải trừ cuối λz."),
            ("Pha terminal / Review Reason", "Khoảng thời gian pha cuối được chọn và ghi nhận căn cứ khoa học khi can thiệp thủ công."),
            ("Xử lý endpoint thiếu", "Quy định xử lý trường hợp khuyết thiếu thông số PK theo kế hoạch phân tích thống kê (SAP)."),
        )),
        HelpGroup("Cột / hàng thông số NCA", NCA_PARAMETERS),
        HelpGroup("Cột bảng chi tiết mẫu và pha cuối", NCA_DETAIL_COLUMNS),
    ),
    (
        HelpGroup("Ô nhập thống kê BE", (
            ("Thiết kế / Thang raw, ln, log10", "Cấu trúc thiết kế thử nghiệm và thang đo biến đổi của thông số PK đầu vào."),
            ("Mapping Subject, Sequence, Period, Treatment", "Ánh xạ các cột định danh thiết kế nghiên cứu vào mô hình phân tích ANOVA."),
            ("Phương sai parallel pooled / welch", "Lựa chọn phân tích phương sai gộp (Pooled ANOVA) hoặc hiệu chỉnh Welch cho mẫu song song."),
        )),
        HelpGroup("Cột thống kê BE / ANOVA / scaling", BE_RESULTS),
        HelpGroup("Bảng so sánh Tmax phi tham số", TMAX_RESULTS),
    ),
    (
        HelpGroup("Ô chọn đồ thị", (
            ("Đối tượng / Profile", "Lựa chọn đối tượng, kỳ thử nghiệm, thuốc và chất phân tích để hiển thị đường cong PK."),
            ("Semilog / Bán log", "Biểu diễn đồ thị trên trục tung logarit giúp quan sát tuyến tính hóa pha thải trừ cuối."),
            ("Mean / SD", "Đường cong nồng độ trung bình kèm thanh độ lệch chuẩn (SD) theo từng nhóm điều trị T và R."),
        )),
        HelpGroup("Chỉ tiêu và trục đồ thị", (
            ("Time (h) / Concentration (ng/mL)", "Trục hoành biểu thị thời gian sau liều (giờ) / Trục tung biểu thị nồng độ huyết tương."),
            ("GMR / CI 90%", "Tỷ số trung bình nhân T/R và khoảng tin cậy 90% biểu diễn trên biểu đồ Forest Plot."),
            ("Residual / Predicted", "Biểu đồ phân tán phần dư so với giá trị dự đoán dùng kiểm tra tính chuẩn và đồng nhất phương sai."),
            ("Endpoint", "Thông số dược động học (Cmax, AUClast, AUCinf) được trực quan hóa trên đồ thị."),
        )),
    ),
    (
        HelpGroup("Ô nhập báo cáo / xuất", (
            ("Protocol / SAP", "Thông tin định danh đề cương và kế hoạch phân tích thống kê trích dẫn trong báo cáo chính thức."),
            ("Ngôn ngữ báo cáo", "Ngôn ngữ văn bản xuất báo cáo tổng kết thử nghiệm lâm sàng (Tiếng Việt hoặc Tiếng Anh)."),
            ("Archive / .bewf.zip", "Tệp lưu trữ dự án chứa toàn bộ dữ liệu thô, cấu hình, mã băm và kết quả để phục dựng."),
        )),
        HelpGroup("Cột / mã truy vết kết quả", (
            ("Endpoint / Decision / Reason", "Chỉ tiêu PK, kết luận tương đương sinh học và luận cứ thống kê của từng lần phân tích."),
            ("analysis_run_id / run", "Mã băm duy nhất (Analysis Run ID) xác thực lần chạy mô hình tạo nên kết quả báo cáo."),
            ("dataset_revision / config_revision", "Chỉ số phiên bản của bộ dữ liệu và cấu hình phân tích tương ứng với lần chạy."),
            ("input_fingerprint / SHA256", "Mã băm mật mã SHA-256 xác thực tính toàn vẹn và bất biến của dữ liệu đầu vào."),
            ("CURRENT / STALE", "Trạng thái xác thực kết quả: Khớp chính xác với dữ liệu hiện hành hay đã bị thay đổi."),
        )),
    ),
    (
        HelpGroup("Cột nhật ký / quản trị", (
            ("timestamp / Thời điểm", "Dấu thời gian chính xác (ISO 8601 kèm múi giờ) khi sự kiện được hệ thống ghi nhận."),
            ("action / event", "Loại thao tác thực hiện: Nhập dữ liệu, QC hiệu chỉnh, Freeze, Khóa SAP, Chạy mô hình, Xuất báo cáo."),
            ("operator / actor", "Định danh người dùng hoặc vai trò thao tác được ghi nhận trong vệt kiểm toán (Audit Trail)."),
            ("details / payload", "Dữ liệu chi tiết về thay đổi, tham số cấu hình hoặc giá trị trước/sau khi tác động."),
            ("input_revision / dataset_revision", "Phiên bản dữ liệu và cấu hình ghi nhận tại thời điểm phát sinh sự kiện."),
            ("journal / checkpoint", "Bản ghi nhật ký tuần tự / Điểm kiểm tra trạng thái toàn vẹn của cơ sở dữ liệu."),
            ("fingerprint / hash", "Mã băm toàn vẹn (Integrity Hash) phục vụ phát hiện mọi hành vi can thiệp trái phép."),
        )),
    ),
)


INDEPENDENT_HELP = {
    "pk": (
        HelpGroup("Ô và cột nhập nồng độ", (
            ("profile_id / Mã hồ sơ", "Mã định danh riêng cho từng đường cong nồng độ–thời gian của đối tượng nghiên cứu."),
            ("time_h / Thời gian (giờ)", "Thời điểm lấy mẫu thực tế sau liều tính theo thang đo giờ (Time after dose)."),
            ("concentration / Cplasma", "Nồng độ hoạt chất đo được trong mẫu sinh học tương ứng với thời điểm lấy mẫu."),
            ("blq / BLQ", "Cờ đánh dấu nồng độ dưới giới hạn định lượng phân tích (Below Limit of Quantification)."),
            ("τ / Khoảng cách giữa hai liều", "Khoảng thời gian dùng thuốc lặp lại (Dosing interval, tau) trong phác đồ đa liều."),
            ("Tổng số liều đã dùng", "Số lần đưa thuốc thực tế của đối tượng trước thời điểm đánh giá dược động học."),
            ("Đường dùng / Liều / Đơn vị", "Đường dùng thuốc (Uống, Tiêm TM) và liều lượng cần thiết để ước tính thể tích và độ thanh thải."),
            ("Số điểm pha cuối / Adjusted R²", "Số điểm nồng độ tối thiểu và ngưỡng R²adj để giải thuật tự động nhận diện pha đào thải λz."),
        )),
        HelpGroup("Cột kết quả PK / mô hình", (
            ("Cmax / Tmax / AUClast / AUCINF", "Các thông số PK cơ bản: Nồng độ đỉnh, thời điểm đạt đỉnh, AUC đến mẫu cuối và AUC vô cùng."),
            ("AUCτ / Cmin,ss / Cavg,ss", "Thông số trạng thái ổn định: AUC trong khoảng liều, nồng độ đáy và nồng độ trung bình."),
            ("AUMC / MRT", "Diện tích tích số thời gian-nồng độ (AUMC) và thời gian lưu trung bình trong cơ thể (MRT)."),
            ("lambda_z / t_half", "Hằng số tốc độ đào thải pha cuối (λz) và thời gian bán thải sinh học tương ứng (t1/2)."),
            ("CL/F / Vz/F", "Độ thanh thải biểu kiến và thể tích phân bố biểu kiến khi dùng qua đường uống (chưa biết F)."),
            ("RMSE (ng/mL)", "Căn bậc hai trung bình bình phương sai số dự đoán nồng độ (Root Mean Squared Error)."),
            ("AICc / BIC", "Tiêu chuẩn thông tin Akaike hiệu chỉnh và Bayesian dùng so sánh độ tối ưu giữa các mô hình PK."),
            ("Trọng số / Điều kiện Jacobian", "Sơ đồ gán trọng số phương sai sai số và chỉ số điều kiện ma trận Jacobian đánh giá độ ổn định số."),
        )),
    ),
    "quick": (
        HelpGroup("Ô và cột đầu vào BE nhanh", (
            ("Subject / Sequence / Period / Treatment", "Bốn biến định danh bắt buộc: Đối tượng, Trình tự ngẫu nhiên, Kỳ thử nghiệm và Thuốc T/R."),
            ("Cplasma / Time (h)", "Cặp dữ liệu nồng độ và thời gian sau liều dùng khi tính trực tiếp thông số NCA."),
            ("Cmax / AUClast / AUCinf", "Các chỉ tiêu dược động học đầu vào nếu người dùng tải lên bảng thông số đã tính sẵn."),
            ("Thang raw / ln / log10", "Thang đo thực tế của dữ liệu PK nhập vào (cần khai báo chính xác để biến đổi log tự nhiên)."),
            ("Mapping / Đơn vị", "Ánh xạ các cột của tệp tải lên vào các biến hệ thống và xác nhận đơn vị đo lường."),
        )),
        HelpGroup("Cột bảng kết quả BE nhanh", (
            ("Endpoint / GMR / CI 90%", "Chỉ tiêu PK, tỷ số trung bình nhân T/R và khoảng tin cậy 90% đánh giá tương đương sinh học."),
            ("N / Quyết định / Lý do", "Số đối tượng hoàn tất đánh giá, kết luận tương đương sinh học (ĐẠT/KHÔNG ĐẠT) và luận cứ."),
            ("status / reason", "Trạng thái ước tính NCA của từng cá thể và nguyên nhân nếu hồ sơ không đủ điều kiện."),
            ("auc_extrap_pct", "Tỷ lệ phần trăm AUC ngoại suy ngoài thời điểm quan sát cuối cùng (khuyến cáo ≤ 20%)."),
            *TMAX_RESULTS,
        )),
    ),
}


def field_help_for(page: int | str) -> tuple[HelpGroup, ...]:
    """Return UI label help for a full-BE step or independent workflow."""
    if isinstance(page, int):
        return PAGE_HELP[page]
    return INDEPENDENT_HELP[page]
import re
from collections.abc import Iterable
import streamlit as st


EXPLICIT_TERMS: dict[str, str] = {
    # BE Results & Statistics
    "endpoint": "Thông số PK đánh giá tương đương sinh học (thường trên thang ln(Cmax), ln(AUC)).",
    "method": "Mô hình thống kê áp dụng: ANOVA OLS/REML (2×2), Pooled/Welch (Parallel) hoặc ABEL/RSABE.",
    "phương pháp": "Mô hình thống kê áp dụng: ANOVA OLS/REML (2×2), Pooled/Welch (Parallel) hoặc ABEL/RSABE.",
    "vai trò": "Vai trò chỉ tiêu theo SAP: Primary (quyết định BE chính) hoặc Secondary (tham khảo hỗ trợ).",
    "n": "Số lượng đối tượng nghiên cứu hoàn tất và có đủ dữ liệu đưa vào mô hình phân tích BE.",
    "n_subjects": "Số lượng đối tượng nghiên cứu hoàn tất và có đủ dữ liệu đưa vào mô hình phân tích BE.",
    "n_observations": "Tổng số lượt quan sát PK trong mô hình; lớn hơn số đối tượng trong thiết kế lặp lại.",
    "n_excluded": "Số lượng bản ghi hoặc đối tượng bị loại khỏi tập phân tích theo tiêu chuẩn SAP.",
    "gmr": "Tỷ số trung bình nhân (Geometric Mean Ratio) của Test so với Reference: exp(LSM_T - LSM_R).",
    "ci 90%": "Khoảng tin cậy 90% cho GMR (tương đương hai kiểm định một phía TOST ở mức α = 0,05).",
    "ci 90% (bổ trợ nếu rsabe)": "Khoảng tin cậy 90% cho GMR; trong FDA RSABE chỉ dùng tham khảo bên cạnh chuẩn GMR [80–125%] và UCB95 ≤ 0.",
    "ci_lower": "Giới hạn dưới của khoảng tin cậy 90% cho GMR (mức ý nghĩa α = 0,05).",
    "ci_upper": "Giới hạn trên của khoảng tin cậy 90% cho GMR (mức ý nghĩa α = 0,05).",
    "lower_%": "Giới hạn dưới của khoảng tin cậy 90% cho GMR biểu diễn theo phần trăm (%).",
    "upper_%": "Giới hạn trên của khoảng tin cậy 90% cho GMR biểu diễn theo phần trăm (%).",
    "giới hạn": "Khoảng chấp nhận BE áp dụng: 80,00–125,00% (chuẩn), 90,00–111,11% (NTI) hoặc mở rộng theo ABEL.",
    "ucb scaling": "Cận trên tin cậy 95% theo Howe (RSABE FDA) phải ≤ 0 cùng điểm ước lượng GMR trong [80,00–125,00%].",
    "trạng thái": "Kết luận tương đương sinh học hoặc tính hợp lệ: ĐẠT (PASS), KHÔNG ĐẠT (FAIL) hoặc NOT EVALUABLE.",
    "decision": "Kết luận tương đương sinh học: ĐẠT (PASS), KHÔNG ĐẠT (FAIL) hoặc NOT EVALUABLE.",
    "quyết định": "Kết luận tương đương sinh học cho endpoint: PASS (ĐẠT), FAIL (KHÔNG ĐẠT) hoặc NOT EVALUABLE.",
    "reason": "Căn cứ thống kê chi tiết dẫn đến kết luận hoặc giải trình nguyên nhân không thể đánh giá.",
    "lý do": "Căn cứ thống kê chi tiết dẫn đến kết luận hoặc giải trình nguyên nhân không thể đánh giá.",
    "khoảng đạt": "Tỷ lệ phần trăm giới hạn chấp nhận BE đang áp dụng cho endpoint (%).",
    "gmr (%)": "Tỷ số trung bình nhân T/R biểu diễn dưới dạng tỷ lệ phần trăm (%).",
    "ci90 thấp (%)": "Giới hạn dưới của khoảng tin cậy 90% biểu diễn theo tỷ lệ phần trăm (%).",
    "ci90 cao (%)": "Giới hạn trên của khoảng tin cậy 90% biểu diễn theo tỷ lệ phần trăm (%).",
    "cv nội (%)": "Hệ số biến thiên trong cá thể (CV_intra) từ mô hình ANOVA crossover/replicate; trống nếu Parallel.",
    "cv_intra": "Hệ số biến thiên trong cá thể (CV_intra) trên thang log; không tách riêng được trong thiết kế Parallel.",
    "cv_within": "Hệ số biến thiên trong cá thể (intra-subject CV), tính từ phương sai sai số mô hình.",
    "swr": "Độ lệch chuẩn trong cá thể của thuốc đối chứng R trên thang log (s_wR).",
    "swt": "Độ lệch chuẩn trong cá thể của thuốc thử T trên thang log (s_wT).",
    "cvwr": "Hệ số biến thiên trong cá thể của thuốc đối chứng R: sqrt(exp(s_wR²) - 1).",
    "cvwt": "Hệ số biến thiên trong cá thể của thuốc thử T: sqrt(exp(s_wT²) - 1).",
    "mse": "Trung bình bình phương phần dư (Mean Squared Error); đo lường phương sai trong cá thể s²_intra.",
    "ucb_95": "Cận trên 95% của tiêu chuẩn co giãn (Scaled Upper Confidence Bound theo US FDA ≤ 0).",
    "scaled_ucb": "Cận trên của tiêu chuẩn tương đương co giãn theo FDA (95% Upper Confidence Bound ≤ 0).",
    "sd_ratio_ci90_lower": "Giới hạn dưới của khoảng tin cậy 90% cho tỷ số độ lệch chuẩn sWT/sWR (FDA NTI).",
    "sd_ratio_ci90_upper": "Giới hạn trên của khoảng tin cậy 90% cho tỷ số độ lệch chuẩn sWT/sWR (tiêu chuẩn ≤ 2,5).",
    "lower_limit": "Ngưỡng chấp nhận dưới của khoảng tương đương sinh học (thường 80,00% hoặc 90,00%).",
    "upper_limit": "Ngưỡng chấp nhận trên của khoảng tương đương sinh học (thường 125,00% hoặc 111,11%).",
    "applicable_lower_percent": "Ngưỡng chấp nhận dưới áp dụng cho endpoint theo quy chế được chọn (%).",
    "applicable_upper_percent": "Ngưỡng chấp nhận trên áp dụng cho endpoint theo quy chế được chọn (%).",
    "reflsm": "Trung bình bình phương tối thiểu (Least Squares Means) trên thang log của thuốc đối chứng R.",
    "testlsm": "Trung bình bình phương tối thiểu (Least Squares Means) trên thang log của thuốc thử T.",
    "refgeolsm": "Trung bình hình học hiệu chỉnh của thuốc đối chứng R sau khi mũ hóa ngược exp(LSM).",
    "testgeolsm": "Trung bình hình học hiệu chỉnh của thuốc thử T sau khi mũ hóa ngược exp(LSM).",
    "difference": "Ước lượng độ chênh lệch trên thang log tự nhiên (LSM_T - LSM_R) từ mô hình ANOVA.",
    "estimate": "Giá trị ước lượng điểm của tham số hoặc độ chênh lệch hiệu ứng điều trị.",
    "stderror": "Sai số chuẩn của độ chênh lệch (Standard Error of Difference) dùng tính khoảng tin cậy.",
    "diff_se": "Sai số chuẩn của độ chênh lệch (Standard Error of Difference) dùng tính khoảng tin cậy.",
    "denom_df": "Bậc tự do của phần dư (Residual Degrees of Freedom) dùng tra cứu phân vị phân phối Student.",
    "diff_df": "Bậc tự do của độ chênh lệch dùng trong suy luận thống kê và tính khoảng tin cậy.",
    "t_stat": "Giá trị thống kê kiểm định t của hai kiểm định một phía (TOST).",
    "p_value": "Mức ý nghĩa p-value của kiểm định thống kê; so sánh với ngưỡng ý nghĩa α = 0,05.",
    "conf_level": "Mức độ tin cậy thống kê của khoảng ước lượng (mặc định 90% theo quy chuẩn ABE).",
    "t_critical": "Giá trị t tới hạn tra cứu từ phân vị phân phối Student tại bậc tự do tương ứng.",
    "power": "Lực kiểm định thống kê (thường chọn ≥ 80% hoặc ≥ 90% theo quy chuẩn quốc tế).",
    "power_tost": "Lực kiểm định thống kê hậu nghiệm (post-hoc power); chỉ số tham khảo, không bác bỏ kết luận BE.",
    "power_80_20": "Chỉ số power bổ trợ theo nguyên tắc 80/20 của thống kê thử nghiệm lâm sàng.",
    "tost": "Thủ tục hai kiểm định một phía đồng thời (Two One-Sided Tests) ở mức ý nghĩa α = 0,05.",
    "alpha": "Mức ý nghĩa thống kê α trong TOST (mặc định 0,05 ~ 90% CI); hoặc hằng số tốc độ pha phân bố nhanh α (1/h) trong PK đa ngăn.",

    # PK & NCA Parameters
    "cmax": "Nồng độ đỉnh huyết tương quan sát được (Cmax); chỉ tiêu chính đánh giá tốc độ và mức độ hấp thu.",
    "tmax": "Thời điểm nồng độ đỉnh huyết tương quan sát được (Tmax); phản ánh tốc độ hấp thu của thuốc.",
    "auc_last": "Diện tích dưới đường cong nồng độ–thời gian từ 0 đến Tlast (Linear-up/Log-down hoặc Linear).",
    "auclast": "Diện tích dưới đường cong nồng độ–thời gian từ 0 đến Tlast (Linear-up/Log-down hoặc Linear).",
    "auc_inf": "AUC ngoại suy đến vô cùng dựa trên Clast quan sát: AUC0-∞ = AUClast + Clast/λz.",
    "aucinf_obs": "AUC ngoại suy đến vô cùng dựa trên Clast quan sát: AUC0-∞ = AUClast + Clast/λz.",
    "auc_inf_pred": "AUC ngoại suy đến vô cùng dùng nồng độ dự đoán tại Tlast: AUClast + Clast,pred/λz.",
    "aucinf_pred": "AUC ngoại suy đến vô cùng dùng nồng độ dự đoán tại Tlast: AUClast + Clast,pred/λz.",
    "auc_extrap_pct": "Tỷ lệ phần trăm AUC ngoại suy ngoài Tlast: (AUC∞ - AUClast)/AUC∞ × 100% (khuyến cáo ≤ 20%).",
    "auc_%extrap_obs": "Tỷ lệ phần trăm AUC ngoại suy ngoài Tlast: (AUC∞ - AUClast)/AUC∞ × 100% (khuyến cáo ≤ 20%).",
    "auc_%extrap_pred": "Tỷ lệ phần trăm AUC ngoại suy ngoài Tlast tính theo Clast dự đoán (khuyến cáo ≤ 20%).",
    "half_life": "Thời gian bán thải pha đào thải cuối (t1/2 = ln(2)/λz).",
    "hl_lambda_z": "Thời gian bán thải pha đào thải cuối (t1/2 = ln(2)/λz).",
    "lambda_z": "Hằng số tốc độ đào thải pha cuối (terminal elimination rate constant, λz, đơn vị 1/h).",
    "span": "Độ dài khoảng hồi quy pha cuối tính theo số lần chu kỳ bán thải (khuyến cáo Span ≥ 2×t1/2).",
    "tlast": "Thời điểm lấy mẫu cuối cùng có nồng độ định lượng được (Clast ≥ LLOQ).",
    "clast": "Nồng độ huyết tương đo được tại thời điểm định lượng cuối cùng (Tlast).",
    "clast_pred": "Nồng độ tại Tlast dự đoán từ phương trình hồi quy log-tuyến tính pha thải trừ cuối.",
    "rsq": "Hệ số xác định R² của đường hồi quy log-tuyến tính các điểm nồng độ thuộc pha thải trừ cuối.",
    "rsq_adjusted": "Hệ số xác định hiệu chỉnh (Adjusted R²) theo số điểm lấy mẫu pha cuối; tiêu chuẩn chọn pha λz.",
    "corr_xy": "Hệ số tương quan Pearson giữa thời gian và ln(nồng độ) ở pha thải trừ cuối (giá trị âm).",
    "no_points_lambda_z": "Số điểm nồng độ pha cuối được giải thuật tối ưu (hoặc kiểm định viên) chọn để ước tính λz.",
    "vz_f_obs": "Thể tích phân bố biểu kiến ở pha đào thải (Vz/F) tính theo Clast quan sát (Dose / [λz × AUC∞]).",
    "cl_f_obs": "Độ thanh thải biểu kiến toàn thân (CL/F) tính theo Clast quan sát (Dose / AUC∞).",
    "aumclast": "Diện tích dưới đường cong thời gian nhân nồng độ từ 0 đến Tlast (tích phân mô men bậc một).",
    "aumcinf_obs": "Diện tích tích số thời gian-nồng độ ngoại suy đến vô cùng theo Clast quan sát.",
    "mrtlast": "Thời gian lưu trung bình trong cơ thể đến thời điểm Tlast, MRTlast = AUMClast/AUClast.",
    "mrtinf_obs": "Thời gian lưu trung bình (MRT) ngoại suy đến vô cùng theo Clast quan sát.",

    # Raw columns & Study design
    "subject_id": "Mã định danh đối tượng nghiên cứu (người tình nguyện); bảo toàn cấu trúc kể cả số 0 ở đầu.",
    "subject": "Mã định danh đối tượng nghiên cứu (người tình nguyện); bảo toàn cấu trúc kể cả số 0 ở đầu.",
    "sequence": "Trình tự dùng thuốc (ví dụ TR, RT, TRTR, RTRT) được phân bổ ngẫu nhiên theo kế hoạch ban đầu.",
    "period": "Kỳ điều trị (Period) trong thiết kế chéo; mỗi kỳ cách nhau khoảng thời gian đào thải (washout).",
    "treatment": "Thuốc nghiên cứu dùng trong kỳ: Thuốc thử (T - Test) hoặc Thuốc đối chứng (R - Reference).",
    "actual_time_h": "Thời điểm lấy mẫu thực tế sau liều (actual time); dữ liệu bắt buộc để tính toán NCA chính xác.",
    "nominal_time_h": "Thời điểm lấy mẫu dự kiến theo đề cương (nominal time), tính từ lúc bắt đầu dùng thuốc.",
    "concentration": "Nồng độ hoạt chất (hoặc chất chuyển hóa) trong huyết tương định lượng bằng LC-MS/MS hoặc HPLC.",
    "concentration_unit": "Đơn vị nồng độ chuẩn hóa của dữ liệu đầu vào (ví dụ: ng/mL, µg/L, pg/mL).",
    "blq_flag": "Cờ đánh dấu nồng độ dưới giới hạn định lượng (Below Limit of Quantification) xử lý theo SAP.",
    "blq": "Cờ đánh dấu nồng độ dưới giới hạn định lượng (Below Limit of Quantification) xử lý theo SAP.",
    "lloq": "Giới hạn định lượng dưới (Lower Limit of Quantification) của quy trình phân tích sinh học.",
    "dose_datetime": "Thời điểm dùng thuốc thực tế (ngày, giờ, phút và múi giờ ISO 8601) theo hồ sơ lâm sàng.",
    "sample_datetime": "Thời điểm lấy mẫu máu thực tế (ngày, giờ, phút) ghi nhận tại trung tâm nghiên cứu lâm sàng.",
    "sample_id": "Mã định danh duy nhất của mẫu sinh học; dùng đối chiếu chuỗi lưu giữ (chain of custody) và audit.",
    "analyte": "Tên hoạt chất mẹ hoặc chất chuyển hóa có hoạt tính cần xác định nồng độ theo đề cương.",
    "source_batch": "Mã lô phân tích sinh học (Bioanalytical Batch Run) phục vụ truy vết tính hợp lệ phân tích.",
    "study_id": "Mã nghiên cứu (Study ID); liên kết duy nhất mọi dòng dữ liệu phân tích với đề cương thử nghiệm.",
    "status": "Trạng thái hợp lệ của dữ liệu hoặc kết quả phân tích theo tiêu chuẩn kiểm tra.",
    "severity": "Mức độ sai sót: ERROR (chặn tiến trình phân tích) hoặc WARNING (cảnh báo cần rà soát).",
    "row": "Vị trí hàng trong tệp dữ liệu nguồn phát sinh vấn đề kiểm soát chất lượng (QC).",
    "column": "Tên cột dữ liệu phát sinh vấn đề kiểm soát chất lượng (QC).",
    "code": "Mã định danh quy chuẩn của quy tắc kiểm tra QC dữ liệu.",
    "message": "Nội dung thông báo chẩn đoán hoặc giải thích chi tiết phát hiện QC.",

    # Model evaluation criteria
    "rmse (ng/ml)": "Căn bậc hai trung bình bình phương sai số dự đoán nồng độ (Root Mean Squared Error).",
    "rmse": "Căn bậc hai trung bình bình phương sai số dự đoán nồng độ (Root Mean Squared Error).",
    "aicc": "Tiêu chuẩn thông tin Akaike hiệu chỉnh cho cỡ mẫu nhỏ; dùng so sánh độ tối ưu giữa các mô hình PK.",
    "bic": "Tiêu chuẩn thông tin Bayesian (Schwarz criterion) phạt mạnh số lượng tham số trong mô hình PK.",
    "jacobian_condition": "Chỉ số điều kiện ma trận Jacobian đánh giá độ ổn định số và mức độ đa cộng tuyến.",
    "điều kiện jacobian": "Chỉ số điều kiện ma trận Jacobian đánh giá độ ổn định số và mức độ đa cộng tuyến.",

    # Planning & Randomization
    "cv_auc": "Hệ số biến thiên trong cá thể (intra-subject CV) giả định của AUC từ y văn.",
    "cv_cmax": "Hệ số biến thiên trong cá thể (intra-subject CV) giả định của Cmax từ y văn.",
    "target_power": "Lực kiểm định thống kê mong muốn (thường chọn 80% hoặc 90% theo quy chuẩn quốc tế).",
    "dropout_rate": "Tỷ lệ dự kiến đối tượng bỏ cuộc hoặc loại khỏi nghiên cứu để bù trừ vào số tuyển sinh.",
    "sample_size": "Tổng số người tình nguyện cần phân bổ đều vào các trình tự điều trị (Sequence).",
    "seed": "Giá trị khởi tạo bộ sinh số giả ngẫu nhiên; bắt buộc ghi nhận để tái lập danh sách phân nhóm.",
    "block_size": "Quy mô khối hoán vị (Block Size) đảm bảo cân bằng tỷ lệ đối tượng giữa các nhánh thử nghiệm.",

    # Non-parametric Tmax
    "trung vị (giờ)": "Giá trị trung vị (Median) của thời điểm Tmax (giờ) kèm khoảng tứ phân vị hoặc cực trị.",
    "nhỏ nhất (giờ)": "Giá trị Tmax cực tiểu quan sát được trong nhóm nghiên cứu.",
    "lớn nhất (giờ)": "Giá trị Tmax cực đại quan sát được trong nhóm nghiên cứu.",
    "p hai phía": "Giá trị p của kiểm định Wilcoxon signed-rank (2×2) hoặc Mann-Whitney U (Parallel); tham khảo hỗ trợ.",
    "n cặp": "Số cặp đối tượng ghép đôi hoàn tất cả hai kỳ điều trị đưa vào so sánh Tmax.",
    "trung vị (t−r)": "Trung vị độ chênh lệch Tmax giữa Test và Reference theo ước lượng Hodges-Lehmann.",
    "nhóm": "Nhóm thuốc nghiên cứu: Thuốc thử (T) hoặc Thuốc đối chứng (R).",

    # Sample size planning & Randomization
    "evaluable": "Số đối tượng cần hoàn tất phân tích để đạt lực kiểm định (Power) mục tiêu.",
    "recruit": "Tổng số đối tượng cần tuyển sinh ban đầu sau khi đã bù tỷ lệ bỏ cuộc (dropout).",
    "per_group": "Số đối tượng phân tích tối thiểu trên mỗi trình tự (2×2) hoặc mỗi nhánh (Parallel).",
    "achieved_power": "Lực kiểm định TOST thực tế đạt được tại cỡ mẫu đã làm tròn theo số nhánh.",
    "dropout": "Tỷ lệ bỏ cuộc giả định dùng quy đổi từ N đánh giá sang N cần tuyển sinh.",
    "cv_type": "Loại biến thiên đầu vào: CVw nội cá thể (2×2) hoặc CV tổng giữa cá thể (Parallel).",
    "lower": "Giới hạn tương đương sinh học dưới dùng để tính power/cỡ mẫu (thường 0,80 hoặc 0,90).",
    "upper": "Giới hạn tương đương sinh học trên dùng để tính power/cỡ mẫu (thường 1,25 hoặc 1,1111).",

    # Standalone PK (NCA_VI_COLUMNS & Compartmental Modeling tables)
    "hồ sơ": "Mã định danh đường cong nồng độ–thời gian của từng cá thể hoặc hồ sơ PK.",
    "mã hồ sơ": "Mã định danh đường cong nồng độ–thời gian của từng cá thể hoặc hồ sơ PK.",
    "đường dùng": "Đường đưa thuốc đã chọn cho phân tích (Uống, Tiêm IV nhanh, Truyền IV).",
    "số mẫu": "Tổng số mẫu nồng độ định lượng hợp lệ đưa vào tính NCA hoặc khớp mô hình.",
    "thời điểm đầu": "Thời điểm lấy mẫu đầu tiên sau liều được ghi nhận trong hồ sơ nồng độ.",
    "auc đầu–cuối": "Diện tích dưới đường cong tính từ thời điểm quan sát đầu tiên đến Tlast.",
    "aumc đầu–cuối": "Diện tích mô men bậc một tính từ thời điểm quan sát đầu tiên đến Tlast.",
    "auc0–last": "Diện tích dưới đường cong nồng độ–thời gian từ t = 0 đến thời điểm Tlast.",
    "aumc0–last": "Diện tích mô men bậc một tích số (t × C) từ t = 0 đến Tlast.",
    "c0 ngoại suy": "Nồng độ ước tính tại t = 0 cho đường IV bolus bằng hồi quy log-tuyến tính các điểm sớm.",
    "lambda-z": "Hằng số tốc độ thải trừ pha cuối (λz, 1/giờ) ước tính bằng hồi quy log-tuyến tính.",
    "t½": "Thời gian bán thải pha đào thải cuối: t½ = ln(2)/λz.",
    "auc0–∞": "Diện tích dưới đường cong ngoại suy tới vô cùng: AUClast + Clast/λz.",
    "auc0-∞": "Diện tích dưới đường cong ngoại suy tới vô cùng: AUClast + Clast/λz.",
    "auc ngoại suy": "Tỷ lệ phần trăm diện tích ngoại suy ngoài Tlast: (AUC∞ − AUClast)/AUC∞ × 100%.",
    "aumc0–∞": "Diện tích mô men bậc một ngoại suy đến vô cùng (từ t = 0 đến ∞).",
    "mrt quan sát": "Thời gian lưu trung bình (Mean Residence Time) ngoại suy tới vô cùng trước khi trừ Tinf/2.",
    "mrt iv hiệu chỉnh": "MRT thực của truyền tĩnh mạch sau khi hiệu chỉnh thời gian truyền: MRT_inf − Tinf/2.",
    "cl": "Độ thanh thải toàn thân (Clearance = Dose / AUC0–∞) khi biết F = 1 (đường tiêm/truyền TM).",
    "cl/f": "Độ thanh thải biểu kiến qua đường uống (Dose / AUC0–∞); phụ thuộc sinh khả dụng F.",
    "vz": "Thể tích phân bố ở pha đào thải cuối khi F = 1: Vz = Dose / (λz × AUC0–∞).",
    "vz/f": "Thể tích phân bố biểu kiến qua đường uống (Vz/F = Dose / [λz × AUC0–∞]).",
    "vss": "Thể tích phân bố ở trạng thái ổn định: IV bolus = CL × MRT; 2/3 ngăn = Vc + các Vp.",
    "r² hiệu chỉnh pha cuối": "Hệ số xác định hiệu chỉnh Adjusted R² đánh giá độ tuyến tính của pha thải trừ λz.",
    "điểm pha cuối": "Danh sách các thời điểm nồng độ được chọn để hồi quy ước tính λz.",
    "chế độ liều": "Phác đồ đưa thuốc đã khai báo: Đơn liều, Đa liều hoặc Trạng thái ổn định.",
    "khoảng liều τ": "Khoảng thời gian cố định giữa hai lần dùng thuốc liên tiếp (giờ).",
    "thời điểm liều cuối": "Mốc thời gian bắt đầu liều cuối cùng trên thang thời gian tổng.",
    "đã xác nhận trạng thái ổn định": "Xác nhận của người dùng về bằng chứng đạt steady-state trước khi tính CLss.",
    "cmax,τ": "Nồng độ đỉnh quan sát được trong khoảng liều cuối [0, τ].",
    "tmax,τ": "Thời điểm đạt nồng độ đỉnh tính từ khi dùng liều cuối cùng trong khoảng [0, τ].",
    "cmin,τ quan sát": "Nồng độ cực tiểu quan sát được trong khoảng liều [0, τ].",
    "ctrough tại τ": "Nồng độ đáy ngay trước liều tiếp theo ở cuối khoảng liều (t = τ).",
    "aucτ": "Diện tích dưới đường cong trong một khoảng liều [0, τ] ở phác đồ đa liều/steady-state.",
    "cavg,τ": "Nồng độ trung bình trong khoảng liều: Cavg,τ = AUCτ / τ.",
    "dao động đỉnh–đáy": "Biên độ dao động đỉnh–đáy chuẩn hóa (PTF% = (Cmax,τ − Cmin,τ)/Cavg,τ × 100%).",
    "clss": "Độ thanh thải ở trạng thái ổn định (Dose / AUCτ,ss) đối với đường IV (F = 1).",
    "cl/fss": "Độ thanh thải biểu kiến ở trạng thái ổn định qua đường uống (Dose / AUCτ,ss).",
    "tỷ số tích lũy aucτ cuối/đầu": "Tỷ số tích lũy thuốc giữa chu kỳ cuối và liều đầu (Rac = AUCτ,cuối / AUCτ,đầu).",
    "cảnh báo": "Các cảnh báo chuyên môn NCA hoặc mô hình (ví dụ: ngoại suy > 20%, chạm biên, flip-flop).",
    "số ngăn": "Số ngăn dược động học của mô hình đang khớp (1, 2 hoặc 3 ngăn).",
    "trọng số": "Hàm trọng số sai số áp dụng khi tối ưu hóa phi tuyến (Không trọng số, 1/C hoặc 1/C²).",
    "r²": "Hệ số xác định đánh giá mức độ giải thích phương sai của mô hình hoặc hồi quy.",
    "r² hiệu chỉnh": "Hệ số xác định hiệu chỉnh (Adjusted R²) theo bậc tự do để hạn chế thiên lệch thêm biến.",
    "cmax quan sát": "Nồng độ đỉnh đo được thực nghiệm trực tiếp từ bảng dữ liệu.",
    "cmax dự đoán": "Nồng độ đỉnh suy ra từ đường cong mô hình ngăn đã khớp.",
    "vc": "Thể tích phân bố ngăn trung tâm (L) trong mô hình IV 1, 2 hoặc 3 ngăn.",
    "q": "Độ thanh thải liên ngăn giữa ngăn trung tâm và ngăn ngoại vi (L/h).",
    "vp": "Thể tích phân bố ngăn ngoại vi (L) trong mô hình 2 ngăn.",
    "q2": "Độ thanh thải liên ngăn giữa ngăn trung tâm và ngăn ngoại vi nông V2 (L/h).",
    "vp2": "Thể tích phân bố ngăn ngoại vi nông V2 (L) trong mô hình 3 ngăn.",
    "q3": "Độ thanh thải liên ngăn giữa ngăn trung tâm và ngăn ngoại vi sâu V3 (L/h).",
    "vp3": "Thể tích phân bố ngăn ngoại vi sâu V3 (L) trong mô hình 3 ngăn.",
    "v/f": "Thể tích phân bố biểu kiến ngăn trung tâm đường uống (chưa biết sinh khả dụng F).",
    "q/f": "Độ thanh thải liên ngăn biểu kiến đường uống giữa V/F và Vp/F.",
    "vp/f": "Thể tích phân bố biểu kiến ngăn ngoại vi đường uống (mô hình 2 ngăn).",
    "q2/f": "Độ thanh thải liên ngăn biểu kiến đường uống tới ngăn nông Vp2/F.",
    "vp2/f": "Thể tích phân bố biểu kiến ngăn ngoại vi nông đường uống (mô hình 3 ngăn).",
    "q3/f": "Độ thanh thải liên ngăn biểu kiến đường uống tới ngăn sâu Vp3/F.",
    "vp3/f": "Thể tích phân bố biểu kiến ngăn ngoại vi sâu đường uống (mô hình 3 ngăn).",
    "ka": "Hằng số tốc độ hấp thu bậc 1 từ ống tiêu hóa vào ngăn trung tâm (1/h).",
    "k10": "Hằng số tốc độ thải trừ bậc 1 trực tiếp khỏi ngăn trung tâm (k10 = CL/Vc, 1/h).",
    "beta": "Hằng số tốc độ vĩ mô pha β (1/h; pha cuối ở mô hình 2 ngăn hoặc pha trung gian ở 3 ngăn).",
    "gamma": "Hằng số tốc độ vĩ mô pha thải trừ sâu γ (1/h) trong mô hình 3 ngăn.",
    "t1/2_alpha": "Thời gian bán thải pha phân bố nhanh (t½,α = ln(2)/α).",
    "t1/2_beta": "Thời gian bán thải pha β (t½,β = ln(2)/β).",
    "t1/2_gamma": "Thời gian bán thải pha thải trừ sâu γ (t½,γ = ln(2)/γ).",
}


def get_field_description(name: object) -> str | None:
    """Return a concise explanation for a form input or table column name."""
    if name is None:
        return None
    raw_key = str(name).strip().casefold()
    if not raw_key:
        return None
    if raw_key in EXPLICIT_TERMS:
        return EXPLICIT_TERMS[raw_key]

    stripped = re.sub(r"\(.*?\)", "", raw_key).strip()
    if stripped in EXPLICIT_TERMS:
        return EXPLICIT_TERMS[stripped]

    underscored = raw_key.replace(" ", "_")
    if underscored in EXPLICIT_TERMS:
        return EXPLICIT_TERMS[underscored]
    spaced = raw_key.replace("_", " ")
    if spaced in EXPLICIT_TERMS:
        return EXPLICIT_TERMS[spaced]

    for groups in (*PAGE_HELP, *INDEPENDENT_HELP.values()):
        for group in groups:
            for label, meaning in group.entries:
                parts = [p.strip().casefold() for p in label.split("/")]
                if raw_key in parts or stripped in parts:
                    return meaning
                for part in parts:
                    if part.replace(" ", "_") == underscored or part.replace("_", " ") == spaced:
                        return meaning
    return None


def table_column_config(columns: Iterable[object], existing: dict | None = None) -> dict:
    """Build column_config with hover tooltips for all recognized table columns."""
    config = dict(existing or {})
    if not hasattr(st, "column_config"):
        return config
    for col in columns:
        col_str = str(col)
        if col_str in config:
            continue
        desc = get_field_description(col_str)
        if desc:
            config[col_str] = st.column_config.Column(col_str, help=desc)
    return config


def render_table_legend(
    columns: Iterable[object],
    *,
    title: str = "ℹ️ Chú thích tiêu đề cột & thuật ngữ bảng này",
    expanded: bool = False,
) -> None:
    """Render an in-table collapsible legend with explanations for present columns."""
    if not hasattr(st, "expander"):
        return
    items: list[tuple[str, str]] = []
    seen: set[str] = set()
    for col in columns:
        col_str = str(col).strip()
        if not col_str or col_str in seen:
            continue
        seen.add(col_str)
        desc = get_field_description(col_str)
        if desc:
            items.append((col_str, desc))
    if not items:
        return

    with st.expander(title, expanded=expanded):
        st.caption("Giải thích ngắn gọn ý nghĩa các chỉ tiêu và tiêu đề cột trong bảng:")
        if len(items) >= 4 and hasattr(st, "columns"):
            half = (len(items) + 1) // 2
            col1, col2 = st.columns(2)
            with col1:
                for name, mean in items[:half]:
                    st.markdown(f"- **`{name}`**: {mean}")
            with col2:
                for name, mean in items[half:]:
                    st.markdown(f"- **`{name}`**: {mean}")
        else:
            for name, mean in items:
                st.markdown(f"- **`{name}`**: {mean}")
