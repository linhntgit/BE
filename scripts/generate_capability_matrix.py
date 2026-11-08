"""Generate the current regulatory capability table from the engine registry."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from be_app import __version__
from be_app.regulations import CAPABILITIES, RULES

DECISIONS = {
    "available": "Có (DRAFT)",
    "conditional": "Có điều kiện (DRAFT)",
    "blocked": "Khóa — NOT EVALUABLE",
}


def render_matrix() -> str:
    if set(CAPABILITIES) != set(RULES):
        raise ValueError("Registry quy tắc và capability không đồng bộ.")
    lines = [
        "# Ma trận capability BE hiện hành (sinh từ registry)",
        "",
        f"Phiên bản engine: **{__version__}**. Nguồn dữ liệu: `be_app/regulations.py` "
        "(`RULES` và `CAPABILITIES`). Chạy `python scripts/generate_capability_matrix.py` "
        "để cập nhật bảng khi thay đổi mã nguồn.",
        "",
        "`supported=True` chỉ biểu thị profile có đường thực thi trong engine. "
        "Cột **kết luận endpoint** mới cho biết khả năng trả đánh giá; "
        "**đã qualification độc lập** là một trạng thái khác. Mọi kết quả hiện vẫn thuộc "
        "phạm vi phát triển, không dùng thay quyết định chuyên gia hoặc thẩm định phần mềm.",
        "",
        "| Profile | Thiết kế | Thành phần tính toán | Kết luận endpoint | Planning | Đã qualification độc lập | Giới hạn/điều kiện |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for rule_id, rule in RULES.items():
        cap = CAPABILITIES[rule_id]
        decision = DECISIONS[cap.endpoint_decision]
        available = "Có" if cap.numerical_components else "Chưa"
        planning = "Có" if cap.planning else "Khóa"
        qualification = "Có" if cap.independently_qualified else "Chưa"
        limitation = cap.limitation.replace("|", "\\|").replace("\n", " ")
        lines.append(
            f"| `{rule_id}` | {', '.join(rule.designs)} | {available} | {decision} | "
            f"{planning} | {qualification} | {limitation} |"
        )
    lines += [
        "",
        "**Scope chung của BE:** IR đường uống, liều đơn, đúng thiết kế và rule, "
        "đủ bằng chứng protocol/SAP và guideline/PSG. Thiết kế thiếu kỳ hoặc trường hợp đặc biệt "
        "có thể trả NOT EVALUABLE dù profile ở bảng là 'Có'.",
        "",
        "**Phân hệ PK độc lập:** Có xử lý dữ liệu PK/NCA ở các chế độ khác, bao gồm "
        "một số trường hợp đa liều/steady-state; khả năng này không tự mở khóa "
        "đánh giá BE đa liều. Xem `docs/PK_STANDALONE_VI.md`.",
        "",
        "Các trường hợp FDA conventional replicate ABE chưa qualification được gate riêng; "
        "xem `docs/CONVENTIONAL_ABE_GATE.md`. Kiểm chứng thuật toán một số nhánh ở "
        "`docs/PHOENIX_BE_COMPARISON.md` chưa tương đương qualification toàn bộ phương pháp.",
        "",
    ]
    return "\n".join(lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("docs/CAPABILITY_MATRIX.md"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render_matrix(), encoding="utf-8")
    print(f"Wrote {args.output}")
