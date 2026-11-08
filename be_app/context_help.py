from be_app.context_equations import (
    EQUATIONS_0,
    EQUATIONS_1,
    EQUATIONS_2,
    EQUATIONS_3,
    EQUATIONS_4,
    EQUATIONS_5,
    EQUATIONS_6,
    EQUATIONS_7,
    EQUATIONS_8,
    EQUATIONS_9,
    EQUATIONS_10,
    EQUATIONS_11,
)
from be_app.diagram_svg import DIAGRAM_SVGS
"""Teaching-oriented, read-only contextual help for the BE workflow.

Provides comprehensive graduate-level pedagogical modules (Master/PhD) covering:
1. Hướng dẫn thao tác (Interface elements & sequential action guide).
2. Tóm tắt lý thuyết (kèm sơ đồ minh họa) và tiêu chuẩn pháp quy (Theory, diagrams & regulations).
3. Phương trình toán học và giải thích biến số (KaTeX equations & detailed variable nomenclature).
4. Thuật ngữ (Terminology & Data Integrity ALCOA+ principles).
5. Câu hỏi gợi ý và chủ đề tự học (Guiding seminar questions & critical reflection).
6. Tài liệu tham khảo (Authoritative guidelines & seminal literature).
"""

from dataclasses import dataclass

from be_app.regulations import RULES, capability_for


@dataclass(frozen=True)
class Lesson:
    interface: tuple[str, ...]
    actions: tuple[str, ...]
    theory: tuple[str, ...]
    terms: tuple[str, ...]
    exercise: str
    diagram: str = ""
    regulations: tuple[str, ...] = ()
    equations: tuple[tuple[str, str], ...] = ()
    questions: tuple[str, ...] = ()
    references: tuple[str, ...] = ()


@dataclass(frozen=True)
class IntegrityTerm:
    name: str
    meaning: str
    app_example: str


