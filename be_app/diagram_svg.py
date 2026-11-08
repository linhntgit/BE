"""Vector SVG graphical diagrams for pharmacokinetic and bioequivalence teaching modules."""

def _svg_wrapper(width: int, height: int, content: str) -> str:
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" '
        f'width="{width}" height="{height}">\n'
        f'  <defs>\n'
        f'    <marker id="arrow" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">\n'
        f'      <path d="M 0 1 L 10 5 L 0 9 z" fill="#2563eb" />\n'
        f'    </marker>\n'
        f'    <marker id="arrow-slate" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">\n'
        f'      <path d="M 0 1 L 10 5 L 0 9 z" fill="#475569" />\n'
        f'    </marker>\n'
        f'    <marker id="arrow-green" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">\n'
        f'      <path d="M 0 1 L 10 5 L 0 9 z" fill="#16a34a" />\n'
        f'    </marker>\n'
        f'    <marker id="arrow-red" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">\n'
        f'      <path d="M 0 1 L 10 5 L 0 9 z" fill="#dc2626" />\n'
        f'    </marker>\n'
        f'    <marker id="arrow-purple" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">\n'
        f'      <path d="M 0 1 L 10 5 L 0 9 z" fill="#9333ea" />\n'
        f'    </marker>\n'
        f'    <marker id="arrow-amber" viewBox="0 0 10 10" refX="6" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">\n'
        f'      <path d="M 0 1 L 10 5 L 0 9 z" fill="#d97706" />\n'
        f'    </marker>\n'
        f'  </defs>\n'
        f'  <rect width="100%" height="100%" fill="#ffffff" rx="10" stroke="#e2e8f0" stroke-width="1.5"/>\n'
        f'{content}\n'
        f'</svg>'
    )


# -----------------------------------------------------------------------------
# Lesson 0: Study Setup & Governance
# -----------------------------------------------------------------------------
def get_diagram_0() -> str:
    content = """  <text x="380" y="26" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" font-weight="700" fill="#0f172a">Quy trình Thiết kế &amp; Khởi tạo Nghiên cứu Bất biến</text>
  <g transform="translate(20, 45)">
    <!-- Step 1 -->
    <rect x="0" y="0" width="160" height="60" rx="8" fill="#f8fafc" stroke="#3b82f6" stroke-width="1.5"/>
    <text x="80" y="24" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#1e40af">1. Đề cương &amp; SAP</text>
    <text x="80" y="44" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#64748b">Phê duyệt trước thử</text>

    <line x1="160" y1="30" x2="190" y2="30" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <!-- Step 2 -->
    <rect x="190" y="0" width="165" height="60" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
    <text x="272" y="24" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#92400e">2. Hàm lượng T vs R</text>
    <text x="272" y="44" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#b45309">Chênh lệch ≤ 5%</text>

    <line x1="355" y1="30" x2="385" y2="30" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <!-- Step 3 -->
    <rect x="385" y="0" width="165" height="60" rx="8" fill="#f3e8ff" stroke="#9333ea" stroke-width="1.5"/>
    <text x="467" y="24" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#6b21a8">3. Điều kiện dùng</text>
    <text x="467" y="44" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#7e22ce">Đói (≥10h) hoặc No</text>

    <line x1="550" y1="30" x2="580" y2="30" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <!-- Step 4 -->
    <rect x="580" y="0" width="140" height="60" rx="8" fill="#dcfce7" stroke="#16a34a" stroke-width="1.5"/>
    <text x="650" y="24" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#166534">4. Băm SHA-256</text>
    <text x="650" y="44" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#15803d">Khóa nghiên cứu</text>
  </g>"""
    return _svg_wrapper(760, 130, content)


# -----------------------------------------------------------------------------
# Lesson 1: Sample Size & Protocol Design
# -----------------------------------------------------------------------------
def get_diagram_1() -> str:
    content = """  <text x="380" y="26" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" font-weight="700" fill="#0f172a">Thuật toán Ước tính Cỡ mẫu Phân bố t Không tâm (Owen's Q / Diletti)</text>
  <g transform="translate(15, 45)">
    <rect x="0" y="0" width="155" height="65" rx="8" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.5"/>
    <text x="77" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#1e40af">CV_intra (%)</text>
    <text x="77" y="48" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#3b82f6">Từ pilot / y văn</text>

    <line x1="155" y1="32" x2="185" y2="32" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <rect x="185" y="0" width="165" height="65" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
    <text x="267" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#92400e">Phương sai logarit</text>
    <text x="267" y="48" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="600" fill="#b45309">s² = ln(CV² + 1)</text>

    <line x1="350" y1="32" x2="380" y2="32" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <rect x="380" y="0" width="180" height="65" rx="8" fill="#f3e8ff" stroke="#9333ea" stroke-width="1.5"/>
    <text x="470" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#6b21a8">Tích phân Non-central t</text>
    <text x="470" y="48" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#7e22ce">Power ≥ 80% (α=0.05)</text>

    <line x1="560" y1="32" x2="590" y2="32" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <rect x="590" y="0" width="140" height="65" rx="8" fill="#dcfce7" stroke="#16a34a" stroke-width="1.5"/>
    <text x="660" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#166534">N_evaluable</text>
    <text x="660" y="48" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#15803d">Bù Dropout → N tuyển</text>
  </g>"""
    return _svg_wrapper(760, 135, content)


# -----------------------------------------------------------------------------
# Lesson 2: Sampling Schedule & Pharmacokinetic Profile
# -----------------------------------------------------------------------------
def get_diagram_2() -> str:
    content = """  <text x="380" y="24" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" font-weight="700" fill="#0f172a">Đồ thị Nồng độ Dược động học Chuẩn &amp; Quy chuẩn Lịch Lấy mẫu</text>
  <g transform="translate(40, 35)">
    <!-- Axes -->
    <line x1="40" y1="140" x2="680" y2="140" stroke="#334155" stroke-width="2" marker-end="url(#arrow-slate)"/>
    <line x1="40" y1="140" x2="40" y2="10" stroke="#334155" stroke-width="2" marker-end="url(#arrow-slate)"/>
    <text x="685" y="145" font-family="system-ui, sans-serif" font-size="11" font-weight="600" fill="#334155">Thời gian (t)</text>
    <text x="35" y="10" text-anchor="end" font-family="system-ui, sans-serif" font-size="11" font-weight="600" fill="#334155">Nồng độ (C)</text>

    <!-- Curve Area fill -->
    <path d="M 40 140 Q 90 20 180 30 T 360 115 T 520 135 L 520 140 Z" fill="#dbeafe" opacity="0.6"/>

    <!-- PK Curve line -->
    <path d="M 40 140 Q 90 20 180 30 T 360 115 T 520 135" fill="none" stroke="#2563eb" stroke-width="2.5"/>

    <!-- LLOQ dashed line -->
    <line x1="40" y1="135" x2="550" y2="135" stroke="#94a3b8" stroke-width="1.5" stroke-dasharray="4,4"/>
    <text x="555" y="138" font-family="system-ui, sans-serif" font-size="10" fill="#64748b">LLOQ</text>

    <!-- Sampling points -->
    <circle cx="40" cy="140" r="4" fill="#1e40af"/>
    <circle cx="70" cy="95" r="3.5" fill="#1e40af"/>
    <circle cx="105" cy="55" r="3.5" fill="#1e40af"/>
    <circle cx="140" cy="35" r="3.5" fill="#1e40af"/>

    <!-- Cmax / Tmax peak -->
    <circle cx="180" cy="30" r="5" fill="#dc2626"/>
    <line x1="180" y1="30" x2="180" y2="140" stroke="#dc2626" stroke-width="1.5" stroke-dasharray="3,3"/>
    <line x1="40" y1="30" x2="180" y2="30" stroke="#dc2626" stroke-width="1.5" stroke-dasharray="3,3"/>
    <text x="180" y="20" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#dc2626">Cmax tại Tmax</text>

    <!-- More points -->
    <circle cx="230" cy="48" r="3.5" fill="#1e40af"/>
    <circle cx="280" cy="75" r="3.5" fill="#1e40af"/>
    <circle cx="340" cy="108" r="3.5" fill="#1e40af"/>
    <circle cx="410" cy="125" r="3.5" fill="#1e40af"/>
    <circle cx="470" cy="132" r="3.5" fill="#1e40af"/>
    <circle cx="520" cy="135" r="4" fill="#16a34a"/>

    <text x="520" y="155" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="600" fill="#166534">t_last ≥ 3·t½</text>
    <text x="280" y="100" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#1e40af">AUC(0-t)</text>

    <!-- Phase Annotations -->
    <text x="100" y="125" font-family="system-ui, sans-serif" font-size="9" fill="#2563eb">≥3 điểm hấp thu</text>
    <text x="390" y="105" font-family="system-ui, sans-serif" font-size="9" fill="#2563eb">≥3-4 điểm thải trừ (λz)</text>

    <!-- Washout Period -->
    <rect x="545" y="45" width="145" height="45" rx="6" fill="#fef3c7" stroke="#d97706" stroke-width="1.2"/>
    <text x="617" y="64" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#92400e">WASHOUT PERIOD</text>
    <text x="617" y="78" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" fill="#b45309">≥ 5 đến 7 lần t½ → Kỳ 2</text>
  </g>"""
    return _svg_wrapper(760, 210, content)


