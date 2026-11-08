# Truy xuất yêu cầu tới thuật toán và kiểm thử

| Đặc tả | Mã thực thi | Bằng chứng tự động | Giới hạn |
|---|---|---|---|
| §2 RuleSet và phạm vi | be_app/regulations.py, pipeline.py | test_scope_unverified_blocks_endpoint, test_custom_limits_cannot_masquerade_as_profile | PSG do chuyên gia xác nhận từng sản phẩm |
| §5.2 Power | be_app/design.py | test_power_public_golden, test_joint_probability_against_independent_simulation | Equal log variance, không dùng cho Welch/replicate |
| §5.3 Randomization | be_app/design.py | test_randomization_balanced_reproducible | Không có blinding/RBAC |
| §6 Nhập/QC/actual time | be_app/imports.py | test_imports.py | Long only, trường hợp thiếu có cổng chặn |
| §6.3 Correction/freeze | be_app/persistence.py | test_correction_preserves_raw, test_freeze_hash_detects_direct_edit | Người review khai báo, chưa xác thực chữ ký |
| §7 NCA | be_app/nca.py | test_nca.py, PKNCA golden kể cả terminal/extrapolation với policy tương thích, nghiệm exponential | Cần mở rộng golden datasets và expert review terminal policy |
| §8.1 ABE crossover | be_app/statistics.py | Public R BE NCAResult4BE; independent OLS | Cần đủ hai kỳ, không mixed model mất kỳ |
| §8.1 Parallel | be_app/statistics.py | test_parallel_independent_statsmodels | Không covariates/strata |
| §8.2–3 ABEL/RSABE | be_app/regulations.py, statistics.py | Helper boundary tests, unsupported gates | Chưa phát hành phép thử replicate |
| §8.4 Kết luận endpoint | be_app/pipeline.py | test_aggregation_fails_closed, test_pipeline_demo_no_study_pass | Không thay độc lập PK/QA/RA review |
| §9 Report | be_app/reporting.py | test_reporting_ui.py; PDF render QA | Word layout chưa render được; CSR là khung tóm tắt |
| §10 Archive/DB | be_app/persistence.py | test_persistence_pipeline.py | Schema 1; version chưa biết bị từ chối, chưa có migration khác |
| §11 Audit | be_app/persistence.py | Audit/hash/triggers/conflict/backup tests | Không có external anchor hoặc Part 11 validation |
| §12 CI | .github/workflows/ci.yml | pytest + ruff + mypy + benchmark + pip-audit | CI workflow đã tạo; chưa chạy remote |

Các trường hợp outlier không được tự loại; absence of evidence không được biến thành PASS.
Các helpers ABEL/RSABE không là bằng chứng xác nhận model thống kê hay power simulation.
