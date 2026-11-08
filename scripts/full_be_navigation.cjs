const stages = [
  ['Xác định nghiên cứu', ['Tổng quan / Quản lý nghiên cứu']],
  ['Thiết kế và kế hoạch phân tích', ['Thiết kế và cỡ mẫu BE', 'Ngẫu nhiên hóa và lịch lấy mẫu']],
  ['Nhập và kiểm tra dữ liệu', ['Nhập dữ liệu nồng độ', 'Kiểm soát chất lượng (QC)']],
  ['Duyệt thông số PK', ['Phân tích NCA']],
  ['Đánh giá BE', ['Thống kê BE — EMA / FDA', 'Đồ thị và chẩn đoán']],
  ['Rà soát và xuất', ['Báo cáo CTD / Xuất dữ liệu', 'Nhật ký kiểm toán / Quản trị']],
];
exports.stageForPage = page => {
  const entry = stages.find(([, pages]) => pages.includes(page));
  if (!entry) throw Error('Unknown Full BE page: ' + page);
  return entry[0];
};
exports.singlePageStages = new Set(stages.filter(([, pages]) => pages.length === 1).map(([name]) => name));