# -----------------------------------------------------------------------------
# Lesson 3: Data Import & Mapping
# -----------------------------------------------------------------------------
def get_diagram_3() -> str:
    content = """  <text x="380" y="24" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" font-weight="700" fill="#0f172a">Quy trình Thu nhận &amp; Ánh xạ Dữ liệu Sắc ký LC-MS/MS</text>
  <g transform="translate(15, 42)">
    <rect x="0" y="0" width="160" height="65" rx="8" fill="#f8fafc" stroke="#64748b" stroke-width="1.5"/>
    <text x="80" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#334155">Tệp LIMS / LC-MS</text>
    <text x="80" y="46" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#64748b">CSV / Excel nguồn</text>

    <line x1="160" y1="32" x2="190" y2="32" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <rect x="190" y="0" width="165" height="65" rx="8" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.5"/>
    <text x="272" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#1e40af">Ánh xạ 5 Cột Chuẩn</text>
    <text x="272" y="46" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#3b82f6">Subj, Seq, Per, Trt, Conc</text>

    <line x1="355" y1="32" x2="385" y2="32" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <rect x="385" y="0" width="170" height="65" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
    <text x="470" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#92400e">Quy tắc Xử lý BLQ</text>
    <text x="470" y="46" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#b45309">Predose=0 · Sau Clast=Bỏ</text>

    <line x1="555" y1="32" x2="585" y2="32" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <rect x="585" y="0" width="145" height="65" rx="8" fill="#dcfce7" stroke="#16a34a" stroke-width="1.5"/>
    <text x="657" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#166534">Lưu trữ Bất biến</text>
    <text x="657" y="46" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#15803d">Ghi băm SHA-256</text>
  </g>"""
    return _svg_wrapper(760, 135, content)


# -----------------------------------------------------------------------------
# Lesson 4: QC Gates & Data Freeze
# -----------------------------------------------------------------------------
def get_diagram_4() -> str:
    content = """  <text x="380" y="24" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" font-weight="700" fill="#0f172a">Hệ thống Kiểm tra QC Dữ liệu Tự động &amp; Khóa Niêm phong Data Freeze</text>
  <g transform="translate(20, 40)">
    <!-- Input -->
    <rect x="0" y="25" width="135" height="55" rx="8" fill="#f8fafc" stroke="#64748b" stroke-width="1.5"/>
    <text x="67" y="48" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#334155">Bảng Dữ liệu Thô</text>
    <text x="67" y="66" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#64748b">Nồng độ &amp; Thời gian</text>

    <line x1="135" y1="52" x2="175" y2="52" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <!-- 4 QC Gates -->
    <rect x="175" y="10" width="190" height="85" rx="8" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.5"/>
    <text x="270" y="30" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#1e40af">Bộ Kiểm tra 4 Cổng QC</text>
    <text x="185" y="50" font-family="system-ui, sans-serif" font-size="10" fill="#3b82f6">• C_predose &gt; 5% Cmax</text>
    <text x="185" y="66" font-family="system-ui, sans-serif" font-size="10" fill="#3b82f6">• Nồng độ âm hoặc thiếu</text>
    <text x="185" y="82" font-family="system-ui, sans-serif" font-size="10" fill="#3b82f6">• Sai thứ tự thời gian / trùng</text>

    <!-- Branching -->
    <line x1="365" y1="35" x2="415" y2="20" stroke="#16a34a" stroke-width="2" marker-end="url(#arrow-green)"/>
    <line x1="365" y1="70" x2="415" y2="85" stroke="#dc2626" stroke-width="2" marker-end="url(#arrow-red)"/>

    <!-- Clean -->
    <rect x="415" y="2" width="140" height="38" rx="6" fill="#dcfce7" stroke="#16a34a" stroke-width="1.2"/>
    <text x="485" y="22" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#166534">Dữ liệu hợp lệ (Clean)</text>

    <!-- Error -->
    <rect x="415" y="68" width="140" height="38" rx="6" fill="#fee2e2" stroke="#dc2626" stroke-width="1.2"/>
    <text x="485" y="84" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#991b1b">Hiệu chỉnh có Phê duyệt</text>
    <text x="485" y="97" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" fill="#b91c1c">Ghi nhật ký Audit Trail</text>

    <!-- Merge to Freeze -->
    <line x1="555" y1="21" x2="595" y2="45" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>
    <line x1="555" y1="87" x2="595" y2="60" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <rect x="595" y="25" width="125" height="55" rx="8" fill="#ede9fe" stroke="#7c3aed" stroke-width="2"/>
    <text x="657" y="47" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#5b21b6">DATA FREEZE</text>
    <text x="657" y="66" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#6d28d9">Khóa SAP phân tích</text>
  </g>"""
    return _svg_wrapper(760, 160, content)


# -----------------------------------------------------------------------------
# Lesson 5: NCA Lin-Log Trapezoid
# -----------------------------------------------------------------------------
def get_diagram_5() -> str:
    content = """  <text x="380" y="24" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" font-weight="700" fill="#0f172a">Phương pháp Tích phân Hình thang Tuyến tính – Logarit (Linear-Log Trapezoidal Rule)</text>
  <g transform="translate(30, 40)">
    <!-- Left: Linear Trapezoid (Absorption) -->
    <g transform="translate(0, 0)">
      <rect width="330" height="150" fill="#f8fafc" rx="8" stroke="#cbd5e1"/>
      <text x="165" y="22" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#1e40af">1. Pha Hấp thu (C_{i+1} ≥ C_i): Hình thang Tuyến tính</text>
      
      <!-- Coordinate lines -->
      <line x1="45" y1="120" x2="280" y2="120" stroke="#64748b" stroke-width="1.5"/>
      <line x1="45" y1="120" x2="45" y2="35" stroke="#64748b" stroke-width="1.5"/>

      <!-- Trapezoid polygon -->
      <polygon points="90,120 90,85 210,50 210,120" fill="#bfdbfe" stroke="#2563eb" stroke-width="2"/>

      <text x="90" y="135" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#475569">t_i</text>
      <text x="210" y="135" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#475569">t_{i+1}</text>
      <text x="80" y="85" text-anchor="end" font-family="system-ui, sans-serif" font-size="10" font-weight="600" fill="#1e40af">C_i</text>
      <text x="220" y="50" text-anchor="start" font-family="system-ui, sans-serif" font-size="10" font-weight="600" fill="#1e40af">C_{i+1}</text>

      <text x="150" y="90" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#1d4ed8">ΔAUC = ½(C_i + C_{i+1})·Δt</text>
    </g>

    <!-- Right: Log Trapezoid (Elimination) -->
    <g transform="translate(370, 0)">
      <rect width="330" height="150" fill="#f8fafc" rx="8" stroke="#cbd5e1"/>
      <text x="165" y="22" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#92400e">2. Pha Thải trừ (C_{i+1} &lt; C_i): Hình thang Logarit</text>
      
      <!-- Coordinate lines -->
      <line x1="45" y1="120" x2="280" y2="120" stroke="#64748b" stroke-width="1.5"/>
      <line x1="45" y1="120" x2="45" y2="35" stroke="#64748b" stroke-width="1.5"/>

      <!-- Curved/Log Trapezoid representation -->
      <path d="M 90 120 L 90 50 Q 140 75 210 95 L 210 120 Z" fill="#fde68a" stroke="#d97706" stroke-width="2"/>

      <text x="90" y="135" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#475569">t_i</text>
      <text x="210" y="135" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#475569">t_{i+1}</text>
      <text x="80" y="50" text-anchor="end" font-family="system-ui, sans-serif" font-size="10" font-weight="600" fill="#92400e">C_i</text>
      <text x="220" y="95" text-anchor="start" font-family="system-ui, sans-serif" font-size="10" font-weight="600" fill="#92400e">C_{i+1}</text>

      <text x="150" y="85" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#b45309">ΔAUC = [(C_i - C_{i+1})/ln(C_i/C_{i+1})]·Δt</text>
    </g>
  </g>"""
    return _svg_wrapper(760, 210, content)


