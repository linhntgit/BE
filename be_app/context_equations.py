"""Mathematical models, equations, and comprehensive variable explanations for BE and PK.

Provides peer-reviewed, pedagogically structured formulas adhering to ICH M13A,
EMA, FDA, WHO, and pharmacometrics textbooks (Rowland & Tozer, Gibaldi & Perrier).
"""

from __future__ import annotations

# =============================================================================
# MODULE 0: TẠO NGHIÊN CỨU & THÔNG TIN BAN ĐẦU
# =============================================================================
EQUATIONS_0: tuple[tuple[str, str], ...] = (
    (
        r"\Delta_{\text{Assay}} = \left| \frac{\text{Assay}_T - \text{Assay}_R}{\text{Assay}_R} \right| \times 100\% \le 5.0\%",
        (
            "**Độ chênh lệch hàm lượng giữa lô thuốc Thử và Đối chứng:**\n"
            "- $\\Delta_{\\text{Assay}}$: Phần trăm chênh lệch hàm lượng hoạt chất giữa hai lô thuốc nghiên cứu (%).\n"
            "- $\\text{Assay}_T$: Hàm lượng hoạt chất thực tế định lượng được trong lô thuốc Thử (% so với nhãn).\n"
            "- $\\text{Assay}_R$: Hàm lượng hoạt chất thực tế định lượng được trong lô thuốc Đối chứng (% so với nhãn).\n"
            "- Ngưỡng $5.0\\%$: Tiêu chuẩn khống chế bắt buộc theo ICH M13A (Mục 2.1.2) và EMA (Mục 4.1.2). Nếu sai khác vượt quá $5.0\\%$, nghiên cứu không đủ điều kiện chứng minh TĐSH nếu không có phê duyệt trước từ cơ quan quản lý. Tuyệt đối không tự ý hiệu chỉnh kết quả BE theo hàm lượng (potency adjustment)."
        ),
    ),
    (
        r"F_{\text{rel}} = \frac{AUC_T / \text{Dose}_T}{AUC_R / \text{Dose}_R} \times 100\%",
        (
            "**Sinh khả dụng tương đối (Relative Bioavailability):**\n"
            "- $F_{\\text{rel}}$: Sinh khả dụng tương đối của thuốc Thử so với thuốc Đối chứng (%).\n"
            "- $AUC_T, AUC_R$: Diện tích dưới đường cong nồng độ–thời gian của thuốc Thử và Đối chứng ($\\text{mg}\\cdot\\text{h}/\\text{L}$ hoặc $\\text{ng}\\cdot\\text{h}/\\text{mL}$).\n"
            "- $\\text{Dose}_T, \\text{Dose}_R$: Mức liều thực tế đưa vào cơ thể đối tượng ($\\text{mg}$). Trong nghiên cứu TĐSH chuẩn, hai mức liều này luôn được thiết kế bằng nhau."
        ),
    ),
)

# =============================================================================
# MODULE 1: THIẾT KẾ NGHIÊN CỨU & CỠ MẪU
# =============================================================================
EQUATIONS_1: tuple[tuple[str, str], ...] = (
    (
        r"\sigma_W^2 = \ln(CV_W^2 + 1) \quad \Longleftrightarrow \quad CV_W = \sqrt{e^{\sigma_W^2} - 1}",
        (
            "**Mối quan hệ giữa Hệ số biến thiên và Phương sai sai số phần dư trên thang logarit:**\n"
            "- $CV_W$: Hệ số biến thiên nội cá thể (Intra-subject coefficient of variation) của chỉ tiêu PK ($C_{\\max}$ hoặc $AUC$) trên thang gốc (dạng thập phân, ví dụ $0.20$ cho $20\\%$).\n"
            "- $\\sigma_W^2$ (hoặc $s_W^2, \\text{MSE}$): Phương sai sai số phần dư nội cá thể thu được từ phân tích phương sai ANOVA trên thang đo logarit tự nhiên ($\\ln$)."
        ),
    ),
    (
        r"T_L = \frac{(\bar{Y}_T - \bar{Y}_R) - \ln(0.80)}{s_W \sqrt{\frac{1}{2n_1} + \frac{1}{2n_2}}} \ge t_{1-\alpha, \, \nu}, \qquad T_U = \frac{\ln(1.25) - (\bar{Y}_T - \bar{Y}_R)}{s_W \sqrt{\frac{1}{2n_1} + \frac{1}{2n_2}}} \ge t_{1-\alpha, \, \nu}",
        (
            "**Thủ tục kiểm định hai phía một lần đồng thời TOST (Schuirmann):**\n"
            "- $T_L, T_U$: Thống kê kiểm định $t$ của hai giả thuyết một phía (Lower và Upper) trong thủ tục TOST Schuirmann.\n"
            "- $\\bar{Y}_T, \\bar{Y}_R$: Trung bình bình phương tối thiểu (LSMeans) trên thang $\\ln$ của thuốc Thử và Đối chứng. Hiệu số $(\\bar{Y}_T - \\bar{Y}_R)$ là ước tính điểm của hiệu ứng điều trị.\n"
            "- $\\ln(0.80) \\approx -0.2231, \\ln(1.25) \\approx +0.2231$: Giới hạn tương đương sinh học quy ước theo chuẩn ICH M13A trên thang $\\ln$.\n"
            "- $s_W$: Căn bậc hai của $\\text{MSE}$ (Residual standard deviation) từ bảng ANOVA.\n"
            "- $n_1, n_2$: Số lượng đối tượng hoàn thành nghiên cứu trong chuỗi 1 ($TR$) và chuỗi 2 ($RT$). Với thiết kế cân bằng, $n_1 = n_2 = N/2$.\n"
            "- $\\alpha$: Mức ý nghĩa thống kê cho từng kiểm định một phía ($\\alpha = 0.05$, tương đương khoảng tin cậy hai phía $90\\% = 1 - 2\\alpha$).\n"
            "- $\\nu$: Bậc tự do phần dư nội cá thể ($\\nu = n_1 + n_2 - 2 = N - 2$ trong thiết kế $2\\times 2$ chuẩn).\n"
            "- $t_{1-\\alpha, \\, \\nu}$: Phân vị Student tại mức tin cậy $1-\\alpha$ với $\\nu$ bậc tự do."
        ),
    ),
    (
        r"N \ge \frac{2 \cdot \sigma_W^2 \cdot (t_{1-\alpha, \, \nu} + t_{1-\beta, \, \nu})^2}{(\ln(\theta_0) - \ln(\theta_{\text{limit}}))^2}, \qquad N_{\text{recruited}} = \left\lceil \frac{N}{1 - d} \right\rceil",
        (
            "**Công thức ước lượng cỡ mẫu giải tích (Diletti et al.) và hiệu chỉnh bỏ cuộc:**\n"
            "- $N$: Cỡ mẫu tối thiểu cần hoàn thành hợp lệ (evaluable sample size).\n"
            "- $\\sigma_W^2$: Phương sai sai số nội cá thể trên thang $\\ln$ ($\\sigma_W^2 = \\ln(CV_W^2 + 1)$).\n"
            "- $1-\\beta$: Lực của thử nghiệm (Statistical power, thông thường đặt $80\\%$ hoặc $90\\%$).\n"
            "- $t_{1-\\beta, \\, \\nu}$: Phân vị Student tương ứng với lực thống kê $1-\\beta$.\n"
            "- $\\theta_0$: Tỷ số trung bình kỳ vọng giữa hai thuốc (Expected Geometric Mean Ratio, thường giả định $0.95$ hoặc $1.05$ trong hoạch định an toàn).\n"
            "- $\\theta_{\\text{limit}}$: Giới hạn biên TĐSH gần nhất ($0.80$ nếu $\\theta_0 < 1.00$, hoặc $1.25$ nếu $\\theta_0 > 1.00$).\n"
            "- $d$: Tỷ lệ đối tượng dự kiến bỏ cuộc hoặc vi phạm đề cương (Dropout rate, thường ước tính từ $10\\%$ đến $20\\%$).\n"
            "- $N_{\\text{recruited}}$: Cỡ mẫu thực tế cần tuyển chọn ban đầu để bù trừ hao hụt."
        ),
    ),
)