# Keys follow the existing workflow page indices (0 to 9); adding help must not shift the steps.
LESSONS: tuple[Lesson, ...] = (
    # -------------------------------------------------------------------------
    # BƯỚC 0: TỔNG QUAN / QUẢN LÝ NGHIÊN CỨU (STUDY SETUP & PROVENANCE)
    # -------------------------------------------------------------------------
    Lesson(
        interface=(
            "**Khởi tạo nghiên cứu:** Khai báo mã định danh nghiên cứu (Study ID), thiết kế thử nghiệm lâm sàng (chéo đôi 2×2, song song, replicate), bộ quy tắc pháp lý (EMA, FDA, ICH M13A) và quản lý phiên bản Đề cương (Protocol) / Kế hoạch phân tích thống kê (SAP).",
            "**Điều kiện nghiên cứu:** Lựa chọn trạng thái dùng thuốc khi Đói (Fasted, nhịn ăn tối thiểu 8–10 giờ) hoặc sau ăn No (Fed, bữa ăn chuẩn giàu chất béo/năng lượng cao theo guideline); ghi nhận đơn vị tài trợ (Sponsor), địa điểm nghiên cứu (CRO/Bệnh viện) và Nghiên cứu viên chính (Principal Investigator - PI).",
            "**Thuốc thử T (Test) và Thuốc thử R (Reference - Thuốc đối chứng):** Khai báo tên thương mại, tên hoạt chất, dạng bào chế, nồng độ/hàm lượng mỗi đơn vị phân liều, nhà sản xuất, số lô sản xuất, ngày sản xuất và hạn dùng (kèm phiếu kiểm nghiệm xuất xưởng CoA).",
            "**Mốc thời gian nghiên cứu:** Ngày phê duyệt của Hội đồng Đạo đức (IRB/IEC), thời gian bắt đầu/kết thúc giai đoạn lâm sàng, thời gian phân tích mẫu sinh học (Bioanalytical phase) và ngày chốt cơ sở dữ liệu (Data Lock / Data Freeze).",
            "**Nguồn gốc dữ liệu & Phạm vi áp dụng (Provenance & Scope):** Đối chiếu đặc tính hoạt chất quy ước giải phóng tức thì (IR) theo khuyến cáo ICH M13A, mục đích sử dụng và các hướng dẫn chuyên biệt (Product-Specific Guidance - PSG).",
            "**Tiến độ & Quản lý cấu hình (Preset/Archive):** Theo dõi trạng thái hoàn thành từng chặng, áp dụng cấu hình mẫu chuẩn hóa và khôi phục dự án từ tệp nén lưu trữ.",
        ),
        actions=(
            "Xác nhận thiết kế và hồ sơ pháp lý phù hợp với đặc tính dược động học của thuốc giải phóng tức thì (IR) đường uống theo khuyến cáo ICH M13A.",
            "Điền chính xác thông tin thuốc thử T và thuốc thử R (thuốc đối chứng) từ nhãn thuốc và hồ sơ lô (Batch Record); phân biệt rõ hàm lượng hoạt chất trong mỗi đơn vị phân liều.",
            "Lựa chọn điều kiện Đói/No theo đúng đề cương đã được Hội đồng Đạo đức phê duyệt; các mốc thời gian chưa có bằng chứng nghiệm thu thực tế cần để trống.",
            "Khai báo đầy đủ mã và phiên bản của Đề cương (Protocol), Kế hoạch phân tích thống kê (SAP), nguồn gốc dữ liệu rồi chọn **Tạo nghiên cứu**.",
            "Trong quá trình học thử/thực hành, chọn tình huống mẫu rồi bấm **Điền dữ liệu mẫu vào biểu mẫu nghiên cứu**; đối chiếu từng trường số liệu trước khi bấm **Tạo nghiên cứu**.",
        ),
        theory=(
            "Nghiên cứu tương đương sinh học (BE) in vivo đóng vai trò làm bằng chứng thay thế lâm sàng (clinical surrogate) để chứng minh sự tương đồng về sinh khả dụng (tốc độ và mức độ hấp thu) giữa thuốc generic và thuốc phát minh.",
            "Bữa ăn giàu chất béo (High-fat meal, ~800–1000 kcal với ~50% từ lipid) có thể làm chậm quá trình làm rỗng dạ dày (gastric emptying), thay đổi pH đường tiêu hóa, hoặc kích thích bài tiết mật làm tăng độ tan của hoạt chất kém tan (BCS II/IV). Điều kiện nhịn đói (Fasted) thường là điều kiện nhạy nhất để phát hiện sai khác giải phóng in vivo giữa hai công thức IR.",
            "Các giai đoạn lâm sàng, phân tích mẫu sinh học (Bioanalytical phase) và khóa dữ liệu (Data Freeze) có mốc thời gian độc lập; không suy diễn ngày hoàn thành nghiên cứu từ ngày chạy phân tích thống kê.",
            "Hướng dẫn ICH M13A áp dụng thống nhất cho các thuốc quy ước giải phóng tức thì; các thuốc biến thiên cao (HVDP), khoảng điều trị hẹp (NTI) hoặc thuốc có tác dụng tại chỗ yêu cầu thiết kế và tiêu chí mở rộng riêng biệt.",
        ),
        terms=(
            "Protocol: Đề cương nghiên cứu đã được Hội đồng Đạo đức (IRB/IEC) phê duyệt; SAP: Kế hoạch phân tích thống kê (Statistical Analysis Plan) định trước.",
            "T/R: Thuốc thử T (Test) và Thuốc thử R (Reference - Thuốc đối chứng); CoA: Phiếu kiểm nghiệm xuất xưởng của lô nghiên cứu (Certificate of Analysis).",
            "Fasted/Fed: Trạng thái nhịn ăn (tối thiểu 8–10h) hoặc sau bữa ăn chuẩn giàu chất béo; Data Lock: Thời điểm chốt cơ sở dữ liệu lâm sàng trước khi mở mù.",
            "PSG: Hướng dẫn chuyên biệt cho từng hoạt chất (Product-Specific Guidance); Provenance: Nguồn gốc và lịch sử truy vết dữ liệu.",
            "BCS (Biopharmaceutics Classification System): Hệ thống phân loại sinh dược học dựa trên độ tan trong nước và tính thấm qua màng ruột.",
        ),
        exercise="Dựa trên nguyên lý dược động học và hướng dẫn ICH M13A, hãy giải thích cơ sở khoa học vì sao một hoạt chất có tính hấp thu biến thiên cao (HVDP) hoặc khoảng điều trị hẹp (NTI) không thể áp dụng chung một bộ quy tắc đánh giá tương đương sinh học (80,00–125,00%) như thuốc chéo đôi 2×2 thông thường?",
        diagram=DIAGRAM_SVGS[0],
        regulations=(
            "ICH Guideline M13A (Step 5, 2024): Bioequivalence for Immediate-Release Solid Oral Dosage Forms (Mục 2.1 Phạm vi, 2.2 Thiết kế nghiên cứu).",
            "EMA Guideline on the Investigation of Bioequivalence (CPMP/EWP/QWP/1401/98 Rev. 1/Corr**, 2010): Mục 4.1.1 Yêu cầu về lô thuốc và hoạt chất.",
            "US FDA Guidance for Industry (2021/2026): Bioequivalence Studies with Pharmacokinetic Endpoints for Drugs Submitted Under an ANDA.",
            "Bộ Y tế Việt Nam: Thông tư số 08/2022/TT-BYT quy định về đăng ký lưu hành thuốc và thử tương đương sinh học.",
            "ICH Harmonised Guideline E6(R3): Good Clinical Practice (GCP) - Nguyên tắc đạo đức và toàn vẹn dữ liệu thử nghiệm lâm sàng.",
        ),
        equations=EQUATIONS_0,
        questions=(
            "1. Tại sao cả ICH M13A và US FDA đều nghiêm cấm việc tự ý hiệu chỉnh kết quả phơi nhiễm (potency adjustment) theo tỷ lệ hàm lượng thực tế của hai lô thuốc nếu độ lệch nằm trong khoảng cho phép (<= 5%)?",
            "2. Trong trường hợp nào một hoạt chất thuộc nhóm BCS I hoặc III được xem xét miễn thử tương đương sinh học in vivo (Biowaiver dựa trên độ hòa tan in vitro theo ICH M9)?",
            "3. Phân tích tác động sinh học của bữa ăn chuẩn giàu chất béo (High-fat fed state) lên tốc độ rỗng dạ dày và độ hấp thu của các thuốc có tính kiềm yếu (Weak bases).",
        ),
        references=(
            "ICH Harmonised Guideline (2024). ICH M13A: Bioequivalence for immediate-release solid oral dosage forms. International Council for Harmonisation.",
            "EMA (2010). Guideline on the investigation of bioequivalence (CPMP/EWP/QWP/1401/98 Rev. 1/Corr**). European Medicines Agency.",
            "US FDA (2021). Bioequivalence Studies with Pharmacokinetic Endpoints for Drugs Submitted Under an ANDA. Center for Drug Evaluation and Research.",
            "Chow, S. C., & Liu, J. P. (2008). Design and Analysis of Bioavailability and Bioequivalence Studies (3rd ed.). Chapman and Hall/CRC.",
        ),
    ),

    # -------------------------------------------------------------------------
    # BƯỚC 1: THIẾT KẾ VÀ CỠ MẪU BE (DESIGN & SAMPLE SIZE PLANNING)
    # -------------------------------------------------------------------------
    Lesson(
        interface=(
            "**Hệ số biến thiên (CV):** Giả định độ biến thiên nội cá thể (CV_intra đối với thiết kế chéo) hoặc giữa các cá thể (CV_inter đối với thiết kế song song) cho từng chỉ tiêu AUC và Cmax.",
            "**Tỷ số trung bình nhân dự kiến (GMR):** Tỷ lệ μT/μR kỳ vọng (thường giả định 0.95 hoặc 1.00); **Lực thống kê mục tiêu (Power, 1-β):** Thường thiết lập ở mức ≥ 80% hoặc 90%.",
            "**Tỷ lệ bỏ cuộc (Dropout rate):** Dự phòng số đối tượng rút khỏi nghiên cứu; **Tài liệu nguồn:** Trích dẫn tài liệu xuất bản hoặc nghiên cứu tiền cứu (Pilot study) làm căn cứ cho giả định CV.",
            "**Quy mô nghiên cứu:** Số lượng đối tượng hoàn thành đánh giá (N_evaluable) và số đối tượng cần tuyển dụng (N_recruited) sau khi bù trừ tỷ lệ dropout.",
        ),
        actions=(
            "Xác nhận profile pháp lý, thiết kế và khoảng chấp nhận tương đương sinh học (80.00 - 125.00% đối với ABE chuẩn).",
            "Nhập hệ số biến thiên CV, tỷ số GMR, lực thống kê mục tiêu, tỷ lệ dropout và trích dẫn nguồn giả định rồi chọn **Tính cỡ mẫu và power**.",
            "Đánh giá độc lập kết quả cỡ mẫu cho cả hai chỉ tiêu AUC và Cmax; nếu có cảnh báo STALE, bắt buộc phải tính lại sau khi thay đổi bất kỳ tham số giả định nào.",
        ),
        theory=(
            "Lực thống kê (Power, 1-β) là xác suất bác bỏ đúng giả thuyết vô hiệu H0 (không tương đương) khi hai thuốc thực sự tương đương sinh học. Thủ tục kiểm định hai phía đồng thời (Two One-Sided Tests - TOST, Schuirmann) tương đương việc xác định khoảng tin cậy 90% nằm gọn trong biên BE.",
            "Hệ thống hỗ trợ tính toán cỡ mẫu cho thiết kế chéo đôi 2×2 và thiết kế song song; quy trình tính cỡ mẫu cho thiết kế lặp (Replicate/ABEL/RSABE) hoặc thuốc NTI đòi hỏi mô phỏng Monte Carlo nâng cao.",
            "Theo nguyên lý hợp các giao (Intersection-Union Principle), nghiên cứu chỉ đạt khi cả AUC và Cmax cùng đạt; cỡ mẫu chính thức của thử nghiệm phải chọn theo chỉ tiêu đòi hỏi số lượng đối tượng lớn hơn.",
        ),
        terms=(
            "CV (Coefficient of Variation): Hệ số biến thiên; GMR (Geometric Mean Ratio): Tỷ số trung bình nhân giữa T và R.",
            "TOST (Two One-Sided Tests): Kiểm định hai phía đồng thời của Schuirmann; Dropout: Tỷ lệ người tình nguyện rút lui hoặc bị loại khỏi nghiên cứu.",
            "Intersection-Union Principle: Nguyên lý kiểm định đồng thời nhiều endpoint mà không làm tăng sai lầm loại I (không cần hiệu chỉnh Bonferroni).",
            "Non-central t-distribution: Hàm phân phối t không tâm sử dụng trong giải tích lực thống kê chính xác (Owen's Q-function / Diletti).",
        ),
        exercise="Trong nghiên cứu tương đương sinh học chéo đôi 2×2, nếu hệ số biến thiên nội cá thể CV_intra thực tế của Cmax tăng từ 20% lên 30% trong khi GMR kỳ vọng giữ nguyên ở mức 0.95, cỡ mẫu cần tuyển dụng sẽ thay đổi như thế nào và điều này ảnh hưởng ra sao đến tính khả thi của thử nghiệm lâm sàng?",
        diagram=DIAGRAM_SVGS[1],
        regulations=(
            "ICH M13A (2024) Mục 2.2.2: Cỡ mẫu tối thiểu cho thiết kế chéo không được ít hơn 12 đối tượng hoàn thành đánh giá.",
            "EMA Guideline (2010) Mục 4.1.4: Số lượng đối tượng phải dựa trên tính toán cỡ mẫu khoa học; tối thiểu 12 người.",
            "US FDA Statistical Approaches (2026) Mục II.C: Lực thống kê danh nghĩa tối thiểu khuyến cáo >= 80% cho cả Cmax và AUC.",
        ),
        equations=EQUATIONS_1,
        questions=(
            "1. Tại sao mối quan hệ giữa hệ số biến thiên nội cá thể CV và cỡ mẫu yêu cầu lại mang tính phi tuyến tính (cỡ mẫu tăng vọt khi CV vượt ngưỡng 30%)?",
            "2. Trong thiết kế chéo đôi 2x2, vì sao mức ý nghĩa thống kê của mỗi kiểm định một phía là alpha = 0.05 nhưng khoảng tin cậy tương ứng lại là 90% thay vì 95%?",
            "3. Hãy phân tích ưu và nhược điểm của Thiết kế thích ứng 2 giai đoạn (Adaptive Two-Stage Design theo Maurer/Potvin) so với thiết kế cố định cỡ mẫu ban đầu.",
        ),
        references=(
            "Schuirmann, D. J. (1987). A comparison of the two one-sided tests procedure and the power approach for assessing the equivalence of average bioavailability. Journal of Pharmacokinetics and Biopharmaceutics, 15(6), 657–680.",
            "Diletti, E., Hauschke, D., & Steinijans, V. W. (1991). Sample size determination for bioequivalence assessment by means of confidence intervals. International Journal of Clinical Pharmacology, Therapy, and Toxicology, 29(1), 1–8.",
            "Hauschke, D., Steinijans, V., & Pigeot, I. (2007). Bioequivalence Studies in Drug Development: Methods and Applications. John Wiley & Sons.",
        ),
    ),

    # -------------------------------------------------------------------------
    # BƯỚC 2: NGẪU NHIÊN HÓA VÀ LỊCH LẤY MẪU (RANDOMIZATION & SAMPLING)
    # -------------------------------------------------------------------------
    Lesson(
        interface=(
            "**Số lượng tuyển dụng:** Tổng số người tình nguyện khỏe mạnh được phân bổ vào các nhóm/trình tự (Sequence).",
            "**Khởi tạo ngẫu nhiên (Seed) và Kích thước khối (Block size):** Tham số kiểm soát tính tái lập và đảm bảo cân bằng số lượng đối tượng giữa các trình tự điều trị.",
            "**Lịch lấy mẫu máu lâm sàng:** Danh sách các thời điểm lấy mẫu dự kiến (giờ) để xuất bảng phân nhóm và kế hoạch lấy mẫu chi tiết.",
        ),
        actions=(
            "Nhập số lượng người tình nguyện, chọn kích thước block chẵn phù hợp và nhập giá trị seed (hoặc tạo seed ngẫu nhiên bảo mật).",
            "Chọn **Tạo danh sách phân nhóm**, rà soát sự phân bổ ngẫu nhiên giữa các trình tự (ví dụ TR vs RT).",
            "Nhập các mốc thời gian lấy mẫu (giờ) cách nhau bởi dấu phẩy, kết xuất và tải sổ tính Excel để làm cơ sở cho quy trình thao tác chuẩn (SOP) lấy mẫu lâm sàng.",
        ),
        theory=(
            "Phân bổ ngẫu nhiên theo khối (Block Randomization) triệt tiêu sai số lựa chọn (Selection bias) và các biến động môi trường theo thời gian, bảo đảm cân bằng tỷ lệ mẫu giữa các nhánh nghiên cứu.",
            "Lịch lấy mẫu máu phải được xây dựng dựa trên hồ sơ dược động học đã biết: tối thiểu 3–4 điểm trong pha hấp thu trước Tmax, các điểm dày đặc quanh Tmax dự kiến để bắt trúng Cmax, và kéo dài tối thiểu 3–5 lần thời gian bán thải (t1/2) để phần trăm ngoại suy AUC_%extrap ≤ 20%.",
        ),
        terms=(
            "Sequence: Trình tự dùng thuốc (ví dụ TR hoặc RT); Period: Kỳ nghiên cứu lâm sàng cách nhau bởi thời gian rửa giải (Washout period).",
            "Seed: Giá trị khởi tạo thuật toán sinh số giả ngẫu nhiên; Block: Khối phân nhóm cân bằng ngẫu nhiên.",
            "Carry-over Effect: Hiện tượng thuốc dùng ở kỳ trước còn tồn dư làm nhiễu nồng độ ở kỳ sau.",
            "Sampling Window: Cửa sổ thời gian cho phép chênh lệch quanh thời điểm lấy mẫu kế hoạch.",
        ),
        exercise="Phân biệt rõ bản chất thống kê và dược lý giữa ba yếu tố Treatment, Sequence và Period trong mô hình ANOVA chéo đôi 2×2, và giải thích vì sao hiện tượng thuốc tồn đọng (Carry-over effect) có thể làm sai lệch hoàn toàn kết luận về hiệu ứng điều trị?",
        diagram=DIAGRAM_SVGS[2],
        regulations=(
            "ICH M13A (2024) Mục 2.2.4 & 2.2.5: Thời gian lấy mẫu phải kéo dài đủ để AUC0-t bao phủ tối thiểu 80% AUC0-inf. Thời gian rửa giải phải >= 5 lần t1/2. Nồng độ trước liều kỳ 2 phải âm tính hoặc < 5% Cmax.",
            "EMA Guideline (2010) Mục 4.1.5: Nghiêm cấm gộp mẫu; mẫu máu phải lấy đúng cửa sổ thời gian (sampling window).",
            "US FDA (2021) Mục IV.B: Quy định xử lý đối tượng có nồng độ trước liều kỳ 2 (Pre-dose concentration).",
        ),
        equations=EQUATIONS_2,
        questions=(
            "1. Nếu một nghiên cứu có tỷ lệ diện tích ngoại suy AUC_%extrap > 20% ở hơn 30% số người tham gia, cơ quan quản lý sẽ đánh giá độ tin cậy của AUC0-inf như thế nào?",
            "2. Tại sao đối với các thuốc có thời gian bán thải rất dài (t1/2 > 24 giờ), ICH M13A và FDA cho phép cắt ngắn thời gian lấy mẫu tại thời điểm 72 giờ (AUC0-72h) trong thiết kế chéo mà không bắt buộc theo dõi đến 3 lần t1/2?",
        ),
        references=(
            "ICH M13A Guideline (2024). Section 2.2.4 (Sampling Times) & 2.2.5 (Washout Period).",
            "EMA (2010). Guideline on the Investigation of Bioequivalence, Section 4.1.5.",
            "Midha, K. K., et al. (1996). The preparation and reporting of bioequivalence protocols and reports. European Journal of Pharmaceutical Sciences, 4(4), 209–224.",
        ),
    ),

    # -------------------------------------------------------------------------
    # BƯỚC 3: NHẬP DỮ LIỆU NỒNG ĐỘ (CONCENTRATION INGESTION)
    # -------------------------------------------------------------------------
    Lesson(
        interface=(
            "**Tệp dữ liệu nồng độ (CSV/XLSX):** Bảng dữ liệu nồng độ hoạt chất đo được trong huyết tương từ phương pháp phân tích sắc ký sinh học (Bioanalytical assay).",
            "**Ánh xạ cột (Column Mapping):** Ghép nối các cột dữ liệu nguồn vào schema chuẩn hóa (subject_id, sequence, period, treatment, actual_time_h, concentration, blq_flag).",
            "**Kiểm tra cấu trúc và QC tiền phân tích:** Báo cáo các vi phạm về cấu trúc, định dạng số, thiếu trường thông tin hoặc trùng lặp mẫu.",
            "**Bảng duyệt dữ liệu đầy đủ:** Xem chi tiết toàn bộ các dòng nồng độ, hỗ trợ lọc theo đối tượng và kỳ điều trị.",
        ),
        actions=(
            "Chuẩn bị tệp dữ liệu tuân thủ schema; đảm bảo thời gian lấy mẫu là **thời gian thực tế (actual time)** tính từ thời điểm uống thuốc, không dùng thời gian danh nghĩa (nominal time).",
            "Tải tệp CSV/XLSX, cấu hình ánh xạ cột chính xác và xác nhận quy đổi đơn vị nồng độ (ví dụ μg/mL → ng/mL) nếu cần thiết.",
            "Bấm **Kiểm tra cấu trúc và QC**. Rà soát kỹ số lượng đối tượng, các lỗi theo dòng và bảng nồng độ tổng thể; sửa tệp nguồn và kiểm tra lại nếu phát hiện sai lệch.",
            "Khi danh sách phân nhóm đã khớp và kiểm tra đạt 100%, bấm **Nhập và lưu raw bất biến**.",
        ),
        theory=(
            "Tính toán dược động học NCA bắt buộc phải sử dụng thời gian lấy mẫu thực tế ghi nhận trong phiếu thu thập số liệu (CRF), vì chỉ sai lệch 5–10 phút quanh vùng Tmax cũng có thể làm sai lệch đáng kể ước tính Cmax và diện tích hình thang ban đầu.",
            "Dữ liệu thô (Raw Data) sau khi nhập được lưu trữ bất biến (Immutable storage) và gắn mã băm SHA-256 để đáp ứng nguyên tắc toàn vẹn ALCOA+ và ngăn chặn thao túng số liệu sau khi mở mù.",
        ),
        terms=(
            "LLOQ (Lower Limit of Quantification): Giới hạn định lượng dưới của phương pháp phân tích; BLQ: Dưới giới hạn định lượng.",
            "Column Mapping: Ánh xạ chuẩn hóa cột dữ liệu; Raw data: Dữ liệu thô nguyên bản không chỉnh sửa.",
            "SHA-256: Thuật toán hàm băm mật mã học tạo mã định danh duy nhất cho tập dữ liệu thô.",
            "Actual Time vs Nominal Time: Thời gian lấy mẫu thực tế so với thời gian danh nghĩa theo kế hoạch.",
        ),
        exercise="Theo quy định của ICH M13A và EMA, vì sao việc chuyển đổi đơn vị đo nồng độ và bảo toàn thời gian lấy mẫu thực tế (thay vì làm tròn theo thời gian kế hoạch) là yêu cầu bắt buộc trước khi tiến hành phân tích dược động học phi ngăn (NCA)?",
        diagram=DIAGRAM_SVGS[3],
        regulations=(
            "ICH M10 (2022): Bioanalytical Method Validation and Study Sample Analysis (Mục 7: LIMS, Raw Data, Run Logs).",
            "ICH M13A (2024) Mục 2.2.3: Bắt buộc dùng actual sampling time cho tính toán NCA.",
            "US FDA 21 CFR Part 11: Electronic Records; Electronic Signatures (Quy chuẩn bản ghi điện tử).",
            "WHO TRS 996 (2016): Guidance on good data and record management practices.",
        ),
        equations=EQUATIONS_3,
        questions=(
            "1. Tại sao việc thay thế các giá trị BLQ ở pha thải trừ cuối bằng LLOQ/2 hoặc 0 là sai lầm nghiêm trọng trong phân tích NCA và làm sai lệch ước tính lambda-z?",
            "2. Trình bày yêu cầu của FDA và EMA về việc lưu trữ sắc ký đồ thô (Raw Chromatograms) và nhật ký chạy máy LC-MS/MS khi nộp hồ sơ tương đương sinh học.",
        ),
        references=(
            "ICH Guideline M10 (2022). Bioanalytical Method Validation and Study Sample Analysis.",
            "US FDA (2018). Data Integrity and Compliance With Drug CGMP: Questions and Answers.",
            "WHO (2016). Annex 5: Guidance on good data and record management practices (TRS 996).",
        ),
    ),

    # -------------------------------------------------------------------------
    # BƯỚC 4: KIỂM SOÁT CHẤT LƯỢNG (QC & DATA FREEZE)
    # -------------------------------------------------------------------------
    Lesson(
        interface=(
            "**Bảng báo cáo QC:** Phát hiện và phân loại các lỗi chặn (Blockers) và cờ cảnh báo (Warnings) về tính hợp lệ của số liệu nồng độ.",
            "**Bảng chỉnh sửa mẫu có kiểm soát (Data Correction):** Cho phép sửa các trường cho phép theo sample_id khi có biên bản điều tra sai lệch đã được phê duyệt.",
            "**Quy trình giải trình & Khóa dữ liệu (Data Freeze):** Ghi nhận lý do sửa, người rà soát độc lập, bằng chứng; niêm phong cơ sở dữ liệu và SAP trước phân tích.",
        ),
        actions=(
            "Chọn **Kiểm tra / cập nhật QC**, đọc kỹ từng thông báo lỗi chặn và cảnh báo chất lượng.",
            "Nếu cần sửa dữ liệu do nhầm lẫn nhập liệu hoặc mẫu đo lại được phê duyệt, điền đầy đủ: *Lý do sửa*, *Nghiên cứu viên rà soát độc lập*, và *Tài liệu bằng chứng*, sau đó bấm **Áp dụng các sửa đổi**.",
            "Chạy lại QC; khi đạt trạng thái sạch hoàn toàn và không còn bản nháp chưa áp dụng, bấm **Data Freeze và khóa SAP**.",
        ),
        theory=(
            "Kiểm soát chất lượng (QC) trước khi mở mù và phân tích thống kê giúp phát hiện kịp thời các mẫu nồng độ bất thường (ví dụ: mẫu trước liều Cpredose > 5% Cmax, nồng độ âm, mẫu thiếu không rõ lý do) để xử lý theo đúng quy định định trước trong SAP.",
            "Khóa dữ liệu (Data Freeze) tạo ranh giới bảo mật tuyệt đối giữa dữ liệu đầu vào đã được phê duyệt và snapshot kết quả tính toán; mọi chỉnh sửa sau thời điểm này đều bị ghi nhận dấu vết và làm vô hiệu hóa kết quả cũ (đánh dấu STALE).",
        ),
        terms=(
            "QC (Quality Control): Kiểm soát chất lượng dữ liệu; Data correction: Hiệu chỉnh số liệu có lý do và bằng chứng kiểm chứng.",
            "Data Freeze / Data Lock: Đóng băng dữ liệu; STALE: Trạng thái kết quả không còn tương thích với dữ liệu đầu vào hiện hành.",
            "Pre-dose Outlier: Nồng độ trước liều vượt quá 5% Cmax dẫn đến loại trừ kỳ nghiên cứu.",
            "Re-assay SOP: Quy trình thao tác chuẩn phân tích lại mẫu theo quy định sinh học.",
        ),
        exercise="Nếu một mẫu nồng độ bị hiệu chỉnh sau khi đã chạy phân tích thống kê và xuất báo cáo dự thảo, các quy định về Data Integrity và quản lý phiên bản (Revision Control) yêu cầu hệ thống và nghiên cứu viên phải thực hiện những bước gì trước khi công bố kết quả mới?",
        diagram=DIAGRAM_SVGS[4],
        regulations=(
            "ICH M13A (2024) Mục 2.2.4: Tiêu chuẩn loại trừ đối tượng có Cpredose > 5% Cmax.",
            "EMA Guideline (2010) Mục 4.1.8 & 4.2: Nghiêm cấm loại bỏ mẫu ngoại lai PK nếu không có bằng chứng sai sót lâm sàng hoặc phân tích sinh học được chứng minh trước mở mù.",
            "US FDA (2001/2026): Guidance on Statistical Approaches - Xử lý dữ liệu bất thường và khóa dữ liệu.",
        ),
        equations=EQUATIONS_4,
        questions=(
            "1. Tại sao các cơ quan quản lý (US FDA, EMA, WHO) nghiêm cấm việc loại bỏ một đối tượng ra khỏi phân tích BE chỉ với lý do đối tượng đó là 'ngoại lai thống kê' (Statistical outlier)?",
            "2. Hãy thiết kế quy trình thao tác chuẩn (SOP) cho việc điều tra mẫu nồng độ bất thường đáp ứng đầy đủ yêu cầu của ICH M10 và FDA 21 CFR Part 11.",
        ),
        references=(
            "ICH Guideline M10 (2022). Bioanalytical Method Validation, Section 7.2 (Reanalysis of Study Samples).",
            "EMA (2010). Guideline on the Investigation of Bioequivalence, Section 4.1.8 (Removal of data).",
            "US FDA (2018). Data Integrity in Clinical Trials and CGMP.",
        ),
    ),

    # -------------------------------------------------------------------------
    # BƯỚC 5: PHÂN TÍCH NCA (NONCOMPARTMENTAL ANALYSIS)
    # -------------------------------------------------------------------------
    Lesson(
        interface=(
            "**Cấu hình NCA:** Quy tắc tích phân diện tích (Linear Up / Log Down), tiêu chí lựa chọn pha thải trừ cuối (λz), và chính sách xử lý ngoại suy.",
            "**Bảng rà soát pha thải trừ terminal:** Đánh giá số điểm hồi quy, khoảng thời gian bắt đầu/kết thúc, và độ phù hợp R², R²_adj cho từng hồ sơ.",
            "**Bảng kết quả thông số PK:** Hiển thị chi tiết Cmax, Tmax, AUClast, AUCinf, t1/2, λz, AUC_%extrap, MRT kèm chức năng xuất sổ tính Excel.",
        ),
        actions=(
            "Rà soát cấu hình tích phân và tiêu chí pha thải trừ theo đúng SAP đã phê duyệt trước khi khóa dữ liệu.",
            "Đánh giá các điểm nồng độ ở pha cuối; chỉ can thiệp ghi đè khoảng hồi quy (Terminal Override) khi có căn cứ dược động học rõ ràng và được ghi nhận giải trình.",
            "Bấm **Phân tích NCA và BE** trên dữ liệu đã Data Freeze; kiểm tra các cờ cảnh báo (đặc biệt các hồ sơ có AUC_%extrap > 20% hoặc R² < 0.85).",
        ),
        theory=(
            "Quy tắc tích phân hình thang tuyến tính đi lên - logarit đi xuống (Linear Trapezoidal up / Log Trapezoidal down) giảm thiểu tối đa sai số hệ thống khi tính diện tích dưới đường cong nồng độ–thời gian.",
            "Diện tích dưới đường cong ngoại suy đến vô cùng được tính theo công thức: AUC_inf = AUC_last + C_last / λz (với C_last là nồng độ định lượng được cuối cùng, λz là hằng số tốc độ thải trừ ước tính từ độ dốc hồi quy tuyến tính của ln(C) theo thời gian). Thời gian bán thải tính bằng t1/2 = ln(2)/λz.",
            "Lựa chọn pha thải trừ cuối không phù hợp (ví dụ bao gồm cả pha phân bố hoặc các điểm nồng độ dao động ngẫu nhiên gần LLOQ) sẽ làm sai lệch nghiêm trọng λz, dẫn đến ước tính sai lệch AUC_inf và thể tích phân bố.",
        ),
        terms=(
            "NCA (Noncompartmental Analysis): Phân tích dược động học phi ngăn; λz: Hằng số tốc độ thải trừ pha cuối.",
            "AUC (Area Under the Curve): Diện tích dưới đường cong; Extrapolation: Phần trăm diện tích ngoại suy đến vô cùng (AUC_%extrap).",
            "Lin-Up / Log-Down: Quy tắc tích phân hình thang tuyến tính khi nồng độ tăng và logarit khi nồng độ giảm.",
            "MRT (Mean Residence Time): Thời gian lưu trú trung bình của phân tử thuốc trong cơ thể.",
        ),
        exercise="Tại sao việc chỉ có 3 điểm nồng độ ở pha cuối thỏa mãn điều kiện toán học hồi quy tuyến tính vẫn chưa đủ để đảm bảo ước tính hằng số thải trừ λz và diện tích AUC_inf là đáng tin cậy về mặt dược động học?",
        diagram=DIAGRAM_SVGS[5],
        regulations=(
            "ICH M13A (2024) Mục 2.2.3: Bắt buộc đánh giá Cmax và AUC0-t. AUC0-inf là thông số hỗ trợ.",
            "EMA Guideline (2010) Mục 4.1.8: Yêu cầu tính toán AUC0-t, Cmax; với thuốc có t1/2 dài có thể dùng AUC0-72h.",
            "US FDA (2021) Mục IV.A: Yêu cầu báo cáo đầy đủ AUC0-t, AUC0-inf, Cmax, Tmax, lambda_z, t1/2.",
        ),
        equations=EQUATIONS_5,
        questions=(
            "1. Hãy chứng minh bằng khai triển chuỗi Taylor rằng khi tỷ số C_i / C_{i+1} tiến dần tới 1, công thức hình thang logarit hội tụ về công thức hình thang tuyến tính.",
            "2. Tại sao việc chọn các điểm nồng độ trong pha phân bố (distribution phase) để hồi quy lambda-z sẽ dẫn đến ước tính sai lệch nghiêm trọng cả t1/2 và AUC0-inf?",
        ),
        references=(
            "Gabrielsson, J., & Weiner, D. (2016). Pharmacokinetic and Pharmacodynamic Data Analysis: Concepts and Applications (5th ed.). Swedish Pharmaceutical Press.",
            "Yeh, K. C., & Kwan, K. C. (1978). A comparison of numerical integrating algorithms by trapezoidal, Lagrange, and spline approximation. Journal of Pharmacokinetics and Biopharmaceutics, 6(1), 79–98.",
            "Gibaldi, M., & Perrier, D. (1982). Pharmacokinetics (2nd ed.). Marcel Dekker, New York.",
        ),
    ),

    # -------------------------------------------------------------------------
    # BƯỚC 6: THỐNG KÊ BE — EMA / FDA (BE STATISTICAL TESTING)
    # -------------------------------------------------------------------------
    Lesson(
        interface=(
            "**Bảng kết quả BE của nghiên cứu:** Hiển thị Tỷ số trung bình nhân (GMR %), Khoảng tin cậy 90% CI, Giới hạn chấp nhận quy chuẩn và Kết luận đánh giá (PASS / FAIL / NOT EVALUABLE).",
            "**Bảng phân tích phương sai ANOVA & Mô hình tuyến tính:** Chi tiết ước tính các hiệu ứng cố định (Sequence, Period, Treatment), hiệu ứng ngẫu nhiên Subject(Sequence), phương sai nội cá thể swR², swT² và hệ số biến thiên CV_intra.",
            "**Bảng phân tích PK độc lập:** Hỗ trợ nhập và phân tích bảng thông số PK có sẵn phục vụ đối chiếu hoặc phân tích mở rộng cho các thiết kế lặp, thuốc HVDP và NTI.",
        ),
        actions=(
            "Đối chiếu quy tắc pháp lý (ICH M13A, EMA, FDA), thiết kế nghiên cứu và danh mục các endpoint chính (AUC_last, AUC_inf, Cmax).",
            "Rà soát bảng tóm tắt: Kiểm tra xem khoảng tin cậy 90% CI có nằm trọn trong khoảng quy chuẩn [80.00% - 125.00%] (với ABE) hay thỏa mãn tiêu chí scaling UCB và GMR constraint (với RSABE/ABEL).",
            "Đọc kỹ nguyên nhân khi hệ thống báo `NOT EVALUABLE` để nhận diện các điều kiện tiền đề về dữ liệu hoặc thẩm định phương pháp chưa được thỏa mãn.",
        ),
        theory=(
            "Phân tích BE dựa trên giả định các thông số dược động học phơi nhiễm (AUC, Cmax) tuân theo phân bố log-chuẩn (Log-normal distribution). Mô hình tuyến tính áp dụng trên dữ liệu biến đổi ln(PK): ln(Y_ijk) = μ + S_i + P_j + T_k + Subj(S)_l(i) + ε_ijk.",
            "Tỷ số trung bình nhân được tính bằng: GMR = exp(Y_bar_T - Y_bar_R) × 100%. Khoảng tin cậy 90% đối xứng trên thang logarit tương đương với hai kiểm định một phía của Schuirmann ở mức ý nghĩa α = 0.05.",
            "Đối với thuốc có độ biến thiên cao (HVDP), EMA cho phép mở rộng biên Cmax (ABEL) khi CV_wR > 30% kèm giới hạn trần 69.84%–143.19% và ràng buộc GMR điểm; trong khi FDA áp dụng tiêu chí chuẩn hóa RSABE dựa trên cận trên khoảng tin cậy 95% UCB ≤ 0 và ràng buộc điểm GMR ∈ [0.80 - 1.25].",
        ),
        terms=(
            "ABE (Average Bioequivalence): Tương đương sinh học trung bình chuẩn; ABEL: ABE mở rộng biên theo độ biến thiên thuốc đối chứng.",
            "RSABE (Reference-Scaled Average Bioequivalence): ABE chuẩn hóa theo phương sai đối chứng; UCB (Upper Confidence Bound): Cận trên khoảng tin cậy 95%; sWR: Độ lệch chuẩn log nội cá thể của R.",
            "HVDP (Highly Variable Drug Products): Thuốc có độ biến thiên nội cá thể CVwR >= 30%.",
            "NTI (Narrow Therapeutic Index): Thuốc có khoảng điều trị hẹp yêu cầu thu hẹp biên BE (ví dụ 90.00 - 111.11%).",
        ),
        exercise="Tại sao trong đánh giá tương đương sinh học cho thuốc biến thiên cao theo tiêu chuẩn FDA RSABE, việc chỉ kiểm tra khoảng tin cậy 90% CI thông thường nằm trong 80,00–125,00% là không đủ và không phản ánh đúng tiêu chí quyết định pháp lý của cơ quan quản lý?",
        diagram=DIAGRAM_SVGS[6],
        regulations=(
            "ICH M13A (2024) Mục 2.2.3: Khoảng chấp nhận chuẩn 80.00% - 125.00% cho cả Cmax và AUC.",
            "EMA Guideline (2010) Mục 4.1.10 (ABEL cho HVDP) và Mục 4.1.9 (Thuốc NTI: 90.00% - 111.11%).",
            "US FDA Guidance (2026): Statistical Approaches to Establishing Bioequivalence (Tiêu chuẩn RSABE & NTI).",
        ),
        equations=EQUATIONS_6,
        questions=(
            "1. So sánh sự khác nhau căn bản về triết lý quản lý và thuật toán thống kê giữa EMA ABEL và US FDA RSABE đối với thuốc có độ biến thiên cao (HVDP).",
            "2. Tại sao FDA yêu cầu kiểm định thêm tỷ số độ lệch chuẩn nội cá thể sWT/sWR <= 2.50 đối với thuốc có khoảng điều trị hẹp (NTI)?",
        ),
        references=(
            "Chow, S. C., & Liu, J. P. (2008). Design and Analysis of Bioavailability and Bioequivalence Studies (3rd ed.).",
            "Tothfalusi, L., & Endrenyi, L. (2012). Sample sizes for designing bioequivalence studies for highly variable drugs. Journal of Pharmacy & Pharmaceutical Sciences, 15(1), 73–84.",
            "Haidar, V. H., et al. (2008). Bioequivalence approaches for highly variable drugs and drug products. Pharmaceutical Research, 25(1), 237–241.",
        ),
    ),

    # -------------------------------------------------------------------------
    # BƯỚC 7: ĐỒ THỊ VÀ CHẨN ĐOÁN (PLOTS & DIAGNOSTICS)
    # -------------------------------------------------------------------------
    Lesson(
        interface=(
            "**Đồ thị nồng độ cá thể & Thang đo:** Xem đường cong nồng độ–thời gian của từng đối tượng qua các kỳ dùng thuốc; chuyển đổi linh hoạt giữa thang đo tuyến tính và thang bán logarit.",
            "**Đồ thị nồng độ trung bình (Mean ± SD):** So sánh xu hướng phơi nhiễm tổng thể giữa Thuốc thử T và Thuốc đối chứng R.",
            "**Forest plot & Biểu đồ tiêu chí kiểm định:** Trực quan hóa ước tính điểm GMR, khoảng tin cậy 90% CI so với các ngưỡng chấp nhận của từng endpoint.",
        ),
        actions=(
            "Chọn từng đối tượng nghiên cứu để rà soát profile cá thể trên cả thang đo tuyến tính và bán logarit.",
            "Bật thang đo bán logarit để kiểm tra độ dốc của pha thải trừ cuối; so sánh hình thái đường cong thực nghiệm với kết quả hồi quy λz trong NCA.",
            "Đọc đồ thị Forest plot và các biểu đồ tiêu chí kiểm định; đặc biệt lưu ý trạng thái của snapshot (đảm bảo kết quả là CURRENT).",
        ),
        theory=(
            "Đồ thị nồng độ–thời gian là công cụ chẩn đoán quan trọng giúp nhận diện các bất thường dược động học cá thể: hấp thu hai đỉnh (double peak), hấp thu trễ bất thường, hiện tượng trào ngược hoặc sai sót hoán đổi mẫu sinh học (Sample mislabeling).",
            "Forest plot biểu diễn ước lượng điểm GMR và khoảng tin cậy 90% CI so sánh trực quan với ranh giới quyết định. Với FDA RSABE, Forest plot chỉ mang tính bổ trợ; quyết định bắt buộc phải căn cứ trên giá trị số học của tiêu chí UCB.",
        ),
        terms=(
            "Semilog (Semi-logarithmic plot): Đồ thị bán logarit với trục tung nồng độ theo thang log; SD: Độ lệch chuẩn.",
            "Forest plot: Biểu đồ biểu diễn ước tính điểm và khoảng tin cậy; Endpoint: Chỉ tiêu đánh giá dược động học cốt lõi.",
            "Double Peak: Hiện tượng đường cong nồng độ xuất hiện hai đỉnh hấp thu do nhu động dạ dày hoặc tái tuần hoàn gan ruột.",
            "Studentized Residual: Phần dư chuẩn hóa phục vụ kiểm tra giả định phân bố chuẩn của ANOVA.",
        ),
        exercise="Trong quá trình thẩm định dữ liệu nghiên cứu BE, khi nào nghiên cứu sinh cần ưu tiên sử dụng đồ thị bán logarit thay cho đồ thị tuyến tính để phát hiện các bất thường trong pha phân bố và pha thải trừ cuối của thuốc?",
        diagram=DIAGRAM_SVGS[7],
        regulations=(
            "ICH M13A (2024) Mục 2.2.3: Bắt buộc đính kèm đồ thị nồng độ cá thể trên cả thang tuyến tính và bán logarit.",
            "EMA Guideline (2010) Phụ lục IV: Quy định trình bày đồ thị Mean và Individual PK profiles.",
            "US FDA (2021) Mục IV.C: Yêu cầu Forest plot và biểu đồ chẩn đoán phần dư ANOVA.",
        ),
        equations=EQUATIONS_7,
        questions=(
            "1. Khi quan sát đồ thị bán logarit của một cá thể, nếu pha thải trừ xuất hiện hai đoạn thẳng có độ dốc khác nhau rõ rệt, điều này phản ánh cơ chế dược động học gì?",
            "2. Tại sao Forest plot là công cụ trực quan hóa hữu ích nhưng không thể thay thế cho việc kiểm tra giá trị số học của tiêu chí UCB trong FDA RSABE?",
        ),
        references=(
            "Rowland, M., & Tozer, T. N. (2011). Clinical Pharmacokinetics and Pharmacodynamics: Concepts and Applications (4th ed.).",
            "Montgomery, D. C. (2017). Design and Analysis of Experiments (9th ed.). John Wiley & Sons.",
        ),
    ),

    # -------------------------------------------------------------------------
    # BƯỚC 8: BÁO CÁO CTD / XUẤT DỮ LIỆU (REPORTING & CTD ARCHIVING)
    # -------------------------------------------------------------------------
    Lesson(
        interface=(
            "**Mô-đun Đề cương nghiên cứu (Protocol Module):** Khai báo chi tiết 11 nhóm nội dung chuyên sâu (thiết kế, tiêu chuẩn chọn/loại, lịch lấy mẫu, kế hoạch SAP, an toàn, đạo đức và vận hành) để xuất đề cương Word (.docx) và PDF trước khi triển khai lâm sàng.",
            "**Báo cáo tổng kết nghiên cứu (CSR / CTD Module 5.3.1.2):** Tạo báo cáo nghiên cứu tương đương sinh học dự thảo theo cấu trúc ICH E3/M13A bằng tiếng Việt hoặc tiếng Anh.",
            "**Gói lưu trữ dự án hoàn chỉnh (Project Archive .bewf.zip):** Đóng gói toàn vẹn dữ liệu thô, cấu hình, nhật ký kiểm toán và kết quả phân tích.",
            "**Bảng kê tệp & siêu dữ liệu (Analysis Datasets & Manifest):** Kết xuất bộ dữ liệu phân tích dạng bảng kèm mã băm SHA-256 chứng thực số học.",
        ),
        actions=(
            "Hoàn thiện khai báo nghiên cứu tại trang Tổng quan; tại đây rà soát 11 nhóm ghi chú chuyên môn và bấm **Tạo đề cương Word và PDF**.",
            "Tải đề cương nghiên cứu, kiểm tra các trường thông tin được đánh dấu `[CẦN BỔ SUNG / XÁC NHẬN]` và hoàn thiện hồ sơ trước khi trình Hội đồng Đạo đức phê duyệt.",
            "Xác nhận kết quả phân tích đang ở trạng thái `CURRENT` và không có chỉnh sửa dữ liệu đang chờ xử lý (Pending edits) trước khi tạo báo cáo kết quả.",
            "Chọn ngôn ngữ (tiếng Việt báo cáo nội bộ / tiếng Anh hồ sơ dự thảo), bấm tạo báo cáo Word/PDF và xuất bộ dữ liệu kèm Manifest.",
        ),
        theory=(
            "Đề cương nghiên cứu (Protocol) là văn bản pháp lý bắt buộc phải được phê duyệt trước khi thu nhận người tình nguyện; mọi giả định về cỡ mẫu, phương pháp thống kê và tiêu chí loại trừ đều phải được định trước (Pre-specified).",
            "Báo cáo nghiên cứu lâm sàng (CSR) theo định dạng hồ sơ kỹ thuật chung (CTD Module 5) đòi hỏi tính nhất quán tuyệt đối giữa dữ liệu thô, kết quả tính toán NCA, bảng thống kê ANOVA và các kết luận khoa học.",
            "Mã băm SHA-256 và Bảng kê Manifest tạo lập chuỗi chứng thực số học (Cryptographic audit trail), đảm bảo các tệp báo cáo kết xuất liên kết bất biến với đúng snapshot dữ liệu đã được niêm phong (Data Freeze).",
        ),
        terms=(
            "Protocol: Đề cương nghiên cứu lâm sàng; SAP: Kế hoạch phân tích thống kê (Statistical Analysis Plan); Amendment: Sửa đổi đề cương có quản lý phiên bản.",
            "CTD: Hồ sơ kỹ thuật chung (Common Technical Document); CSR: Báo cáo nghiên cứu lâm sàng (Clinical Study Report).",
            "Manifest: Danh mục tệp và siêu dữ liệu chứng thực số; Artifact: Tệp hiện vật kết xuất từ hệ thống.",
            "CDISC (Clinical Data Interchange Standards Consortium): Chuẩn cấu trúc dữ liệu lâm sàng quốc tế (SDTM/ADaM).",
        ),
        exercise="Hãy phân tích sự khác biệt căn bản về mặt pháp lý, thời điểm ban hành, cấu trúc nội dung và thẩm quyền phê duyệt giữa Đề cương nghiên cứu (Clinical Study Protocol) và Báo cáo tổng kết nghiên cứu tương đương sinh học (Clinical Study Report - CSR)?",
        diagram=DIAGRAM_SVGS[8],
        regulations=(
            "ICH E3 (1995): Structure and Content of Clinical Study Reports.",
            "ICH M13A (2024) Phụ lục Báo cáo: Yêu cầu cấu trúc báo cáo nghiên cứu tương đương sinh học.",
            "CTD Module 5 (ICH M4E): Clinical Study Reports for Registration of Pharmaceuticals for Human Use.",
        ),
        equations=EQUATIONS_8,
        questions=(
            "1. Phân biệt rõ sự khác nhau giữa Đề cương nghiên cứu (Protocol) và Báo cáo tổng kết nghiên cứu (CSR) về thời điểm chốt văn bản và thẩm quyền phê duyệt.",
            "2. Trong thẩm định hồ sơ đăng ký thuốc, nếu phát hiện một con số trong bảng tóm tắt kết quả BE không khớp với bảng ANOVA phụ lục do làm tròn, chuyên viên sẽ xử lý như thế nào?",
        ),
        references=(
            "ICH Harmonised Guideline E3 (1995). Structure and Content of Clinical Study Reports.",
            "ICH M4E(R2) (2016). Common Technical Document for the Registration of Pharmaceuticals for Human Use — Efficacy.",
            "CDISC (2021). Analysis Data Model (ADaM) for Pharmacokinetics (ADNCA).",
        ),
    ),

    # -------------------------------------------------------------------------
    # BƯỚC 9: NHẬT KÝ KIỂM TOÁN / QUẢN TRỊ (AUDIT TRAIL & GOVERNANCE)
    # -------------------------------------------------------------------------
    Lesson(
        interface=(
            "**Nhật ký sự kiện kiểm toán (Audit Trail Log):** Bảng ghi nhận tuần tự thời gian mọi tác vụ (Khởi tạo dự án, Nhập dữ liệu, Hiệu chỉnh mẫu QC, Khóa Data Freeze, Chạy phân tích, Xuất báo cáo).",
            "**Bảng chỉ số vận hành & Quản lý phiên bản:** Giám sát các mốc checkpoint cơ sở dữ liệu (db_revision) và phiên bản làm việc hiện hành (working_revision).",
        ),
        actions=(
            "Dò theo chuỗi sự kiện kiểm toán từ thời điểm khởi tạo dự án, nhập dữ liệu raw, các lần sửa mẫu, mốc khóa dữ liệu đến các lần chạy phân tích.",
            "Đối chiếu lý do sửa mẫu (Correction reason) và nghiên cứu viên rà soát độc lập đối với từng thao tác thay đổi số liệu.",
            "Kiểm tra tính liên tục và toàn vẹn của các mốc thời gian (Timestamps); giải trình các bất thường (nếu có) trước khi hoàn tất hồ sơ luận án hoặc nộp cơ quan quản lý.",
        ),
        theory=(
            "Dấu vết kiểm toán (Audit Trail) là tiêu chuẩn bắt buộc theo nguyên tắc Thực hành lâm sàng tốt (GCP), hướng dẫn Data Integrity của WHO và FDA 21 CFR Part 11. Hệ thống phải ghi nhận tự động, chính xác: *Ai đã làm gì, vào thời điểm nào, giá trị ban đầu là gì, giá trị mới là gì và lý do thay đổi là gì*.",
            "Ứng dụng vận hành ở chế độ đơn người dùng (Local single-user), do đó việc hiểu rõ ranh giới kiểm soát giúp nghiên cứu sinh nhận thức đầy đủ các yêu cầu bổ sung khi triển khai trên các hệ thống điện tử lâm sàng thương mại có xác thực người dùng và chữ ký điện tử số.",
        ),
        terms=(
            "Audit trail: Dấu vết kiểm toán ghi nhận lịch sử thao tác hệ thống không thể xóa hoặc sửa đổi.",
            "Revision: Phiên bản thay đổi dữ liệu; Checkpoint: Điểm lưu an toàn trong cơ sở dữ liệu; Journal: Nhật ký theo dõi trạng thái.",
            "Timestamp: Mốc thời gian tạo lập tự động từ đồng hồ hệ thống an toàn.",
            "21 CFR Part 11: Quy chuẩn liên bang Hoa Kỳ về bản ghi điện tử và chữ ký điện tử.",
            "Attributability: Tính quy trách nhiệm (xác định rõ ai là người thực hiện hành động).",
        ),
        exercise="Trong quá trình thanh tra của Cơ quan Quản lý Dược đối với cơ sở thử nghiệm tương đương sinh học, những dấu hiệu bất thường nào trong nhật ký Audit Trail (ví dụ: khoảng trống thời gian không thể giải trình, thao tác chỉnh sửa số liệu tập trung ngay trước thời điểm Data Freeze) sẽ bị xem là vi phạm nghiêm trọng (Critical Deficiency) về tính toàn vẹn dữ liệu?",
        diagram=DIAGRAM_SVGS[9],
        regulations=(
            "US FDA 21 CFR Part 11 (1997): Electronic Records; Electronic Signatures.",
            "EMA (2011): EudraLex Volume 4, Annex 11 - Computerised Systems.",
            "WHO TRS 996 (2016): Guidance on good data and record management practices.",
            "PIC/S (2021): PI 041-1 Good Practices for Data Management and Integrity in Regulated GMP/GDP Environments.",
        ),
        equations=EQUATIONS_9,
        questions=(
            "1. Khi thanh tra viên của US FDA hoặc Cục Quản lý Dược kiểm tra cơ sở thử nghiệm BE, những dấu hiệu nào trong Audit Trail sẽ bị coi là vi phạm nghiêm trọng (Critical Deficiency)?",
            "2. Phân tích sự khác biệt về mặt pháp lý và công nghệ giữa một nhật ký hệ thống đơn thuần (System Log) và một Dấu vết kiểm toán đạt chuẩn GxP (GxP Compliant Audit Trail).",
        ),
        references=(
            "US FDA (2003). Guidance for Industry - Part 11, Electronic Records; Electronic Signatures — Scope and Application.",
            "EMA (2020). Guideline on computerised systems and electronic data in clinical trials.",
            "PIC/S (2021). Good practices for data management and integrity in regulated GMP/GDP environments (PI 041-1).",
        ),
    ),
)


