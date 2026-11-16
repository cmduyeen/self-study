@echo off
chcp 65001 >nul
REM =====================================================================
REM BÀI TẬP 02: Tính toán số học với lệnh set /a
REM Mở bằng lệnh : bt ex02-math-calculation.bat
REM Chạy thử     : Bấm phím F5 ngay trong Micro (hoặc gõ: run)
REM =====================================================================

set /a GIA_SACH=120000
set /a SO_LUONG=3
set /a GIAM_GIA=30000
set /a TONG_TIEN=(%GIA_SACH% * %SO_LUONG%) - %GIAM_GIA%

echo === TÍNH HÓA ĐƠN MUA SÁCH HỌC CODE ===
echo Đơn giá   : %GIA_SACH% VNĐ
echo Số lượng  : %SO_LUONG% quyển
echo Giảm giá  : %GIAM_GIA% VNĐ
echo --------------------------------------
echo Thành tiền: %TONG_TIEN% VNĐ
