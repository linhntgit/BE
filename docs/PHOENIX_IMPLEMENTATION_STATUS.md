# Tiến độ triển khai cải tiến từ khảo sát Phoenix

Yêu cầu được người dùng cho phép ngày 30/10/2026: triển khai các đề xuất trong `PHOENIX_TEMPLATE_SURVEY.md`, lưu tiến độ để tự tiếp tục sau gián đoạn hạn mức 5 giờ.

## Cách tiếp tục

1. Đọc file này và `phoenix_implementation_status.json`, kiểm tra thay đổi trên đĩa trước khi sửa tiếp. Repo hiện có toàn bộ nguồn ở trạng thái untracked; không reset/clean hoặc ghi đè thay đổi không liên quan.
2. Tiếp tục hạng mục đang làm; cập nhật checkpoint sau mỗi mốc có kiểm thử. Không tuyên bố kiểm chứng mẫu Phoenix chỉ từ bảng hiển thị đã làm tròn.
3. Chạy kiểm tra phù hợp, sau đó full pytest, ruff, mypy và hai benchmark Fasted khi hoàn tất một đợt tích hợp. Duy trì freeze, stale gates, snapshot và cache theo profile.
4. Nếu bị giới hạn, scheduler của chat sẽ thử tiếp theo lịch; tiến độ bền vững nằm trên đĩa. Scheduler cần máy bật và ứng dụng desktop hoạt động. Không có cam kết đánh thức đúng giây quota reset; không có API quota đang được dùng trong dự án.

## Trạng thái hiện tại (31/10/2026)

- Khảo sát xong 8 project Phoenix 8.8; bằng chứng tại `docs/phoenix_survey`.
- Benchmark gốc: NCA 1968/1968 (468 cặp missing), ABE 78/78 đạt.
- Đã có biểu đồ giới hạn theo endpoint và đồ thị UCB/SD ratio; bảng reviewer criteria, population matrix/counts và PK mô tả trong UI/Excel. Workflow view dùng cùng snapshot.
- Đã có QQ/residual/box plots và studentized residuals OLS của chính mô hình EMA reference-only hoặc FDA I/D; đối chiếu độc lập statsmodels, không tự loại dữ liệu.
- Đã có per-profile terminal override: identity, data hash, reviewer/reason; freeze từ chối lựa chọn cũ/không còn profile; sửa một profile chỉ refit một profile. Draft làm STALE, archive giữ cấu hình. Empty overrides giữ nguyên hash của project schema-2 cũ.
- Đã có PK import: chọn sheet, mapping cột/T-R/sequence, raw/Ln/log10, xác nhận đơn vị, provenance/hash; source và mapping giữ trong draft. Kết quả PK độc lập đổi đầu vào được gắn STALE và chặn tải.
- Đã có xuất/nhập preset cấu hình có checksum/schema, tạo dự án mới không mang raw/results/freeze/audit nguồn/scope approval/manual slopes. Chưa nghiệm thu trực quan toàn bộ luồng.
- Engine 0.3.1 đóng conventional FDA replicate ABE chưa qualification; không tích hợp prototype. I/D/Howe/variance ratio và các estimator EMA/nonreplicate không đổi. Snapshot engine cũ là LEGACY. Xem `CONVENTIONAL_ABE_GATE.md`.

## Việc tiếp theo

1. Rule/design/NTI/protocol của panel PK độc lập đã lưu theo dự án, giữ qua điều hướng/reload và không tràn sang dự án khác (AppTest đạt). Tiếp tục kiểm tra giao diện thực.
2. PHX-04/10: đã tích hợp 6 bảng reviewer/population/PK mô tả vào Word/PDF từ cùng snapshot. PDF vi/en đã render bằng bundled Poppler và xem đủ 4 trang mỗi bản sau sửa pagination. Word đạt kiểm tra cấu trúc; bundled renderer báo thiếu soffice.exe, nên chưa xác nhận layout Word.
3. PHX-02: đã xuất 525 file dependencies của EMA/FDA NTI/FDA HVD và đối chiếu 28 số: 23 khớp, 5 khác biệt được giải thích (hằng số NTI và estimator/df conventional ABE). Xem `PHOENIX_REPLICATE_COMPARISON.md`. Mẫu EMA có missing, mẫu HVD log lại logData và chọn nhánh unscaled; chưa qualification toàn phương pháp.
4. Kiểm tra giao diện thực (đồ thị/slope/import/preset), bổ sung ca AppTest cho tương tác mới, sửa nhãn/hiệu năng nếu cần.
5. PHX-11/12 vẫn là các chương trình phương pháp riêng cần đặc tả và independent validation; chưa mở missing replicate, MR/partial AUC, IBE/PBE/in vitro.