# -----------------------------------------------------------------------------
# PHÂN TÍCH PK ĐỘC LẬP (STANDALONE PHARMACOKINETICS - LESSON 10)
# -----------------------------------------------------------------------------
PK_STANDALONE_LESSON = Lesson(
    interface=(
        "**Chế độ dùng thuốc:** Lựa chọn Đơn liều (Single dose), Đa liều (Multiple dose) hoặc Trạng thái ổn định (Steady-state); khai báo khoảng cách liều τ (giờ) và số liều thực tế.",
        "**Đường dùng thuốc:** Uống (Oral), Tiêm tĩnh mạch trực tiếp (IV Bolus), hoặc Truyền tĩnh mạch liên tục (IV Infusion kèm thời gian truyền Tinf).",
        "**Phương pháp phân tích:** Phân tích phi ngăn (NCA) hoặc Mô hình hóa ngăn (Compartmental Modeling: 1 ngăn hoặc 2 ngăn đường uống/IV).",
        "**Kết quả và Đồ thị:** Bảng thông số PK toàn diện (Cmax, Tmax, AUC, AUMC, t1/2, CL, Vd, MRT), tiêu chí lựa chọn mô hình AIC/BIC và đồ thị khớp thực nghiệm kèm bảng dư.",
    ),
    actions=(
        "Chuẩn bị tệp dữ liệu CSV/XLSX dạng dài (long format: mỗi dòng một mẫu) hoặc dạng rộng (wide format: mỗi cột một đối tượng); đơn vị thời gian tính từ lúc dùng liều (giờ).",
        "Chọn chế độ liều và đường dùng thuốc; nhập giá trị liều dùng (Dose) và khoảng cách liều (τ) nếu phân tích đa liều hoặc trạng thái ổn định.",
        "Chọn phương pháp phân tích (NCA hoặc Mô hình ngăn); cấu hình trọng số hồi quy phi tuyến (w = 1, 1/Y, hoặc 1/Y²).",
        "Nhấn **Chạy phân tích PK**; rà soát bảng thông số và đồ thị phần dư; so sánh giá trị AICc giữa các mô hình để chọn mô hình tối ưu.",
    ),
    theory=(
        "**Tổng quan Lý thuyết Dược động học Ngăn (Compartmental Modeling Foundations):** Cơ thể được mô hình hóa như một hệ thống gồm một hoặc nhiều khoang (ngăn) đồng nhất, hòa lẫn tức thời. Động học được giả định là tuyến tính (Linear Pharmacokinetics), tuân theo nguyên lý cộng tác dụng (Superposition Principle) và các quá trình phân bố, thải trừ tuân theo động học bậc 1.",
        "**1. ĐƯỜNG TIÊM TĨNH MẠCH NHANH (IV BOLUS):**\n"
        "- *1 Ngăn IV Bolus:* Toàn bộ liều D nạp tức thời vào ngăn trung tâm tại t=0 (F=1). Nồng độ suy giảm hàm mũ đơn điệu C(t) = C₀·e^(-k₁₀t) với C₀ = D/V₁. Độ thanh thải CL = k₁₀·V₁ = D/AUC₀-∞; thời gian bán thải t½ = 0.693/k₁₀. Đồ thị bán logarit là một đường thẳng duy nhất dốc âm -k₁₀. Ví dụ: Aminoglycoside (gentamicin), D = 500 mg, V₁ = 25 L, k₁₀ = 0.10 h⁻¹ ⇒ C₀ = 20 mg/L, CL = 2.5 L/h, t½ = 6.93 h, AUC = 200 mg·h/L.\n"
        "- *2 Ngăn IV Bolus:* Thuốc phân bố thuận nghịch giữa ngăn trung tâm V₁ và ngăn ngoại vi V₂ qua k₁₂ và k₂₁, thải trừ từ V₁ qua k₁₀. Nghiệm biexponential C(t) = A·e^(-αt) + B·e^(-βt) với C₀ = A+B = D/V₁. Pha α phản ánh phân bố nhanh, pha β phản ánh thải trừ chậm. Thể tích trạng thái ổn định Vss = V₁(1 + k₁₂/k₂₁); thể tích theo diện tích Vβ = CL/β (thứ bậc Vc < Vss < Vβ); thanh thải liên ngăn Q = k₁₂·V₁ = k₂₁·V₂. Ví dụ: Vancomycin, D = 1000 mg, V₁ = 20 L, k₁₀ = 0.15 h⁻¹, k₁₂ = 0.25 h⁻¹, k₂₁ = 0.10 h⁻¹ ⇒ α = 0.468 h⁻¹ (t½,α = 1.48 h), β = 0.032 h⁻¹ (t½,β = 21.6 h), Vss = 70 L, CL = 3 L/h, AUC = 403.8 mg·h/L.\n"
        "- *3 Ngăn IV Bolus:* Thuốc phân bố vào ngăn ngoại vi nông V₂ (mô cơ, k₁₂/k₂₁) và ngăn ngoại vi sâu V₃ (mô mỡ, xương, k₁₃/k₃₁). Nghiệm triexponential C(t) = A·e^(-αt) + B·e^(-βt) + C·e^(-γt) với α > β > γ. Pha α (vài phút), pha β (vài giờ) và pha γ (hàng chục đến hàng trăm giờ). Thể tích Vss = V₁ + V₂ + V₃. Ví dụ: Fentanyl 100 µg (0.1 mg) tiêm IV ⇒ V₁ = 12 L, V₂ = 30 L, V₃ = 250 L (Vss = 292 L), CL = 45 L/h; tác dụng dứt nhanh do tái phân bố từ não (V₁) sang mô mỡ (V₃), nhưng khi tiêm nhắc lại nhiều lần thuốc tích lũy sâu trong V₃ gây thức tỉnh chậm.",
        "**2. ĐƯỜNG TRUYỀN TĨNH MẠCH LIÊN TỤC (IV INFUSION):**\n"
        "- *1 Ngăn IV Infusion:* Thuốc đưa vào ngăn trung tâm với tốc độ không đổi bậc 0 R₀ = D/Tinf trong khoảng thời gian truyền Tinf (F=1). Trong lúc truyền (t ≤ Tinf): C(t) = (R₀/CL)(1 - e^(-k₁₀t)). Sau khi ngừng truyền (t > Tinf): C(t) = C(Tinf)·e^(-k₁₀(t - Tinf)). Nồng độ ổn định Css = R₀/CL; thời gian lưu trú trung bình MRTinf = 1/k₁₀ + Tinf/2. Ví dụ: Truyền kháng sinh liều 1000 mg trong Tinf = 2 h (R₀ = 500 mg/h), CL = 5 L/h, V₁ = 20 L ⇒ Css = 100 mg/L; tại 2 h ngừng truyền đạt C(2) = 39.35 mg/L; sau 4 h nồng độ còn C(4) = 23.87 mg/L.\n"
        "- *2 Ngăn IV Infusion:* Nạp R₀ vào ngăn 1, đồng thời phân bố sang ngăn 2 và thải trừ khỏi ngăn 1. Trong lúc truyền nồng độ tăng uốn lượn; sau ngừng truyền nồng độ suy giảm 2 pha (α và β). Khuyến cáo TDM: Mẫu nồng độ đỉnh không được lấy ngay khi vừa rút kim mà phải chờ ít nhất 1–2 giờ để pha phân bố mô α kết thúc. Ví dụ: Vancomycin 1000 mg truyền trong 1 h, CL = 3 L/h, V₁ = 15 L, V₂ = 30 L ⇒ Cpeak ≈ 42 mg/L, Ctrough(12h) ≈ 12.5 mg/L.\n"
        "- *3 Ngăn IV Infusion:* Mô hình chuẩn trong truyền thuốc kiểm soát nồng độ đích (TCI) gây mê hồi sức (propofol, remifentanil). Xuất hiện khái niệm Thời gian bán thải phụ thuộc bối cảnh (Context-Sensitive Half-Time - CSHT): khi thời gian truyền càng kéo dài, lượng thuốc bão hòa ở ngăn sâu V₃ càng lớn, khiến thời gian để nồng độ giảm 50% sau ngừng truyền tăng vọt từ 10 phút lên gần 40 phút.",
        "**3. ĐƯỜNG UỐNG QUA ỐNG TIÊU HÓA (ORAL ABSORPTION):**\n"
        "- *1 Ngăn Đường uống (Bateman):* Hấp thu bậc 1 với hằng số ka và thời gian trễ Tlag vào ngăn trung tâm, thải trừ bậc 1 với kel. Nghiệm Bateman kinh điển: C(t) = [F·D·ka / (V₁(ka - kel))] · [e^(-kel(t - Tlag)) - e^(-ka(t - Tlag))]. Đỉnh nồng độ Tmax = Tlag + ln(ka/kel)/(ka - kel); nồng độ đỉnh Cmax = C(Tmax). Hiện tượng Flip-flop kinetics: khi ka << kel (ở dạng viên phóng thích kéo dài ER/MR), độ dốc pha cuối biểu kiến phản ánh tốc độ hấp thu ka chứ không phải kel. Ví dụ: Paracetamol 500 mg viên nén uống đói, F = 0.88, ka = 1.8 h⁻¹, kel = 0.28 h⁻¹, V₁/F = 50 L, Tlag = 0.15 h ⇒ Tmax = 1.37 h, Cmax = 6.8 mg/L, t½ = 2.48 h, CL/F = 14 L/h, AUC = 35.7 mg·h/L.\n"
        "- *2 Ngăn Đường uống:* Hấp thu bậc 1 (ka) vào ngăn 1, liên thông 2 chiều với ngăn 2 và thải trừ từ ngăn 1. Nghiệm 3 hàm mũ: C(t) = A·e^(-α(t-Tlag)) + B·e^(-β(t-Tlag)) - (A+B)·e^(-ka(t-Tlag)). Các thể tích và độ thanh thải ước tính dưới dạng biểu kiến V₁/F, Vss/F, CL/F, Q/F. Lưu ý thuật toán: cần đủ điểm lấy mẫu sau đỉnh để phân tách được cả ka, α và β, tránh ma trận kỳ dị. Ví dụ: Ciprofloxacin 500 mg uống, ka = 1.2 h⁻¹, α = 0.8 h⁻¹, β = 0.14 h⁻¹, V₁/F = 60 L ⇒ Tmax ≈ 1.5 h, Cmax ≈ 2.4 mg/L, t½,β ≈ 4.95 h, CL/F ≈ 35 L/h.\n"
        "- *3 Ngăn Đường uống:* Thuốc hấp thu vào ngăn 1 và phân bố đồng thời vào ngăn nông và ngăn sâu. Nghiệm 4 hàm mũ: C(t) = A·e^(-αt) + B·e^(-βt) + C·e^(-γt) - (A+B+C)·e^(-kat). Thể tích biểu kiến Vss/F rất lớn (hàng nghìn lít). Ví dụ: Azithromycin 500 mg uống, F ≈ 0.37, Vss/F ≈ 2000–3000 L, t½,γ ≈ 68 h do tích lũy cực mạnh trong tế bào bạch cầu và mô mỡ, duy trì tác dụng kháng khuẩn kéo dài nhiều ngày sau khi ngừng thuốc. Cảnh báo thống kê: mô hình có 7 tham số cần ước lượng, chỉ chấp nhận khi ΔAICc ≥ 10 so với mô hình 2 ngăn và %RSE của mọi tham số < 30–50%.",
        "**4. ĐỘNG HỌC ĐA LIỀU VÀ TRẠNG THÁI ỔN ĐỊNH (STEADY-STATE):** Đạt được sau 4–5 lần thời gian bán thải t½ khi nồng độ đưa vào mỗi chu kỳ bằng đúng lượng thuốc đào thải. Tại trạng thái ổn định: AUC0-τ,ss trong một khoảng liều τ đúng bằng AUC0-∞ của liều đơn đầu tiên khi động học là tuyến tính. Nồng độ trung bình Css,avg = (F·D) / (CL·τ). Hệ số tích lũy Rac = 1 / (1 - e^(-kel·τ)).",
        "**5. CHIẾN LƯỢC LỰA CHỌN MÔ HÌNH NGĂN TỐI ƯU:**\n"
        "- *Chuẩn thông tin Akaike hiệu chỉnh (AICc) và Bayes (BIC):* Mô hình có AICc và BIC nhỏ nhất được ưu tiên. Nếu ΔAICc > 2, mô hình phức tạp hơn có bằng chứng thống kê vượt trội; nếu ΔAICc < 2, ưu tiên mô hình đơn giản hơn theo nguyên lý tiết kiệm (Parsimony Principle).\n"
        "- *Đồ thị phần dư chuẩn hóa (Weighted Residuals - WRES):* Phân bố ngẫu nhiên quanh trục 0, không có xu hướng uốn cong hình sin theo thời gian hay nồng độ dự đoán.\n"
        "- *Độ chính xác ước tính tham số:* Sai số chuẩn tương đối (%RSE = SE / Estimate × 100%) của tất cả các tham số PK phải < 30%–50%.",
    ),
    terms=(
        "Compartmental Modeling (Mô hình hóa ngăn): Phương pháp mô hình hóa động học xem cơ thể gồm các ngăn đồng nhất trao đổi chất qua lại.",
        "Central Compartment (Ngăn trung tâm V₁ / Vc): Ngăn phân bố gồm máu và các cơ quan tưới máu dồi dào (tim, phổi, gan, thận).",
        "Peripheral Compartment (Ngăn ngoại vi V₂, V₃): Ngăn phân bố gồm mô cơ, mô mỡ, mô liên kết có tốc độ cân bằng chậm hơn.",
        "Intercompartmental Clearance (Q): Độ thanh thải liên ngăn mô tả tốc độ trao đổi thuốc giữa ngăn trung tâm và ngăn ngoại vi (L/h).",
        "Microconstants (Hằng số vi mô): Các hằng số tốc độ chuyển ngăn cụ thể như k₁₀, k₁₂, k₂₁, k₁₃, k₃₁, ka (h⁻¹).",
        "Macroconstants (Hằng số vĩ mô): Các hệ số giao điểm (A, B, C) và hằng số tốc độ phân rã (α, β, γ) thu được trực tiếp từ đồ thị nồng độ.",
        "Bateman Equation: Phương trình Bateman mô tả động học nồng độ theo thời gian mô hình 1 ngăn đường uống có hấp thu bậc 1.",
        "Flip-flop Kinetics: Hiện tượng tráo đổi nghiệm khi tốc độ hấp thu chậm hơn nhiều so với tốc độ thải trừ (ka << kel).",
        "Steady-State (Css, Trạng thái ổn định): Trạng thái cân bằng động khi tốc độ nạp thuốc bằng đúng tốc độ đào thải sau 4–5 lần t½.",
        "Context-Sensitive Half-Time (CSHT): Thời gian cần thiết để nồng độ thuốc giảm 50% sau khi ngừng truyền, tăng theo thời gian truyền ở mô hình nhiều ngăn.",
        "Zero-Order Infusion Rate (R₀): Tốc độ nạp thuốc không đổi theo thời gian trong truyền tĩnh mạch liên tục (mg/h).",
        "AICc / BIC: Chuẩn thông tin Akaike hiệu chỉnh và chuẩn Bayes phục vụ so sánh, phạt số tham số và lựa chọn mô hình PK tối ưu.",
        "Weighted Residuals (WRES): Phần dư chuẩn hóa có trọng số dùng để đánh giá độ chệch hệ thống của mô hình dự đoán.",
    ),
    exercise="Trong thử nghiệm lâm sàng giai đoạn 1 của một kháng sinh mới, thuốc cho thấy đồ thị bán logarit gồm 3 pha phân bố và thải trừ rõ rệt khi tiêm tĩnh mạch bolus (mô hình 3 ngăn). Tuy nhiên, khi chuyển sang dạng viên nang phóng thích kéo dài đường uống, đường cong thực nghiệm chỉ khớp tối ưu với mô hình 1 ngăn theo phương trình Bateman. Hãy giải thích cơ chế dược động học của hiện tượng này (gợi ý: liên hệ với tốc độ hấp thu ka, hiện tượng Flip-flop và sự che lấp các pha phân bố mô).",
    diagram=DIAGRAM_SVGS[10],
    regulations=(
        "EMA Guideline on modified release dosage forms (EMA/CPMP/EWP/280/96 Corr1, 2014): Đánh giá PK đa liều, trạng thái ổn định và thẩm định mô hình ngăn.",
        "US FDA Guidance (2020): Bioequivalence Studies for Multiple Doses and Modified Release Formulations.",
        "ICH M13A (2024): Đánh giá tương đương sinh học ở trạng thái ổn định và phân tích dược động học chuyên sâu cho các chế phẩm đặc biệt.",
        "WHO TRS 992 (2015): Guidelines on compartmental pharmacokinetic modeling and bioequivalence evaluation.",
    ),
    equations=EQUATIONS_10,
    questions=(
        "1. Khi nào nghiên cứu sinh nên ưu tiên chọn mô hình 1 ngăn thay vì 2 ngăn hoặc 3 ngăn? Giải thích sự đánh đổi giữa độ khớp (goodness-of-fit) và nguy cơ quá khớp (overfitting) dựa trên tiêu chí AICc và sai số chuẩn tương đối (%RSE).",
        "2. Trong thử nghiệm dược động học của một viên nén phóng thích kéo dài (ER), làm thế nào để phân biệt được hiện tượng Flip-flop kinetics với trường hợp thuốc có thời gian bán thải sinh học thực sự dài? Cần thiết kế thêm thử nghiệm đối chứng nào (ví dụ tiêm tĩnh mạch IV)?",
        "3. Tại sao khi giám sát nồng độ điều trị (TDM) đối với kháng sinh vancomycin truyền ngắt quãng (IV infusion 1 giờ), mẫu nồng độ đỉnh (Cpeak) không được lấy ngay khi kết thúc truyền mà phải chờ 1–2 giờ sau khi ngừng truyền?",
        "4. Giải thích hiện tượng tại sao một bệnh nhân phẫu thuật tỉnh mê rất nhanh sau một liều bolus fentanyl hoặc propofol nhưng lại thức tỉnh rất chậm nếu truyền liên tục thuốc này nhiều ngày trong phòng hồi sức tích cực (ICU), dựa trên động học mô hình 3 ngăn và khái niệm Context-Sensitive Half-Time.",
    ),
    references=(
        "Gibaldi, M., & Perrier, D. (1982). Pharmacokinetics (2nd ed.). Marcel Dekker, New York.",
        "Rowland, M., & Tozer, T. N. (2019). Clinical Pharmacokinetics and Pharmacodynamics: Concepts and Applications (5th ed.). Wolters Kluwer.",
        "Rescigno, A., & Segre, G. (1966). Drug and Tracer Kinetics. Blaisdell Publishing Company.",
        "Wagner, J. G. (1993). Pharmacokinetics for the Pharmaceutical Scientist. Technomic Publishing.",
        "Yamaoka, K., Nakagawa, T., & Uno, T. (1978). Application of Akaike's information criterion (AIC) in the evaluation of linear pharmacokinetic equations. Journal of Pharmacokinetics and Biopharmaceutics, 6(2), 165–175.",
        "Gabrielsson, J., & Weiner, D. (2016). Pharmacokinetic and Pharmacodynamic Data Analysis: Concepts and Applications (5th ed.). Swedish Pharmaceutical Press.",
    ),
)


