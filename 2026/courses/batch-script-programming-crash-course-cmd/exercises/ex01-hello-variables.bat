@echo off
chcp 65001 >nul
REM =====================================================================
REM BÀI TẬP 01: Làm quen với echo và biến (set)
REM Mở bằng lệnh : bt ex01-hello-variables.bat
REM Chạy thử     : Bấm phím F5 ngay trong Micro (hoặc gõ: run)
REM =====================================================================

set HOC_VIEN=Duyên
set KHOA_HOC=Batch Script Programming Crash Course (CMD)
set TRANG_THAI=Đang thực hành bài tập 01

echo ----------------------------------------------------
echo Xin chào học viên : %HOC_VIEN%
echo Khóa đang học     : %KHOA_HOC%
echo Trạng thái        : %TRANG_THAI%
echo ----------------------------------------------------
