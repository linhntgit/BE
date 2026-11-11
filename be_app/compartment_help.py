"""Comprehensive graduate-level documentation and interactive renderer for 9 compartmental PK models.

Provides systematic coverage for:
- 3 Routes: IV Bolus, IV Infusion, Oral Absorption.
- 3 Compartmental orders: 1-Compartment, 2-Compartment, 3-Compartment.
- 5 Standard subsections per model:
  A. Cơ sở lý thuyết (Principles, ADME, assumptions, compartment meaning, indications).
  B. Sơ đồ minh họa (Vector SVG diagrams).
  C. Hệ phương trình toán học (ODEs, analytical solutions, parameter nomenclature).
  D. Các thông số dược động học (Clearances, volumes, half-lives, micro/macro relationships).
  E. Minh họa và diễn giải kết quả (Curve profiles, numerical clinical examples with units, AICc notes).
"""

from dataclasses import dataclass
import streamlit as st

from be_app.diagram_svg import get_diagram_compartment


@dataclass(frozen=True)
class CompartmentModelDoc:
    id: str
    name: str
    route: str
    compartments: int
    theory: str
    ode_latex: str
    solution_latex: str
    parameters: str
    example: str
    notes: str


MODEL_DOCS: dict[str, CompartmentModelDoc] = {
    "1. Tiêm tĩnh mạch nhanh (IV Bolus) — 1 Ngăn": CompartmentModelDoc(
        id="iv_bolus_1cpt",
        name="Tiêm tĩnh mạch nhanh (IV Bolus) — Mô hình 1 Ngăn",
        route="iv_bolus",
        compartments=1,
        theory=(
            "**Khái niệm & Nguyên lý:** Toàn bộ liều thuốc $D$ được đưa tức thời vào tuần hoàn chung tại thời điểm $t=0$. "
            "Cơ thể được xem như một ngăn phân bố duy nhất, đồng nhất và hòa lẫn tức thì với thể tích biểu kiến $V_1$ (hoặc $V_d$).\n\n"
            "**Đặc điểm ADME:**\n"
            "- *Hấp thu:* Tức thời ($t_{\\text{abs}} \\approx 0$, sinh khả dụng tuyệt đối $F = 1$).\n"
            "- *Phân bố:* Hòa lẫn tức thời vào toàn bộ thể tích $V_1$; nồng độ trong máu phản ánh trực tiếp nồng độ tại các mô trong cơ thể.\n"
            "- *Thải trừ:* Thải trừ chỉ diễn ra từ ngăn trung tâm theo động học bậc nhất tuyến tính với hằng số tốc độ đào thải $k_{10}$ (hoặc $k_{el}$).\n\n"
            "**Ý nghĩa ngăn:** Ngăn trung tâm đại diện cho máu (huyết tương), dịch ngoại bào và các cơ quan tưới máu cực nhanh (tim, phổi, gan, thận).\n\n"
            "**Điều kiện áp dụng:** Thuốc phân bố cực nhanh so với tốc độ thải trừ; trên đồ thị bán logarit $\\ln C(t)$ theo thời gian chỉ xuất hiện một đường thẳng duy nhất (chỉ có pha thải trừ $\\beta$, không quan sát thấy pha phân bố $\\alpha$). Ví dụ: Aminoglycoside (gentamicin, tobramycin), theophylline."
        ),
        ode_latex=r"\frac{dC(t)}{dt} = -k_{10} \cdot C(t), \qquad C(0) = C_0 = \frac{D}{V_1}",
        solution_latex=r"C(t) = C_0 \cdot e^{-k_{10} t} = \frac{D}{V_1} \cdot e^{-\frac{CL}{V_1} t}",
        parameters=(
            "- $C(t)$: Nồng độ thuốc trong huyết tương tại thời điểm $t$ ($\\text{mg/L}$ hoặc $\\mu\\text{g/mL}$).\n"
            "- $C_0$: Nồng độ ban đầu ngoại suy tại $t=0$ ($\\text{mg/L}$, với $C_0 = D / V_1$).\n"
            "- $D$: Liều thuốc tiêm tĩnh mạch trực tiếp ($\\text{mg}$).\n"
            "- $V_1$ (hoặc $V_d$): Thể tích phân bố của ngăn trung tâm ($\\text{L}$ hoặc $\\text{L/kg}$).\n"
            "- $k_{10}$ (hoặc $k_{el}$): Hằng số tốc độ đào thải bậc 1 từ ngăn trung tâm ($\\text{h}^{-1}$).\n"
            "- $CL$: Độ thanh thải toàn thân của thuốc ($\\text{L/h}$, với $CL = k_{10} \\cdot V_1 = D / AUC_{0-\\infty}$).\n"
            "- $t_{1/2}$: Thời gian bán thải sinh học ($t_{1/2} = \\frac{\\ln 2}{k_{10}} = \\frac{0.693}{k_{10}}$, đơn vị $\\text{h}$).\n"
            "- $AUC_{0-\\infty}$: Diện tích dưới đường cong nồng độ–thời gian ($AUC_{0-\\infty} = \\frac{C_0}{k_{10}} = \\frac{D}{CL}$, đơn vị $\\text{mg}\\cdot\\text{h/L}$).\n"
            "- $MRT$: Thời gian lưu trú trung bình ($MRT = \\frac{AUMC}{AUC} = \\frac{1}{k_{10}}$, đơn vị $\\text{h}$)."
        ),
        example=(
            "**Bệnh nhân:** Nam, 65 kg, điều trị nhiễm khuẩn huyết bằng Gentamicin tiêm tĩnh mạch nhanh.\n"
            "- **Bộ tham số giả định:**\n"
            "  - Liều dùng: $D = 325\\text{ mg}$ (tương ứng $5\\text{ mg/kg}$).\n"
            "  - Thể tích phân bố: $V_1 = 16.25\\text{ L}$ ($0.25\\text{ L/kg}$ dịch ngoại bào).\n"
            "  - Hằng số thải trừ: $k_{10} = 0.231\\text{ h}^{-1}$.\n"
            "- **Kết quả tính toán dược động học:**\n"
            "  - $C_0 = 325 / 16.25 = 20.0\\text{ mg/L}$ (nồng độ đỉnh tức thời).\n"
            "  - $CL = 0.231 \\times 16.25 = 3.75\\text{ L/h}$ ($62.5\\text{ mL/min}$).\n"
            "  - $t_{1/2} = 0.693 / 0.231 = 3.0\\text{ giờ}$.\n"
            "  - $AUC_{0-\\infty} = 325 / 3.75 = 86.67\\text{ mg}\\cdot\\text{h/L}$.\n"
            "  - Nồng độ tại $t=8\\text{h}$: $C(8) = 20.0 \\cdot e^{-0.231 \\times 8} = 20.0 \\cdot e^{-1.848} = 3.15\\text{ mg/L}$.\n"
            "  - Nồng độ đáy tại $t=24\\text{h}$ ($C_{\\text{trough}}$): $C(24) = 20.0 \\cdot e^{-0.231 \\times 24} = 0.078\\text{ mg/L}$ ($< 0.5\\text{ mg/L}$, bảo đảm an toàn thận)."
        ),
        notes=(
            "- **Hình dạng đường cong:** Trên thang tuyến tính, nồng độ giảm dốc hàm mũ từ $C_0$ về 0. Trên thang bán logarit, đồ thị là một đường thẳng hoàn hảo với độ dốc $-k_{10}/2.303$ và tung độ gốc $\\log C_0$.\n"
            "- **Lưu ý chọn mô hình:** Nếu trên đồ thị bán log xuất hiện độ cong rõ rệt ở các thời điểm sớm (0–2 giờ đầu), mô hình 1 ngăn sẽ đánh giá thấp nồng độ đỉnh thực tế và tính sai thể tích phân bố, khi đó bắt buộc phải chuyển sang mô hình 2 ngăn."
        ),
    ),
    "2. Tiêm tĩnh mạch nhanh (IV Bolus) — 2 Ngăn": CompartmentModelDoc(
        id="iv_bolus_2cpt",
        name="Tiêm tĩnh mạch nhanh (IV Bolus) — Mô hình 2 Ngăn",
        route="iv_bolus",
        compartments=2,
        theory=(
            "**Khái niệm & Nguyên lý:** Thuốc sau tiêm IV phân bố tức thời vào ngăn trung tâm ($V_1$), sau đó diễn ra đồng thời hai quá trình: phân bố thuận nghịch hai chiều giữa ngăn trung tâm và một ngăn ngoại vi ($V_2$), kết hợp với đào thải khỏi ngăn trung tâm.\n\n"
            "**Đặc điểm ADME:**\n"
            "- *Phân bố:* Không tức thời; xuất hiện pha phân bố nhanh (pha $\\alpha$) khi thuốc từ máu khuếch tán sang mô, sau đó đạt trạng thái cân bằng động.\n"
            "- *Thải trừ:* Diễn ra chủ yếu từ ngăn trung tâm (gan, thận) theo động học bậc nhất với hằng số $k_{10}$; khi phân bố đã cân bằng, độ dốc suy giảm nồng độ biểu kiến là pha $\\beta$.\n\n"
            "**Ý nghĩa ngăn:**\n"
            "- *Ngăn 1 (Trung tâm, $V_1$):* Máu, huyết tương, dịch ngoại bào, và các tạng tưới máu dồi dào (tim, phổi, gan, não).\n"
            "- *Ngăn 2 (Ngoại vi, $V_2$):* Các mô tưới máu chậm hơn như mô cơ, da, mô mỡ nông.\n\n"
            "**Điều kiện áp dụng:** Thuốc có quá trình phân bố vào mô cần thời gian đo đạc được ($t_{1/2,\\alpha}$ từ vài chục phút đến vài giờ); đồ thị bán logarit có dạng biexponential 2 pha rõ nét. Ví dụ: Vancomycin, theophylline, lidocaine, digoxin."
        ),
        ode_latex=(
            r"\begin{aligned} "
            r"\frac{dX_1(t)}{dt} &= -(k_{10} + k_{12}) X_1(t) + k_{21} X_2(t), \quad X_1(0) = D \\ "
            r"\frac{dX_2(t)}{dt} &= k_{12} X_1(t) - k_{21} X_2(t), \quad X_2(0) = 0 "
            r"\end{aligned}"
        ),
        solution_latex=r"C(t) = A \cdot e^{-\alpha t} + B \cdot e^{-\beta t}, \qquad C_0 = A + B = \frac{D}{V_1}",
        parameters=(
            "- $C(t)$: Nồng độ thuốc trong ngăn trung tâm tại thời điểm $t$ ($\\text{mg/L}$).\n"
            "- $A, B$: Các giao điểm vĩ mô (macroconstants) của pha $\\alpha$ và pha $\\beta$ trên trục tung tại $t=0$ ($\\text{mg/L}$).\n"
            "- $\\alpha, \\beta$: Các hằng số tốc độ phân rã vĩ mô ($\\text{h}^{-1}$, với $\\alpha > \\beta > 0$); $\\alpha$ đại diện pha phân bố, $\\beta$ đại diện pha thải trừ cuối.\n"
            "- $k_{10}, k_{12}, k_{21}$: Hằng số tốc độ chuyển ngăn vi mô (microconstants, $\\text{h}^{-1}$):\n"
            "  $$\\alpha + \\beta = k_{10} + k_{12} + k_{21}, \\qquad \\alpha \\cdot \\beta = k_{10} \\cdot k_{21}$$\n"
            "  $$k_{21} = \\frac{A\\beta + B\\alpha}{A + B}, \\quad k_{10} = \\frac{\\alpha \\beta}{k_{21}}, \\quad k_{12} = \\alpha + \\beta - k_{10} - k_{21}$$\n"
            "- $V_1$ ($V_c$): Thể tích phân bố ngăn trung tâm ($V_1 = \\frac{D}{A + B} = \\frac{D}{C_0}$, đơn vị L).\n"
            "- $V_2$ ($V_p$): Thể tích phân bố ngăn ngoại vi ($V_2 = V_1 \\cdot \\frac{k_{12}}{k_{21}}$, đơn vị L).\n"
            "- $V_{ss}$: Thể tích phân bố tại trạng thái ổn định ($V_{ss} = V_1 + V_2 = V_1 [1 + \\frac{k_{12}}{k_{21}}] = \\frac{D \\cdot AUMC}{AUC^2}$).\n"
            "- $V_\\beta$: Thể tích phân bố theo diện tích ($V_\\beta = \\frac{CL}{\\beta}$, luôn có quy luật thứ bậc $V_c < V_{ss} < V_\\beta$).\n"
            "- $CL$: Độ thanh thải toàn thân ($CL = k_{10} V_1 = \\frac{D}{AUC_{0-\\infty}} = \\frac{D}{A/\\alpha + B/\\beta}$, đơn vị $\\text{L/h}$).\n"
            "- $Q$: Độ thanh thải liên ngăn ($Q = k_{12} V_1 = k_{21} V_2$, đơn vị $\\text{L/h}$).\n"
            "- $t_{1/2,\\alpha} = \\frac{\\ln 2}{\\alpha}$; $t_{1/2,\\beta} = \\frac{\\ln 2}{\\beta}$ (thời gian bán thải sinh học thực tế)."
        ),
        example=(
            "**Bệnh nhân:** Người lớn 70 kg, tiêm tĩnh mạch liều nạp Vancomycin $D = 1000\\text{ mg}$.\n"
            "- **Bộ tham số vi mô giả định:**\n"
            "  - $V_1 = 20.0\\text{ L}$, $k_{10} = 0.150\\text{ h}^{-1}$, $k_{12} = 0.250\\text{ h}^{-1}$, $k_{21} = 0.100\\text{ h}^{-1}$.\n"
            "- **Quy đổi sang tham số vĩ mô:**\n"
            "  - $\\alpha + \\beta = 0.150 + 0.250 + 0.100 = 0.500\\text{ h}^{-1}$.\n"
            "  - $\\alpha \\cdot \\beta = 0.150 \\times 0.100 = 0.015\\text{ h}^{-2}$.\n"
            "  - Giải phương trình bậc 2: $\\alpha \\approx 0.468\\text{ h}^{-1}$, $\\beta \\approx 0.032\\text{ h}^{-1}$.\n"
            "  - $t_{1/2,\\alpha} = 0.693 / 0.468 \\approx 1.48\\text{ giờ}$ (pha phân bố kết thúc sau $\\approx 4-6\\text{h}$).\n"
            "  - $t_{1/2,\\beta} = 0.693 / 0.032 \\approx 21.6\\text{ giờ}$ (thời gian bán thải pha cuối).\n"
            "  - $A = \\frac{1000}{20} \\frac{0.468 - 0.100}{0.468 - 0.032} = 50 \\times \\frac{0.368}{0.436} = 42.2\\text{ mg/L}$.\n"
            "  - $B = 50 - 42.2 = 7.8\\text{ mg/L}$. Nồng độ đỉnh $C_0 = 50.0\\text{ mg/L}$.\n"
            "- **Thể tích và độ thanh thải:**\n"
            "  - $CL = 0.150 \\times 20.0 = 3.0\\text{ L/h}$.\n"
            "  - $V_2 = 20 \\times (0.250 / 0.100) = 50.0\\text{ L}$.\n"
            "  - $V_{ss} = 20 + 50 = 70.0\\text{ L}$. Thể tích $V_\\beta = 3.0 / 0.032 = 93.75\\text{ L}$.\n"
            "  - $AUC_{0-\\infty} = \\frac{42.2}{0.468} + \\frac{7.8}{0.032} = 90.17 + 243.75 = 333.9\\text{ mg}\\cdot\\text{h/L}$."
        ),
        notes=(
            "- **Hình dạng đường cong:** Đồ thị bán logarit gồm 2 đoạn dốc rõ rệt: đoạn đầu dốc đứng (pha $\\alpha$, thuốc vừa sang mô vừa bị thải trừ), đoạn sau thoai thoải hơn (pha $\\beta$, cân bằng phân bố mô đã thiết lập).\n"
            "- **Lưu ý lâm sàng:** Khi tính liều nạp ban đầu ($Dose_{\\text{loading}} = V \\cdot C_{\\text{target}}$), TUYỆT ĐỐI không dùng $V_\\beta$ vì sẽ gây quá liều độc tính nghiêm trọng; chỉ dùng $V_c$ (nếu muốn đạt đỉnh an toàn tức thì) hoặc $V_{ss}$."
        ),
    ),
    "3. Tiêm tĩnh mạch nhanh (IV Bolus) — 3 Ngăn": CompartmentModelDoc(
        id="iv_bolus_3cpt",
        name="Tiêm tĩnh mạch nhanh (IV Bolus) — Mô hình 3 Ngăn",
        route="iv_bolus",
        compartments=3,
        theory=(
            "**Khái niệm & Nguyên lý:** Thuốc phân bố từ ngăn trung tâm vào 2 ngăn ngoại vi khác biệt về tính chất tưới máu và ái lực liên kết: ngăn ngoại vi nông (mô tưới máu trung bình) và ngăn ngoại vi sâu (mô tưới máu kém, giàu lipid hoặc liên kết bền vững).\n\n"
            "**Đặc điểm ADME:**\n"
            "- *Phân bố:* Trải qua 3 pha động học: phân bố cực nhanh vào các cơ quan trung ương ($\\alpha$), phân bố chuyển tiếp vào mô cơ ($\\beta$), và phân bố/giải phóng chậm từ mô sâu ($\\gamma$).\n"
            "- *Thải trừ:* Thải trừ từ ngăn trung tâm ($k_{10}$); ở pha muộn, tốc độ thải trừ bị khống chế bởi tốc độ nhả thuốc rất chậm từ ngăn sâu trở lại máu ($k_{31}$).\n\n"
            "**Ý nghĩa ngăn:**\n"
            "- *Ngăn 1 (Trung tâm, $V_1$):* Máu và tạng giàu mạch (tim, phổi, gan, não).\n"
            "- *Ngăn 2 (Ngoại vi nông, $V_2$):* Mô cơ và dịch ngoại bào.\n"
            "- *Ngăn 3 (Ngoại vi sâu, $V_3$):* Mô mỡ sâu, xương, protein mô tế bào.\n\n"
            "**Điều kiện áp dụng:** Thuốc thân dầu cao, tích lũy sâu trong mô mỡ hoặc liên kết tế bào đặc hiệu. Ví dụ: Fentanyl, amiodarone, thiopental, propofol."
        ),
        ode_latex=(
            r"\begin{aligned} "
            r"\frac{dX_1(t)}{dt} &= -(k_{10} + k_{12} + k_{13}) X_1 + k_{21} X_2 + k_{31} X_3, \quad X_1(0) = D \\ "
            r"\frac{dX_2(t)}{dt} &= k_{12} X_1 - k_{21} X_2, \quad X_2(0) = 0 \\ "
            r"\frac{dX_3(t)}{dt} &= k_{13} X_1 - k_{31} X_3, \quad X_3(0) = 0 "
            r"\end{aligned}"
        ),
        solution_latex=r"C(t) = A \cdot e^{-\alpha t} + B \cdot e^{-\beta t} + C \cdot e^{-\gamma t}, \qquad C_0 = A + B + C = \frac{D}{V_1}",
        parameters=(
            "- $C(t)$: Nồng độ thuốc trong ngăn trung tâm tại thời điểm $t$ ($\\text{mg/L}$).\n"
            "- $A, B, C$: Hệ số vĩ mô dương tương ứng 3 pha động học ($\\text{mg/L}$), tổng bằng $C(0^+) = D/V_1$ (giá trị ngoại suy ngay sau tiêm, không phải điểm đo tại $t=0$).\n"
            "- $\\alpha > \\beta > \\gamma > 0$: Ba hằng số phân rã vĩ mô ($\\text{h}^{-1}$) là nghiệm của phương trình đặc trưng bậc 3.\n"
            "- $V_1, V_2, V_3$: Thể tích ngăn trung tâm ($V_1$), ngăn nông ($V_2 = V_1 \\frac{k_{12}}{k_{21}}$) và ngăn sâu ($V_3 = V_1 \\frac{k_{13}}{k_{31}}$).\n"
            "- $V_{ss}$: Thể tích trạng thái ổn định ($V_{ss} = V_1 + V_2 + V_3$, đơn vị L).\n"
            "- $Q_2, Q_3$: Độ thanh thải liên ngăn nông ($Q_2 = k_{12} V_1$) và sâu ($Q_3 = k_{13} V_1$).\n"
            "- $t_{1/2,\\alpha}$ (vài phút), $t_{1/2,\\beta}$ (vài giờ), $t_{1/2,\\gamma}$ (thời gian bán thải thực tế, kéo dài nhiều ngày)."
        ),
        example=(
            "**Thuốc gây mê / giảm đau:** Fentanyl liều tiêm tĩnh mạch nhanh $D = 100\\ \\mu\\text{g}$ ($0.1\\text{ mg}$).\n"
            "- **Tham số:** $V_1 = 12.0\\text{ L}, V_2 = 30.0\\text{ L}, V_3 = 250.0\\text{ L} \\Rightarrow V_{ss} = 292.0\\text{ L}$.\n"
            "- $CL = 45.0\\text{ L/h}$ ($750\\text{ mL/min}$, thanh thải gan rất cao).\n"
            "- $t_{1/2,\\alpha} \\approx 1.8\\text{ phút}$; $t_{1/2,\\beta} \\approx 35\\text{ phút}$; $t_{1/2,\\gamma} \\approx 12.5\\text{ giờ}$.\n"
            "- **Diễn giải lâm sàng:** Bệnh nhân hết đau và hồi tỉnh chỉ sau 15–30 phút không phải do thuốc bị chuyển hóa hết, mà do thuốc tái phân bố cực nhanh từ não ($V_1$) sang mô cơ ($V_2$) và mô mỡ ($V_3$). Tuy nhiên, tổng lượng thuốc trong cơ thể vẫn còn rất lớn và đào thải rất chậm với $t_{1/2,\\gamma} = 12.5\\text{ h}$."
        ),
        notes=(
            "- **Cảnh báo quá khớp:** Mô hình 3 ngăn có 6 tham số IV ($CL,V_c,Q_2,V_{p2},Q_3,V_{p3}$), cần mẫu trải đủ pha sớm, giữa và muộn. Ít hơn 15 mẫu, Jacobian thiếu hạng hoặc điều kiện kém là dấu hiệu tham số khó định danh. $C(0^+)$ được ngoại suy từ đường cong, không ghi thành phép đo tại $t=0$."
        ),
    ),
    "4. Truyền tĩnh mạch liên tục (IV Infusion) — 1 Ngăn": CompartmentModelDoc(
        id="iv_infusion_1cpt",
        name="Truyền tĩnh mạch liên tục (IV Infusion) — Mô hình 1 Ngăn",
        route="iv_infusion",
        compartments=1,
        theory=(
            "**Khái niệm & Nguyên lý:** Thuốc được nạp vào ngăn trung tâm với tốc độ không đổi bậc không $R_0 = \\text{Dose}/T_{\\text{inf}}$ trong suốt thời gian truyền $T_{\\text{inf}}$, đồng thời cơ thể đào thải thuốc theo động học bậc nhất.\n\n"
            "**Đặc điểm ADME:**\n"
            "- *Trong khi truyền ($0 \\le t \\le T_{\\text{inf}}$):* Nồng độ tăng dần và tiệm cận nồng độ ổn định $C_{ss}$. Tốc độ tăng nồng độ phụ thuộc hoàn toàn vào $t_{1/2}$ thải trừ của thuốc, không phụ thuộc vào tốc độ truyền $R_0$.\n"
            "- *Sau khi ngừng truyền ($t > T_{\\text{inf}}$):* Quá trình nạp thuốc chấm dứt; nồng độ suy giảm hàm mũ từ đỉnh $C(T_{\\text{inf}})$ theo hằng số đào thải $k_{10}$.\n\n"
            "**Điều kiện áp dụng:** Thuốc truyền tĩnh mạch có thời gian phân bố mô không đáng kể so với thời gian truyền. Ví dụ: Aminoglycoside truyền ngắt quãng 30 phút, theophylline truyền tĩnh mạch."
        ),
        ode_latex=(
            r"\begin{aligned} "
            r"\frac{dC(t)}{dt} &= \frac{R_0}{V_1} - k_{10} C(t), \quad 0 \le t \le T_{\text{inf}} \\ "
            r"\frac{dC(t)}{dt} &= -k_{10} C(t), \quad t > T_{\text{inf}} "
            r"\end{aligned}"
        ),
        solution_latex=(
            r"C(t) = \begin{cases} "
            r"\frac{R_0}{CL} \left( 1 - e^{-k_{10} t} \right), & 0 \le t \le T_{\text{inf}} \\[6pt] "
            r"\frac{R_0}{CL} \left( 1 - e^{-k_{10} T_{\text{inf}}} \right) e^{-k_{10}(t - T_{\text{inf}})}, & t > T_{\text{inf}} "
            r"\end{cases}"
        ),
        parameters=(
            "- $R_0$: Tốc độ truyền tĩnh mạch không đổi bậc 0 ($R_0 = \\frac{D}{T_{\\text{inf}}}$, đơn vị $\\text{mg/h}$).\n"
            "- $T_{\\text{inf}}$: Thời gian truyền tĩnh mạch ($\\text{h}$).\n"
            "- $C_{ss}$: Nồng độ trạng thái ổn định nếu truyền vô hạn định ($C_{ss} = \\frac{R_0}{CL} = \\frac{R_0}{k_{10} V_1}$, đơn vị $\\text{mg/L}$).\n"
            "- Thời gian đạt $C_{ss}$: Đạt $50\\% C_{ss}$ sau $1 \\cdot t_{1/2}$; đạt $90\\% C_{ss}$ sau $3.32 \\cdot t_{1/2}$; đạt $\\approx 97\\% C_{ss}$ sau $5 \\cdot t_{1/2}$.\n"
            "- $MRT_{\\text{inf}}$: Thời gian lưu trú trung bình đường truyền ($MRT_{\\text{inf}} = \\frac{1}{k_{10}} + \\frac{T_{\\text{inf}}}{2}$, cần trừ $T_{\\text{inf}}/2$ để quy về $MRT_{\\text{bolus}}$)."
        ),
        example=(
            "**Truyền Theophylline:** Liều $D = 400\\text{ mg}$ truyền trong $T_{\\text{inf}} = 2.0\\text{ h}$ ($R_0 = 200\\text{ mg/h}$).\n"
            "- Tham số: $CL = 2.8\\text{ L/h}$, $V_1 = 35.0\\text{ L} \\Rightarrow k_{10} = 0.080\\text{ h}^{-1}, t_{1/2} = 8.66\\text{ h}$.\n"
            "- Nồng độ ổn định lý thuyết: $C_{ss} = 200 / 2.8 = 71.43\\text{ mg/L}$.\n"
            "- Nồng độ tại cuối thời gian truyền ($t = 2\\text{h}$): $C(2) = 71.43 \\cdot (1 - e^{-0.080 \\times 2}) = 71.43 \\cdot (1 - 0.8521) = 10.56\\text{ mg/L}$.\n"
            "- Nồng độ sau ngừng truyền 4 giờ ($t = 6\\text{h}$): $C(6) = 10.56 \\cdot e^{-0.080 \\times 4} = 10.56 \\cdot 0.7261 = 7.67\\text{ mg/L}$."
        ),
        notes=(
            "- **Đồ thị đặc trưng:** Đoạn tăng hình chữ S lồi trong pha truyền, đạt đỉnh chính xác tại $t = T_{\\text{inf}}$, sau đó giảm hàm mũ đơn điệu."
        ),
    ),
    "5. Truyền tĩnh mạch liên tục (IV Infusion) — 2 Ngăn": CompartmentModelDoc(
        id="iv_infusion_2cpt",
        name="Truyền tĩnh mạch liên tục (IV Infusion) — Mô hình 2 Ngăn",
        route="iv_infusion",
        compartments=2,
        theory=(
            "**Khái niệm & Nguyên lý:** Nạp thuốc bậc 0 với tốc độ $R_0$ vào ngăn trung tâm trong khi diễn ra đồng thời hai quá trình: phân bố hai chiều với ngăn ngoại vi và đào thải khỏi cơ thể.\n\n"
            "**Đặc điểm ADME:**\n"
            "- *Trong truyền:* Nồng độ tăng uốn lượn do thuốc vừa tích lũy vừa khuếch tán sang mô ngoại vi.\n"
            "- *Sau ngừng truyền:* Đỉnh đạt tại $t = T_{\\text{inf}}$, tiếp theo là 2 pha suy giảm: pha phân bố mô $\\alpha$ và pha thải trừ $\\beta$.\n\n"
            "**Ý nghĩa lâm sàng / TDM:** Vancomycin, phenytoin, digoxin truyền tĩnh mạch ngắt quãng 1 giờ."
        ),
        ode_latex=(
            r"\begin{aligned} "
            r"\frac{dX_1(t)}{dt} &= R_0 \mathbf{1}_{[0,T_{\mathrm{inf}}]}(t) - (k_{10} + k_{12}) X_1 + k_{21} X_2 \\ "
            r"\frac{dX_2(t)}{dt} &= k_{12} X_1 - k_{21} X_2 "
            r"\end{aligned} \quad X_1(0)=X_2(0)=0"
        ),
        solution_latex=(
            r"C(t) = \begin{cases} "
            r"\frac{R_0}{V_1} \left[ \frac{k_{21} - \alpha}{\alpha(\beta - \alpha)} (1 - e^{-\alpha t}) + \frac{k_{21} - \beta}{\beta(\alpha - \beta)} (1 - e^{-\beta t}) \right], & t \le T_{\text{inf}} \\[6pt] "
            r"\frac{R_0}{V_1} \left[ \frac{k_{21} - \alpha}{\alpha(\beta - \alpha)} (1 - e^{-\alpha T_{\text{inf}}}) e^{-\alpha(t - T_{\text{inf}})} + \frac{k_{21} - \beta}{\beta(\alpha - \beta)} (1 - e^{-\beta T_{\text{inf}}}) e^{-\beta(t - T_{\text{inf}})} \right], & t > T_{\text{inf}} "
            r"\end{cases}"
        ),
        parameters=(
            "- $R_0, T_{\\text{inf}}$: Tốc độ truyền ($\\text{mg/h}$) và thời gian truyền ($\\text{h}$).\n"
            "- $C_{ss} = \\frac{R_0}{CL} = \\frac{R_0}{k_{10} V_1}$ (trạng thái ổn định không phụ thuộc vào $V_2$).\n"
            "- $V_1, V_2, V_{ss}, Q, CL, t_{1/2,\\alpha}, t_{1/2,\\beta}$ định nghĩa đồng nhất như mô hình IV Bolus 2 ngăn.\n"
            "- $AUC_{0-\\infty} = \\frac{\\text{Dose}}{CL}$."
        ),
        example=(
            "**Kháng sinh Vancomycin:** Liều $1000\\text{ mg}$ truyền trong $T_{\\text{inf}} = 1.0\\text{ h}$ ($R_0 = 1000\\text{ mg/h}$).\n"
            "- Tham số: $V_1 = 15.0\\text{ L}, k_{10} = 0.20\\text{ h}^{-1}, k_{12} = 0.30\\text{ h}^{-1}, k_{21} = 0.15\\text{ h}^{-1}$.\n"
            "- $CL = 3.0\\text{ L/h}, V_2 = 30.0\\text{ L}, V_{ss} = 45.0\\text{ L}$.\n"
            "- Tại $t = 1\\text{h}$ (ngắt truyền): $C_{\\text{peak}} \\approx 42.0\\text{ mg/L}$.\n"
            "- Tại $t = 2\\text{h}$ (1 giờ sau ngắt truyền, kết thúc pha $\\alpha$): $C(2) \\approx 26.5\\text{ mg/L}$.\n"
            "- Tại $t = 12\\text{h}$ (thời điểm đáy $C_{\\text{trough}}$): $C(12) \\approx 12.5\\text{ mg/L}$ (đạt đích điều trị $10 - 15\\text{ mg/L}$)."
        ),
        notes=(
            "- **Quy tắc vàng trong TDM:** Không lấy mẫu nồng độ đỉnh ngay khi vừa rút kim truyền vì sẽ đo phải nồng độ ngăn 1 giả tạo quá cao; bắt buộc phải chờ 1–2 giờ sau khi kết thúc truyền."
        ),
    ),
    "6. Truyền tĩnh mạch liên tục (IV Infusion) — 3 Ngăn": CompartmentModelDoc(
        id="iv_infusion_3cpt",
        name="Truyền tĩnh mạch liên tục (IV Infusion) — Mô hình 3 Ngăn",
        route="iv_infusion",
        compartments=3,
        theory=(
            "**Khái niệm & Nguyên lý:** Truyền thuốc vào ngăn trung tâm liên thông với 2 ngăn ngoại vi nông và sâu. Mô hình kinh điển trong gây mê hồi sức và truyền thuốc kiểm soát nồng độ đích (TCI - Target Controlled Infusion).\n\n"
            "**Đặc điểm ADME & Khái niệm CSHT:**\n"
            "- *Thời gian bán thải phụ thuộc bối cảnh (Context-Sensitive Half-Time - CSHT):* Thời gian cần thiết để nồng độ thuốc trong huyết tương giảm $50\\%$ sau khi ngừng truyền một khoảng thời gian nhất định.\n"
            "- Với mô hình 1 ngăn, CSHT là hằng số ($t_{1/2}$). Nhưng với mô hình 3 ngăn, khi thời gian truyền càng kéo dài, lượng thuốc bão hòa ở ngăn sâu $V_3$ càng lớn, làm CSHT tăng vọt."
        ),
        ode_latex=(
            r"\begin{aligned} "
            r"\frac{dX_1}{dt} &= R_0 \mathbf{1}_{[0,T_{\mathrm{inf}}]}(t) - (k_{10} + k_{12} + k_{13}) X_1 + k_{21} X_2 + k_{31} X_3 \\ "
            r"\frac{dX_2}{dt} &= k_{12} X_1 - k_{21} X_2, \qquad \frac{dX_3}{dt} = k_{13} X_1 - k_{31} X_3 "
            r"\end{aligned}"
        ),
        solution_latex=(
            r"C(t) = \begin{cases} "
            r"\sum_{i \in \{\alpha, \beta, \gamma\}} \frac{L_i}{\lambda_i} \left( 1 - e^{-\lambda_i t} \right), & t \le T_{\text{inf}} \\[6pt] "
            r"\sum_{i \in \{\alpha, \beta, \gamma\}} \frac{L_i}{\lambda_i} \left( 1 - e^{-\lambda_i T_{\text{inf}}} \right) e^{-\lambda_i (t - T_{\text{inf}})}, & t > T_{\text{inf}} "
            r"\end{cases}"
        ),
        parameters=(
            "- $\\lambda_i \\in \\{\\alpha, \\beta, \\gamma\\}$: Nghiệm phân rã của hệ thống 3 ngăn ($\\text{h}^{-1}$).\n"
            "- $R_0=D/T_{\\text{inf}}$ (mg/h); $X_1(0)=X_2(0)=X_3(0)=0$ nếu chỉ truyền một liều, không có liều nạp.\n"
            "- $L_i=(R_0/V_c)w_i$ với $w_i$ là trọng số phổ của ngăn trung tâm, $\\sum_i w_i=1$; hằng số $L_i$ có đơn vị nồng độ/thời gian.\n"
            "- 6 tham số ước lượng: $CL,V_c,Q_2,V_{p2},Q_3,V_{p3}$; $CL = k_{10} V_c$, $V_{ss} = V_c + V_{p2} + V_{p3}$."
        ),
        example=(
            "**Gây mê Propofol:** Truyền duy trì nồng độ đích với liều nạp $150\\text{ mg}$ và tốc độ truyền duy trì $R_0 = 600\\text{ mg/h}$: $CL = 1.8\\text{ L/min} = 108\\text{ L/h}, V_1 = 16\\text{ L}, V_2 = 30\\text{ L}, V_3 = 200\\text{ L}$ ($V_{ss} = 246\\text{ L}$).\n"
            "- Nếu truyền ngắn 1 giờ: CSHT $\\approx 10\\text{ phút}$ (bệnh nhân tỉnh mê sau 10 phút).\n"
            "- Nếu truyền kéo dài 8 giờ trong phòng ICU: CSHT tăng lên gần $40\\text{ phút}$ do thuốc từ ngăn 3 giải phóng ngược trở lại máu kéo dài thời gian thức tỉnh."
        ),
        notes=(
            "- **Phạm vi:** Bộ khớp hiện tại mô phỏng một lần truyền với tốc độ cố định $R_0=D/T_{\\text{inf}}$ (và chồng chất liều tuyến tính khi chọn đa liều). Ví dụ TCI có liều nạp và tốc độ biến đổi cần mô hình truyền riêng."
        ),
    ),
    "7. Đường uống (Oral) — 1 Ngăn (Bateman)": CompartmentModelDoc(
        id="oral_1cpt",
        name="Đường uống (Oral) — Mô hình 1 Ngăn (Phương trình Bateman)",
        route="oral",
        compartments=1,
        theory=(
            "**Khái niệm & Nguyên lý:** Thuốc được đưa vào ống tiêu hóa, sau đó hấp thu qua niêm mạc ruột vào ngăn trung tâm theo động học bậc 1 với hằng số $k_a$. Phân bố tức thời vào ngăn duy nhất $V_1$ và thải trừ bậc 1 với $k_{el}$. Bộ khớp hiện tại không ước lượng thời gian trễ hấp thu.\n\n"
            "**Hiện tượng tráo đổi nghiệm (Flip-flop Kinetics):**\n"
            "- Bình thường: Tốc độ hấp thu nhanh hơn nhiều so với tốc độ thải trừ ($k_a \\gg k_{el}$).\n"
            "- Hiện tượng Flip-flop ($k_a \\ll k_{el}$): Gặp ở viên phóng thích kéo dài (ER/MR) hoặc hoạt chất rất kém tan; khi đó độ dốc pha cuối biểu kiến trên đồ thị bán logarit phản ánh hằng số hấp thu $k_a$ chứ KHÔNG PHẢI $k_{el}$."
        ),
        ode_latex=(
            r"\begin{aligned} "
            r"\frac{dX_a(t)}{dt} &= -k_a X_a(t), \quad X_a(0) = F \cdot D \\ "
            r"\frac{dX_1(t)}{dt} &= k_a X_a(t) - k_{el} X_1(t), \quad X_1(0) = 0 "
            r"\end{aligned}"
        ),
        solution_latex=r"C(t) = \frac{F \cdot D \cdot k_a}{V_1 (k_a - k_{el})} \left( e^{-k_{el}t} - e^{-k_a t} \right) \quad (t \ge 0)",
        parameters=(
            "- $C(t)$: Nồng độ thuốc tại thời điểm $t$ ($\\text{mg/L}$).\n"
            "- $F$: Sinh khả dụng tuyệt đối đường uống ($0 < F \\le 1$); khi không có số liệu IV, tham số ước tính dưới dạng biểu kiến $V_1/F$ và $CL/F$.\n"
            "- $k_a$: Hằng số tốc độ hấp thu bậc 1 ($\\text{h}^{-1}$).\n"
            "- $k_{el}$: Hằng số tốc độ đào thải bậc 1 ($\\text{h}^{-1}$, $k_{el} = CL/V_1$).\n"
            "- $T_{\\max} = \\frac{\\ln(k_a / k_{el})}{k_a - k_{el}}$; $C_{\\max} = C(T_{\\max})$. Thời gian trễ hấp thu không được ước lượng trong phiên bản này."
        ),
        example=(
            "**Paracetamol viên nén 500 mg:**\n"
            "- Tham số minh họa: $k_a = 1.80\\text{ h}^{-1}$, $k_{el} = 0.280\\text{ h}^{-1}$, $V_1/F = 50.0\\text{ L}$; giả định không có thời gian trễ hấp thu.\n"
            "- $T_{\\max} = \\frac{\\ln(1.80 / 0.280)}{1.80 - 0.280} = \\frac{1.8608}{1.520} = 1.22\\text{ giờ}$.\n"
            "- $C_{\\max} \\approx 7.10\\text{ mg/L}$.\n"
            "- $CL/F = 0.280 \\times 50.0 = 14.0\\text{ L/h}$.\n"
            "- $t_{1/2} = 0.693 / 0.280 = 2.48\\text{ giờ}$.\n"
            "- $AUC_{0-\\infty} = 500 / 14.0 = 35.71\\text{ mg}\\cdot\\text{h/L}$."
        ),
        notes=(
            "- **Đồ thị đặc trưng:** Đi lên từ 0 khi hấp thu bắt đầu tại $t=0$, đạt cực đại nhẵn tại $T_{\\max}$, sau đó suy giảm tiệm cận đường thẳng trên thang bán logarit."
        ),
    ),
    "8. Đường uống (Oral) — 2 Ngăn": CompartmentModelDoc(
        id="oral_2cpt",
        name="Đường uống (Oral) — Mô hình 2 Ngăn",
        route="oral",
        compartments=2,
        theory=(
            "**Khái niệm & Nguyên lý:** Thuốc hấp thu bậc 1 từ ruột ($k_a$) vào ngăn trung tâm ($V_1$), đồng thời phân bố sang ngăn ngoại vi ($V_2$) và thải trừ khỏi ngăn trung tâm.\n\n"
            "**Đặc điểm ADME:** Đường cong phản ánh sự kết hợp của 3 pha: hấp thu, phân bố mô và thải trừ.\n\n"
            "**Điều kiện áp dụng:** Thuốc uống có pha phân bố mô rõ rệt sau khi đạt đỉnh hấp thu. Ví dụ: Ciprofloxacin, omeprazole."
        ),
        ode_latex=(
            r"\begin{aligned} "
            r"\frac{dX_a}{dt} &= -k_a X_a, \quad X_a(0) = F \cdot D \\ "
            r"\frac{dX_1}{dt} &= k_a X_a - (k_{10} + k_{12}) X_1 + k_{21} X_2 \\ "
            r"\frac{dX_2}{dt} &= k_{12} X_1 - k_{21} X_2 "
            r"\end{aligned}"
        ),
        solution_latex=r"C(t) = A \cdot e^{-\alpha t} + B \cdot e^{-\beta t} - (A + B) e^{-k_a t}",
        parameters=(
            "- $A, B$: Hệ số vĩ mô của pha $\\alpha$ và $\\beta$ ($\\text{mg/L}$); dấu của từng hệ số phụ thuộc tương quan giữa $k_a$ và các tốc độ phân rã.\n"
            "- $-(A+B)$: Hệ số pha hấp thu $k_a$, bảo đảm $C(0) = 0$; mô hình không khớp thời gian trễ hấp thu.\n"
            "- $V_1/F, V_2/F, V_{ss}/F, CL/F, Q/F$: Các thể tích và độ thanh thải biểu kiến sau đường uống."
        ),
        example=(
            "**Ciprofloxacin 500 mg viên nén:**\n"
            "- Tham số: $k_a = 1.20\\text{ h}^{-1}, \\alpha = 0.80\\text{ h}^{-1}, \\beta = 0.140\\text{ h}^{-1}, V_1/F = 60.0\\text{ L}$.\n"
            "- $T_{\\max} \\approx 1.50\\text{ h}, C_{\\max} \\approx 2.40\\text{ mg/L}$.\n"
            "- $t_{1/2,\\alpha} = 0.87\\text{ h}, t_{1/2,\\beta} = 4.95\\text{ h}$. $CL/F \\approx 35.0\\text{ L/h}$."
        ),
        notes=(
            "- **Nguy cơ lỗi thuật toán:** Khi dữ liệu lấy mẫu sau đỉnh quá thưa, thuật toán sẽ không phân tách được $k_{12}$ và $k_{21}$, dẫn đến lỗi ma trận kỳ dị."
        ),
    ),
    "9. Đường uống (Oral) — 3 Ngăn": CompartmentModelDoc(
        id="oral_3cpt",
        name="Đường uống (Oral) — Mô hình 3 Ngăn",
        route="oral",
        compartments=3,
        theory=(
            "**Khái niệm & Nguyên lý:** Thuốc hấp thu bậc nhất từ ruột vào ngăn trung tâm, liên thông với ngăn nông và ngăn sâu. Bộ khớp dùng 7 tham số biểu kiến $CL/F,V_c/F,Q_2/F,V_{p2}/F,Q_3/F,V_{p3}/F,k_a$; không khớp thời gian trễ hấp thu.\n\n"
            "**Đặc điểm ADME:** Nghiệm gồm 4 hàm mũ (3 tốc độ phân bố/thải trừ và 1 tốc độ hấp thu); hệ số từng hàm mũ có thể mang dấu khác nhau khi hấp thu chậm. Thể tích phân bố biểu kiến $V_{ss}/F$ có thể lớn khi thuốc tích lũy ở mô sâu.\n\n"
            "**Điều kiện áp dụng:** Thuốc thân dầu cao, tích lũy sâu trong tế bào và mô mỡ. Ví dụ: Azithromycin, amiodarone, chloroquine."
        ),
        ode_latex=(
            r"\begin{aligned} "
            r"\frac{dX_a}{dt} &= -k_a X_a \\ "
            r"\frac{dX_1}{dt} &= k_a X_a - (k_{10} + k_{12} + k_{13}) X_1 + k_{21} X_2 + k_{31} X_3 \\ "
            r"\frac{dX_2}{dt} &= k_{12} X_1 - k_{21} X_2, \quad \frac{dX_3}{dt} = k_{13} X_1 - k_{31} X_3 "
            r"\end{aligned}"
        ),
        solution_latex=r"C(t) = A \cdot e^{-\alpha t} + B \cdot e^{-\beta t} + C \cdot e^{-\gamma t} - (A + B + C) \cdot e^{-k_a t}",
        parameters=(
            "- $A, B, C$: Hệ số vĩ mô ($\\text{mg/L}$); dấu của chúng phụ thuộc $k_a$ so với $\\alpha,\\beta,\\gamma$. Hệ số pha hấp thu bằng $-(A+B+C)$ để thỏa mãn $C(0) = 0$.\n"
            "- $\\alpha, \\beta, \\gamma$: Hằng số tốc độ 3 pha động học ($\\text{h}^{-1}$).\n"
            "- $V_{ss}/F = \\frac{V_1}{F} [1 + \\frac{k_{12}}{k_{21}} + \\frac{k_{13}}{k_{31}}]$, đơn vị L.\n"
            "- $t_{1/2,\\gamma} = \\frac{\\ln 2}{\\gamma}$ (thời gian bán thải pha cuối thực tế)."
        ),
        example=(
            "**Azithromycin 500 mg uống:**\n"
            "- $F \\approx 0.37, V_{ss}/F \\approx 2500\\text{ L}, CL/F \\approx 40\\text{ L/h}$.\n"
            "- $t_{1/2,\\alpha} \\approx 1.5\\text{ h}, t_{1/2,\\beta} \\approx 10\\text{ h}, t_{1/2,\\gamma} \\approx 68\\text{ giờ}$.\n"
            "- Thuốc duy trì nồng độ kháng khuẩn trong mô phổi nhiều ngày sau khi kết thúc đợt điều trị 3 ngày."
        ),
        notes=(
            "- **Đánh giá độ tin cậy:** So sánh AICc/BIC khi các mô hình khớp trên cùng dữ liệu và trọng số, kiểm tra phần dư, độ phủ ba pha, hạng và điều kiện Jacobian cùng các cảnh báo tham số sát biên. AICc tính từ phần dư có trọng số chỉ mang tính chẩn đoán; phiên bản hiện tại chưa tính %RSE và không áp dụng ngưỡng ΔAICc cứng."
        ),
    ),
}