# -----------------------------------------------------------------------------
# BE NHANH — PHÂN TÍCH ĐỘC LẬP (QUICK BE SCREENING - LESSON 11)
# -----------------------------------------------------------------------------
QUICK_BE_LESSON = Lesson(
    interface=(
        "**Nhập liệu nhanh:** Hỗ trợ dán trực tiếp bảng dữ liệu có tiêu đề hoặc tải tệp CSV/XLSX đơn giản.",
        "**Chế độ phân tích:** Tự động nhận diện dữ liệu nồng độ (Cplasma theo thời gian) hoặc dữ liệu thông số PK đã tính sẵn (Cmax, AUClast, AUCinf).",
        "**Ánh xạ cột:** Tự động ghép Subject, Sequence, Period, Treatment và cột giá trị phơi nhiễm.",
        "**Bảng kết quả tức thì:** Hiển thị số lượng mẫu, GMR điểm, khoảng tin cậy 90% CI và lý do quyết định sơ bộ.",
    ),
    actions=(
        "Tải tệp hoặc dán bảng số liệu có tiêu đề vào khung nhập liệu.",
        "Khớp các cột định danh (Subject, Sequence, Period, Treatment) và chọn loại số liệu (Cplasma hoặc thông số PK).",
        "Nhấn **Chạy phân tích BE nhanh** để nhận kết quả đánh giá sơ bộ.",
        "Rà soát bảng kết quả GMR và khoảng tin cậy 90% CI; lưu ý kết quả này chỉ phục vụ sàng lọc sơ bộ R&D, không thay thế cho quy trình phân tích đầy đủ có Data Freeze và Audit Trail.",
    ),
    theory=(
        "Phân tích BE nhanh (Rapid BE Screening) phục vụ các nhà nghiên cứu công thức (Formulation Scientists) và học viên trong giai đoạn sàng lọc thử nghiệm ban đầu (Pre-clinical hoặc Pilot screening), giúp định hướng công thức trước khi triển khai nghiên cứu chính thức.",
        "Giới hạn của sàng lọc nhanh: Không có quy trình khóa dữ liệu (Data Freeze), không lưu trữ bất biến kèm mã băm SHA-256, không có nhật ký kiểm toán điều tra sai lệch. Do đó, kết quả chỉ mang tính định hướng nghiên cứu phát triển.",
        "Kiểm tra tính cân bằng: Dữ liệu thiết kế chéo cần cân bằng về số lượng đối tượng giữa các trình tự để tránh mất lực thống kê.",
    ),
    terms=(
        "Pilot Study: Thử nghiệm tiền trạm quy mô nhỏ phục vụ ước tính độ biến thiên và GMR.",
        "Pivotal Study: Nghiên cứu then chốt chính thức nộp hồ sơ đăng ký lưu hành thuốc.",
        "Screening Tool: Công cụ sàng lọc nhanh phục vụ R&D nội bộ.",
    ),
    exercise="Tại sao một công thức thuốc đạt tương đương sinh học trong nghiên cứu pilot quy mô nhỏ (N = 12) vẫn có thể thất bại trong nghiên cứu chính thức quy mô lớn (N = 36)? Những yếu tố nào chi phối sự khác biệt này?",
    diagram=DIAGRAM_SVGS[11],
    regulations=(
        "ICH M13A (2024) Mục 2.2: Phân biệt giữa thử nghiệm pilot định hướng và thử nghiệm then chốt.",
        "WHO TRS 992 (2015): Guidelines on submission of documentation for a multisource finished pharmaceutical product.",
    ),
    equations=EQUATIONS_11,
    questions=(
        "1. Trong phát triển thuốc generic, khi nào nghiên cứu sinh nên ưu tiên thử nghiệm tương đương in vitro (hòa tan so sánh f2) thay vì tiến hành thử nghiệm BE in vivo trên người?",
    ),
    references=(
        "FDA Guidance for Industry (2021). Bioequivalence Studies with Pharmacokinetic Endpoints for Drugs Submitted Under an ANDA.",
        "ICH M9 (2019). Biopharmaceutics Classification System-based Biowaivers.",
    ),
)