## Kiểm tra đã chạy

- Full pytest: **226 passed / 0 failed**, 33.31 s; JUnit `output/phoenix-integration-tests.xml`.
- Trước đó: 81 tests tích hợp mới/cũ đạt; 54 tests slope/snapshot/reviewer đạt.
- Ruff toàn be_app/scripts/tests và mypy 26 modules đạt sau sửa uploader và bổ sung oracle độc lập.
- NCA Fasted **1968/1968** (468 cặp missing), max abs 3.710738383233547e-10; ABE Fasted **78/78**, max abs 3.696507883432787e-05.
- Chạy pytest/AppTest bằng `exec_command` với `require_escalated`: sandbox Windows gây PermissionError thư mục tạm và treo AppTest; cùng tests ngoài sandbox chạy bình thường. Không bỏ test để che lỗi.
- Đã thêm bảng Word/PDF và xem đủ 4 trang PDF mỗi ngôn ngữ. Đã kiểm tra browser cho đồ thị ABE/EMA NTI/ABEL/FDA HVD/NTI, workflow và residual FDA. Slope manual preview/apply và import workbook second-sheet/Ln/mapping đã xem bằng browser; còn preset/removal sau sửa, đầy đủ EMA residual plots và Word layout. Đối chiếu replicate mới có 23/28 số khớp, 5 sai khác đã phân loại; chưa qualification phương pháp.

Automation ID: `ti-p-t-c-c-i-ti-n-be-app-sau-gi-n-o-n`, ACTIVE, heartbeat trong chat mỗi 30 phút. Chưa tắt vì công việc còn lại.

## Nhật ký mốc

- 30/10/2026: khởi tạo checkpoint và yêu cầu scheduler heartbeat mỗi 30 phút.
- 31/10/2026: tiếp tục từ file sau gián đoạn; hoàn thiện slope/import/preset, giữ tương thích dữ liệu cũ và chạy đạt 205 tests + lint/type checks + hai benchmark Fasted.

- 31/10/2026: thêm bảng reviewer vào Word/PDF, bỏ JSON kết quả trùng lặp khỏi phần diễn giải, sửa heading/pagination và format CI. Lưu PK review theo owner; preset giữ sheet/mapping/log/output preferences và vẫn loại dữ liệu/phê duyệt. 208 tests đạt, lint và type checks đạt. Word renderer thiếu bundled soffice.exe, được ghi nhận là chưa visual-qualified.

- 31/10/2026: xuất thành công dependencies qua Phoenix GUI, giữ nguyên hash 3 project nguồn. Tạo script benchmark replicate với manifest và phân loại sai khác, không nới tolerance. Bổ sung selected points/fitted lines và bảng thời gian terminal, kiểm tra UI apply không sửa raw hoặc tự chạy study (4 tests mới đạt).

- 31/10/2026: nghiệm thu browser bằng database QA riêng, sửa legend đè trục, thêm nhãn ngưỡng UCB/SD và ghi rõ đơn vị residual là thang log/studentized unitless (giữ Source_PK_Units). Cache bảng có render schema version để không dùng nhãn cũ sau cập nhật. Tạo `FDA_REPLICATE_ABE_METHOD_SPEC.md` từ sai khác thực tế và FDA May 2026; prototype mới chưa được nối vào quyết định. Word launch bị timeout ở yêu cầu app approval, không có cửa sổ Word; không tuyên bố Word đã visual QA.