# =============================================================================
# MODULE 2: LỊCH LẤY MẪU & RỬA GIẢI
# =============================================================================
EQUATIONS_2: tuple[tuple[str, str], ...] = (
    (
        r"T_{\text{washout}} \ge 5 \times t_{1/2} = 5 \times \frac{\ln(2)}{\lambda_z}",
        (
            "**Thời gian rửa giải tối thiểu (Washout Period):**\n"
            "- $T_{\\text{washout}}$: Khoảng cách thời gian nghỉ giữa hai lần dùng thuốc liên tiếp giữa các kỳ (giờ hoặc ngày).\n"
            "- $t_{1/2}$: Thời gian bán thải sinh học ở pha thải trừ cuối cùng của hoạt chất ($t_{1/2} = \\ln(2)/\\lambda_z$, đơn vị giờ).\n"
            "- $\\lambda_z$: Hằng số tốc độ thải trừ pha cuối ($\\text{h}^{-1}$).\n"
            "- Hệ số 5: Tương ứng với việc $> 96.875\\%$ lượng thuốc của kỳ trước đã được đào thải hoàn toàn khỏi cơ thể ($1 - (1/2)^5 = 96.875\\%$), ngăn ngừa hiện tượng tồn lưu (Carry-over effect)."
        ),
    ),
    (
        r"AUC_{\%\text{extrap}} = \frac{AUC_{0-\infty} - AUC_{0-t}}{AUC_{0-\infty}} \times 100\% = \frac{C_{\text{last}} / \lambda_z}{AUC_{0-t} + C_{\text{last}} / \lambda_z} \times 100\% \le 20.0\%",
        (
            "**Tỷ lệ phần trăm diện tích ngoại suy đến vô cùng:**\n"
            "- $AUC_{\\%\\text{extrap}}$: Tỷ lệ phần trăm diện tích dưới đường cong ngoại suy từ thời điểm định lượng cuối cùng $t_{\\text{last}}$ đến vô cùng so với $AUC_{0-\\infty}$ (%).\n"
            "- $AUC_{0-t}$: Diện tích dưới đường cong nồng độ–thời gian từ thời điểm $0$ đến $t_{\\text{last}}$ tính bằng tích phân hình thang ($\\text{ng}\\cdot\\text{h}/\\text{mL}$).\n"
            "- $AUC_{0-\\infty}$: Diện tích dưới đường cong toàn phần ngoại suy đến vô cùng ($\\text{ng}\\cdot\\text{h}/\\text{mL}$).\n"
            "- $C_{\\text{last}}$: Nồng độ định lượng được cuối cùng lớn hơn hoặc bằng LLOQ ($\\text{ng}/\\text{mL}$).\n"
            "- $\\lambda_z$: Hằng số tốc độ thải trừ pha cuối ($\\text{h}^{-1}$).\n"
            "- Ngưỡng $20.0\\%$: Tiêu chuẩn khống chế bắt buộc theo ICH M13A (Mục 2.2.3) và EMA (Mục 4.1.4). Nếu $AUC_{\\%\\text{extrap}} > 20\\%$ ở quá $20\\%$ số hồ sơ, lịch lấy mẫu bị coi là chưa đủ dài để phản ánh toàn diện phơi nhiễm thuốc."
        ),
    ),
)

# =============================================================================
# MODULE 3: NHẬP DỮ LIỆU & KIỂM TRA CHẤT LƯỢNG (QC)
# =============================================================================
EQUATIONS_3: tuple[tuple[str, str], ...] = (
    (
        r"\mathcal{H} = \text{SHA-256}(\text{canonical\_bytes}(\text{Raw Concentration Table}))",
        (
            "**Mã băm toàn vẹn SHA-256 của tập dữ liệu thô:**\n"
            "- $\\mathcal{H}$: Chuỗi băm mật mã học 64 ký tự thập lục phân (hexadecimal string) đại diện duy nhất cho tập dữ liệu thô.\n"
            "- $\\text{canonical\\_bytes}(\\cdot)$: Chuỗi byte chuẩn hóa không phụ thuộc nền tảng hệ điều hành, bảo toàn thứ tự dòng, cột và định dạng số.\n"
            "- Ý nghĩa: Theo ICH E6(R3) và FDA Data Integrity Guidance, bất kỳ thay đổi nào dù chỉ 1 ký tự hay dấu chấm phẩy trong dữ liệu thô đều làm thay đổi hoàn toàn mã $\\mathcal{H}$, phát hiện ngay lập tức hành vi sửa chữa dữ liệu trái phép."
        ),
    ),
    (
        r"\text{Error}_{\text{nominal}} = \frac{C_1 + C_2}{2} \cdot (t_{2,\text{nominal}} - t_{1,\text{nominal}}) - \frac{C_1 + C_2}{2} \cdot (t_{2,\text{actual}} - t_{1,\text{actual}}) = \frac{C_1 + C_2}{2} \cdot \Delta t",
        (
            "**Sai số tích phân hình thang khi dùng thời gian danh nghĩa:**\n"
            "- $\\text{Error}_{\\text{nominal}}$: Sai số diện tích tích phân hình thang khi tự ý dùng mốc thời gian lý thuyết (nominal time) thay vì thời gian thực tế (actual time).\n"
            "- $C_1, C_2$: Nồng độ thuốc đo được tại hai thời điểm lấy mẫu kế tiếp nhau ($\\text{ng}/\\text{mL}$).\n"
            "- $t_{\\text{nominal}}, t_{\\text{actual}}$: Thời điểm lấy mẫu lý thuyết theo đề cương và thời điểm lấy mẫu thực tế được ghi nhận trên bệnh án nghiên cứu CRF ($\\text{h}$).\n"
            "- $\\Delta t$: Độ sai lệch thời gian lấy mẫu thực tế so với đề cương. Trong pha hấp thu có độ dốc nồng độ rất lớn, sai số thời gian dù chỉ vài phút cũng gây sai lệch nghiêm trọng lên trị số $C_{\\max}$ và $AUC_{0-t}$."
        ),
    ),
)

