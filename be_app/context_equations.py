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
            "- Ngưỡng $5.0\\%$: Theo ICH M13A (Mục 2.1.3) và EMA (Mục 4.1.2), chênh lệch hàm lượng giữa hai lô nên $\\le 5.0\\%$. Trường hợp ngoại lệ bất khả kháng không tìm được lô Đối chứng chênh $\\le 5.0\\%$ ở hàm lượng cao nhất, việc hiệu chỉnh theo hàm lượng (potency adjustment) chỉ được xem xét nếu được định trước trong đề cương, có biện giải khoa học và nộp đồng thời cả kết quả hiệu chỉnh lẫn chưa hiệu chỉnh.\n"
            "- **Phạm vi BE_app:** Ứng dụng ghi nhận hàm lượng để kiểm soát chất lượng tiền phân tích và **không tự động hiệu chỉnh** kết quả PK/BE theo hàm lượng."
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
        r"\sigma_W^2 = \ln(CV_W^2 + 1) \quad \Longleftrightarrow \quad CV_W = \sqrt{e^{\sigma_W^2} - 1}, \qquad \sigma_{\text{total}}^2 = \ln(CV_{\text{total}}^2 + 1)",
        (
            "**Mối quan hệ giữa Hệ số biến thiên và Phương sai sai số trên thang logarit:**\n"
            "- $CV_W$: Hệ số biến thiên nội cá thể (Intra-subject CV) của $C_{\\max}$ hoặc $AUC$ trong thiết kế chéo/lặp ($2\\times 2$, replicate; dạng thập phân, ví dụ $0.20$ cho $20\\%$).\n"
            "- $\\sigma_W^2$ (hoặc $s_W^2, \\text{MSE}$): Phương sai sai số phần dư nội cá thể từ mô hình ANOVA trên thang $\\ln$.\n"
            "- $CV_{\\text{total}}, \\sigma_{\\text{total}}^2$: Áp dụng cho **thiết kế song song (Parallel)** vì mỗi đối tượng chỉ dùng 1 thuốc nên không tách riêng được phương sai nội cá thể khỏi phương sai giữa các cá thể."
        ),
    ),
    (
        r"T_L = \frac{(\bar{Y}_T - \bar{Y}_R) - \ln(0.80)}{\text{SE}} \ge t_{1-\alpha, \, \nu}, \qquad T_U = \frac{\ln(1.25) - (\bar{Y}_T - \bar{Y}_R)}{\text{SE}} \ge t_{1-\alpha, \, \nu}",
        (
            "**Thủ tục kiểm định hai phía một lần đồng thời TOST (Schuirmann):**\n"
            "- $T_L, T_U$: Hai thống kê kiểm định $t$ một phía đồng thời ở mức $\\alpha = 0.05$ mỗi phía (tương đương khoảng tin cậy $90\\% = 1 - 2\\alpha$).\n"
            "- $\\bar{Y}_T, \\bar{Y}_R$: Trung bình bình phương tối thiểu (LSMeans) trên thang $\\ln$ của thuốc Thử và Đối chứng.\n"
            "- $\\text{SE}$: Sai số chuẩn của hiệu số $(\\bar{Y}_T - \\bar{Y}_R)$: bằng $s_W \\sqrt{\\frac{1}{4}\\left(\\frac{1}{n_1}+\\frac{1}{n_2}\\right)}$ trong chéo $2\\times 2$ (cân bằng: $s_W\\sqrt{2/N}$ cho $T_L, T_U$ theo hiệu $I$ hay $\\text{SE} = s_W\\sqrt{1/(2n_1)+1/(2n_2)}$ với $s_W$ là $\\sqrt{\\text{MSE}}$ ở thang từng kỳ — lưu ý trong $2\\times 2$ $s_{\\text{diff}} = \\sqrt{2}\\,s_W$, nên $\\text{SE} = s_W \\sqrt{\\frac{1}{2}\\left(\\frac{1}{n_1}+\\frac{1}{n_2}\\right)}$), hoặc $s_{\\text{pool}}\\sqrt{\\frac{1}{n_T}+\\frac{1}{n_R}}$ trong thiết kế song song.\n"
            "- $\\ln(0.80) \\approx -0.2231, \\ln(1.25) \\approx +0.2231$: Giới hạn TĐSH quy ước theo chuẩn ICH M13A trên thang $\\ln$.\n"
            "- $\\nu$: Bậc tự do sai số ($N - 2$ cho $2\\times 2$ và song song phương sai gộp).\n"
            "- $t_{1-\\alpha, \\, \\nu}$: Phân vị Student $t$ một phía ở xác suất tích lũy $1-\\alpha = 0.95$ với $\\nu$ bậc tự do."
        ),
    ),
    (
        r"N_{\text{approx}} \ge \frac{2 \cdot \sigma_W^2 \cdot (t_{1-\alpha, \, \nu} + t_{1-\beta, \, \nu})^2}{(\ln(\theta_0) - \ln(\theta_{\text{limit}}))^2}, \qquad N_{\text{recruited}} = \left\lceil \frac{N}{1 - d} \right\rceil",
        (
            "**Ước lượng cỡ mẫu sơ bộ (Diletti et al.), tính lực chính xác trong BE_app và hiệu chỉnh bỏ cuộc:**\n"
            "- $N_{\\text{approx}}$: Công thức giải tích nhanh cho thiết kế chéo $2\\times 2$ cân bằng (thay $2\\sigma_W^2$ bằng $4\\sigma_{\\text{total}}^2$ nếu mở rộng gần đúng cho song song). Khi $\\theta_0 \\approx 1.00$, công thức này dùng xấp xỉ đơn phía nên có thể ước tính hơi thấp hơn thực tế.\n"
            "- **Thuật toán thực tế trong BE_app (`design.py`):** Hệ thống tính xác suất bác bỏ đồng thời $(T_L \\ge t_{1-\\alpha,\\nu} \\text{ và } T_U \\ge t_{1-\\alpha,\\nu})$ bằng **tích phân số chính xác** phân phối chuẩn có điều kiện trên phân phối $\\chi^2_\\nu$ độc lập (phương pháp Owen / `scipy.integrate.quad`) cho cả **$2\\times 2$** và **Song song**; **chưa mở module tính lực/cỡ mẫu tự động cho thiết kế replicate 3–4 kỳ**.\n"
            "- $1-\\beta$: Lực thống kê mục tiêu (thường $80\\%$ hoặc $90\\%$); $\\theta_0$: GMR kỳ vọng (thường đặt $0.95$ hoặc $1.05$); $\\theta_{\\text{limit}}$: biên gần nhất ($0.80$ hoặc $1.25$).\n"
            "- $d$: Tỷ lệ bỏ cuộc/vi phạm đề cương dự kiến; $N_{\\text{recruited}}$: cỡ mẫu cần tuyển ban đầu."
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
            "- Ngưỡng $20.0\\%$: Theo ICH M13A (Mục 2.2.3) và EMA (Mục 4.1.4), $AUC_{0-t}$ nên bao phủ ít nhất $80\\%$ giá trị $AUC_{0-\\infty}$ ($AUC_{\\%\\text{extrap}} \\le 20.0\\%$). Nếu hơn $20\\%$ số hồ sơ có $AUC_{\\%\\text{extrap}} > 20\\%$, tính hợp lệ của lịch lấy mẫu và $AUC_{0-\\infty}$ cần được xem xét/biện giải lại. Với thuốc giải phóng tức thời (IR) có $t_{1/2}$ rất dài, ICH M13A/EMA cho phép xem xét cắt cụt $AUC_{0-72\\text{h}}$ (thông tin tham khảo nếu đề cương áp dụng)."
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
            "- Quy tắc theo ICH M13A (Mục 2.2.4) & EMA (Mục 4.1.4): Nếu $C_{\\text{predose}} \\le 5.0\\% \\, C_{\\max}$, hồ sơ kỳ đó được giữ nguyên mà không hiệu chỉnh; nếu $C_{\\text{predose}} > 5.0\\% \\, C_{\\max}$, dữ liệu của đối tượng tại kỳ đó (hoặc toàn đối tượng trong thiết kế $2\\times 2$ đầy đủ) phải bị loại khỏi phân tích thống kê BE.\n"
            "- **Cách xử lý trong BE_app (`imports.py` / `nca.py`):** Ở Bước 3–4, mọi điểm tiền liều vượt $5\\%$ bị gắn cờ lỗi `ERROR` và **chặn khóa dữ liệu (Data Freeze)** cho tới khi được xử lý hợp lệ; ở Bước 5 NCA, hồ sơ vượt ngưỡng này tự động nhận trạng thái `NOT EVALUABLE`."
        ),
    ),
)

