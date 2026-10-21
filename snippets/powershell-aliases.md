# ⚡ PowerShell Quick Aliases & Utilities

Tổng hợp các lệnh PowerShell hữu ích cho công việc hằng ngày.

## Git Quick Shortcuts

```powershell
# Xem trạng thái ngắn gọn
function gst { git status -sb }

# Commit nhanh
function gcm ($msg) { git commit -m "$msg" }

# Push lên main
function gpush { git push origin main }
```

## System Shortcuts

```powershell
# Xóa cache tạm
Clear-History
```