# =============================================================================
# MODULE 4: KHÓA DỮ LIỆU & XỬ LÝ LOẠI TRỪ
# =============================================================================
EQUATIONS_4: tuple[tuple[str, str], ...] = (
    (
        r"\text{Ratio}_{\text{predose}} = \frac{C_{\text{predose}}}{C_{\max}} \times 100\% \le 5.0\%",
        (
            "**Tiêu chuẩn chấp nhận nồng độ trước liều (Pre-dose acceptance criterion):**\n"
            "- $\\text{Ratio}_{\\text{predose}}$: Tỷ lệ nồng độ thuốc trước khi uống liều kỳ 2 so với nồng độ đỉnh của chính cá thể đó ở kỳ 2 (%).\n"
            "- $C_{\\text{predose}}$: Nồng độ thuốc định lượng được tại thời điểm $0$ giờ (ngay trước khi uống thuốc) của giai đoạn 2 ($\\text{ng}/\\text{mL}$).\n"
            "- $C_{\\max}$: Nồng độ đỉnh đo được của cá thể đó trong giai đoạn nghiên cứu tương ứng ($\\text{ng}/\\text{mL}$).\n"
            "- Quy tắc xử lý theo ICH M13A (Mục 2.2.4): Nếu $C_{\\text{predose}} \\le 5\\% \\, C_{\\max}$, đối tượng được giữ nguyên trong tập dữ liệu phân tích thống kê mà không cần hiệu chỉnh. Nếu $C_{\\text{predose}} > 5\\% \\, C_{\\max}$, đối tượng bị loại khỏi toàn bộ phân tích TĐSH do hiện tượng tồn lưu (Carry-over) làm sai lệch kết quả sinh khả dụng."
        ),
    ),
)

# =============================================================================
# MODULE 5: PHÂN TÍCH DƯỢC ĐỘNG HỌC NCA
# =============================================================================
EQUATIONS_5: tuple[tuple[str, str], ...] = (
    (
        r"\Delta AUC_i = \begin{cases} \frac{C_i + C_{i+1}}{2} \cdot (t_{i+1} - t_i) & \text{khi } C_{i+1} \ge C_i \text{ (Linear Up)} \\[6pt] \frac{C_i - C_{i+1}}{\ln(C_i / C_{i+1})} \cdot (t_{i+1} - t_i) & \text{khi } C_{i+1} < C_i \text{ (Log Down)} \end{cases}",
        (
            "**Phương pháp tích phân hình thang hỗn hợp Linear Up / Log Down:**\n"
            "- $\\Delta AUC_i$: Diện tích dưới đường cong giữa hai thời điểm lấy mẫu liên tiếp $t_i$ và $t_{i+1}$ ($\\text{ng}\\cdot\\text{h}/\\text{mL}$).\n"
            "- $C_i, C_{i+1}$: Nồng độ thuốc đo được tại thời điểm $t_i$ và $t_{i+1}$ ($\\text{ng}/\\text{mL}$).\n"
            "- $t_i, t_{i+1}$: Thời điểm lấy mẫu thực tế liên tiếp ($\\text{h}$).\n"
            "- Ý nghĩa: Áp dụng hình thang tuyến tính trong pha nồng độ tăng (Linear Up) và hình thang logarit trong pha nồng độ giảm hàm số mũ (Log Down) để tránh hiện tượng ước tính vượt mức (over-estimation) của phương pháp tuyến tính thuần túy."
        ),
    ),
    (
        r"AUC_{0-\infty} = AUC_{0-t} + \frac{C_{\text{last}}}{\lambda_z}, \qquad t_{1/2} = \frac{\ln(2)}{\lambda_z}, \qquad MRT = \frac{AUMC_{0-\infty}}{AUC_{0-\infty}}",
        (
            "**Thông số phơi nhiễm toàn phần và thời gian lưu trú trung bình:**\n"
            "- $AUC_{0-\\infty}$: Diện tích dưới đường cong toàn phần ngoại suy đến vô cùng ($\\text{ng}\\cdot\\text{h}/\\text{mL}$).\n"
            "- $AUC_{0-t}$: Diện tích dưới đường cong từ thời điểm 0 đến thời điểm đo cuối cùng $t_{\\text{last}}$ ($\\text{ng}\\cdot\\text{h}/\\text{mL}$).\n"
            "- $C_{\\text{last}}$: Nồng độ thuốc định lượng được tại thời điểm lấy mẫu cuối cùng $t_{\\text{last}}$ ($\\text{ng}/\\text{mL}$).\n"
            "- $\\lambda_z$: Hằng số tốc độ đào thải pha cuối ($\\text{h}^{-1}$), được ước lượng bằng hồi quy tuyến tính OLS của $\\ln(C)$ theo thời gian $t$.\n"
            "- $t_{1/2}$: Thời gian bán thải biểu kiến ở pha cuối ($\\text{h}$).\n"
            "- $AUMC_{0-\\infty}$: Diện tích dưới đường cong tích số mô-men bậc 1 ($t \\cdot C(t)$) ngoại suy đến vô cùng ($\\text{ng}\\cdot\\text{h}^2/\\text{mL}$).\n"
            "- $MRT$: Thời gian lưu trú trung bình của phân tử thuốc trong cơ thể (Mean Residence Time, đơn vị $\\text{h}$)."
        ),
    ),
)