- Cuối mốc: sửa hai cột Value hỗn hợp trong UI (criteria/diagnostics) để không phát sinh Arrow fallback, giữ nguyên kiểu số ở Excel; AppTest kiểm tra log. Full pytest 212 passed (22.93 s), Ruff và mypy 25 modules đạt. Tab/server QA riêng đã đóng; database nghiên cứu và ba project Phoenix nguồn được bảo toàn. Heartbeat tiếp tục ACTIVE.

- 31/10/2026: đặc tả và prototype full4 FA0 REML observed-Satterthwaite nằm ngoài production; 6 tests độc lập/invariant/fail-closed đạt. Xuất thêm basic replicate bằng GUI, giữ hash nguồn. Audit NTI/basic đạt 60/60 đại lượng comparable; likelihood normalization khác được giữ và replay riêng. Cả hai balanced/near-boundary, chưa qualification. Xem `REPLICATE_ABE_EXPERIMENTAL_VALIDATION.md`; không mở kết luận mới. Full regression đợt mới đang chờ chạy.

- Cuối mốc prototype: full pytest **218 passed / 0 failed** (35.00 s), Ruff toàn be_app/scripts/tests và mypy 26 modules đạt. NCA Fasted 1968/1968, ABE Fasted 78/78 vẫn đạt. Tiếp tục visual QA UI bằng database output riêng.

- 31/10/2026: tiếp tục sau gián đoạn; giữ server QA hiện hữu, không chạy trùng. Thêm oracle REML độc lập bằng orthonormal error contrasts, covariance tuyến tính, Nelder-Mead và finite-difference Hessian/sensitivity: fixture nội miền lệch sequence 9/21 khớp covariance, SE, df, CI trong tolerance chốt trước. Không đổi production/inference gate.

- Sửa hồi quy uploader: thao tác gỡ file nay xóa staged source trong draft, kết quả PK cũ STALE và download/calculation disabled; giữ nguyên canonical raw và cached values. Thêm AppTest cho callback removal và nút tạo dự án từ preset. Full pytest **221 passed** (30.46 s), Ruff/mypy và benchmark NCA 1968/1968, ABE 78/78 đạt. Audit prototype Phoenix vẫn 60/60 comparable.

- Ghi nghiệm thu UI trong `PHOENIX_UI_QA.md`: manual slope/apply và import PK workbook đã được xem trước gián đoạn; chưa xem đủ EMA reference-only/Method A plots và preset/removal sau sửa. Browser hiện bị tắt trong Work settings, đã thông báo người dùng cần bật. Người dùng đã cho phép mọi bước cần thiết; không hỏi lại quyền, nhưng không tự vượt setting. Bundled runtime vẫn không có LibreOffice, Word layout còn pending. Heartbeat giữ ACTIVE.

- 31/10/2026: từ sai khác estimator đã xác nhận và Appendix C/F FDA (mở lại nguồn), đóng suy luận conventional ABE ở FDA_REPLICATE_STANDARD/FDA_NTI/HVD sWR<0.294. Giữ I-contrast CI chỉ chẩn đoán, ABE criterion chưa đánh giá; không dùng prototype mở kết luận. Engine/package 0.3.1, ba rule FDA replicate 2.0.1; snapshot 0.3.0 được nhận LEGACY, không ghi đè hay tự refit.

- Kiểm tra mốc 0.3.1: 226 tests đạt (40.14 s), Ruff/mypy 26 modules, uv offline lock check 84 packages đạt; NCA 1968/1968, ABE 78/78, replicate component audit 23/28 (5 sai khác phân loại), prototype 60/60 comparable vẫn đạt. `PHOENIX_METHOD_EXTENSION_PLAN.md` tách PHX-11/12 thành phạm vi/epic và acceptance; chưa triển khai phương pháp mới.