# The glossary is teaching content. It describes good practice, not a claim
# that this single-user app provides validated GxP controls.
DATA_INTEGRITY_TERMS: dict[str, IntegrityTerm] = {
    "integrity": IntegrityTerm(
        "Data Integrity (tính toàn vẹn dữ liệu)",
        "Dữ liệu nghiên cứu phải đảm bảo tính chính xác, đầy đủ, nhất quán và có thể truy nguyên nguồn gốc trong toàn bộ vòng đời "
        "từ lúc thu thập ban đầu, xử lý, hiệu chỉnh, phân tích thống kê đến lưu trữ và nộp hồ sơ đăng ký.",
        "Đối chiếu dữ liệu nồng độ đã nhập, lịch sử sửa và bộ dữ liệu tạo ra kết quả BE.",
    ),
    "alcoa": IntegrityTerm(
        "ALCOA+",
        "Nguyên tắc cốt lõi về chất lượng dữ liệu: Attributable (quy được rõ người và thiết bị thực hiện), Legible (dễ đọc và rõ ràng), "
        "Contemporaneous (ghi nhận tức thời tại thời điểm phát sinh), Original (bản ghi nguyên gốc hoặc bản sao có chứng thực), "
        "Accurate (chính xác không sai lệch). Phần dấu cộng (+) bao gồm Complete (đầy đủ toàn diện), Consistent (nhất quán không mâu thuẫn), "
        "Enduring (lưu trữ bền vững không bị phai mờ) và Available (sẵn sàng truy cập khi thanh tra).",
        "Thảo luận vì sao phải giữ file nguồn, lý do sửa, thời điểm và dữ liệu xuất; "
        "app chưa xác thực danh tính người thao tác.",
    ),
    "sap": IntegrityTerm(
        "SAP — Statistical Analysis Plan (kế hoạch phân tích thống kê)",
        "Văn bản pháp lý kỹ thuật định trước toàn bộ phương pháp thống kê, quần thể phân tích (Per-Protocol vs Safety), "
        "định nghĩa các endpoint chính, mô hình ANOVA/LMM, quy tắc xử lý mẫu ngoại lai và chính sách xử lý dữ liệu thiếu hoặc BLQ. "
        "SAP đóng vai trò chốt chặn chống thao túng phương pháp (P-hacking / Data dredging) và là tiêu chuẩn bắt buộc của ICH E9/M13A.",
        "Nhập mã/phiên bản SAP khi lập nghiên cứu; đối chiếu lựa chọn ANOVA, "
        "scaling và missing data với SAP trước Data Freeze.",
    ),
    "audit_trail": IntegrityTerm(
        "Audit trail (dấu vết kiểm toán)",
        "Bản ghi nhật ký an toàn, độc lập, có gắn mốc thời gian (Computer-generated timestamped record) ghi nhận lại mọi thao tác "
        "tạo lập, chỉnh sửa hoặc xóa dữ liệu lâm sàng, cho phép tái dựng chính xác tiến trình nghiên cứu mà không thể bị can thiệp.",
        "Mở Nhật ký kiểm toán để xem các sự kiện; định danh trong ứng dụng "
        "single-user chưa được xác thực bằng tài khoản.",
    ),
    "protocol": IntegrityTerm(
        "Protocol (đề cương nghiên cứu lâm sàng)",
        "Văn bản pháp lý mô tả mục tiêu khoa học, thiết kế thử nghiệm, phương pháp chọn mẫu, quy trình thu thập dữ liệu và tiêu chí đánh giá "
        "đã được Hội đồng Đạo đức trong nghiên cứu y sinh học (IRB/IEC) và Cơ quan Quản lý Dược phê duyệt.",
        "Đối chiếu thiết kế TR/RT, lịch lấy mẫu, endpoint và phiên bản protocol.",
    ),
    "prespec": IntegrityTerm(
        "Prespecification (định trước phương pháp luận)",
        "Nguyên tắc bắt buộc chốt toàn bộ giả định mô hình, công thức và ngưỡng quyết định trong Đề cương/SAP trước khi mở mù dữ liệu, "
        "nhằm ngăn chặn việc lựa chọn phương pháp thiên lệch sau khi đã biết kết quả sơ bộ.",
        "Ghi căn cứ chọn EMA ABEL/FDA RSABE và cách xử lý dữ liệu thiếu trước phân tích.",
    ),
    "provenance": IntegrityTerm(
        "Data provenance (nguồn gốc và lịch sử dữ liệu)",
        "Hồ sơ ghi nhận nguồn gốc xuất phát của dữ liệu (máy sắc ký, phần mềm LIMS, người đo), các thuật toán và các bước biến đổi trung gian "
        "mà dữ liệu đã trải qua trước khi đưa vào phân tích cuối cùng.",
        "Ghi nguồn CV đầu vào và giữ tệp nồng độ đã dùng để nhập dữ liệu.",
    ),
    "version": IntegrityTerm(
        "Version control / revision (kiểm soát phiên bản)",
        "Quy trình quản lý các thay đổi của tài liệu và cơ sở dữ liệu qua các mã số phiên bản (r1, r2...), đảm bảo xác định chính xác "
        "phiên bản dữ liệu và cấu hình nào đã tạo ra từng kết quả phân tích cụ thể.",
        "So sánh SAP v1 với v2 và tạo revision khi thay đổi phương pháp.",
    ),
    "traceability": IntegrityTerm(
        "Traceability (khả năng truy xuất nguồn gốc)",
        "Khả năng lần ngược không đứt đoạn từ một con số trong báo cáo tổng kết (CSR) về đúng biểu đồ, bảng ANOVA, kết quả NCA, "
        "dữ liệu nồng độ cá thể và hồ sơ gốc của người tình nguyện tại cơ sở lâm sàng.",
        "Từ báo cáo BE kiểm tra snapshot, input fingerprint và tệp dữ liệu.",
    ),
    "blinding": IntegrityTerm(
        "Blinding / unblinding (làm mù và giải mù)",
        "Quy trình bảo mật thông tin phân nhóm đối tượng (ai nhận T, ai nhận R ở kỳ nào) nhằm loại bỏ định kiến chủ quan trong quá trình "
        "chăm sóc lâm sàng, lấy mẫu và định lượng sinh học; việc mở mù chỉ được thực hiện sau khi cơ sở dữ liệu đã được khóa hoàn tất.",
        "Thảo luận thời điểm được đối chiếu sequence với T/R và quyền xem phân nhóm.",
    ),
    "source": IntegrityTerm(
        "Source data / source records (dữ liệu và hồ sơ nguồn)",
        "Tất cả các tài liệu, hồ sơ gốc (CRF, nhật ký lấy mẫu, sắc ký đồ thô) cần thiết cho việc tái dựng và thẩm định độc lập nghiên cứu lâm sàng.",
        "So sánh hồ sơ lấy mẫu và báo cáo xét nghiệm với các dòng CSV/XLSX.",
    ),
    "raw": IntegrityTerm(
        "Raw data (dữ liệu thô ban đầu)",
        "Dữ liệu gốc thu nhận trực tiếp từ hệ thống phân tích sinh học trước bất kỳ thao tác lọc, làm sạch, quy đổi hay chỉnh sửa nào; "
        "tuyệt đối không được ghi đè hay xóa bỏ.",
        "Giữ dữ liệu nồng độ nhập ban đầu; việc chỉnh sửa đi qua luồng correction.",
    ),
    "metadata": IntegrityTerm(
        "Metadata (siêu dữ liệu)",
        "Dữ liệu mô tả ngữ cảnh cần thiết để hiểu đúng giá trị đo được, bao gồm đơn vị đo, thời điểm lấy mẫu thực tế, định danh thiết bị, "
        "mã phân tích và điều kiện vận hành.",
        "Đối chiếu subject, period, treatment, giờ lấy mẫu thực tế và đơn vị nồng độ.",
    ),
    "validation": IntegrityTerm(
        "Data validation (thẩm định tính hợp lệ của dữ liệu)",
        "Các bước kiểm tra tự động và thủ công đối với cấu trúc, giới hạn sinh học, tính logic và ràng buộc dữ liệu trước khi chấp nhận vào cơ sở dữ liệu chính thức.",
        "Chạy Kiểm tra cấu trúc và QC để phát hiện cột thiếu, sai kiểu và lỗi từng dòng.",
    ),
    "reconciliation": IntegrityTerm(
        "Data reconciliation (đối soát và khớp dữ liệu)",
        "Hoạt động so khớp chéo giữa danh sách phân nhóm ngẫu nhiên, hồ sơ phát thuốc lâm sàng, nhật ký lấy mẫu và bảng nồng độ sinh học "
        "nhằm phát hiện các sai lệch về đối tượng hoặc hoán đổi kỳ nghiên cứu.",
        "Đối chiếu subject/period/treatment của bảng nồng độ với danh sách phân nhóm.",
    ),
    "correction": IntegrityTerm(
        "Data correction (hiệu chỉnh số liệu có kiểm soát)",
        "Quy trình sửa đổi dữ liệu sai sót kỹ thuật đòi hỏi phải có biên bản điều tra sai lệch, lý do giải trình, phê duyệt của người có thẩm quyền "
        "và bảo toàn vĩnh viễn giá trị ban đầu trong nhật ký kiểm toán.",
        "Sửa một concentration theo sample_id, điền lý do và người rà soát rồi chạy QC lại.",
    ),
    "freeze": IntegrityTerm(
        "Data Freeze / Data Lock (đóng băng và khóa cơ sở dữ liệu)",
        "Mốc pháp lý chốt chặn toàn bộ cơ sở dữ liệu lâm sàng và sinh học sau khi đã hoàn tất các bước làm sạch và kiểm tra QC; "
        "sau mốc này, không một chỉnh sửa nào được phép thực hiện mà không có quy trình phá khóa (Database Unlock) có văn bản phê duyệt.",
        "Chọn Data Freeze và khóa SAP sau QC; thay đổi sẽ cần quy trình revision.",
    ),
    "qcqa": IntegrityTerm(
        "QC / QA — Quality Control / Quality Assurance",
        "QC là các hoạt động tác nghiệp cụ thể nhằm kiểm tra chất lượng sản phẩm/dữ liệu ở từng công đoạn; QA là hệ thống quản lý độc lập "
        "nhằm bảo đảm toàn bộ quy trình tuân thủ đúng GCP/GLP và các quy định pháp luật.",
        "QC của app phát hiện lỗi nồng độ; việc thẩm định và QA độc lập "
        "không tự động hoàn tất chỉ bằng một lần chạy QC.",
    ),
    "deviation": IntegrityTerm(
        "Protocol deviation (sai lệch đề cương)",
        "Bất kỳ sự không tuân thủ nào so với Đề cương nghiên cứu đã phê duyệt; cần được ghi nhận tức thời, phân loại (Minor vs Major) "
        "và đánh giá tác động đối với an toàn của đối tượng và tính toàn vẹn của kết luận tương đương sinh học.",
        "Thảo luận cách xử lý mẫu lấy ngoài cửa sổ thời gian quy định.",
    ),
    "reproducibility": IntegrityTerm(
        "Reproducibility (khả năng tái lập kết quả)",
        "Khả năng một chuyên gia độc lập hoặc chuyên viên xét duyệt hồ sơ có thể tái lập chính xác 100% các bảng kết quả NCA và thống kê BE "
        "khi chạy lại trên cùng tập dữ liệu thô và cấu hình thuật toán đã công bố.",
        "Đối chiếu AUC/NCA hoặc BE từ cùng snapshot với workbook xuất.",
    ),
    "snapshot": IntegrityTerm(
        "Analysis snapshot (ảnh chụp trạng thái phân tích)",
        "Bản ghi bất biến liên kết toàn bộ kết quả tính toán với đúng phiên bản dữ liệu đầu vào, cấu hình thuật toán và mã băm SHA-256 tại thời điểm thực thi.",
        "Kiểm tra snapshot CURRENT/STALE trước khi tải báo cáo.",
    ),
    "audit_review": IntegrityTerm(
        "Audit trail review (rà soát dấu vết kiểm toán)",
        "Hoạt động đánh giá định kỳ và trước khi nghiệm thu của cán bộ QA/chuyên gia thống kê đối với toàn bộ nhật ký sự kiện, "
        "nhằm phát hiện các bất thường, chỉnh sửa số liệu không hợp lệ hoặc các khoảng trống thời gian không thể giải trình.",
        "Tìm sự kiện sửa nồng độ, lý do correction, freeze và lần xuất báo cáo.",
    ),
    "rbac": IntegrityTerm(
        "RBAC — Role-Based Access Control (phân quyền theo vai trò)",
        "Cơ chế kiểm soát an ninh hệ thống giới hạn quyền hạn thao tác (chỉ đọc, nhập liệu, sửa đổi, phê duyệt, khóa dữ liệu) "
        "dựa trên vai trò và trách nhiệm được phân công trong thử nghiệm lâm sàng.",
        "Bài tập thiết kế quyền học viên/giảng viên; app hiện chưa có RBAC hoặc đăng nhập.",
    ),
    "esign": IntegrityTerm(
        "Electronic signature (chữ ký điện tử)",
        "Chữ ký số hóa gắn liền với danh tính người ký và nội dung bản ghi, có giá trị pháp lý tương đương chữ ký tay theo quy định "
        "của US FDA 21 CFR Part 11 và các văn bản pháp luật hiện hành.",
        "Nhật ký hoặc trường người rà soát trong app không phải chữ ký "
        "điện tử đạt chuẩn GxP/21 CFR Part 11.",
    ),
    "retention": IntegrityTerm(
        "Retention / backup (lưu trữ và sao lưu dữ liệu)",
        "Quy trình bảo quản an toàn cơ sở dữ liệu và hồ sơ nghiên cứu trong thời hạn tối thiểu theo luật định (thường từ 15–25 năm) "
        "với các biện pháp sao lưu dự phòng chống mất mát dữ liệu do sự cố phần cứng hoặc thảm họa.",
        "Xuất archive/manifest và thảo luận cách kiểm tra khả năng khôi phục dữ liệu.",
    ),
}