# =============================================================================
# MODULE 6: ĐÁNH GIÁ TƯƠNG ĐƯƠNG SINH HỌC
# =============================================================================
EQUATIONS_6: tuple[tuple[str, str], ...] = (
    (
        r"\text{GMR} = \exp(\bar{Y}_T - \bar{Y}_R) \times 100\%, \qquad 90\% \text{ CI} = \exp\left( (\bar{Y}_T - \bar{Y}_R) \pm t_{0.05, \, \nu} \cdot s_W \sqrt{\frac{1}{2n_1} + \frac{1}{2n_2}} \right) \times 100\%",
        (
            "**Đánh giá TĐSH Trung bình ABE (Average Bioequivalence):**\n"
            "- $\\text{GMR}$: Tỷ số trung bình hình học (Geometric Mean Ratio) của chỉ tiêu phơi nhiễm giữa thuốc Thử và Đối chứng (%).\n"
            "- $90\\% \\text{ CI}$: Khoảng tin cậy 90% của tỷ số trung bình hình học (tương đương với hai kiểm định một phía $\\alpha = 0.05$).\n"
            "- $\\bar{Y}_T, \\bar{Y}_R$: Trung bình bình phương tối thiểu (LSMeans) trên thang đo $\\ln$ của thuốc Thử và thuốc Đối chứng từ mô hình ANOVA.\n"
            "- $s_W$: Căn bậc hai của phương sai phần dư nội cá thể ($\\sqrt{\\text{MSE}}$) từ mô hình ANOVA.\n"
            "- $n_1, n_2$: Số lượng đối tượng hoàn thành nghiên cứu trong hai chuỗi điều trị $TR$ và $RT$.\n"
            "- $\\nu$: Bậc tự do của sai số phần dư ANOVA ($\\nu = N - 2$ trong thiết kế chéo đôi $2\\times 2$).\n"
            "- $t_{0.05, \\, \\nu}$: Phân vị Student hai phía ở mức ý nghĩa $10\\%$ (mỗi phía $5\\%$) với $\\nu$ bậc tự do.\n"
            "- Tiêu chuẩn chấp nhận TĐSH ABE: Khoảng tin cậy $90\\%$ phải nằm hoàn toàn trong giới hạn quy ước $[80.00\\% - 125.00\\%]$."
        ),
    ),
    (
        r"[L, U] = \exp\left( \pm k \cdot s_{wR} \right) \times 100\%, \qquad \text{với } k = \frac{\ln(1.25)}{\sigma_{w0}} = \frac{0.22314}{0.25} \approx 0.760",
        (
            "**Tiêu chuẩn EMA ABEL cho thuốc biến thiên cao (HVDP):**\n"
            "- $[L, U]$: Giới hạn mở rộng tương đương sinh học cho thuốc biến thiên cao (HVDP) theo tiêu chuẩn EMA.\n"
            "- $s_{wR}$: Độ lệch chuẩn nội cá thể trên thang $\\ln$ của thuốc Đối chứng trong thiết kế lặp (replicate design), xác định qua $s_{wR} = \\sqrt{\\ln(CV_{wR}^2 + 1)}$.\n"
            "- $CV_{wR}$: Hệ số biến thiên nội cá thể của thuốc Đối chứng. Khi $CV_{wR} > 30\\%$, khoảng BE được mở rộng theo công thức; độ mở rộng tối đa đạt trần tại $CV_{wR} = 50\\%$ tương ứng $[69.84\\% - 143.19\\%]$.\n"
            "- $\\sigma_{w0}$: Hằng số phương sai chuẩn tắc ($\\sigma_{w0} = 0.25$, tương ứng với $CV_{w0} \\approx 30\\%$).\n"
            "- $k$: Hệ số điều chỉnh độ dốc mở rộng chuẩn hóa ($k = 0.760$)."
        ),
    ),
    (
        r"(\bar{Y}_T - \bar{Y}_R)^2 - \theta s_{wR}^2 \le 0 \quad \text{với } \theta = \left(\frac{\ln(1.25)}{\sigma_{w0}}\right)^2 \approx 0.7967, \qquad \text{UCB}_{95\%} \le 0",
        (
            "**Tiêu chí US FDA RSABE cho thuốc biến thiên cao:**\n"
            "- $\\text{UCB}_{95\\%}$: Giới hạn trên của khoảng tin cậy 95% (Upper Confidence Bound) tính theo chuẩn hóa tham chiếu tuyến tính Howe.\n"
            "- $\\bar{Y}_T, \\bar{Y}_R$: LSMeans trên thang $\\ln$ của thuốc Thử và Đối chứng.\n"
            "- $s_{wR}$: Độ lệch chuẩn nội cá thể của thuốc Đối chứng.\n"
            "- $\\theta$: Hằng số tiêu chuẩn hóa tương đương sinh học tham chiếu US FDA ($\\theta \\approx 0.7967$).\n"
            "- Tiêu chuẩn US FDA RSABE: Yêu cầu $\\text{UCB}_{95\\%} \\le 0$ đồng thời tỷ số trung bình hình học $\\text{GMR}$ phải nằm trong khoảng $[80.00\\% - 125.00\\%]$."
        ),
    ),
)

# =============================================================================
# MODULE 7: PHÂN TÍCH CHẨN ĐOÁN & NGOẠI LAI
# =============================================================================
EQUATIONS_7: tuple[tuple[str, str], ...] = (
    (
        r"y = \ln(C(t)) = \ln(C_0) - \lambda_z \cdot t, \qquad \frac{d\ln C}{dt} = -\lambda_z",
        (
            "**Phương trình biểu diễn đường cong trên thang bán logarit:**\n"
            "- $C(t)$: Nồng độ thuốc tại thời điểm $t$ ($\\text{ng}/\\text{mL}$ hoặc $\\text{mg}/\\text{L}$).\n"
            "- $C_0$: Nồng độ ngoại suy tại thời điểm $t=0$ của pha thải trừ.\n"
            "- $\\lambda_z$: Hằng số tốc độ đào thải pha cuối ($\\text{h}^{-1}$), tính từ hệ số góc hồi quy tuyến tính: $\\text{slope} = -\\lambda_z$.\n"
            "- $R^2$: Hệ số xác định của đường hồi quy tuyến tính. Tiêu chuẩn quốc tế khuyến cáo $R^2 \\ge 0.85$ để đảm bảo độ tin cậy của việc ước lượng $\\lambda_z$ và ngoại suy $AUC_{0-\\infty}$."
        ),
    ),
    (
        r"r_i = \frac{e_i}{s_W \sqrt{1 - h_{ii}}}",
        (
            "**Phần dư chuẩn hóa Studentized Residuals:**\n"
            "- $r_i$: Phần dư chuẩn hóa nội tại Studentized Residual của quan sát thứ $i$.\n"
            "- $e_i$: Phần dư thô của quan sát thứ $i$ ($e_i = Y_i - \\hat{Y}_i$, với $Y_i$ là giá trị logarit thực tế và $\\hat{Y}_i$ là giá trị dự báo từ mô hình ANOVA).\n"
            "- $s_W$: Căn bậc hai phương sai phần dư của toàn bộ mô hình ANOVA ($\\sqrt{\\text{MSE}}$).\n"
            "- $h_{ii}$: Phần tử đường chéo thứ $i$ của ma trận đòn bẩy Hat Matrix ($H = X(X^TX)^{-1}X^T$), phản ánh mức độ đòn bẩy của quan sát.\n"
            "- Ngưỡng chẩn đoán ngoại lai: Điểm quan sát có $|r_i| > 3.0$ được xếp vào nhóm nghi ngờ ngoại lai. Theo quy định pháp quy, việc phát hiện ngoại lai chỉ phục vụ phân tích chẩn đoán độ nhạy (Sensitivity Analysis), tuyệt đối không được tự ý xóa bỏ điểm dữ liệu để làm đẹp kết quả TĐSH."
        ),
    ),
)