# -----------------------------------------------------------------------------
# Lesson 6: BE Statistical Decision Tree
# -----------------------------------------------------------------------------
def get_diagram_6() -> str:
    content = """  <text x="380" y="24" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" font-weight="700" fill="#0f172a">Cây Quyết định Đánh giá Tương đương Sinh học (ICH M13A · EMA · FDA)</text>
  <g transform="translate(15, 38)">
    <!-- Top model -->
    <rect x="225" y="0" width="270" height="42" rx="8" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.8"/>
    <text x="360" y="18" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#1e40af">Mô hình ANOVA / Tuyến tính Hỗn hợp</text>
    <text x="360" y="33" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#2563eb">ln(AUC), ln(Cmax) · Ước lượng s_wR (CV_wR)</text>

    <!-- Branch lines -->
    <line x1="280" y1="42" x2="160" y2="70" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>
    <line x1="440" y1="42" x2="550" y2="70" stroke="#9333ea" stroke-width="2" marker-end="url(#arrow-purple)"/>

    <!-- Left Branch: Standard Drug -->
    <rect x="30" y="70" width="260" height="95" rx="8" fill="#f0fdf4" stroke="#16a34a" stroke-width="1.5"/>
    <text x="160" y="90" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#166534">Thuốc thường (CV_wR ≤ 30%)</text>
    <text x="160" y="110" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="600" fill="#15803d">ABE Truyền thống (Conventional ABE)</text>
    <rect x="50" y="120" width="220" height="35" rx="6" fill="#dcfce7" stroke="#16a34a" stroke-width="1"/>
    <text x="160" y="142" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#14532d">90% CI ∈ [80.00 – 125.00%]</text>

    <!-- Right Branch: HVD -->
    <rect x="420" y="70" width="295" height="95" rx="8" fill="#faf5ff" stroke="#9333ea" stroke-width="1.5"/>
    <text x="567" y="90" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#6b21a8">Thuốc biến thiên cao (CV_wR &gt; 30%)</text>
    <g transform="translate(430, 102)">
      <!-- EMA -->
      <rect x="0" y="0" width="135" height="53" rx="6" fill="#f3e8ff" stroke="#9333ea" stroke-width="1"/>
      <text x="67" y="16" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#581c87">EMA ABEL</text>
      <text x="67" y="32" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" fill="#6b21a8">Mở rộng [L, U] theo swR</text>
      <text x="67" y="45" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" font-weight="600" fill="#581c87">GMR ∈ [80.00–125.00%]</text>

      <!-- FDA -->
      <rect x="142" y="0" width="135" height="53" rx="6" fill="#fef3c7" stroke="#d97706" stroke-width="1"/>
      <text x="209" y="16" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#78350f">FDA RSABE</text>
      <text x="209" y="32" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" fill="#92400e">95% UCB ≤ 0</text>
      <text x="209" y="45" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" font-weight="600" fill="#78350f">GMR ∈ [80.00–125.00%]</text>
    </g>
  </g>"""
    return _svg_wrapper(760, 185, content)


# -----------------------------------------------------------------------------
# Lesson 7: Linear vs Semi-log Charts
# -----------------------------------------------------------------------------
def get_diagram_7() -> str:
    content = """  <text x="380" y="24" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" font-weight="700" fill="#0f172a">Khảo sát Đồ thị Nồng độ Cá thể: Tuyến tính (Linear) vs Bán Logarit (Semi-log)</text>
  <g transform="translate(30, 40)">
    <!-- Linear Chart -->
    <g transform="translate(0, 0)">
      <rect width="330" height="150" fill="#f8fafc" rx="8" stroke="#cbd5e1"/>
      <text x="165" y="22" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#1e40af">Đồ thị Tuyến tính (Linear Scale)</text>
      <line x1="40" y1="120" x2="290" y2="120" stroke="#64748b" stroke-width="1.5" marker-end="url(#arrow-slate)"/>
      <line x1="40" y1="120" x2="40" y2="35" stroke="#64748b" stroke-width="1.5" marker-end="url(#arrow-slate)"/>
      <text x="295" y="123" font-family="system-ui, sans-serif" font-size="10" fill="#475569">t</text>
      <text x="35" y="35" text-anchor="end" font-family="system-ui, sans-serif" font-size="10" fill="#475569">C</text>

      <path d="M 40 120 Q 75 35 120 45 T 200 95 T 280 115" fill="none" stroke="#2563eb" stroke-width="2.5"/>
      <circle cx="120" cy="45" r="4" fill="#dc2626"/>
      <text x="120" y="38" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" font-weight="700" fill="#dc2626">Cmax, Tmax</text>
      <text x="165" y="140" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" fill="#1e40af">Quan sát đỉnh Cmax, Tmax &amp; mức độ phơi nhiễm toàn phần</text>
    </g>

    <!-- Semi-log Chart -->
    <g transform="translate(370, 0)">
      <rect width="330" height="150" fill="#f8fafc" rx="8" stroke="#cbd5e1"/>
      <text x="165" y="22" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#92400e">Đồ thị Bán Logarit (Semi-log Scale)</text>
      <line x1="40" y1="120" x2="290" y2="120" stroke="#64748b" stroke-width="1.5" marker-end="url(#arrow-slate)"/>
      <line x1="40" y1="120" x2="40" y2="35" stroke="#64748b" stroke-width="1.5" marker-end="url(#arrow-slate)"/>
      <text x="295" y="123" font-family="system-ui, sans-serif" font-size="10" fill="#475569">t</text>
      <text x="35" y="35" text-anchor="end" font-family="system-ui, sans-serif" font-size="10" fill="#475569">ln C</text>

      <path d="M 40 110 Q 70 45 110 50 L 270 115" fill="none" stroke="#d97706" stroke-width="2.5"/>
      <!-- Straight elimination line -->
      <line x1="140" y1="62" x2="270" y2="115" stroke="#dc2626" stroke-width="2" stroke-dasharray="3,3"/>
      <text x="210" y="78" font-family="system-ui, sans-serif" font-size="9" font-weight="700" fill="#dc2626">Độ dốc = -λz</text>
      <text x="165" y="140" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" fill="#92400e">Pha thải trừ là đường thẳng → Tính t½ = ln(2)/λz &amp; R²</text>
    </g>
  </g>"""
    return _svg_wrapper(760, 210, content)


# -----------------------------------------------------------------------------
# Lesson 8: Reporting & Artifact Packaging
# -----------------------------------------------------------------------------
def get_diagram_8() -> str:
    content = """  <text x="380" y="24" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" font-weight="700" fill="#0f172a">Đóng gói Hồ sơ Báo cáo Nghiên cứu CTD Module 5.3.1.2 &amp; Băm Toàn vẹn</text>
  <g transform="translate(15, 42)">
    <rect x="0" y="0" width="160" height="65" rx="8" fill="#f8fafc" stroke="#3b82f6" stroke-width="1.5"/>
    <text x="80" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#1e40af">Dữ liệu &amp; Nhật ký</text>
    <text x="80" y="46" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#3b82f6">Raw + SAP + Audit log</text>

    <line x1="160" y1="32" x2="190" y2="32" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <rect x="190" y="0" width="170" height="65" rx="8" fill="#ede9fe" stroke="#7c3aed" stroke-width="1.5"/>
    <text x="275" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#5b21b6">Bộ Kết xuất CTD</text>
    <text x="275" y="46" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#6d28d9">Module 5.3.1.2 / ICH E3</text>

    <line x1="360" y1="32" x2="390" y2="32" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <rect x="390" y="0" width="165" height="65" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
    <text x="472" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#92400e">Bộ Ba Tệp Đầu ra</text>
    <text x="472" y="46" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#b45309">Word DOCX + Excel + ZIP</text>

    <line x1="555" y1="32" x2="585" y2="32" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <rect x="585" y="0" width="145" height="65" rx="8" fill="#dcfce7" stroke="#16a34a" stroke-width="1.5"/>
    <text x="657" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#166534">Bảng kê Manifest</text>
    <text x="657" y="46" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#15803d">SHA-256 từng tài liệu</text>
  </g>"""
    return _svg_wrapper(760, 135, content)


