# =====================================================================
# BÀI TẬP 02: Danh sách (List) và Vòng lặp (for)
# Mở bằng lệnh : bt  (rồi chọn ex02-todo-loop.py)
# Chạy thử     : Bấm phím F5 ngay trong Micro (hoặc gõ: run)
# =====================================================================

bai_tap_tuan_nay = [
    ("Đọc ghi chú Chương 1 trong thư mục notes/", True),
    ("Chạy thử bài tập ex01-greeting.py bằng phím F5", True),
    ("Tự viết thêm 1 bài tập mới vào thư mục exercises/", False),
]

so_bai_xong = sum(1 for _, da_xong in bai_tap_tuan_nay if da_xong)
print(f"📊 Tiến độ hoàn thành: {so_bai_xong}/{len(bai_tap_tuan_nay)} mục tiêu\n")

for thu_tu, (ten_muc_tieu, da_xong) in enumerate(bai_tap_tuan_nay, start=1):
    trang_thai = "[x] Đã xong" if da_xong else "[ ] Chưa xong"
    print(f"  {thu_tu}. {trang_thai} - {ten_muc_tieu}")

# 💡 TEST THỬ TÍNH NĂNG DỊCH LỖI TIẾNG VIỆT:
# Bạn hãy thử xóa dấu '#' ở đầu dòng dưới rồi bấm F5 để xem máy giải thích lỗi:
# print("Dòng này cố tình thiếu dấu nháy đóng ở cuối câu