# =============================================================================
# MODULE 8: XUẤT HIỆN VẬT & BÁO CÁO PHÁP QUY
# =============================================================================
EQUATIONS_8: tuple[tuple[str, str], ...] = (
    (
        r"\mathcal{H}_{\text{artifact}} = \text{SHA-256}(\text{Binary Stream of Final File})",
        (
            "**Mã băm chứng thực số học của từng tệp hiện vật kết xuất:**\n"
            "- $\\mathcal{H}_{\\text{artifact}}$: Chuỗi băm mật mã học 64 ký tự hex đại diện cho từng tệp hiện vật kết xuất (Báo cáo Word DOCX, Sổ tính Excel XLSX, Gói lưu trữ ZIP).\n"
            "- Ý nghĩa: Mỗi tệp xuất xưởng đều được sinh mã băm SHA-256 độc lập và đối chiếu trong bảng kê Manifest, đảm bảo tính toàn vẹn dữ liệu bất biến ALCOA+ khi nộp hồ sơ đăng ký thuốc CTD Module 5.3.1.2."
        ),
    ),
)

# =============================================================================
# MODULE 9: RÀ SOÁT KIỂM TOÁN & KHÓA NGHIÊN CỨU
# =============================================================================
EQUATIONS_9: tuple[tuple[str, str], ...] = (
    (
        r"\mathcal{H}_k = \text{SHA-256}(\mathcal{H}_{k-1} \,\|\,\, \text{Timestamp}_k \,\|\,\, \text{Action}_k \,\|\,\, \text{User}_k \,\|\,\, \text{Details}_k)",
        (
            "**Mô hình chuỗi khối kiểm toán liên kết bất biến (Hash-chained Audit Record):**\n"
            "- $\\mathcal{H}_k$: Mã băm SHA-256 của sự kiện kiểm toán thứ $k$.\n"
            "- $\\mathcal{H}_{k-1}$: Mã băm của sự kiện kiểm toán ngay trước đó ($k-1$). Với sự kiện khởi tạo đầu tiên, $\\mathcal{H}_0 = \\text{SHA-256}(\\text{Genesis Block})$.\n"
            "- $\\text{Timestamp}_k$: Dấu thời gian chuẩn UTC của hành động.\n"
            "- $\\text{Action}_k$: Loại hành vi người dùng (tạo mới, nhập dữ liệu, loại trừ, chạy mô hình, ký số).\n"
            "- $\\text{User}_k$: Định danh người thực hiện theo phân quyền RBAC.\n"
            "- $\\text{Details}_k$: Dữ liệu chi tiết về thay đổi tham số hoặc trạng thái nghiên cứu.\n"
            "- $\\|$: Phép toán nối chuỗi byte (byte concatenation).\n"
            "- Ý nghĩa: Cấu trúc nhật ký kiểm toán liên kết chuỗi khối bất biến (Hash-chained Audit Trail) đáp ứng 21 CFR Part 11 và EU GMP Annex 11, ngăn chặn hoàn toàn việc chèn, xóa hoặc sửa đổi lịch sử thao tác hồi cứu."
        ),
    ),
)

