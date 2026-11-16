// File xử lý tương tác: web01.js (Bấm F3 để quay về web01.html)
let soLanBam = 0;

function doiTrangThai() {
    soLanBam++;
    const p = document.getElementById("thong-bao");
    p.textContent = "✅ Bạn đã bấm nút " + soLanBam + " lần! (Được xử lý từ file web01.js)";
}