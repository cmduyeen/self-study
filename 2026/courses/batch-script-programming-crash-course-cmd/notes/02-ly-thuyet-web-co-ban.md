# Bài 2: Lý thuyết Cơ Bản Về Web (HTML, CSS & JavaScript)
> Ngày ghi: 2026-11-15
> Mẹo nhanh: Bấm **Ctrl+B** ẩn/hiện cây thư mục | **F3** đổi Tab | **F8** hỏi AI

---

## 1. Ba thành phần cốt lõi của một trang Web

- [x] **HTML** (`HyperText Markup Language`): Khung xương và nội dung của trang web (tiêu đề, đoạn văn, nút bấm, hình ảnh).
- [x] **CSS** (`Cascading Style Sheets`): Lớp áo trang trí (màu sắc, phông chữ, bố cục chia cột, hiệu ứng).
- [ ] **JavaScript** (`JS`): Bộ não tạo sự tương tác (bấm nút thì đổi nội dung, tính toán, kiểm tra biểu mẫu).

---

## 2. Bảng các thẻ HTML5 hay dùng nhất

| Thẻ HTML       | Ý nghĩa               | Ví dụ ngắn                     |
| :------------- | :-------------------- | :----------------------------- |
| `<h1>`..`<h3>` | Tiêu đề lớn / nhỏ     | `<h1>Xin chào</h1>`            |
| `<p>`          | Đoạn văn bản          | `<p>Nội dung bài viết</p>`     |
| `<button>`     | Nút bấm tương tác     | `<button>Bấm vào đây</button>` |
| `<input>`      | Ô nhập dữ liệu        | `<input placeholder="Tên...">` |
| `<div>`        | Khối gom nhóm bố cục  | `<div class="card">...</div>`  |

---

## 3. Ba bước nối JavaScript vào HTML

1. Đặt thuộc tính `id="ket-qua"` vào thẻ HTML muốn thay đổi: `<p id="ket-qua"></p>`
2. Trong thẻ `<script>`, dùng lệnh `document.getElementById("ket-qua")` để tìm thẻ đó.
3. Gán `.textContent = "Nội dung mới"` để thay đổi chữ trên màn hình ngay lập tức.

---
*Bài tập thực hành nằm tại thư mục `exercises/`: `web01.html`, `web01.css`, `web01.js`.*