# =============================================================================
# MODULE 5: PHÂN TÍCH DƯỢC ĐỘNG HỌC NCA
# =============================================================================
EQUATIONS_5: tuple[tuple[str, str], ...] = (
    (
        r"\Delta AUC_i = \begin{cases} \frac{C_i - C_{i+1}}{\ln(C_i / C_{i+1})} \cdot (t_{i+1} - t_i) & \text{khi } C_i > C_{i+1} > 0 \text{ (Log Down)} \\[6pt] \frac{C_i + C_{i+1}}{2} \cdot (t_{i+1} - t_i) & \text{trường hợp còn lại (Linear Up hoặc } C_{i+1}=0\text{)} \end{cases}",
        (
            "**Phương pháp tích phân hình thang hỗn hợp Linear Up / Log Down (`nca.py`):**\n"
            "- $\\Delta AUC_i$: Diện tích dưới đường cong giữa hai thời điểm lấy mẫu liên tiếp $t_i$ và $t_{i+1}$ ($\\text{ng}\\cdot\\text{h}/\\text{mL}$).\n"
            "- $C_i, C_{i+1}$: Nồng độ thuốc đo được tại thời điểm $t_i$ và $t_{i+1}$ ($\\text{ng}/\\text{mL}$).\n"
            "- $t_i, t_{i+1}$: Thời điểm lấy mẫu thực tế liên tiếp ($\\text{h}$).\n"
            "- Cơ chế bảo vệ khi nồng độ về $0$ (BLQ): Khi $C_{i+1} = 0$ trong pha giảm ($C_i > C_{i+1}$), công thức tự động lùi về **hình thang tuyến tính** để tránh phép chia cho $\\ln(0)$ gây lỗi toán học."
        ),
    ),
    (
        r"AUC_{0-\infty,\text{obs}} = AUC_{0-t} + \frac{C_{\text{last}}}{\lambda_z}, \qquad AUC_{0-\infty,\text{pred}} = AUC_{0-t} + \frac{\hat{C}_{\text{last}}}{\lambda_z}, \qquad t_{1/2} = \frac{\ln(2)}{\lambda_z}, \qquad MRT_{\text{obs}} = \frac{AUMC_{0-\infty,\text{obs}}}{AUC_{0-\infty,\text{obs}}}",
        (
            "**Thông số phơi nhiễm toàn phần (`obs` vs `pred`), bán thải và lưu trú trung bình:**\n"
            "- $AUC_{0-\\infty}$: BE_app tính cả phiên bản dùng $C_{\\text{last}}$ thực đo (`obs`, mặc định dùng cho BE) và $\\hat{C}_{\\text{last}}$ ước lượng từ đường hồi quy pha cuối (`pred`).\n"
            "- $AUC_{0-t}$: Diện tích từ $0$ đến thời điểm đo cuối có nồng độ định lượng được $t_{\\text{last}}$ ($\\text{ng}\\cdot\\text{h}/\\text{mL}$).\n"
            "- $\\lambda_z$: Hằng số tốc độ thải trừ pha cuối ($\\text{h}^{-1}$), ước lượng bằng hồi quy tuyến tính OLS của $\\ln(C)$ theo thời gian $t$ với tiêu chí `adjusted R²` và `span >= min_span`.\n"
            "- $t_{1/2}$: Thời gian bán thải biểu kiến ở pha cuối ($\\text{h}$).\n"
            "- $AUMC_{0-\\infty}$: Diện tích dưới đường cong mô-men bậc 1 ($t \\cdot C(t)$) ngoại suy đến vô cùng ($AUMC_{0-t} + \\frac{t_{\\text{last}} C_{\\text{last}}}{\\lambda_z} + \\frac{C_{\\text{last}}}{\\lambda_z^2}$).\n"
            "- $MRT$: Thời gian lưu trú trung bình ($\\text{h}$). Với truyền tĩnh mạch có thời gian $T_{\\text{inf}}$, cần lưu ý $MRT_{\\text{iv-bolus}} = MRT_{\\text{inf}} - T_{\\text{inf}}/2$."
        ),
    ),
)