# -----------------------------------------------------------------------------
# Lesson 9: Audit Trail & ALCOA+
# -----------------------------------------------------------------------------
def get_diagram_9() -> str:
    content = """  <text x="380" y="24" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" font-weight="700" fill="#0f172a">Chu trình Ghi nhận &amp; Thẩm tra Nhật ký Kiểm toán (Audit Trail · ALCOA+)</text>
  <g transform="translate(15, 42)">
    <rect x="0" y="0" width="160" height="65" rx="8" fill="#f8fafc" stroke="#64748b" stroke-width="1.5"/>
    <text x="80" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#334155">Thao tác Người dùng</text>
    <text x="80" y="46" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#64748b">Sửa / Chạy phân tích</text>

    <line x1="160" y1="32" x2="190" y2="32" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <rect x="190" y="0" width="170" height="65" rx="8" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.5"/>
    <text x="275" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#1e40af">Ghi nhận Tự động</text>
    <text x="275" y="46" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#3b82f6">Thời gian NTP · User · Lý do</text>

    <line x1="360" y1="32" x2="390" y2="32" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <rect x="390" y="0" width="165" height="65" rx="8" fill="#ede9fe" stroke="#7c3aed" stroke-width="1.5"/>
    <text x="472" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#5b21b6">CSDL Bất biến</text>
    <text x="472" y="46" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#6d28d9">Chống sửa / xóa trái phép</text>

    <line x1="555" y1="32" x2="585" y2="32" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <rect x="585" y="0" width="145" height="65" rx="8" fill="#dcfce7" stroke="#16a34a" stroke-width="1.5"/>
    <text x="657" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#166534">Thẩm tra Thanh tra</text>
    <text x="657" y="46" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#15803d">Truy vết nguồn gốc 100%</text>
  </g>"""
    return _svg_wrapper(760, 135, content)