# All pages teach common principles; additional terms follow the current workflow.
_INTEGRITY_CONTEXT: tuple[tuple[str, ...], ...] = (
    ("protocol", "prespec", "provenance", "version"),
    ("prespec", "provenance", "traceability"),
    ("blinding", "protocol", "reconciliation"),
    ("source", "raw", "metadata", "validation", "reconciliation"),
    ("correction", "freeze", "qcqa", "deviation"),
    ("prespec", "reproducibility", "snapshot"),
    ("prespec", "blinding", "reproducibility"),
    ("traceability", "metadata", "qcqa"),
    ("snapshot", "traceability", "version", "retention"),
    ("audit_review", "version", "rbac", "esign", "retention"),
)


def integrity_terms_for(page_index: int) -> tuple[IntegrityTerm, ...]:
    """Ordered, page-specific teaching terms; no changes to project state."""
    if page_index >= len(_INTEGRITY_CONTEXT):
        context_keys = ("protocol", "provenance", "traceability", "reproducibility")
    else:
        context_keys = _INTEGRITY_CONTEXT[page_index]
    keys = dict.fromkeys(("integrity", "alcoa", "sap", "audit_trail", *context_keys))
    return tuple(DATA_INTEGRITY_TERMS[key] for key in keys)


PROFILE_LESSONS: dict[str, tuple[str, str]] = {
    "EMA_IR_NONREPLICATE_M13A": (
        "ABE theo hướng dẫn ICH M13A (EMA): Áp dụng cho thiết kế chéo đôi 2×2 hoặc song song cho dạng thuốc quy ước giải phóng tức thì (IR). Mô hình ANOVA đánh giá trên biến đổi ln(AUC) và ln(Cmax), yêu cầu khoảng tin cậy 90% CI của GMR nằm gọn trong khoảng [80.00% - 125.00%].",
        "Biên chấp nhận chuẩn cho cả AUC và Cmax là 80,00–125,00%; nghiên cứu sinh cần kiểm tra kỹ phạm vi của hoạt chất trước khi kết luận.",
    ),
    "FDA_ABE_2026": (
        "ABE theo US-FDA: Đối chiếu hướng dẫn hòa hợp quốc tế ICH M13A, tài liệu hướng dẫn thống kê Statistical Approaches (2026) và các khuyến cáo chuyên biệt trong PSG của từng hoạt chất.",
        "Khoảng tin cậy 90% CI của tỷ số trung bình nhân (GMR) phải nằm trọn trong khoảng quy chuẩn 80,00–125,00%; mô-đun planning được kích hoạt cho thiết kế 2×2 và thiết kế song song hợp lệ.",
    ),
    "EMA_REPLICATE_STANDARD": (
        "Replicate ABE theo EMA: Sử dụng thiết kế lặp (Partial replicate 3 kỳ hoặc Full replicate 4 kỳ) nhằm ước tính độ biến thiên nội cá thể của thuốc đối chứng (CVwR) và thuốc thử (CVwT).",
        "Thiết kế lặp không tự động kích hoạt mở rộng biên; công cụ planning cỡ mẫu cho thiết kế replicate chưa được mở trong phiên bản thử nghiệm này.",
    ),
    "EMA_HVDP_ABEL": (
        "EMA ABEL cho thuốc biến thiên cao (HVDP): Khi thỏa mãn điều kiện định trước trong SAP và CVwR > 30%, biên chấp nhận cho Cmax được mở rộng theo công thức [L, U] = exp(±0.760 · swR) với mức mở rộng tối đa là 69.84%–143.19% (khi CVwR ≥ 50%).",
        "Yêu cầu bắt buộc phải sử dụng thiết kế replicate hợp chuẩn, có bằng chứng chứng minh hoạt chất là HVDP và ước tính điểm GMR phải nằm trong khoảng [80.00% - 125.00%]; chỉ tiêu AUC vẫn áp dụng biên chuẩn 80.00–125.00%.",
    ),
    "FDA_HVD_RSABE_2026": (
        "FDA RSABE cho thuốc biến thiên cao: Áp dụng thủ tục chuẩn hóa tham chiếu (Reference-Scaled Average Bioequivalence) với tiêu chí hỗn hợp dựa trên phương sai thuốc đối chứng và cận trên khoảng tin cậy 95% (Upper Confidence Bound - UCB ≤ 0).",
        "Khoảng tin cậy 90% CI chỉ mang tính chất bổ trợ; khi sWR < 0,294 (tương ứng CVwR < 30%), FDA yêu cầu chuyển về phương pháp conventional replicate ABE thông thường chưa qualified nên hệ thống ghi nhận NOT EVALUABLE.",
    ),
    "FDA_NTI": (
        "FDA NTI: Hướng dẫn chuyên biệt cho thuốc có khoảng điều trị hẹp (Narrow Therapeutic Index Drugs) đòi hỏi thiết kế full replicate 4 kỳ, đánh giá đồng thời tiêu chí RSABE thu hẹp và kiểm định tỷ số phương sai trong cá thể sWT/sWR ≤ 2.5.",
        "Các thành phần thống kê có thể được tính toán nhưng quyết định kết luận endpoint hiện đang bị khóa (NOT EVALUABLE) để tránh đưa ra kết luận pháp lý khi chưa có thẩm định đầy đủ.",
    ),
    "EMA_NTI": (
        "EMA NTI: Quy chế của EMA đối với thuốc có khoảng điều trị hẹp yêu cầu thu hẹp biên tương đương sinh học của AUC về khoảng [90.00% - 111.11%]; biên Cmax cũng bị thu hẹp nếu được quy định cụ thể trong chuyên khảo sản phẩm.",
        "Cần khai báo thuộc tính NTI đồng bộ với Đề cương và SAP ngay từ bước Tổng quan; mô-đun planning cho thuốc NTI hiện chưa được mở.",
    ),
    "FDA_REPLICATE_STANDARD": (
        "FDA replicate ABE tiêu chuẩn: Áp dụng mô hình tuyến tính hỗn hợp (Linear Mixed-Effects Model) để phân tích dữ liệu thiết kế lặp mà không áp dụng thủ tục scaling.",
        "Mô hình mixed replicate ABE thông thường chưa qua quy trình thẩm định độc lập; hệ thống chặn kết luận chính thức (NOT EVALUABLE).",
    ),
}