# =============================================================================
# MODULE 6: ĐÁNH GIÁ TƯƠNG ĐƯƠNG SINH HỌC
# =============================================================================
EQUATIONS_6: tuple[tuple[str, str], ...] = (
    (
        r"\text{GMR} = \exp(\bar{Y}_T - \bar{Y}_R) \times 100\%, \qquad 90\% \text{ CI} = \exp\left( (\bar{Y}_T - \bar{Y}_R) \pm t_{1-\alpha, \, \nu} \cdot \text{SE} \right) \times 100\%",
        (
            "**Đánh giá TĐSH Trung bình ABE (2×2 chéo đôi & Song song):**\n"
            "- $\\text{GMR}$: Tỷ số trung bình hình học của $C_{\\max}$ hoặc $AUC$ giữa thuốc Thử và Đối chứng (%).\n"
            "- $90\\% \\text{ CI}$: Khoảng tin cậy 90% hai phía tương đương hai kiểm định một phía ở mức $\\alpha = 0.05$ ($t_{1-\\alpha,\\,\\nu} = t_{0.95,\\,\\nu}$).\n"
            "- $\\bar{Y}_T, \\bar{Y}_R$: Trung bình bình phương tối thiểu (LSMeans) trên thang $\\ln$. Trong chéo đôi $2\\times 2$, $\\text{SE} = s_W \\sqrt{\\frac{1}{2n_1} + \\frac{1}{2n_2}}$ với $s_W = \\sqrt{\\text{MSE}}$ từ ANOVA và $\\nu = n_1 + n_2 - 2$. Trong thiết kế song song, $\\text{SE} = s_{\\text{pool}} \\sqrt{\\frac{1}{n_T} + \\frac{1}{n_R}}$ (hoặc Welch $t$-test nếu phương sai bất đồng nhất $p < 0.05$).\n"
            "- Tiêu chuẩn chấp nhận ABE chuẩn: $90\\% \\text{ CI}$ nằm hoàn toàn trong $[80.00\\% - 125.00\\%]$."
        ),
    ),
    (
        r"[L, U] = \exp\left( \pm k \cdot s_{wR} \right) \times 100\%, \qquad k = 0.760 \;\; \left(\text{từ } \frac{\ln(1.25)}{\sigma_{w0,\text{EMA}}}, \; \sigma_{w0,\text{EMA}} = \sqrt{\ln(1 + 0.30^2)} \approx 0.29356\right)",
        (
            "**Tiêu chuẩn EMA ABEL cho thuốc biến thiên cao (HVDP — Method A):**\n"
            "- **Phạm vi mở rộng:** Chỉ áp dụng nới giới hạn $[L, U]$ cho **$C_{\\max}$** khi $CV_{wR} > 30\\%$, đạt trần tối đa tại $CV_{wR} = 50\\%$ tương ứng $[69.84\\% - 143.19\\%]$; **giới hạn $AUC$ luôn giữ nguyên $[80.00\\% - 125.00\\%]$**.\n"
            "- $s_{wR}$: Độ lệch chuẩn nội cá thể của thuốc Đối chứng trên thang $\\ln$, xác định qua mô hình tham chiếu cố định ($s_{wR} = \\sqrt{\\ln(CV_{wR}^2 + 1)}$).\n"
            "- $\\sigma_{w0,\\text{EMA}} \\approx 0.29356$: Độ lệch chuẩn quy chiếu ứng với $CV_{w0} = 30\\%$, dẫn tới hệ số $k = 0.760$ (khác với hằng số $\\sigma_{w0} = 0.25$ của US FDA).\n"
            "- Điều kiện kép bắt buộc của EMA: $90\\% \\text{ CI}$ của $C_{\\max}$ nằm trong $[L, U]$ **đồng thời** điểm ước lượng $\\text{GMR}$ phải nằm trong $[80.00\\% - 125.00\\%]$."
        ),
    ),
    (
        r"(\bar{Y}_T - \bar{Y}_R)^2 - \theta s_{wR}^2 \le 0 \quad \text{với } \theta = \left(\frac{\ln(1.25)}{\sigma_{w0,\text{FDA}}}\right)^2 \approx 0.7967 \; (\sigma_{w0,\text{FDA}} = 0.25), \qquad \text{UCB}_{95\%} \le 0",
        (
            "**Tiêu chí US FDA RSABE cho thuốc biến thiên cao ($s_{wR} \\ge 0.294$):**\n"
            "- $\\text{UCB}_{95\\%}$: Giới hạn trên khoảng tin cậy 95% theo phép xấp xỉ Howe dựa trên các tương phản nội cá thể $I_i$ và $D_i$.\n"
            "- Điều kiện kích hoạt mở rộng FDA: Khi $s_{wR} \\ge 0.294$ ($CV_{wR} \\ge 30.05\\%$), phải đạt $\\text{UCB}_{95\\%} \\le 0$ đồng thời $\\text{GMR} \\in [80.00\\% - 125.00\\%]$.\n"
            "- Khi $s_{wR} < 0.294$: Phải quay về tiêu chuẩn ABE chuẩn $[80.00\\% - 125.00\\%]$. (**Lưu ý thuật toán BE_app:** `replicate.py` đánh giá nhánh này bằng phân tích tương phản đối tượng $I$ (OLS, $df_I$), chưa nối mô hình hỗn hợp tuyến tính Phụ lục C của FDA vào quy trình chính)."
        ),
    ),
    (
        r"\text{EMA NTI}: [90.00\%, \, 111.11\%], \qquad \text{FDA NTI}: \left\{\text{ABE}_{[80,125]} \;\cap\; \text{UCB}_{95\%}(\theta_{\text{NTI}}) \le 0 \;\cap\; \frac{s_{wT}/s_{wR}}{\sqrt{F_{0.05, \, \nu_T, \, \nu_R}}} \le 2.5\right\}",
        (
            "**Tiêu chuẩn Thuốc khoảng điều trị hẹp (NTI — EMA vs. US FDA):**\n"
            "- **EMA NTI:** Thu hẹp khoảng chấp nhận $90\\% \\text{ CI}$ xuống $[90.00\\% - 111.11\\%]$ cho $AUC$ (và cả $C_{\\max}$ nếu có ý nghĩa lâm sàng về an toàn/hiệu quả).\n"
            "- **US FDA NTI (bắt buộc thiết kế lặp toàn phần 4 kỳ `full4`):** Đồng thời thỏa mãn cả 3 tiêu chí: (1) ABE chuẩn $90\\% \\text{ CI} \\subset [80.00\\% - 125.00\\%]$; (2) RSABE thu hẹp với $\\sigma_{w0} = 0.10, \\; \\theta_{\\text{NTI}} = (\\ln(1/0.9)/0.10)^2 \\approx 1.1099$ sao cho $\\text{UCB}_{95\\%} \\le 0$; (3) Giới hạn trên của $90\\% \\text{ CI}$ cho tỷ số độ lệch chuẩn nội cá thể $s_{wT}/s_{wR}$ phải $\\le 2.5$."
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
            "- $R^2_{\\text{adj}}$ (Adjusted $R^2$): Hệ số xác định hiệu chỉnh theo số điểm hồi quy. Trong **BE_app (`nca.py`)**, ngưỡng mặc định lọc hồi quy pha cuối là $R^2_{\\text{adj}} \\ge 0.80$ cùng khoảng thời gian $\\text{span} \\ge \\text{ngưỡng bán thải}$ (có thể cấu hình theo SAP ở Bước 5; khuyến cáo thực hành nâng cao thường nhắm $\\ge 0.85$ khi số điểm cho phép)."
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
            "**Mô hình chuỗi băm kiểm toán liên kết bất biến (Hash-chained Audit Record):**\n"
            "- $\\mathcal{H}_k$: Mã băm SHA-256 của sự kiện kiểm toán thứ $k$.\n"
            "- $\\mathcal{H}_{k-1}$: Mã băm SHA-256 (`previous`) của sự kiện kiểm toán ngay trước đó ($k-1$). Với sự kiện đầu tiên của dự án, `previous` là chuỗi rỗng `\"\"`.\n"
            "- $\\text{Timestamp}_k$: Dấu thời gian chuẩn UTC theo chuẩn ISO-8601 của hành động.\n"
            "- $\\text{Action}_k$: Loại hành động được ghi nhận (tạo mới, nhập dữ liệu, khóa dữ liệu, tính NCA, chạy thống kê, xuất báo cáo).\n"
            "- $\\text{User}_k$: Tên người thực hiện được khai báo trong thông tin nghiên cứu (`actor`, mặc định `study.operator`).\n"
            "- $\\text{Details}_k$: Dữ liệu chi tiết dạng JSON về tham số hoặc trạng thái nghiên cứu.\n"
            "- $\\|$: Phép toán ghép dữ liệu sự kiện vào cấu trúc JSON chuẩn hóa trước khi băm SHA-256 (`persistence.py`).\n"
            "- Ý nghĩa & giới hạn triển khai: Chuỗi băm liên kết giúp phát hiện sửa đổi hồi cứu trên SQLite cục bộ. Tuy nhiên phiên bản desktop đơn người dùng (single-user) **chưa tích hợp phân quyền đăng nhập RBAC và chữ ký điện tử**, nên chưa đáp ứng trọn vẹn 21 CFR Part 11 / EU GMP Annex 11 nếu thiếu kiểm soát hệ thống tổ chức đi kèm."
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
            "**Truyền tĩnh mạch liên tục (IV Infusion) — Mô hình 2 ngăn:**\n"
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
            "**Truyền tĩnh mạch liên tục (IV Infusion) — Mô hình 3 ngăn:**\n"
            "- $\\lambda_i \\in \\{\\alpha, \\beta, \\gamma\\}$: Ba hằng số suy giảm đặc trưng của mô hình 3 ngăn ($\\text{h}^{-1}$).\n"
            "- $L_i$: Các hệ số vi mô tương ứng suy ra từ tích chập giữa tốc độ truyền $R_0$ và hàm đáp ứng xung của hệ 3 ngăn.\n"
            "- Ứng dụng lâm sàng: Mô hình nền tảng trong gây mê hồi sức và truyền thuốc kiểm soát nồng độ đích (Target Controlled Infusion - TCI).\n"
            "- Thời gian bán thải phụ thuộc bối cảnh (Context-Sensitive Half-Time - CSHT): Thời gian giảm $50\\%$ nồng độ sau ngừng truyền tăng vọt khi thời gian truyền kéo dài do bão hòa ngăn sâu $V_3$."
        ),
    ),
    (
        r"C(t) = \frac{F \cdot D \cdot k_a}{V_1 (k_a - k_{el})} \left( e^{-k_{el}(t - T_{\text{lag}})} - e^{-k_a (t - T_{\text{lag}})} \right) \quad (\text{với } t \ge T_{\text{lag}})",
        (
            "**Đường uống (Oral) — Mô hình 1 ngăn (Phương trình Bateman; tổng quát có $T_{\\text{lag}}$, `BE_app` cố định $T_{\\text{lag}}=0$):**\n"
            "- $C(t)$: Nồng độ thuốc trong huyết tương tại thời điểm $t$ ($\\text{mg/L}$ hoặc $\\mu\\text{g/mL}$).\n"
            "- $D$: Liều thuốc đường uống dùng cho đối tượng ($\\text{mg}$).\n"
            "- $F$: Sinh khả dụng tuyệt đối đường uống ($0 < F \\le 1$; khi phân tích đường uống thường xác định dưới dạng $V_1/F, CL/F$).\n"
            "- $k_a$: Hằng số tốc độ hấp thu bậc 1 qua niêm mạc đường tiêu hóa ($\\text{h}^{-1}$).\n"
            "- $k_{el}$: Hằng số tốc độ đào thải bậc 1 từ ngăn trung tâm ($\\text{h}^{-1}$, với $k_{el} = CL / V_1$).\n"
            "- $V_1$: Thể tích phân bố biểu kiến của ngăn trung tâm (L hoặc $\\text{L/kg}$).\n"
            "- $T_{\\text{lag}}$: Thời gian trễ sinh dược học trước khi thuốc bắt đầu hấp thu ($\\text{h}$). **Lưu ý trong BE_app (`pk_models.py`):** Bộ khớp phi tuyến đường uống hiện **cố định $T_{\\text{lag}} = 0$** (tại $t=0, C=0$); không ước lượng tham số $T_{\\text{lag}}$ tự do cho thuốc giải phóng muộn/bao tan trong ruột."
        ),
    ),
    (
        r"C(t) = A \cdot e^{-\alpha t} + B \cdot e^{-\beta t} - (A + B) e^{-k_a t} \quad (\text{khi } T_{\text{lag}} = 0)",
        (
            "**Đường uống (Oral) — Mô hình 2 ngăn (Triexponential Oral):**\n"
            "- $C(t)$: Nồng độ thuốc trong ngăn trung tâm sau uống tại thời điểm $t$ ($\\text{mg/L}$); trường hợp tổng quát có thể thay $t$ bằng $(t - T_{\\text{lag}})$, còn trong **BE_app hiện cố định $T_{\\text{lag}} = 0$**.\n"
            "- $A, B$: Hệ số vĩ mô từ phép giải vi phân tuyến tính; điều kiện biên bảo đảm $C(0) = 0$ khi hệ số pha hấp thu $k_a$ cân bằng với $-(A+B)$.\n"
            "- $\\alpha, \\beta$: Hằng số tốc độ phân bố và thải trừ ($\\text{h}^{-1}$); $k_a$: hằng số tốc độ hấp thu bậc 1 ($\\text{h}^{-1}$).\n"
            "- $V_1/F, V_p/F, CL/F, Q/F$: 5 tham số biểu kiến đường uống được BE_app tối ưu hóa trực tiếp ($F$ không xác định riêng từ dữ liệu đường uống đơn độc).\n"
            "- Hệ ODE: $dX_a/dt = -k_a X_a; \\quad dX_1/dt = k_a X_a - (k_{10}+k_{12})X_1 + k_{21}X_2; \\quad dX_2/dt = k_{12}X_1 - k_{21}X_2$."
        ),
    ),
    (
        r"C(t) = A \cdot e^{-\alpha t} + B \cdot e^{-\beta t} + C \cdot e^{-\gamma t} - (A + B + C) \cdot e^{-k_a t}",
        (
            "**Đường uống (Oral) — Mô hình 3 ngăn (Four-Exponential Oral):**\n"
            "- $C(t)$: Nồng độ thuốc trong ngăn trung tâm mô hình 3 ngăn đường uống ($\\text{mg/L}$).\n"
            "- $A, B, C$: Hệ số vĩ mô của 3 pha phân bố và thải trừ ($\\text{mg/L}$); tổng hệ số ban đầu tại $t=0$ bằng $0$.\n"
            "- $\\alpha, \\beta, \\gamma$: Ba hằng số tốc độ suy giảm của hệ 3 ngăn ($\\text{h}^{-1}$).\n"
            "- $V_{ss}/F$: Thể tích phân bố biểu kiến trạng thái ổn định ($V_{ss}/F = \\frac{V_1}{F} + \\frac{V_2}{F} + \\frac{V_3}{F}$, đơn vị $\\text{L}$).\n"
            "- $CL/F$: Độ thanh thải toàn thân biểu kiến ($CL/F = D / AUC_{0-\\infty}$, đơn vị $\\text{L/h}$).\n"
            "- Khuyến cáo thống kê: Mô hình có 7 tham số ($CL/F, V/F, Q_2/F, V_{p2}/F, Q_3/F, V_{p3}/F, k_a$); BE_app cảnh báo khi $N < 15$ điểm định lượng hoặc hai ngăn ngoại vi có $k_{21}, k_{31}$ chênh lệch $< 5\\%$."
        ),
    ),
    (
        r"T_{\max} = T_{\text{lag}} + \frac{\ln(k_a / k_{el})}{k_a - k_{el}}, \qquad C_{\max} = C(T_{\max}), \qquad C_{\text{ss}, \text{avg}} = \frac{F \cdot D}{CL \cdot \tau}, \qquad R_{ac} = \frac{1}{1 - e^{-k_{el} \tau}}",
        (
            "**Đặc trưng đỉnh và Động học Đa liều / Trạng thái ổn định (chồng chất tuyến tính):**\n"
            "- $T_{\\max}$: Thời điểm đạt nồng độ đỉnh ($\\text{h}$; với $T_{\\text{lag}}=0$ trong bộ khớp uống 1 ngăn, hai nghiệm hoán đổi $(k_a, k_{el})$ tạo cùng đường cong $C(t)$ và BE_app quy ước hiển thị nhánh $k_a \\ge k_{el}$, đồng thời cảnh báo khả năng Flip-flop).\n"
            "- $C_{\\max}$: Nồng độ đỉnh cực đại ($\\text{mg/L}$ hoặc $\\mu\\text{g/mL}$), đạt khi $dC/dt = 0$.\n"
            "- $C_{\\text{ss}, \\text{avg}}$: Nồng độ trung bình tại trạng thái ổn định ($AUC_{0-\\tau,\\text{ss}} / \\tau = F\\cdot D / (CL\\cdot \\tau)$, đơn vị $\\text{mg/L}$).\n"
            "- $\\tau$: Khoảng cách đưa liều đều đặn ($\\text{h}$); $R_{ac}$: Hệ số tích lũy tuyến tính ở trạng thái ổn định.\n"
            "- Đa liều trong **BE_app (`pk_multiple.py`)**: Áp dụng nguyên lý **chồng chất tuyến tính các liều bằng nhau** $C_{\\text{multi}}(t) = \\sum_{j=0}^{m-1} C_{\\text{single}}(t - j\\tau)$ với giả định dược động học tuyến tính theo thời gian."
        ),
    ),
    (
        r"AICc = N \cdot \ln\left(\frac{WSSR}{N}\right) + 2p + \frac{2p(p+1)}{N - p - 1} \quad (N > p + 1), \qquad BIC = N \cdot \ln\left(\frac{WSSR}{N}\right) + p \cdot \ln(N)",
        (
            "**Chuẩn thông tin Akaike hiệu chỉnh (AICc) và Bayes (BIC) chọn số ngăn (`pk_models.py`):**\n"
            "- $WSSR$: Tổng bình phương phần dư có trọng số $WSSR = \\sum_{i=1}^N \\left(\\frac{C_{i,\\text{pred}} - C_{i,\\text{obs}}}{d_i}\\right)^2$, trong đó mẫu số chuẩn hóa $d_i$ là $1$ (bằng nhau), $\\sqrt{\\text{scale}_i}$ (trọng số $1/C$), hoặc $\\text{scale}_i$ (trọng số $1/C^2$) với $\\text{scale}_i = \\max(C_{i,\\text{obs}}, 10^{-3} C_{\\max})$.\n"
            "- $N$: Số điểm nồng độ đưa vào khớp (lưu ý `IV bolus` loại bỏ điểm $t=0$ có $C=0$); $p$: Số tham số mô hình.\n"
            "- Điều kiện $AICc$: Chỉ xác định khi $N > p + 1$ (nếu $N \\le p + 1$, trường `AICc` để trống).\n"
            "- **Giới hạn so sánh trọng số:** Chỉ dùng `AICc`/`BIC` để so sánh các mô hình ngăn **trên cùng một sơ đồ trọng số** (`equal`, `1/C`, hoặc `1/C²`); khi trọng số $\\neq$ `equal`, `AICc`/`BIC` chỉ mang tính chẩn đoán."
        ),
    ),
)