# -----------------------------------------------------------------------------
# Lesson 10: PK Standalone (Compartmental Models - 9 Architectures)
# -----------------------------------------------------------------------------
def get_diagram_compartment(route: str, compartments: int) -> str:
    """Generate high-resolution, focused vector diagram for a specific route x compartment model."""
    route_key = route.lower().replace("-", "_").replace(" ", "_")
    if "bolus" in route_key:
        r_type = "bolus"
        r_title = "Tiêm tĩnh mạch nhanh (IV Bolus)"
        input_label = "Liều D (t=0)"
        input_sub = "Tiêm IV trực tiếp (F=1)"
        input_color = "#fef3c7"
        input_stroke = "#d97706"
        input_text = "#92400e"
        in_arrow = "arrow"
        arrow_label = "Nạp tức thời"
    elif "infusion" in route_key or "truyền" in route_key:
        r_type = "infusion"
        r_title = "Truyền tĩnh mạch liên tục (IV Infusion)"
        input_label = "Bơm truyền R₀"
        input_sub = "R₀ = D/Tinf (0 ≤ t ≤ Tinf)"
        input_color = "#dcfce7"
        input_stroke = "#16a34a"
        input_text = "#166534"
        in_arrow = "arrow-green"
        arrow_label = "Bậc 0 (R₀)"
    else:
        r_type = "oral"
        r_title = "Đường uống qua ống tiêu hóa (Oral Absorption)"
        input_label = "Ruột / Ống TH"
        input_sub = "Liều D · F (Tlag)"
        input_color = "#fef3c7"
        input_stroke = "#d97706"
        input_text = "#92400e"
        in_arrow = "arrow"
        arrow_label = "Hấp thu ka"

    if compartments == 1:
        cpt_title = f"{r_title} — Mô hình 1 Ngăn"
        cl_label = "CL = k₁₀·V₁" if r_type != "oral" else "CL/F = kel·V₁"
        eq_badge = (
            '<rect x="500" y="45" width="245" height="150" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.2"/>\n'
            '<text x="515" y="68" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#1e293b">Đặc trưng Mô hình 1 Ngăn:</text>\n'
            f'<text x="515" y="90" font-family="system-ui, sans-serif" font-size="10" fill="#475569">• Thể tích phân bố: {"V₁ (hoặc Vc)" if r_type != "oral" else "V₁/F (biểu kiến)"}</text>\n'
            f'<text x="515" y="110" font-family="system-ui, sans-serif" font-size="10" fill="#475569">• Độ thanh thải: {cl_label}</text>\n'
            '<text x="515" y="130" font-family="system-ui, sans-serif" font-size="10" fill="#475569">• Thời gian bán thải: t½ = 0.693 / k₁₀</text>\n'
            '<text x="515" y="150" font-family="system-ui, sans-serif" font-size="10" fill="#475569">• Diện tích dưới đường cong: AUC = D / CL</text>\n'
            f'<text x="515" y="172" font-family="system-ui, sans-serif" font-size="10" font-weight="600" fill="#2563eb">• Nghiệm C(t): {"C₀·e^(-k₁₀t)" if r_type=="bolus" else ("(R₀/CL)(1-e^(-kt))" if r_type=="infusion" else "Bateman (ka, kel)")}</text>'
        )
        body = f"""  <text x="380" y="24" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" font-weight="700" fill="#0f172a">{cpt_title}</text>
  <!-- Input -->
  <rect x="25" y="70" width="110" height="60" rx="8" fill="{input_color}" stroke="{input_stroke}" stroke-width="1.8"/>
  <text x="80" y="96" text-anchor="middle" font-family="system-ui, sans-serif" font-size="12" font-weight="700" fill="{input_text}">{input_label}</text>
  <text x="80" y="114" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="{input_text}">{input_sub}</text>

  <!-- In arrow -->
  <line x1="135" y1="100" x2="195" y2="100" stroke="{input_stroke}" stroke-width="2" marker-end="url(#{in_arrow})"/>
  <text x="165" y="92" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="{input_stroke}">{arrow_label}</text>

  <!-- Central Compartment -->
  <rect x="205" y="60" width="155" height="75" rx="8" fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
  <text x="282" y="88" text-anchor="middle" font-family="system-ui, sans-serif" font-size="12" font-weight="700" fill="#1e40af">Ngăn Trung tâm (V₁)</text>
  <text x="282" y="106" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" fill="#3b82f6">Nồng độ huyết tương C₁(t)</text>
  <text x="282" y="122" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" fill="#1d4ed8">Máu &amp; các mô tưới máu cao</text>

  <!-- Kel arrow -->
  <line x1="282" y1="135" x2="282" y2="165" stroke="#dc2626" stroke-width="2" marker-end="url(#arrow-red)"/>
  <text x="296" y="152" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#dc2626">k₁₀</text>

  <!-- Elimination -->
  <rect x="215" y="167" width="135" height="30" rx="6" fill="#fee2e2" stroke="#dc2626" stroke-width="1.2"/>
  <text x="282" y="187" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="600" fill="#991b1b">Thải trừ ({cl_label})</text>

  <!-- Summary badge -->
  {eq_badge}"""
    elif compartments == 2:
        cpt_title = f"{r_title} — Mô hình 2 Ngăn"
        cl_label = "CL = k₁₀·V₁" if r_type != "oral" else "CL/F = k₁₀·V₁"
        eq_badge = (
            '<rect x="520" y="45" width="225" height="150" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.2"/>\n'
            '<text x="532" y="68" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#1e293b">Đặc trưng Mô hình 2 Ngăn:</text>\n'
            '<text x="532" y="90" font-family="system-ui, sans-serif" font-size="10" fill="#475569">• Thể tích Vss = V₁·(1 + k₁₂/k₂₁)</text>\n'
            '<text x="532" y="110" font-family="system-ui, sans-serif" font-size="10" fill="#475569">• Thanh thải liên ngăn Q = k₁₂·V₁ = k₂₁·V₂</text>\n'
            '<text x="532" y="130" font-family="system-ui, sans-serif" font-size="10" fill="#475569">• Pha phân bố α: t½,α = 0.693 / α</text>\n'
            '<text x="532" y="150" font-family="system-ui, sans-serif" font-size="10" fill="#475569">• Pha thải trừ β: t½,β = 0.693 / β</text>\n'
            '<text x="532" y="172" font-family="system-ui, sans-serif" font-size="10" font-weight="600" fill="#9333ea">• C(t) = A·e^(-αt) + B·e^(-βt)</text>'
        )
        body = f"""  <text x="380" y="24" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" font-weight="700" fill="#0f172a">{cpt_title}</text>
  <!-- Input -->
  <rect x="15" y="70" width="85" height="55" rx="8" fill="{input_color}" stroke="{input_stroke}" stroke-width="1.5"/>
  <text x="57" y="94" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="{input_text}">{input_label}</text>
  <text x="57" y="110" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" fill="{input_text}">{input_sub}</text>

  <!-- In arrow -->
  <line x1="100" y1="97" x2="140" y2="97" stroke="{input_stroke}" stroke-width="1.8" marker-end="url(#{in_arrow})"/>
  <text x="120" y="89" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" font-weight="700" fill="{input_stroke}">{arrow_label}</text>

  <!-- Central Compartment 1 -->
  <rect x="145" y="58" width="130" height="75" rx="8" fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
  <text x="210" y="84" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#1e40af">Ngăn 1 (V₁)</text>
  <text x="210" y="100" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#3b82f6">Trung tâm (C₁)</text>
  <text x="210" y="116" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" fill="#1d4ed8">Máu &amp; dịch ngoại bào</text>

  <!-- Exchange k12 / k21 -->
  <line x1="275" y1="80" x2="335" y2="80" stroke="#9333ea" stroke-width="1.8" marker-end="url(#arrow-purple)"/>
  <text x="305" y="73" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#9333ea">k₁₂</text>
  <line x1="335" y1="104" x2="275" y2="104" stroke="#9333ea" stroke-width="1.8" marker-end="url(#arrow-purple)"/>
  <text x="305" y="118" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#9333ea">k₂₁</text>

  <!-- Peripheral Compartment 2 -->
  <rect x="340" y="58" width="140" height="75" rx="8" fill="#f3e8ff" stroke="#9333ea" stroke-width="1.8"/>
  <text x="410" y="84" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#6b21a8">Ngăn 2 (V₂)</text>
  <text x="410" y="100" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#7e22ce">Ngoại vi (C₂)</text>
  <text x="410" y="116" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" fill="#581c87">Mô cơ, mô liên kết</text>

  <!-- Kel arrow -->
  <line x1="210" y1="133" x2="210" y2="162" stroke="#dc2626" stroke-width="2" marker-end="url(#arrow-red)"/>
  <text x="222" y="150" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#dc2626">k₁₀</text>

  <!-- Elimination -->
  <rect x="150" y="165" width="120" height="28" rx="6" fill="#fee2e2" stroke="#dc2626" stroke-width="1.2"/>
  <text x="210" y="184" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="600" fill="#991b1b">Thải trừ ({cl_label})</text>

  <!-- Summary badge -->
  {eq_badge}"""
    else:
        # 3 compartments
        cpt_title = f"{r_title} — Mô hình 3 Ngăn"
        cl_label = "CL = k₁₀·V₁" if r_type != "oral" else "CL/F = k₁₀·V₁"
        eq_badge = (
            '<rect x="535" y="45" width="210" height="150" rx="8" fill="#f8fafc" stroke="#cbd5e1" stroke-width="1.2"/>\n'
            '<text x="545" y="68" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#1e293b">Đặc trưng Mô hình 3 Ngăn:</text>\n'
            '<text x="545" y="88" font-family="system-ui, sans-serif" font-size="10" fill="#475569">• Vss = V₁ + V₂ + V₃</text>\n'
            '<text x="545" y="106" font-family="system-ui, sans-serif" font-size="10" fill="#475569">• Q₂ = k₁₂·V₁; Q₃ = k₁₃·V₁</text>\n'
            '<text x="545" y="124" font-family="system-ui, sans-serif" font-size="10" fill="#475569">• 3 pha: α (nhanh), β (chậm), γ (cuối)</text>\n'
            '<text x="545" y="142" font-family="system-ui, sans-serif" font-size="10" fill="#475569">• t½,γ phản ánh thải trừ mô sâu</text>\n'
            '<text x="545" y="162" font-family="system-ui, sans-serif" font-size="9.5" font-weight="600" fill="#0d9488">• Triexponential: A·e^-αt+B·e^-βt+C·e^-γt</text>'
        )
        body = f"""  <text x="380" y="24" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" font-weight="700" fill="#0f172a">{cpt_title}</text>
  <!-- Input -->
  <rect x="10" y="72" width="75" height="50" rx="6" fill="{input_color}" stroke="{input_stroke}" stroke-width="1.5"/>
  <text x="47" y="94" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="{input_text}">{input_label}</text>
  <text x="47" y="108" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" fill="{input_text}">{input_sub}</text>

  <!-- In arrow -->
  <line x1="85" y1="97" x2="115" y2="97" stroke="{input_stroke}" stroke-width="1.8" marker-end="url(#{in_arrow})"/>

  <!-- Central Compartment 1 -->
  <rect x="120" y="60" width="115" height="75" rx="8" fill="#dbeafe" stroke="#2563eb" stroke-width="2"/>
  <text x="177" y="86" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#1e40af">Ngăn 1 (V₁)</text>
  <text x="177" y="102" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#3b82f6">Trung tâm (C₁)</text>
  <text x="177" y="118" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" fill="#1d4ed8">Máu &amp; tạng tuần hoàn</text>

  <!-- Exchange 1 <-> 2 (Nông) -->
  <line x1="235" y1="72" x2="280" y2="58" stroke="#9333ea" stroke-width="1.5" marker-end="url(#arrow-purple)"/>
  <line x1="280" y1="70" x2="235" y2="84" stroke="#9333ea" stroke-width="1.5" marker-end="url(#arrow-purple)"/>
  <rect x="285" y="44" width="135" height="46" rx="6" fill="#f3e8ff" stroke="#9333ea" stroke-width="1.5"/>
  <text x="352" y="64" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#6b21a8">Ngăn 2 (V₂ - Nông)</text>
  <text x="352" y="78" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8.5" fill="#7e22ce">Mô cơ (k₁₂ / k₂₁)</text>

  <!-- Exchange 1 <-> 3 (Sâu) -->
  <line x1="235" y1="108" x2="280" y2="122" stroke="#0d9488" stroke-width="1.5" marker-end="url(#arrow-green)"/>
  <line x1="280" y1="134" x2="235" y2="120" stroke="#0d9488" stroke-width="1.5" marker-end="url(#arrow-green)"/>
  <rect x="285" y="105" width="135" height="46" rx="6" fill="#ccfbf1" stroke="#0d9488" stroke-width="1.5"/>
  <text x="352" y="125" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#0f766e">Ngăn 3 (V₃ - Sâu)</text>
  <text x="352" y="139" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8.5" fill="#115e59">Mô mỡ, xương (k₁₃ / k₃₁)</text>

  <!-- Kel arrow -->
  <line x1="177" y1="135" x2="177" y2="162" stroke="#dc2626" stroke-width="2" marker-end="url(#arrow-red)"/>
  <text x="189" y="152" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#dc2626">k₁₀</text>

  <!-- Elimination -->
  <rect x="122" y="165" width="110" height="28" rx="6" fill="#fee2e2" stroke="#dc2626" stroke-width="1.2"/>
  <text x="177" y="184" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="600" fill="#991b1b">Thải trừ ({cl_label})</text>

  <!-- Summary badge -->
  {eq_badge}"""

    return _svg_wrapper(760, 215, body)


