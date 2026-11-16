# =====================================================================
# BÀI TẬP 01: Biến, phép tính và ghép chuỗi (f-string) trong Python
# Mở bằng lệnh : bt  (rồi chọn ex01-greeting.py)
# Chạy thử     : Bấm phím F5 ngay trong Micro (hoặc gõ: run)
# =====================================================================

hoc_vien = "Duyên"
so_phut_moi_ngay = 45
so_ngay_trong_tuan = 7

tong_phut = so_phut_moi_ngay * so_ngay_trong_tuan
tong_gio = tong_phut / 60

print("=== THỐNG KÊ THỜI GIAN TỰ HỌC PYTHON ===")
print(f"Học viên       : {hoc_vien}")
print(f"Mỗi ngày học   : {so_phut_moi_ngay} phút")
print(f"Tổng 1 tuần    : {tong_phut} phút (tương đương {tong_gio:.2f} giờ)")
