# Ma trận capability BE hiện hành (sinh từ registry)

Phiên bản engine: **0.3.1**. Nguồn dữ liệu: `be_app/regulations.py` (`RULES` và `CAPABILITIES`). Chạy `python scripts/generate_capability_matrix.py` để cập nhật bảng khi thay đổi mã nguồn.

`supported=True` chỉ biểu thị profile có đường thực thi trong engine. Cột **kết luận endpoint** mới cho biết khả năng trả đánh giá; **đã qualification độc lập** là một trạng thái khác. Mọi kết quả hiện vẫn thuộc phạm vi phát triển, không dùng thay quyết định chuyên gia hoặc thẩm định phần mềm.

| Profile | Thiết kế | Thành phần tính toán | Kết luận endpoint | Planning | Đã qualification độc lập | Giới hạn/điều kiện |
| --- | --- | --- | --- | --- | --- | --- |
| `EMA_IR_NONREPLICATE_M13A` | 2x2, parallel | Có | Có (DRAFT) | Có | Chưa | Power TOST 2×2/parallel; kết quả vẫn là bản phát triển cần thẩm định. |
| `FDA_ABE_2026` | 2x2, parallel | Có | Có (DRAFT) | Có | Chưa | Power TOST 2×2/parallel; kết quả vẫn là bản phát triển cần thẩm định. |
| `EMA_REPLICATE_STANDARD` | partial3, full4 | Có | Có (DRAFT) | Khóa | Chưa | Chưa có lập kế hoạch power replicate được đối chiếu độc lập. |
| `EMA_HVDP_ABEL` | partial3, full4 | Có | Có điều kiện (DRAFT) | Khóa | Chưa | ABEL chỉ khi đủ điều kiện scaling; chưa hỗ trợ planning replicate. |
| `FDA_HVD_RSABE_2026` | partial3, full4 | Có | Có điều kiện (DRAFT) | Khóa | Chưa | sWR < 0,294 cần conventional replicate ABE chưa qualified: NOT EVALUABLE; sWR cao dùng RSABE theo điều kiện. |
| `FDA_NTI` | full4 | Có | Khóa — NOT EVALUABLE | Khóa | Chưa | Conventional replicate ABE chưa qualified: NOT EVALUABLE, dù đã có thành phần tính toán. |
| `EMA_NTI` | 2x2, parallel, partial3, full4 | Có | Có (DRAFT) | Khóa | Chưa | Cỡ mẫu NTI đang khóa chờ oracle độc lập; AUC 0,90–1,1111, Cmax thu hẹp khi được chỉ định. |
| `FDA_REPLICATE_STANDARD` | partial3, full4 | Có | Khóa — NOT EVALUABLE | Khóa | Chưa | Conventional mixed replicate ABE chưa qualified: NOT EVALUABLE. |

**Scope chung của BE:** IR đường uống, liều đơn, đúng thiết kế và rule, đủ bằng chứng protocol/SAP và guideline/PSG. Thiết kế thiếu kỳ hoặc trường hợp đặc biệt có thể trả NOT EVALUABLE dù profile ở bảng là 'Có'.

**Phân hệ PK độc lập:** Có xử lý dữ liệu PK/NCA ở các chế độ khác, bao gồm một số trường hợp đa liều/steady-state; khả năng này không tự mở khóa đánh giá BE đa liều. Xem `docs/PK_STANDALONE_VI.md`.

Các trường hợp FDA conventional replicate ABE chưa qualification được gate riêng; xem `docs/CONVENTIONAL_ABE_GATE.md`. Kiểm chứng thuật toán một số nhánh ở `docs/PHOENIX_BE_COMPARISON.md` chưa tương đương qualification toàn bộ phương pháp.