# A concrete piece of evidence to produce at each step of the guided study.
RESEARCH_TASKS = (
    "Từ Đề cương (Protocol) và Kế hoạch Phân tích Thống kê (SAP), lập bảng đối chiếu thiết kế nghiên cứu, danh mục endpoint chính (Cmax, AUC) và quy tắc quyết định tương đương sinh học. Ghi rõ số hiệu phiên bản tài liệu tương ứng.",
    "Trên tập dữ liệu học thử, thử nghiệm thay đổi hệ số biến thiên nội cá thể CV_intra của Cmax rồi tính lại cỡ mẫu. Ghi nhận số đối tượng đánh giá (N_evaluable), số đối tượng cần tuyển (N_recruited) và chỉ ra endpoint nào chi phối cỡ mẫu trước và sau thay đổi.",
    "Lập bảng thống kê số lượng người tình nguyện được phân bổ vào từng trình tự (Sequence) và kỳ (Period). Chọn ngẫu nhiên một mã đối tượng và truy vết theo lịch dùng thuốc T/R để kiểm tra tính cân bằng của thuật toán ngẫu nhiên hóa.",
    "Truy ngược một dòng nồng độ đã nhập về đúng tệp dữ liệu, trang tính (sheet) và cột nguồn ban đầu. Xác nhận đơn vị đo, thời điểm lấy mẫu thực tế và quy tắc nhận diện cờ BLQ trước khi đưa vào phân tích NCA.",
    "Chọn một mẫu nồng độ bị cảnh báo trong bảng QC. Ghi nhận mã mẫu (sample_id), giá trị nồng độ gốc, căn cứ điều tra sai lệch và giá trị hiệu chỉnh được phê duyệt. Kiểm tra bảng nháp trước khi thực hiện Data Freeze.",
    "Chọn một hồ sơ nồng độ cá thể và thực hiện tính tay diện tích hình thang giữa hai thời điểm liên tiếp theo quy tắc tích phân Linear Up / Log Down. Đối chiếu kết quả với đồ thị và phân tích ảnh hưởng của mật độ lấy mẫu đến việc xác định Cmax và Tmax.",
    "Với một endpoint chính (AUC hoặc Cmax), ghi nhận các giá trị N, GMR, 90% CI, tiêu chí quy chuẩn của profile pháp lý và lý do kết luận. Nếu kết quả là NOT EVALUABLE, chỉ rõ điều kiện tiền đề hoặc số liệu nào đang còn thiếu.",
    "So sánh hình thái đường cong nồng độ của cùng một đối tượng trên cả hai đồ thị thang tuyến tính và bán logarit. Xác định các điểm nồng độ chi phối việc ước tính pha thải trừ cuối (λz) và đối chiếu với bảng thông số NCA.",
    "Phân biệt rõ Đề cương nghiên cứu (mô tả kế hoạch thử nghiệm tiền cứu) với Báo cáo tổng kết CSR (trình bày kết quả thực nghiệm sau khi khóa dữ liệu). Truy vết một con số thống kê trong báo cáo về đúng snapshot phân tích và mã băm SHA-256.",
    "Chọn một thao tác hiệu chỉnh dữ liệu và tái dựng lại trình tự: Nhập dữ liệu → Sửa mẫu QC → Khóa Data Freeze → Chạy phân tích từ nhật ký Audit Trail. Xác định những bằng chứng tài liệu nào cần lưu trữ kèm theo để bảo đảm khả năng tái lập độc lập.",
)