def get_diagram_10() -> str:
    """Master comparative architectural diagram illustrating all 9 compartmental PK models."""
    content = """  <text x="400" y="24" text-anchor="middle" font-family="system-ui, sans-serif" font-size="14" font-weight="700" fill="#0f172a">Hệ Thống 9 Mô Hình Dược Động Học Ngăn (Compartmental PK Architectures)</text>

  <!-- ================= ROW 1: TIÊM TĨNH MẠCH NHANH (IV BOLUS) ================= -->
  <g transform="translate(15, 38)">
    <rect width="770" height="152" fill="#f8fafc" rx="8" stroke="#cbd5e1" stroke-width="1.2"/>
    <rect width="770" height="24" fill="#eff6ff" rx="8" stroke="#bfdbfe" stroke-width="1"/>
    <text x="12" y="16" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#1e40af">1. ĐƯỜNG TIÊM TĨNH MẠCH NHANH (IV BOLUS) — Nạp tức thời toàn bộ liều D tại t=0 (F = 1)</text>

    <!-- 1.1 IV Bolus 1 Ngăn -->
    <g transform="translate(10, 30)">
      <rect width="240" height="112" fill="#ffffff" rx="6" stroke="#e2e8f0"/>
      <text x="120" y="16" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#334155">1 Ngăn IV Bolus</text>
      <rect x="8" y="32" width="55" height="32" rx="5" fill="#fef3c7" stroke="#d97706" stroke-width="1.2"/>
      <text x="35" y="47" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" font-weight="700" fill="#92400e">Liều D</text>
      <text x="35" y="58" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" fill="#b45309">t = 0</text>
      <line x1="63" y1="48" x2="88" y2="48" stroke="#2563eb" stroke-width="1.8" marker-end="url(#arrow)"/>
      <rect x="90" y="26" width="138" height="42" rx="6" fill="#dbeafe" stroke="#2563eb" stroke-width="1.8"/>
      <text x="159" y="43" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#1e40af">Ngăn Trung tâm (V₁)</text>
      <text x="159" y="58" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" fill="#3b82f6">Nồng độ C(t) = C₀·e^(-k₁₀t)</text>
      <line x1="159" y1="68" x2="159" y2="85" stroke="#dc2626" stroke-width="1.8" marker-end="url(#arrow-red)"/>
      <text x="169" y="80" font-family="system-ui, sans-serif" font-size="9" font-weight="700" fill="#dc2626">k₁₀</text>
      <rect x="105" y="87" width="108" height="20" rx="4" fill="#fee2e2" stroke="#dc2626" stroke-width="1"/>
      <text x="159" y="101" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" font-weight="600" fill="#991b1b">Thải trừ (CL = k₁₀·V₁)</text>
    </g>

    <!-- 1.2 IV Bolus 2 Ngăn -->
    <g transform="translate(260, 30)">
      <rect width="250" height="112" fill="#ffffff" rx="6" stroke="#e2e8f0"/>
      <text x="125" y="16" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#334155">2 Ngăn IV Bolus</text>
      <rect x="6" y="32" width="46" height="32" rx="5" fill="#fef3c7" stroke="#d97706" stroke-width="1.2"/>
      <text x="29" y="52" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" font-weight="700" fill="#92400e">Liều D</text>
      <line x1="52" y1="48" x2="68" y2="48" stroke="#2563eb" stroke-width="1.5" marker-end="url(#arrow)"/>
      <rect x="70" y="26" width="85" height="42" rx="6" fill="#dbeafe" stroke="#2563eb" stroke-width="1.8"/>
      <text x="112" y="43" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#1e40af">Ngăn 1 (V₁)</text>
      <text x="112" y="58" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" fill="#3b82f6">Trung tâm (C₁)</text>
      <line x1="155" y1="39" x2="175" y2="39" stroke="#9333ea" stroke-width="1.5" marker-end="url(#arrow-purple)"/>
      <text x="165" y="35" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#9333ea">k₁₂</text>
      <line x1="175" y1="53" x2="155" y2="53" stroke="#9333ea" stroke-width="1.5" marker-end="url(#arrow-purple)"/>
      <text x="165" y="64" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#9333ea">k₂₁</text>
      <rect x="178" y="26" width="64" height="42" rx="6" fill="#f3e8ff" stroke="#9333ea" stroke-width="1.5"/>
      <text x="210" y="43" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#6b21a8">Ngăn 2</text>
      <text x="210" y="58" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" fill="#7e22ce">V₂, C₂</text>
      <line x1="112" y1="68" x2="112" y2="85" stroke="#dc2626" stroke-width="1.8" marker-end="url(#arrow-red)"/>
      <text x="120" y="80" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#dc2626">k₁₀</text>
      <rect x="68" y="87" width="88" height="20" rx="4" fill="#fee2e2" stroke="#dc2626" stroke-width="1"/>
      <text x="112" y="101" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="600" fill="#991b1b">Thải trừ (CL)</text>
    </g>

    <!-- 1.3 IV Bolus 3 Ngăn -->
    <g transform="translate(520, 30)">
      <rect width="240" height="112" fill="#ffffff" rx="6" stroke="#e2e8f0"/>
      <text x="120" y="16" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#334155">3 Ngăn IV Bolus</text>
      <rect x="5" y="42" width="42" height="28" rx="4" fill="#fef3c7" stroke="#d97706" stroke-width="1.2"/>
      <text x="26" y="59" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#92400e">Liều D</text>
      <line x1="47" y1="56" x2="58" y2="56" stroke="#2563eb" stroke-width="1.5" marker-end="url(#arrow)"/>
      <rect x="60" y="38" width="68" height="38" rx="6" fill="#dbeafe" stroke="#2563eb" stroke-width="1.8"/>
      <text x="94" y="53" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" font-weight="700" fill="#1e40af">Ngăn 1 (V₁)</text>
      <text x="94" y="67" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" fill="#3b82f6">Trung tâm</text>
      <line x1="128" y1="44" x2="160" y2="34" stroke="#9333ea" stroke-width="1.3" marker-end="url(#arrow-purple)"/>
      <line x1="160" y1="42" x2="128" y2="52" stroke="#9333ea" stroke-width="1.3" marker-end="url(#arrow-purple)"/>
      <rect x="163" y="24" width="70" height="28" rx="4" fill="#f3e8ff" stroke="#9333ea" stroke-width="1.2"/>
      <text x="198" y="38" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#6b21a8">Ngăn 2 (V₂)</text>
      <text x="198" y="48" text-anchor="middle" font-family="system-ui, sans-serif" font-size="7" fill="#7e22ce">Nông (k₁₂/k₂₁)</text>
      <line x1="128" y1="62" x2="160" y2="72" stroke="#0d9488" stroke-width="1.3" marker-end="url(#arrow-green)"/>
      <line x1="160" y1="80" x2="128" y2="70" stroke="#0d9488" stroke-width="1.3" marker-end="url(#arrow-green)"/>
      <rect x="163" y="68" width="70" height="28" rx="4" fill="#ccfbf1" stroke="#0d9488" stroke-width="1.2"/>
      <text x="198" y="82" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#0f766e">Ngăn 3 (V₃)</text>
      <text x="198" y="92" text-anchor="middle" font-family="system-ui, sans-serif" font-size="7" fill="#115e59">Sâu (k₁₃/k₃₁)</text>
      <line x1="94" y1="76" x2="94" y2="90" stroke="#dc2626" stroke-width="1.5" marker-end="url(#arrow-red)"/>
      <rect x="56" y="92" width="76" height="17" rx="3" fill="#fee2e2" stroke="#dc2626" stroke-width="1"/>
      <text x="94" y="104" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="600" fill="#991b1b">CL (k₁₀)</text>
    </g>
  </g>

  <!-- ================= ROW 2: TRUYỀN TĨNH MẠCH (IV INFUSION) ================= -->
  <g transform="translate(15, 202)">
    <rect width="770" height="152" fill="#f8fafc" rx="8" stroke="#cbd5e1" stroke-width="1.2"/>
    <rect width="770" height="24" fill="#f0fdf4" rx="8" stroke="#bbf7d0" stroke-width="1"/>
    <text x="12" y="16" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#166534">2. ĐƯỜNG TRUYỀN TĨNH MẠCH LIÊN TỤC (IV INFUSION) — Nạp tốc độ hằng định R₀ = Dose / Tinf (0 ≤ t ≤ Tinf)</text>

    <!-- 2.1 IV Infusion 1 Ngăn -->
    <g transform="translate(10, 30)">
      <rect width="240" height="112" fill="#ffffff" rx="6" stroke="#e2e8f0"/>
      <text x="120" y="16" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#334155">1 Ngăn IV Infusion</text>
      <rect x="6" y="30" width="62" height="34" rx="5" fill="#dcfce7" stroke="#16a34a" stroke-width="1.2"/>
      <text x="37" y="45" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" font-weight="700" fill="#166534">Bơm R₀</text>
      <text x="37" y="57" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" fill="#15803d">0 ≤ t ≤ Tinf</text>
      <line x1="68" y1="47" x2="88" y2="47" stroke="#16a34a" stroke-width="1.8" marker-end="url(#arrow-green)"/>
      <rect x="90" y="26" width="138" height="42" rx="6" fill="#dbeafe" stroke="#2563eb" stroke-width="1.8"/>
      <text x="159" y="43" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#1e40af">Ngăn Trung tâm (V₁)</text>
      <text x="159" y="58" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" fill="#3b82f6">Css = R₀ / CL</text>
      <line x1="159" y1="68" x2="159" y2="85" stroke="#dc2626" stroke-width="1.8" marker-end="url(#arrow-red)"/>
      <text x="169" y="80" font-family="system-ui, sans-serif" font-size="9" font-weight="700" fill="#dc2626">k₁₀</text>
      <rect x="105" y="87" width="108" height="20" rx="4" fill="#fee2e2" stroke="#dc2626" stroke-width="1"/>
      <text x="159" y="101" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" font-weight="600" fill="#991b1b">Thải trừ (CL = k₁₀·V₁)</text>
    </g>

    <!-- 2.2 IV Infusion 2 Ngăn -->
    <g transform="translate(260, 30)">
      <rect width="250" height="112" fill="#ffffff" rx="6" stroke="#e2e8f0"/>
      <text x="125" y="16" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#334155">2 Ngăn IV Infusion</text>
      <rect x="5" y="32" width="50" height="32" rx="5" fill="#dcfce7" stroke="#16a34a" stroke-width="1.2"/>
      <text x="30" y="47" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#166534">Bơm R₀</text>
      <text x="30" y="58" text-anchor="middle" font-family="system-ui, sans-serif" font-size="7" fill="#15803d">Tinf</text>
      <line x1="55" y1="48" x2="68" y2="48" stroke="#16a34a" stroke-width="1.5" marker-end="url(#arrow-green)"/>
      <rect x="70" y="26" width="85" height="42" rx="6" fill="#dbeafe" stroke="#2563eb" stroke-width="1.8"/>
      <text x="112" y="43" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#1e40af">Ngăn 1 (V₁)</text>
      <text x="112" y="58" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" fill="#3b82f6">Trung tâm</text>
      <line x1="155" y1="39" x2="175" y2="39" stroke="#9333ea" stroke-width="1.5" marker-end="url(#arrow-purple)"/>
      <text x="165" y="35" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#9333ea">k₁₂</text>
      <line x1="175" y1="53" x2="155" y2="53" stroke="#9333ea" stroke-width="1.5" marker-end="url(#arrow-purple)"/>
      <text x="165" y="64" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#9333ea">k₂₁</text>
      <rect x="178" y="26" width="64" height="42" rx="6" fill="#f3e8ff" stroke="#9333ea" stroke-width="1.5"/>
      <text x="210" y="43" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#6b21a8">Ngăn 2</text>
      <text x="210" y="58" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" fill="#7e22ce">V₂, C₂</text>
      <line x1="112" y1="68" x2="112" y2="85" stroke="#dc2626" stroke-width="1.8" marker-end="url(#arrow-red)"/>
      <text x="120" y="80" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#dc2626">k₁₀</text>
      <rect x="68" y="87" width="88" height="20" rx="4" fill="#fee2e2" stroke="#dc2626" stroke-width="1"/>
      <text x="112" y="101" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="600" fill="#991b1b">Thải trừ (CL)</text>
    </g>

    <!-- 2.3 IV Infusion 3 Ngăn -->
    <g transform="translate(520, 30)">
      <rect width="240" height="112" fill="#ffffff" rx="6" stroke="#e2e8f0"/>
      <text x="120" y="16" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#334155">3 Ngăn IV Infusion</text>
      <rect x="5" y="42" width="44" height="28" rx="4" fill="#dcfce7" stroke="#16a34a" stroke-width="1.2"/>
      <text x="27" y="55" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#166534">Bơm R₀</text>
      <text x="27" y="65" text-anchor="middle" font-family="system-ui, sans-serif" font-size="7" fill="#15803d">Tinf</text>
      <line x1="49" y1="56" x2="58" y2="56" stroke="#16a34a" stroke-width="1.5" marker-end="url(#arrow-green)"/>
      <rect x="60" y="38" width="68" height="38" rx="6" fill="#dbeafe" stroke="#2563eb" stroke-width="1.8"/>
      <text x="94" y="53" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" font-weight="700" fill="#1e40af">Ngăn 1 (V₁)</text>
      <text x="94" y="67" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" fill="#3b82f6">Trung tâm</text>
      <line x1="128" y1="44" x2="160" y2="34" stroke="#9333ea" stroke-width="1.3" marker-end="url(#arrow-purple)"/>
      <line x1="160" y1="42" x2="128" y2="52" stroke="#9333ea" stroke-width="1.3" marker-end="url(#arrow-purple)"/>
      <rect x="163" y="24" width="70" height="28" rx="4" fill="#f3e8ff" stroke="#9333ea" stroke-width="1.2"/>
      <text x="198" y="38" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#6b21a8">Ngăn 2 (V₂)</text>
      <text x="198" y="48" text-anchor="middle" font-family="system-ui, sans-serif" font-size="7" fill="#7e22ce">Nông (k₁₂/k₂₁)</text>
      <line x1="128" y1="62" x2="160" y2="72" stroke="#0d9488" stroke-width="1.3" marker-end="url(#arrow-green)"/>
      <line x1="160" y1="80" x2="128" y2="70" stroke="#0d9488" stroke-width="1.3" marker-end="url(#arrow-green)"/>
      <rect x="163" y="68" width="70" height="28" rx="4" fill="#ccfbf1" stroke="#0d9488" stroke-width="1.2"/>
      <text x="198" y="82" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#0f766e">Ngăn 3 (V₃)</text>
      <text x="198" y="92" text-anchor="middle" font-family="system-ui, sans-serif" font-size="7" fill="#115e59">Sâu (k₁₃/k₃₁)</text>
      <line x1="94" y1="76" x2="94" y2="90" stroke="#dc2626" stroke-width="1.5" marker-end="url(#arrow-red)"/>
      <rect x="56" y="92" width="76" height="17" rx="3" fill="#fee2e2" stroke="#dc2626" stroke-width="1"/>
      <text x="94" y="104" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="600" fill="#991b1b">CL (k₁₀)</text>
    </g>
  </g>

  <!-- ================= ROW 3: ĐƯỜNG UỐNG (ORAL ABSORPTION) ================= -->
  <g transform="translate(15, 366)">
    <rect width="770" height="152" fill="#f8fafc" rx="8" stroke="#cbd5e1" stroke-width="1.2"/>
    <rect width="770" height="24" fill="#fffbeb" rx="8" stroke="#fde68a" stroke-width="1"/>
    <text x="12" y="16" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#92400e">3. ĐƯỜNG UỐNG (ORAL) — Hấp thu bậc 1 qua ống tiêu hóa (kₐ, F, Tlag) vào Ngăn Trung tâm</text>

    <!-- 3.1 Oral 1 Ngăn -->
    <g transform="translate(10, 30)">
      <rect width="240" height="112" fill="#ffffff" rx="6" stroke="#e2e8f0"/>
      <text x="120" y="16" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#334155">1 Ngăn Đường uống (Bateman)</text>
      <rect x="6" y="30" width="62" height="34" rx="5" fill="#fef3c7" stroke="#d97706" stroke-width="1.2"/>
      <text x="37" y="45" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" font-weight="700" fill="#92400e">Ruột (GI)</text>
      <text x="37" y="57" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" fill="#b45309">Liều D · F</text>
      <line x1="68" y1="47" x2="88" y2="47" stroke="#2563eb" stroke-width="1.8" marker-end="url(#arrow)"/>
      <text x="78" y="40" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#2563eb">kₐ</text>
      <rect x="90" y="26" width="138" height="42" rx="6" fill="#dbeafe" stroke="#2563eb" stroke-width="1.8"/>
      <text x="159" y="43" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#1e40af">Ngăn Trung tâm (V₁)</text>
      <text x="159" y="58" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" fill="#3b82f6">Tmax = Tlag + ln(ka/kel)/(ka-kel)</text>
      <line x1="159" y1="68" x2="159" y2="85" stroke="#dc2626" stroke-width="1.8" marker-end="url(#arrow-red)"/>
      <text x="169" y="80" font-family="system-ui, sans-serif" font-size="9" font-weight="700" fill="#dc2626">kₑₗ</text>
      <rect x="105" y="87" width="108" height="20" rx="4" fill="#fee2e2" stroke="#dc2626" stroke-width="1"/>
      <text x="159" y="101" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" font-weight="600" fill="#991b1b">Thải trừ (CL/F)</text>
    </g>

    <!-- 3.2 Oral 2 Ngăn -->
    <g transform="translate(260, 30)">
      <rect width="250" height="112" fill="#ffffff" rx="6" stroke="#e2e8f0"/>
      <text x="125" y="16" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#334155">2 Ngăn Đường uống</text>
      <rect x="5" y="32" width="50" height="32" rx="5" fill="#fef3c7" stroke="#d97706" stroke-width="1.2"/>
      <text x="30" y="47" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#92400e">Ruột</text>
      <text x="30" y="58" text-anchor="middle" font-family="system-ui, sans-serif" font-size="7" fill="#b45309">D·F</text>
      <line x1="55" y1="48" x2="68" y2="48" stroke="#2563eb" stroke-width="1.5" marker-end="url(#arrow)"/>
      <text x="61" y="42" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#2563eb">kₐ</text>
      <rect x="70" y="26" width="85" height="42" rx="6" fill="#dbeafe" stroke="#2563eb" stroke-width="1.8"/>
      <text x="112" y="43" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#1e40af">Ngăn 1 (V₁)</text>
      <text x="112" y="58" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" fill="#3b82f6">Trung tâm</text>
      <line x1="155" y1="39" x2="175" y2="39" stroke="#9333ea" stroke-width="1.5" marker-end="url(#arrow-purple)"/>
      <text x="165" y="35" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#9333ea">k₁₂</text>
      <line x1="175" y1="53" x2="155" y2="53" stroke="#9333ea" stroke-width="1.5" marker-end="url(#arrow-purple)"/>
      <text x="165" y="64" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#9333ea">k₂₁</text>
      <rect x="178" y="26" width="64" height="42" rx="6" fill="#f3e8ff" stroke="#9333ea" stroke-width="1.5"/>
      <text x="210" y="43" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" font-weight="700" fill="#6b21a8">Ngăn 2</text>
      <text x="210" y="58" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" fill="#7e22ce">V₂, C₂</text>
      <line x1="112" y1="68" x2="112" y2="85" stroke="#dc2626" stroke-width="1.8" marker-end="url(#arrow-red)"/>
      <text x="120" y="80" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#dc2626">k₁₀</text>
      <rect x="68" y="87" width="88" height="20" rx="4" fill="#fee2e2" stroke="#dc2626" stroke-width="1"/>
      <text x="112" y="101" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="600" fill="#991b1b">Thải trừ (CL/F)</text>
    </g>

    <!-- 3.3 Oral 3 Ngăn -->
    <g transform="translate(520, 30)">
      <rect width="240" height="112" fill="#ffffff" rx="6" stroke="#e2e8f0"/>
      <text x="120" y="16" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#334155">3 Ngăn Đường uống</text>
      <rect x="5" y="42" width="44" height="28" rx="4" fill="#fef3c7" stroke="#d97706" stroke-width="1.2"/>
      <text x="27" y="55" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#92400e">Ruột</text>
      <text x="27" y="65" text-anchor="middle" font-family="system-ui, sans-serif" font-size="7" fill="#b45309">D·F</text>
      <line x1="49" y1="56" x2="58" y2="56" stroke="#2563eb" stroke-width="1.5" marker-end="url(#arrow)"/>
      <rect x="60" y="38" width="68" height="38" rx="6" fill="#dbeafe" stroke="#2563eb" stroke-width="1.8"/>
      <text x="94" y="53" text-anchor="middle" font-family="system-ui, sans-serif" font-size="9" font-weight="700" fill="#1e40af">Ngăn 1 (V₁)</text>
      <text x="94" y="67" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" fill="#3b82f6">Trung tâm</text>
      <line x1="128" y1="44" x2="160" y2="34" stroke="#9333ea" stroke-width="1.3" marker-end="url(#arrow-purple)"/>
      <line x1="160" y1="42" x2="128" y2="52" stroke="#9333ea" stroke-width="1.3" marker-end="url(#arrow-purple)"/>
      <rect x="163" y="24" width="70" height="28" rx="4" fill="#f3e8ff" stroke="#9333ea" stroke-width="1.2"/>
      <text x="198" y="38" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#6b21a8">Ngăn 2 (V₂)</text>
      <text x="198" y="48" text-anchor="middle" font-family="system-ui, sans-serif" font-size="7" fill="#7e22ce">Nông (k₁₂/k₂₁)</text>
      <line x1="128" y1="62" x2="160" y2="72" stroke="#0d9488" stroke-width="1.3" marker-end="url(#arrow-green)"/>
      <line x1="160" y1="80" x2="128" y2="70" stroke="#0d9488" stroke-width="1.3" marker-end="url(#arrow-green)"/>
      <rect x="163" y="68" width="70" height="28" rx="4" fill="#ccfbf1" stroke="#0d9488" stroke-width="1.2"/>
      <text x="198" y="82" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="700" fill="#0f766e">Ngăn 3 (V₃)</text>
      <text x="198" y="92" text-anchor="middle" font-family="system-ui, sans-serif" font-size="7" fill="#115e59">Sâu (k₁₃/k₃₁)</text>
      <line x1="94" y1="76" x2="94" y2="90" stroke="#dc2626" stroke-width="1.5" marker-end="url(#arrow-red)"/>
      <rect x="56" y="92" width="76" height="17" rx="3" fill="#fee2e2" stroke="#dc2626" stroke-width="1"/>
      <text x="94" y="104" text-anchor="middle" font-family="system-ui, sans-serif" font-size="8" font-weight="600" fill="#991b1b">CL/F (k₁₀)</text>
    </g>
  </g>"""
    return _svg_wrapper(800, 530, content)