# =============================================================================
# MODULE 10: PHÂN TÍCH DƯỢC ĐỘNG HỌC ĐỘC LẬP (PK STANDALONE)
# =============================================================================
EQUATIONS_10: tuple[tuple[str, str], ...] = (
    (
        r"C(t) = C_0 \cdot e^{-k_{10} t} = \frac{D}{V_1} e^{-\frac{CL}{V_1} t}",
        (
            "**Tiêm tĩnh mạch nhanh (IV Bolus) — Mô hình 1 ngăn:**\n"
            "- $C(t)$: Nồng độ thuốc trong huyết tương tại thời điểm $t$ ($\\text{mg/L}$ hoặc $\\mu\\text{g/mL}$).\n"
            "- $C_0$: Nồng độ ban đầu ngoại suy tại $t=0$ ($\\text{mg/L}$, với $C_0 = D / V_1$).\n"
            "- $D$: Liều thuốc tiêm tĩnh mạch trực tiếp ($\\text{mg}$).\n"
            "- $V_1$ (hoặc $V_d$): Thể tích phân bố của ngăn trung tâm (L hoặc $\\text{L/kg}$).\n"
            "- $k_{10}$ (hoặc $k_{el}$): Hằng số tốc độ đào thải bậc 1 từ ngăn trung tâm ($\\text{h}^{-1}$).\n"
            "- $CL$: Độ thanh thải toàn thân của thuốc ($\\text{L/h}$, với $CL = k_{10} \\cdot V_1 = D / AUC_{0-\\infty}$).\n"
            "- $t_{1/2}$: Thời gian bán thải sinh học ($t_{1/2} = \\frac{\\ln 2}{k_{10}} = \\frac{0.693}{k_{10}}$, đơn vị $\\text{h}$).\n"
            "- Hệ vi phân: $dC/dt = -k_{10} C$ với $C(0) = C_0$; diện tích $AUC_{0-\\infty} = C_0 / k_{10} = D / CL$."
        ),
    ),
    (
        r"C(t) = A \cdot e^{-\alpha t} + B \cdot e^{-\beta t}, \qquad C_0 = A + B = \frac{D}{V_1}",
        (
            "**Tiêm tĩnh mạch nhanh (IV Bolus) — Mô hình 2 ngăn (Biexponential):**\n"
            "- $C(t)$: Nồng độ thuốc trong ngăn trung tâm tại thời điểm $t$ ($\\text{mg/L}$).\n"
            "- $A, B$: Các giao điểm vĩ mô (macroconstants) của pha phân bố $\\alpha$ và pha thải trừ $\\beta$ trên trục tung ($\\text{mg/L}$).\n"
            "- $\\alpha, \\beta$: Hằng số tốc độ suy giảm vĩ mô ($\\text{h}^{-1}$, với $\\alpha > \\beta > 0$); $\\alpha$ đại diện pha phân bố, $\\beta$ đại diện pha thải trừ cuối.\n"
            "- $k_{10}, k_{12}, k_{21}$: Hằng số tốc độ vi mô (microconstants, $\\text{h}^{-1}$): $\\alpha + \\beta = k_{10} + k_{12} + k_{21}$ và $\\alpha \\cdot \\beta = k_{10} \\cdot k_{21}$.\n"
            "- $V_1$ ($V_c$): Thể tích ngăn trung tâm ($V_1 = \\frac{D}{A + B} = \\frac{D}{C_0}$, đơn vị L).\n"
            "- $V_2$ ($V_p$): Thể tích ngăn ngoại vi ($V_2 = V_1 \\cdot \\frac{k_{12}}{k_{21}}$, đơn vị L).\n"
            "- $V_{ss}$: Thể tích phân bố tại trạng thái ổn định ($V_{ss} = V_1 + V_2 = V_1 [1 + \\frac{k_{12}}{k_{21}}] = \\frac{D \\cdot AUMC}{AUC^2}$).\n"
            "- $V_\\beta$: Thể tích phân bố theo diện tích ($V_\\beta = \\frac{CL}{\\beta}$, với quy luật thứ bậc $V_c < V_{ss} < V_\\beta$).\n"
            "- $Q$: Độ thanh thải liên ngăn ($Q = k_{12} V_1 = k_{21} V_2$, đơn vị $\\text{L/h}$); độ thanh thải toàn thân $CL = k_{10} V_1$."
        ),
    ),
    (
        r"C(t) = A \cdot e^{-\alpha t} + B \cdot e^{-\beta t} + C \cdot e^{-\gamma t}, \qquad C_0 = A + B + C = \frac{D}{V_1}",
        (
            "**Tiêm tĩnh mạch nhanh (IV Bolus) — Mô hình 3 ngăn (Triexponential):**\n"
            "- $C(t)$: Nồng độ thuốc trong ngăn trung tâm tại thời điểm $t$ ($\\text{mg/L}$).\n"
            "- $A, B, C$: Hệ số vĩ mô của 3 pha động học ($\\text{mg/L}$), tổng $A + B + C = C_0 = D / V_1$.\n"
            "- $\\alpha, \\beta, \\gamma$: Hằng số tốc độ vĩ mô ($\\text{h}^{-1}$, với $\\alpha > \\beta > \\gamma > 0$): $\\alpha$ (phân bố nhanh vào mô giàu mạch), $\\beta$ (phân bố chậm/trung gian), $\\gamma$ (thải trừ cuối từ mô sâu).\n"
            "- $V_1, V_2, V_3$: Thể tích ngăn trung tâm ($V_1$), ngăn ngoại vi nông ($V_2 = V_1 \\frac{k_{12}}{k_{21}}$), và ngăn ngoại vi sâu ($V_3 = V_1 \\frac{k_{13}}{k_{31}}$).\n"
            "- $V_{ss}$: Thể tích trạng thái ổn định ($V_{ss} = V_1 + V_2 + V_3 = V_1 [1 + \\frac{k_{12}}{k_{21}} + \\frac{k_{13}}{k_{31}}]$).\n"
            "- $Q_2, Q_3$: Độ thanh thải liên ngăn giữa ngăn trung tâm với ngăn nông ($Q_2 = k_{12} V_1$) và ngăn sâu ($Q_3 = k_{13} V_1$).\n"
            "- $t_{1/2,\\gamma}$: Thời gian bán thải sinh học thực sự ở pha cuối ($t_{1/2,\\gamma} = \\frac{\\ln 2}{\\gamma}$, đơn vị $\\text{h}$).\n"
            "- Hệ ODE: $dX_1/dt = -(k_{10}+k_{12}+k_{13})X_1 + k_{21}X_2 + k_{31}X_3; \\quad dX_2/dt = k_{12}X_1 - k_{21}X_2; \\quad dX_3/dt = k_{13}X_1 - k_{31}X_3$."
        ),
    ),
    (
        r"C(t) = \begin{cases} \frac{R_0}{CL} \left( 1 - e^{-k_{10} t} \right), & 0 \le t \le T_{\text{inf}} \\[6pt] \frac{R_0}{CL} \left( 1 - e^{-k_{10} T_{\text{inf}}} \right) e^{-k_{10}(t - T_{\text{inf}})}, & t > T_{\text{inf}} \end{cases}",
        (
            "**Truyền tĩnh mạch liên tục (IV Infusion) — Mô hình 1 ngăn:**\n"
            "- $R_0$: Tốc độ truyền tĩnh mạch không đổi bậc 0 ($R_0 = \\frac{D}{T_{\\text{inf}}}$, đơn vị $\\text{mg/h}$).\n"
            "- $T_{\\text{inf}}$: Thời gian truyền tĩnh mạch ($\\text{h}$).\n"
            "- $C_{ss}$: Nồng độ tại trạng thái ổn định nếu truyền liên tục ($C_{ss} = \\frac{R_0}{CL} = \\frac{R_0}{k_{10} V_1}$, đơn vị $\\text{mg/L}$).\n"
            "- Giai đoạn đang truyền ($t \\le T_{\\text{inf}}$): Nồng độ tăng tiệm cận theo quy luật nạp hàm mũ $(1 - e^{-k_{10} t})$.\n"
            "- Giai đoạn sau khi ngừng truyền ($t > T_{\\text{inf}}$): Nồng độ suy giảm hàm mũ từ đỉnh $C(T_{\\text{inf}})$ với hằng số $k_{10}$.\n"
            "- $MRT_{\\text{inf}}$: Thời gian lưu trú trung bình sau truyền ($MRT_{\\text{inf}} = \\frac{1}{k_{10}} + \\frac{T_{\\text{inf}}}{2}$, cần trừ $T_{\\text{inf}}/2$ để quy đổi về $MRT_{\\text{bolus}}$)."
        ),
    ),
    (
        r"C(t) = \begin{cases} \frac{R_0}{V_1} \left[ \frac{k_{21} - \alpha}{\alpha(\beta - \alpha)} (1 - e^{-\alpha t}) + \frac{k_{21} - \beta}{\beta(\alpha - \beta)} (1 - e^{-\beta t}) \right], & t \le T_{\text{inf}} \\[6pt] \frac{R_0}{V_1} \left[ \frac{k_{21} - \alpha}{\alpha(\beta - \alpha)} (1 - e^{-\alpha T_{\text{inf}}}) e^{-\alpha(t - T_{\text{inf}})} + \frac{k_{21} - \beta}{\beta(\alpha - \beta)} (1 - e^{-\beta T_{\text{inf}}}) e^{-\beta(t - T_{\text{inf}})} \right], & t > T_{\text{inf}} \end{cases}",
        (
            "**Truyền tĩnh mạch (IV Infusion) — Mô hình 2 ngăn:**\n"
            "- $R_0, T_{\\text{inf}}$: Tốc độ truyền ($\\text{mg/h}$) và thời gian truyền tĩnh mạch ($\\text{h}$).\n"
            "- $C(t)$: Nồng độ trong ngăn trung tâm, phản ánh tương tác giữa nạp thuốc bậc 0, phân bố sang ngăn ngoại vi và thải trừ.\n"
            "- Nồng độ đỉnh đạt tại thời điểm ngắt truyền ($t = T_{\\text{inf}}$).\n"
            "- Sau khi ngừng truyền ($t > T_{\\text{inf}}$): Nồng độ suy giảm theo 2 pha $\\alpha$ (phân bố) và $\\beta$ (thải trừ).\n"
            "- $C_{ss}$: Nồng độ trạng thái ổn định khi truyền dài hạn ($C_{ss} = \\frac{R_0}{CL} = \\frac{R_0}{k_{10} V_1}$, không phụ thuộc vào $V_2$).\n"
            "- Khuyến cáo TDM: Mẫu nồng độ đỉnh không lấy ngay lúc dứt truyền mà phải chờ ít nhất 1 giờ để pha phân bố mô hoàn tất."
        ),
    ),
    (
        r"C(t) = \begin{cases} \sum_{i \in \{\alpha, \beta, \gamma\}} \frac{L_i}{\lambda_i} \left( 1 - e^{-\lambda_i t} \right), & 0 \le t \le T_{\text{inf}} \\[6pt] \sum_{i \in \{\alpha, \beta, \gamma\}} \frac{L_i}{\lambda_i} \left( 1 - e^{-\lambda_i T_{\text{inf}}} \right) e^{-\lambda_i (t - T_{\text{inf}})}, & t > T_{\text{inf}} \end{cases}",
        (
            "**Truyền tĩnh mạch (IV Infusion) — Mô hình 3 ngăn:**\n"
            "- $\\lambda_i \\in \\{\\alpha, \\beta, \\gamma\\}$: Ba hằng số suy giảm đặc trưng của mô hình 3 ngăn ($\\text{h}^{-1}$).\n"
            "- $L_i$: Các hệ số vi mô tương ứng suy ra từ tích chập giữa tốc độ truyền $R_0$ và hàm đáp ứng xung của hệ 3 ngăn.\n"
            "- Ứng dụng lâm sàng: Mô hình nền tảng trong gây mê hồi sức và truyền thuốc kiểm soát nồng độ đích (Target Controlled Infusion - TCI).\n"
            "- Thời gian bán thải phụ thuộc bối cảnh (Context-Sensitive Half-Time - CSHT): Thời gian giảm $50\\%$ nồng độ sau ngừng truyền tăng vọt khi thời gian truyền kéo dài do bão hòa ngăn sâu $V_3$."
        ),
    ),
    (
        r"C(t) = \frac{F \cdot D \cdot k_a}{V_1 (k_a - k_{el})} \left( e^{-k_{el}(t - T_{\text{lag}})} - e^{-k_a (t - T_{\text{lag}})} \right) \quad (\text{với } t \ge T_{\text{lag}})",
        (
            "**Phương trình Bateman mô hình 1 ngăn đường uống (có thời gian trễ $T_{\\text{lag}}$):**\n"
            "- $C(t)$: Nồng độ thuốc trong huyết tương tại thời điểm $t$ ($\\text{mg/L}$ hoặc $\\mu\\text{g/mL}$).\n"
            "- $D$: Liều thuốc đường uống dùng cho đối tượng ($\\text{mg}$).\n"
            "- $F$: Sinh khả dụng tuyệt đối đường uống ($0 < F \\le 1$; khi phân tích đường uống thường xác định dưới dạng $V_1/F, CL/F$).\n"
            "- $k_a$: Hằng số tốc độ hấp thu bậc 1 qua niêm mạc đường tiêu hóa ($\\text{h}^{-1}$).\n"
            "- $k_{el}$: Hằng số tốc độ đào thải bậc 1 từ ngăn trung tâm ($\\text{h}^{-1}$, với $k_{el} = CL / V_1$).\n"
            "- $V_1$: Thể tích phân bố biểu kiến của ngăn trung tâm (L hoặc $\\text{L/kg}$).\n"
            "- $T_{\\text{lag}}$: Thời gian trễ sinh dược học trước khi thuốc bắt đầu hấp thu vào vòng tuần hoàn chung ($\\text{h}$).\n"
            "- Điều kiện: Áp dụng khi $t \\ge T_{\\text{lag}}$; với $t < T_{\\text{lag}}$ thì $C(t) = 0$."
        ),
    ),
    (
        r"C(t) = A \cdot e^{-\alpha(t - T_{\text{lag}})} + B \cdot e^{-\beta(t - T_{\text{lag}})} - (A + B) e^{-k_a (t - T_{\text{lag}})} \quad (\text{với } t \ge T_{\text{lag}})",
        (
            "**Đường uống (Oral) — Mô hình 2 ngăn (Triexponential Oral):**\n"
            "- $C(t)$: Nồng độ thuốc trong ngăn trung tâm sau uống tại thời điểm $t$ ($\\text{mg/L}$).\n"
            "- $A, B$: Các hệ số vĩ mô dương của pha phân bố $\\alpha$ và pha thải trừ $\\beta$ ($\\text{mg/L}$).\n"
            "- $-(A + B)$: Hệ số pha hấp thu $k_a$, bảo đảm điều kiện ban đầu $C(T_{\\text{lag}}) = 0$.\n"
            "- $\\alpha, \\beta$: Hằng số tốc độ phân bố và thải trừ ($\\text{h}^{-1}$).\n"
            "- $k_a$: Hằng số tốc độ hấp thu bậc 1 qua ruột ($\\text{h}^{-1}$).\n"
            "- $V_1/F, V_2/F, CL/F, Q/F$: Các thể tích và độ thanh thải biểu kiến đường uống.\n"
            "- Hệ ODE: $dX_a/dt = -k_a X_a; \\quad dX_1/dt = k_a X_a - (k_{10}+k_{12})X_1 + k_{21}X_2; \\quad dX_2/dt = k_{12}X_1 - k_{21}X_2$."
        ),
    ),
    (
        r"C(t) = A \cdot e^{-\alpha t} + B \cdot e^{-\beta t} + C \cdot e^{-\gamma t} - (A + B + C) \cdot e^{-k_a t}",
        (
            "**Đường uống (Oral) — Mô hình 3 ngăn (Four-Exponential Oral):**\n"
            "- $C(t)$: Nồng độ thuốc trong ngăn trung tâm mô hình 3 ngăn đường uống ($\\text{mg/L}$).\n"
            "- $A, B, C$: Hệ số vĩ mô của 3 pha phân bố và thải trừ ($\\text{mg/L}$); hệ số pha hấp thu bằng $-(A+B+C)$ để thỏa mãn $C(0) = 0$.\n"
            "- $\\alpha, \\beta, \\gamma$: Ba hằng số tốc độ suy giảm tương ứng với ngăn trung tâm, ngăn nông và ngăn sâu ($\\text{h}^{-1}$).\n"
            "- $V_{ss}/F$: Thể tích phân bố biểu kiến trạng thái ổn định ($V_{ss}/F = \\frac{V_1}{F} [1 + \\frac{k_{12}}{k_{21}} + \\frac{k_{13}}{k_{31}}]$, đơn vị L).\n"
            "- $CL/F$: Độ thanh thải toàn thân biểu kiến ($CL/F = D / AUC_{0-\\infty}$, đơn vị $\\text{L/h}$).\n"
            "- Khuyến cáo thống kê: Mô hình có 7 tham số cần ước lượng; cần tối thiểu 12–15 điểm lấy mẫu/hồ sơ để tránh ma trận Fisher bị suy biến (singularity)."
        ),
    ),
    (
        r"T_{\max} = T_{\text{lag}} + \frac{\ln(k_a / k_{el})}{k_a - k_{el}}, \qquad C_{\max} = C(T_{\max}), \qquad C_{ss, avg} = \frac{F \cdot D}{CL \cdot \tau}, \qquad R_{ac} = \frac{1}{1 - e^{-k_{el} \tau}}",
        (
            "**Đặc trưng đỉnh và Động học Đa liều / Trạng thái ổn định:**\n"
            "- $T_{\\max}$: Thời điểm đạt nồng độ đỉnh trong huyết tương ($\\text{h}$).\n"
            "- $C_{\\max}$: Nồng độ đỉnh cực đại trong huyết tương ($\\text{mg/L}$ hoặc $\\mu\\text{g/mL}$), đạt được khi $dC/dt = 0$.\n"
            "- $C_{ss, avg}$: Nồng độ trung bình tại trạng thái ổn định sau khi dùng đa liều lặp lại ($\\text{mg/L}$).\n"
            "- $\\tau$: Khoảng cách thời gian giữa hai lần đưa liều kế tiếp nhau (Dosing interval, đơn vị $\\text{h}$).\n"
            "- $R_{ac}$: Hệ số tích lũy nồng độ thuốc tại trạng thái ổn định (Accumulation ratio).\n"
            "- Lưu ý Flip-flop: Khi $k_a \\ll k_{el}$, độ dốc pha cuối phản ánh tốc độ hấp thu $k_a$ chứ không phải tốc độ thải trừ $k_{el}$."
        ),
    ),
    (
        r"AICc = N \cdot \ln\left(\frac{WSSR}{N}\right) + 2p + \frac{2p(p+1)}{N - p - 1}, \qquad BIC = N \cdot \ln\left(\frac{WSSR}{N}\right) + p \cdot \ln(N)",
        (
            "**Chuẩn thông tin Akaike hiệu chỉnh (AICc) và Bayes (BIC) phục vụ chọn mô hình:**\n"
            "- $AICc$: Chuẩn thông tin Akaike hiệu chỉnh cho cỡ mẫu hữu hạn (Akaike Information Criterion corrected), tiêu chuẩn vàng so sánh mô hình PK.\n"
            "- $BIC$: Chuẩn thông tin Bayes (Schwarz Bayesian Criterion), áp dụng mức phạt số tham số nặng hơn $AICc$ khi số mẫu quan sát $N$ lớn.\n"
            "- $WSSR$: Tổng bình phương phần dư có trọng số (Weighted Sum of Squared Residuals: $\\sum w_i [C_{i,\\text{obs}} - C_{i,\\text{pred}}]^2$).\n"
            "- $N$: Tổng số điểm nồng độ quan sát thực tế trong hồ sơ PK cá thể.\n"
            "- $p$: Số lượng tham số cần ước tính trong mô hình (ví dụ $p=3$ cho 1 ngăn, $p=5$ cho 2 ngăn, $p=7$ cho 3 ngăn đường uống).\n"
            "- Quy tắc chọn mô hình: Mô hình có $AICc$ nhỏ hơn được ưu tiên. Nếu $\\Delta AICc > 2$, có bằng chứng thống kê ủng hộ mô hình tốt hơn; nếu $\\Delta AICc > 10$, bằng chứng là áp đảo."
        ),
    ),
)