QUICK_TASKS = {
    "input": "Tải tệp hoặc dán bảng có tiêu đề. Để học thử, điền dữ liệu mẫu rồi xác định mỗi dòng là một mẫu nồng độ hay một endpoint của người tham gia trong một kỳ.",
    "mapping": "Đối chiếu Subject, Sequence, Period và Treatment với bảng nguồn. Mỗi cột chỉ có một ý nghĩa. Chọn Cplasma cho dữ liệu mẫu hoặc Cmax/AUC cho dữ liệu PK đã tính.",
    "time": "Ánh xạ cột thời gian thực (giờ) cho từng mẫu Cplasma. Chọn hai mẫu liên tiếp và giải thích vì sao khoảng thời gian giữa chúng ảnh hưởng đến AUClast.",
    "labels": "Đối chiếu một người tham gia với lịch cấp thuốc. Xác nhận nhãn thuốc T/R và trình tự của tất cả các kỳ theo thiết kế đã chọn.",
    "concentration": "Kiểm tra đơn vị Cplasma, Time và quy tắc tích phân. Sau khi chạy, chọn một Subject/Period và truy Cmax, Tmax và AUClast về các mẫu nồng độ.",
    "endpoint": "Đối chiếu thang raw, ln hoặc log10 với bảng PK nguồn. Giải thích ảnh hưởng của việc khai báo sai thang đo lên GMR trước khi chạy.",
    "stale": "Dữ liệu hoặc cấu hình đã đổi từ lần chạy trước. Ghi lại thay đổi, chạy lại rồi đối chiếu cùng một endpoint giữa hai lần phân tích.",
    "results": "Đọc N, GMR, CI 90% và lý do quyết định cho từng endpoint chính. Với Tmax, đối chiếu trung vị, thiết kế và số cặp nếu có. Diễn giải p hai phía như phân tích hỗ trợ, tách riêng khỏi quyết định BE.",
}


def lesson_for(index: int) -> Lesson:
    """Return the structured postgraduate teaching lesson for any page index (0 to 11)."""
    if index == 10:
        return PK_STANDALONE_LESSON
    if index == 11:
        return QUICK_BE_LESSON
    return LESSONS[index]


def profile_help(rule_id: str) -> tuple[tuple[str, str], str, tuple[str, ...]]:
    """Method explanation, live implementation status, and authoritative reference URLs."""
    rule = RULES[rule_id]
    capability = capability_for(rule_id)
    status = (
        f"Kết luận endpoint: {capability.endpoint_decision}; "
        f"planning: {'mở' if capability.planning else 'chưa mở'}; "
        f"thẩm định độc lập: {'đã có' if capability.independently_qualified else 'chưa có'}. "
        f"{capability.limitation}"
    )
    return PROFILE_LESSONS[rule_id], status, rule.sources