# -----------------------------------------------------------------------------
# Lesson 11: Quick BE Screening
# -----------------------------------------------------------------------------
def get_diagram_11() -> str:
    content = """  <text x="380" y="24" text-anchor="middle" font-family="system-ui, sans-serif" font-size="13" font-weight="700" fill="#0f172a">Luồng Xử lý Sàng lọc Tương đương Sinh học Nhanh (R&amp;D / Pilot)</text>
  <g transform="translate(15, 42)">
    <rect x="0" y="0" width="160" height="65" rx="8" fill="#f8fafc" stroke="#64748b" stroke-width="1.5"/>
    <text x="80" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#334155">Bảng Dán Nhanh</text>
    <text x="80" y="46" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#64748b">Ctrl+V từ Excel</text>

    <line x1="160" y1="32" x2="190" y2="32" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <rect x="190" y="0" width="165" height="65" rx="8" fill="#eff6ff" stroke="#3b82f6" stroke-width="1.5"/>
    <text x="272" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#1e40af">Ánh xạ Tức thời</text>
    <text x="272" y="46" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#3b82f6">Subj, Per, Trt, Cmax/AUC</text>

    <line x1="355" y1="32" x2="385" y2="32" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <rect x="385" y="0" width="170" height="65" rx="8" fill="#fef3c7" stroke="#d97706" stroke-width="1.5"/>
    <text x="470" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#92400e">Tính NCA &amp; ANOVA</text>
    <text x="470" y="46" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#b45309">Ước tính GMR &amp; 90% CI</text>

    <line x1="555" y1="32" x2="585" y2="32" stroke="#2563eb" stroke-width="2" marker-end="url(#arrow)"/>

    <rect x="585" y="0" width="145" height="65" rx="8" fill="#dcfce7" stroke="#16a34a" stroke-width="1.5"/>
    <text x="657" y="25" text-anchor="middle" font-family="system-ui, sans-serif" font-size="11" font-weight="700" fill="#166534">Bảng Kết luận Sơ bộ</text>
    <text x="657" y="46" text-anchor="middle" font-family="system-ui, sans-serif" font-size="10" fill="#15803d">Quyết định thử chính thức</text>
  </g>"""
    return _svg_wrapper(760, 135, content)


DIAGRAM_SVGS = {
    0: get_diagram_0(),
    1: get_diagram_1(),
    2: get_diagram_2(),
    3: get_diagram_3(),
    4: get_diagram_4(),
    5: get_diagram_5(),
    6: get_diagram_6(),
    7: get_diagram_7(),
    8: get_diagram_8(),
    9: get_diagram_9(),
    10: get_diagram_10(),
    11: get_diagram_11(),
}
