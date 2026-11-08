# Bằng chứng khảo sát Phoenix, 30/10/2026

Đọc [báo cáo và backlog đề xuất](../PHOENIX_TEMPLATE_SURVEY.md) trước khi diễn giải các file này.

## Phương pháp

Các file `.txt` là văn bản accessibility lấy qua giao diện Phoenix 8.8.0.20523 sau khi mở project và mở rộng cây workflow. Đã giới hạn nội dung theo project liên quan, bỏ menu và thông tin của các project khác. Chỉ số phần tử UI có ý nghĩa tại thời điểm quan sát; không phải object ID ổn định hoặc hướng dẫn tự động hóa có thể phát lại.

Đây là bằng chứng khảo sát. Kết quả đang lưu trong project chưa được chạy lại trong đợt khảo sát này. Giá trị trên bảng cuối đã làm tròn, chưa đủ để tạo golden fixture.

## Mẫu và bằng chứng

| Mẫu | Bằng chứng |
|---|---|
| Bioequivalence 2x2x2 | [Workflow](abe_2x2_workflow.txt) |
| Bioequivalence IndPop | [Workflow](indpop_workflow.txt) |
| Bioequivalence replicated | [Workflow](replicate_workflow.txt), [đối tượng BE đã xem](replicate_model.txt) |
| EMA ABEL | [Workflow](ema_workflow.txt), [bảng cuối](ema_conclusion.txt) |
| FDA HVD RSABE | [Workflow](fda_hvd_workflow.txt) |
| FDA NTI | [Workflow](fda_nti_workflow.txt), [bảng ba tiêu chí](fda_nti_final.txt) |
| Methylphenidate | [Workflow](methylphenidate_workflow.txt) |
| In vitro | [Workflow](invitro_workflow.txt) |

[Inventory và SHA-256](inventory.json) nhận diện tám `.phxproj` được mở. Hash được thu thập trong đợt khảo sát, không phải bản hash trước/sau để chứng minh file nguồn bất biến. Không bấm Save Project trong Phoenix.

## Benchmark app đã chạy lại

- [NCA Fasted summary](baseline_nca_summary.json): 1.968 mục khớp, bao gồm 468 cặp cùng missing.
- [ABE Fasted summary](baseline_be_summary.json): 78 thống kê khớp.

Hai benchmark này dùng các workbook Fasted đã có tại gốc dự án; không phải benchmark tám project vừa khảo sát. Workbook so sánh đầy đủ được tạo bởi script hiện có trong `output/phoenix_nca` và `output/phoenix_be`.

Không chứa bản sao `.phxproj`, mã chương trình của Certara hay dữ liệu xuất để fit mới. Giữ bộ khảo sát trong phạm vi sử dụng nội bộ của dự án.