# =============================================================================
# MODULE 11: ĐÁNH GIÁ TƯƠNG ĐƯƠNG SINH HỌC NHANH (QUICK BE)
# =============================================================================
EQUATIONS_11: tuple[tuple[str, str], ...] = (
    (
        r"\text{GMR} = \exp(\bar{Y}_T - \bar{Y}_R) \times 100\%, \quad 90\% \text{ CI} = \exp\left( (\bar{Y}_T - \bar{Y}_R) \pm t_{0.05, \, N-2} \sqrt{\frac{2 \cdot \text{MSE}}{N}} \right) \times 100\%",
        (
            "**Mô hình ANOVA sàng lọc nhanh 2x2 crossover:**\n"
            "- $\\text{GMR}$: Tỷ số trung bình hình học ước tính nhanh trên dữ liệu pilot (%).\n"
            "- $\\bar{Y}_T, \\bar{Y}_R$: Trung bình số học của các giá trị $\\ln(C_{\\max})$ hoặc $\\ln(AUC)$ theo từng nhóm thuốc Thử và Đối chứng.\n"
            "- $\\text{MSE}$: Bình phương trung bình sai số phần dư (Mean Squared Error) từ phân tích ANOVA sơ bộ trên thang logarit tự nhiên.\n"
            "- $N$: Tổng số đối tượng tham gia phân tích trong thiết kế chéo đôi cân bằng ($n_1 = n_2 = N/2$).\n"
            "- $N-2$: Bậc tự do phần dư nội cá thể.\n"
            "- $t_{0.05, \\, N-2}$: Giá trị tới hạn phân vị Student tương ứng với mức tin cậy $90\\%$ hai phía ($\\alpha = 0.05$ mỗi phía).\n"
            "- Khuyến cáo: Luồng BE Nhanh phục vụ sàng lọc sơ bộ trong giai đoạn R&D/Pilot; mọi hồ sơ đăng ký chính thức lên Cục Quản lý Dược (DAV), US FDA hoặc EMA bắt buộc phải sử dụng luồng BE Đầy đủ với quy trình khóa dữ liệu và nhật ký kiểm toán toàn vẹn."
        ),
    ),
)

ALL_EQUATIONS: dict[int, tuple[tuple[str, str], ...]] = {
    0: EQUATIONS_0,
    1: EQUATIONS_1,
    2: EQUATIONS_2,
    3: EQUATIONS_3,
    4: EQUATIONS_4,
    5: EQUATIONS_5,
    6: EQUATIONS_6,
    7: EQUATIONS_7,
    8: EQUATIONS_8,
    9: EQUATIONS_9,
    10: EQUATIONS_10,
    11: EQUATIONS_11,
}