- Word đã mở thành công bản QA tiếng Việt sau quyền cho phép mới. Kiểm tra một phần trang 1/4 cho thấy viền Title xanh và theme font có thể ghi đè Arial; đã sửa generator và thêm kiểm tra OOXML, 6 report tests đạt. Chưa render/xem hết bản mới vi/en nên layout vẫn pending; không dùng bản QA cũ như kết quả engine 0.3.1.

- Cuối đợt: full pytest sau sửa report style **226 passed** (33.31 s), không còn process test đang chạy; checkpoint đã lưu. Giữ heartbeat ACTIVE để tiếp tục từ đây, không chạy lại từ đầu.

- 31/10/2026 16:30 Perth: browser đã truy cập được sau restart ứng dụng; QA server riêng khởi động khi cổng 8511 không có listener. Xem đủ residual-fitted/QQ/box của EMA Method A và reference-only R trên viewport 714px. Uploader thật gắn/gỡ workbook xác nhận STALE và disabled download/preview/calculation. Đọc lại QA project: raw không đổi, một override, zero runs, staged file null, mapping giữ nguyên. Còn preset browser và latest Word layout.

- 31/10/2026: nghiệm thu browser preset hoàn tất: prepare → download → file chooser upload → tạo dự án mới d7e2e95b. Đọc lại đĩa xác nhận dự án mới không có raw/runs/freeze/protocol/SAP/scope approval/demo/manual override/staged file; giữ sheet PK/Ln/mapping và buộc xác nhận lại đơn vị. Raw nguồn và một terminal override nguồn nguyên vẹn. Không đổi mã đợt QA này; kết quả 226 tests trước đó còn áp dụng. Còn latest Word render/layout và qualification mixed model.

- 31/10/2026: sinh mới Word/PDF vi/en từ export thật engine 0.3.1, n=4 giả lập, cùng snapshot; artifacts và SHA-256 ở output/phoenix_report_qa/current_031/manifest.json. Cả hai DOCX có 8 bảng, không Title border kế thừa, nhãn engine 0.3.1. Kiểm tra JUnit trên đĩa xác nhận 226 tests/0 failure/0 error. Không sửa mã hoặc dữ liệu nghiên cứu.

- Runtime đổi sang bundle 26.1026.10807, đã thử canonical render lại: thiếu LibreOffice soffice.exe trên PATH. Thử mở Word bằng computer-use gặp app approval timed out. Chưa visual-qualified output mới; cần người dùng mở/cho phép Word để tiếp tục đọc trực tiếp. Không cài phần mềm, không dùng COM hoặc bypass app approval. Heartbeat giữ ACTIVE; không mở inference mixed model.

- 31/10/2026 (QA cải tiến): full regression mới **236 passed / 0 failed / 0 errors / 0 skipped** trong 45,17 s; Ruff toàn be_app/tests/scripts, mypy 27 modules đạt. Kịch bản synthetic **77/77** expected checks; browser smoke **13 checks** với viewport 714/1440px. Manifest hiện hành tại `output/qa_20261031/improvement_evidence_20261031.json`, JUnit `output/qa_20261031/improvement_pytest.xml` (không thay mốc baseline 226 trước đó). Báo cáo mới vi/en dùng cùng snapshot, mỗi DOCX có 8 bảng, mỗi PDF có 7 trang; cảnh báo synthetic/QA trong bản Anh đã bản địa hóa, tên nghiên cứu gốc vẫn nguyên văn. Đã xem montages đầy đủ 7/7 trang vi và 7/7 trang en (thêm trang 1 Anh độ phân giải gốc): chưa thấy cắt biên/tràn bảng, tiêu đề bảng lặp khi sang trang. Kiểm tra bố cục PDF liên kết SHA-256 chính xác trong `output/qa_20261031/pdf_visual_review_20261031.json`; phạm vi chỉ là layout PDF, chưa xác nhận nội dung khoa học hay render trực quan Word. Giữ gate `NOT EVALUABLE` dữ liệu QA; còn EMA NTI planning oracle, FDA conventional replicate ABE/RSABE/HVD thấp-sWR/NTI qualification, full browser UAT, Word vi/en layout, reviewer sign-off.
