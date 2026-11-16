// =====================================================================
// BÀI TẬP 04: Thực hành JavaScript cơ bản (Chạy trực tiếp trên Terminal)
// Mở bằng lệnh : bt ex04-javascript-co-ban.js
// Chạy thử     : Bấm phím F5 ngay trong Micro (hoặc gõ: run)
// =====================================================================

const hocVien = "Duyên";
const kyNangWeb = [
    { ten: "HTML5 (Khung trang web)", trangThai: "Đã nắm cơ bản" },
    { ten: "CSS3 (Trang trí & Màu Serein)", trangThai: "Đang thực hành" },
    { ten: "JavaScript (Xử lý tương tác)", trangThai: "Đang thực hành" }
];

console.log(`=== 🌐 LỘ TRÌNH HỌC WEB CỦA ${hocVien.toUpperCase()} ===`);
kyNangWeb.forEach((mon, index) => {
    console.log(`  ${index + 1}. ${mon.ten} -> [${mon.trangThai}]`);
});

// Tính nhanh tiến độ
const ngayBatDau = "2026-11-15";
console.log(`\n📅 Bắt đầu từ ngày: ${ngayBatDau}`);
console.log("💡 Mẹo: Để xem giao diện Web thực tế, hãy mở bài ex03-mini-web.html và bấm F5!");
