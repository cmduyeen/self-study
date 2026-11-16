# 📓 Bài 1: Lý thuyết Batch Script (CMD) Cơ Bản

## 1. Cấu trúc một file Batch (`.bat` / `.cmd`)
- Mọi file Batch thường bắt đầu bằng dòng `@echo off` để ẩn các dòng lệnh hệ thống, chỉ hiện kết quả in ra màn hình.
- Để hiển thị tiếng Việt có dấu không bị lỗi font, thêm dòng `chcp 65001 >nul` ngay dưới `@echo off`.
- Để viết ghi chú (comment) trong code, dùng từ khóa `REM` ở đầu dòng.

## 2. Bảng tóm tắt các lệnh quan trọng

| Câu lệnh | Cú pháp | Ý nghĩa |
| :--- | :--- | :--- |
| **`echo`** | `echo Xin chào` | In dòng chữ ra màn hình |
| **`set`** | `set TEN=Duyên` | Gán giá trị chữ cho biến (không có dấu cách quanh dấu `=`) |
| **`set /a`** | `set /a TONG=10 + 20` | Tính toán biểu thức toán học (`+`, `-`, `*`, `/`) |
| **`set /p`** | `set /p TEN=Nhập tên: ` | Dừng màn hình chờ người dùng nhập dữ liệu từ bàn phím |
| **`%BIEN%`** | `echo %TEN%` | Lấy giá trị của biến ra để sử dụng |
| **`pause`** | `pause` | Dừng màn hình chờ nhấn phím bất kỳ |

## 3. Lưu ý hay nhầm lẫn khi làm bài tập
1. **Tuyệt đối không để khoảng trắng trước và sau dấu `=`** khi dùng lệnh `set` (ví dụ viết `set A=5` thay vì `set A = 5`).
2. Khi muốn tính toán số học, bắt buộc phải có `/a` (`set /a`). Nếu thiếu `/a`, máy sẽ hiểu `10 + 20` là chuỗi chữ `"10 + 20"` chứ không phải số `30`.

---
*👉 Bài tập thực hành tương ứng nằm tại thư mục `exercises/`: `ex01-hello-variables.bat` và `ex02-math-calculation.bat` (Gõ lệnh `bt` để mở).*