def render_compartment_model_details(selected_model_title: str) -> None:
    """Render the standard 5-section pedagogical content for a specific model."""
    doc = MODEL_DOCS.get(selected_model_title)
    if not doc:
        st.info("Đang hiển thị Sơ đồ Kiến trúc Tổng quan của cả 9 mô hình ngăn bên dưới.")
        return

    st.markdown(f"### {doc.name}")

    # A. Cơ sở lý thuyết
    st.markdown("#### A. Cơ sở lý thuyết & Sinh dược học")
    st.markdown(doc.theory)

    # B. Sơ đồ minh họa
    st.markdown("#### B. Sơ đồ minh họa kiến trúc ngăn")
    svg_diag = get_diagram_compartment(doc.route, doc.compartments)
    try:
        st.image(svg_diag, use_container_width=True)
    except TypeError:
        st.image(svg_diag, width="stretch")

    # C. Hệ phương trình toán học
    st.markdown("#### C. Hệ phương trình toán học & Nghiệm giải tích")
    st.caption("Hệ phương trình vi phân mô tả biến thiên lượng/nồng độ:")
    st.latex(doc.ode_latex)
    st.caption("Phương trình nghiệm giải tích C(t):")
    st.latex(doc.solution_latex)

    # D. Các thông số dược động học
    st.markdown("#### D. Các thông số dược động học & Quan hệ Micro/Macro")
    st.markdown(doc.parameters)

    # E. Minh họa và diễn giải kết quả
    st.markdown("#### E. Minh họa và diễn giải kết quả")
    st.markdown(doc.example)
    st.markdown(doc.notes)