# =============================================================================
# MODULE 11: ĐÁNH GIÁ TƯƠNG ĐƯƠNG SINH HỌC NHANH (QUICK BE)
# =============================================================================
EQUATIONS_11: tuple[tuple[str, str], ...] = (
    (
        r"\text{GMR} = \exp(\bar{Y}_T - \bar{Y}_R) \times 100\%, \quad 90\% \text{ CI} = \exp\left( (\bar{Y}_T - \bar{Y}_R) \pm t_{1-\alpha, \, \nu} \cdot \text{SE} \right) \times 100\%",
        (
            "**Mô hình thống kê BE Nhanh (2×2 / Song song / Replicate theo `quick_be.py`):**\n"
            "- $\\text{GMR}$: Tỷ số trung bình hình học của $C_{\\max}$ hoặc $AUC$ giữa thuốc Thử và Đối chứng (%).\n"
            "- Trong thiết kế $2\\times 2$ (cân bằng hoặc lệch chuỗi $n_1 \\neq n_2$): $\\text{SE} = s_W \\sqrt{\\frac{1}{2}\\left(\\frac{1}{n_1} + \\frac{1}{n_2}\\right)}$ với $\\nu = n_1 + n_2 - 2$ và $t_{1-\\alpha,\\,\\nu} = t_{0.95,\\,\\nu}$ (khi $n_1 = n_2 = N/2$, rút gọn thành $s_W\\sqrt{2/N}$).\n"
            "- Trong thiết kế **Song song (Parallel)**: dùng $t$-test phương sai gộp (hoặc Welch–Satterthwaite khi $F$-test bất đồng nhất phương sai $p < 0.05$), chỉ số $CV_{\\text{total}}$ thay cho $CV_{\\text{intra}}$.\n"
            "- Trong thiết kế **Replicate (`partial3` / `full4`)**: gọi chung bộ giải `analyze_replicate()` với quy chế EMA ABEL hoặc US FDA RSABE/NTI.\n"
            "- **Kiểm định $T_{\\max}$ (chỉ mang tính mô tả/hỗ trợ, không quyết định BE):** Hỗ trợ **Wilcoxon signed-rank** ($2\\times 2$, yêu cầu đủ cặp T/R trên từng đối tượng) và **Mann–Whitney U** (Song song); chưa hỗ trợ kiểm định phi tham số $T_{\\max}$ cho replicate."
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
