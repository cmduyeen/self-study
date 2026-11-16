# =====================================================================
# BRAIN2ND CLI: HỆ THỐNG NĂNG SUẤT CÁ NHÂN (TERMINAL + VSCODE + OBSIDIAN + BLOG)
# Root: D:\Brain2nd
# =====================================================================

$Global:BrainRoot = "D:\Brain2nd"
$Global:VibeCodingRoot = "D:\Brain2nd\Code"
$Global:StudyRoot = "D:\Brain2nd\Code\cmduyeen-self-study"
$Global:BlogRoot = "D:\Brain2nd\Code\cmduyeen-github-page"
$Global:BlogScript = Join-Path $Global:BlogRoot "tools\blog.py"
$Global:TrackScript = Join-Path $Global:StudyRoot "scripts\track-productivity.py"
$Global:LearnScript = Join-Path $Global:StudyRoot "scripts\learn.py"
$Global:RunCodeScript = Join-Path $Global:StudyRoot "scripts\run-code.py"
$Global:AiHelperScript = Join-Path $Global:StudyRoot "scripts\ai-helper.py"
$Global:GenReadmeScript = Join-Path $Global:StudyRoot "scripts\generate-readme.py"
$Global:LastFileCache = Join-Path $Global:StudyRoot ".last_study_file"
$Global:LastVibeProjectCache = Join-Path $Global:StudyRoot ".last_vibe_project"

# Đảm bảo PATH có VS Code, Neovim, Antigravity CLI (agy) và các công cụ vừa cài qua winget
$ExtraPaths = @(
    (Join-Path $env:LOCALAPPDATA "Programs\Microsoft VS Code\bin"),
    (Join-Path $env:LOCALAPPDATA "Microsoft\WinGet\Links"),
    (Join-Path $env:LOCALAPPDATA "agy\bin"),
    "C:\Program Files\Neovim\bin",
    "C:\Program Files\fzf\bin"
)
foreach ($ep in $ExtraPaths) {
    if ((Test-Path $ep) -and ($env:Path -notlike "*$ep*")) {
        $env:Path += ";$ep"
    }
}

# Đồng bộ bảng màu của bat & fzf theo đúng theme Serein (Alabaster / Obsidian) của Terminal
$env:BAT_THEME = "ansi"
$env:FZF_DEFAULT_OPTS = "--color=16"

function Get-SystemThemeMode {
    try {
        $reg = Get-ItemProperty -Path "HKCU:\Software\Microsoft\Windows\CurrentVersion\Themes\Personalize" -ErrorAction Stop
        if ($reg.AppsUseLightTheme -eq 1) { return "light" }
    } catch {}
    return "dark"
}

function Get-ActiveStudyFolder {
    $studyFiles = Get-ChildItem -Path $Global:StudyRoot -Filter "study.json" -Recurse -ErrorAction SilentlyContinue
    foreach ($sf in $studyFiles) {
        try {
            $json = Get-Content $sf.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
            if ($json.status -eq "studying") {
                return $sf.Directory.FullName
            }
        } catch {}
    }
    if ($studyFiles.Count -gt 0) {
        return $studyFiles[0].Directory.FullName
    }
    return $Global:StudyRoot
}

function Set-LastStudyFile([string]$FilePath) {
    if ($FilePath -and (Test-Path $FilePath)) {
        $resolved = (Resolve-Path $FilePath).Path
        [System.IO.File]::WriteAllText($Global:LastFileCache, $resolved, (New-Object System.Text.UTF8Encoding($false)))
    }
}

function Get-LastStudyFile {
    if (Test-Path $Global:LastFileCache) {
        $p = (Get-Content $Global:LastFileCache -Raw -Encoding UTF8).Trim()
        if ($p -and (Test-Path $p)) {
            return $p
        }
    }
    return $null
}

function Open-InMicro([string]$FilePath, [int]$Line = 0) {
    if (-not $FilePath) { return }
    if ([System.IO.Path]::GetExtension($FilePath).ToLower() -ne ".md") {
        Set-LastStudyFile $FilePath
    }
    $activeDir = Get-ActiveStudyFolder
    $vsCmd = Join-Path $env:LOCALAPPDATA "Programs\Microsoft VS Code\bin\code.cmd"
    if (Test-Path -LiteralPath $vsCmd) {
        if ($Line -gt 0) {
            & $vsCmd "$activeDir" --goto "${FilePath}:${Line}"
        } else {
            & $vsCmd "$activeDir" "$FilePath"
        }
    } else {
        code "$activeDir" "$FilePath"
    }
}

# =====================================================================
# LUỒNG 1: GHI CHÚ LÝ THUYẾT (Thư mục `notes/`)
# =====================================================================

# Lệnh `n`: Chọn mở bài ghi chú trong `notes/` HOẶC tạo bài ghi chú mới (`n ten-bai`)
function n {
    param([string]$NoteName)
    $activeDir = Get-ActiveStudyFolder
    $notesDir = Join-Path $activeDir "notes"
    if (-not (Test-Path $notesDir)) {
        New-Item -ItemType Directory -Path $notesDir -Force | Out-Null
    }

    if ($NoteName) {
        if (-not [System.IO.Path]::HasExtension($NoteName)) {
            $NoteName = "$NoteName.md"
        }
        $target = Join-Path $notesDir $NoteName
        if (-not (Test-Path $target)) {
            $title = [System.IO.Path]::GetFileNameWithoutExtension($target)
            $content = @"
# 📓 Ghi chú: $title
> 📅 Ngày ghi: $(Get-Date -Format "yyyy-MM-dd")

## 1. Khái niệm chính
- 

## 2. Cú pháp / Câu lệnh cần nhớ
- 

## 3. Lưu ý quan trọng
- 
"@
            [System.IO.File]::WriteAllText($target, $content, (New-Object System.Text.UTF8Encoding($false)))
        }
        Open-InMicro $target
        return
    }

    # Nếu chỉ gõ `n` -> Liệt kê toàn bộ file ghi chú trong các thư mục `notes/`
    Push-Location $Global:StudyRoot
    try {
        $noteFiles = rg --files -g "**/notes/*.md" -g "!.git/*"
        if (-not $noteFiles) {
            Write-Host "Chưa có bài ghi chú nào trong notes/. Hãy gõ: n ten-bai-hoc" -ForegroundColor Yellow
            return
        }
        $selected = $noteFiles | fzf --height=85% --layout=reverse --border `
            --prompt="📓 Chọn bài Ghi chú (notes/) > " `
            --header="Enter: Mở ghi chú bằng Micro | ESC: Thoát | Tạo mới: gõ 'n tên-bài'" `
            --preview="bat --color=always --style=numbers --line-range=:200 {}" `
            --preview-window="right:60%:wrap"
        if ($selected) {
            Open-InMicro (Join-Path $Global:StudyRoot $selected)
        }
    } finally {
        Pop-Location
    }
}
Set-Alias -Name note -Value n -Scope Global

# Lệnh `nr`: Đọc bài ghi chú trong `notes/` trình bày đẹp như sách bằng Glow
function nr {
    Push-Location $Global:StudyRoot
    try {
        $mdFiles = rg --files -g "**/notes/*.md" -g "README.md" -g "!.git/*"
        $selected = $mdFiles | fzf --height=85% --layout=reverse --border `
            --prompt="📖 Chọn bài Ghi chú để đọc (Glow) > " `
            --preview="bat --color=always --style=plain {}" `
            --preview-window="right:60%:wrap"
        if ($selected) {
            $style = Get-SystemThemeMode
            glow -s $style -p (Join-Path $Global:StudyRoot $selected)
        }
    } finally {
        Pop-Location
    }
}

# =====================================================================
# LUỒNG 2: CODE BÀI TẬP THỰC HÀNH (Thư mục `exercises/`)
# =====================================================================

# Lệnh `bt` (Bài tập): Chọn mở file code trong `exercises/` HOẶC tạo bài tập mới (`bt ex03.bat`, `bt bai1.py`)
function bt {
    param([string]$FileName)
    $activeDir = Get-ActiveStudyFolder
    $exDir = Join-Path $activeDir "exercises"
    if (-not (Test-Path $exDir)) {
        New-Item -ItemType Directory -Path $exDir -Force | Out-Null
    }

    if ($FileName) {
        # Nếu quên gõ đuôi file -> tự động gợi ý theo khóa học hiện tại
        if (-not [System.IO.Path]::HasExtension($FileName)) {
            if ($activeDir -match "batch|cmd") {
                $FileName = "$FileName.bat"
            } else {
                $FileName = "$FileName.py"
            }
        }
        $target = Join-Path $exDir $FileName
        if (-not (Test-Path $target)) {
            $ext = [System.IO.Path]::GetExtension($target).ToLower()
            $nameOnly = [System.IO.Path]::GetFileName($target)
            if ($ext -in @(".bat", ".cmd")) {
                $tpl = "@echo off`r`nchcp 65001 >nul`r`nREM Bài tập: $nameOnly (Bấm F5 để chạy thử)`r`n`r`necho Xin chào từ bài tập $nameOnly!`r`n"
            } elseif ($ext -eq ".py") {
                $tpl = "# Bài tập: $nameOnly (Bấm F5 để chạy thử)`r`n`r`nprint('Xin chào từ bài tập $nameOnly!')`r`n"
            } elseif ($ext -eq ".js") {
                $tpl = "// Bài tập JavaScript: $nameOnly (Bấm F5 để chạy thử bằng Node.js)`r`n`r`nconsole.log('Xin chào từ bài tập $nameOnly!');`r`n"
            } elseif ($ext -in @(".html", ".htm")) {
                $tpl = @"
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bài tập Web: $nameOnly</title>
    <style>
        body {
            font-family: system-ui, sans-serif;
            max-width: 680px;
            margin: 40px auto;
            padding: 20px;
            line-height: 1.6;
            background: #f6f4f0;
            color: #3d3a36;
        }
        button {
            padding: 8px 16px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <h1>🌐 Xin chào từ $nameOnly!</h1>
    <p>Sửa file này trong <b>Micro</b>, bấm <b>Ctrl+S</b> để lưu, hoặc bấm <b>F5</b> để mở trên trình duyệt.</p>
    <button onclick="chao()">Bấm thử vào tôi</button>
    <p id="ket-qua"></p>

    <script>
        function chao() {
            document.getElementById("ket-qua").textContent = "✅ JavaScript hoạt động tốt! Giờ hiện tại: " + new Date().toLocaleTimeString();
        }
    </script>
</body>
</html>
"@
            } else {
                $tpl = ""
            }
            [System.IO.File]::WriteAllText($target, $tpl, (New-Object System.Text.UTF8Encoding($false)))
        }
        Open-InMicro $target
        return
    }

    # Nếu chỉ gõ `bt` -> Liệt kê toàn bộ file code bài tập trong `exercises/`
    Push-Location $Global:StudyRoot
    try {
        $exFiles = rg --files -g "**/exercises/*" -g "!.git/*"
        if (-not $exFiles) {
            Write-Host "Chưa có bài tập nào trong exercises/. Hãy gõ: bt ex01.bat hoặc bt ex01.py" -ForegroundColor Yellow
            return
        }
        $selected = $exFiles | fzf --height=85% --layout=reverse --border `
            --prompt="💻 Chọn Bài tập Code (exercises/) > " `
            --header="Enter: Mở Code bằng Micro (Bấm F5 để chạy) | Tạo mới: gõ 'bt tên-file'" `
            --preview="bat --color=always --style=numbers --line-range=:200 {}" `
            --preview-window="right:60%:wrap"
        if ($selected) {
            Open-InMicro (Join-Path $Global:StudyRoot $selected)
        }
    } finally {
        Pop-Location
    }
}
Set-Alias -Name nc -Value bt -Scope Global
Set-Alias -Name hoc -Value bt -Scope Global

# Lệnh `btw` (Bài tập Web): Tạo & mở cùng lúc bộ 3 file .html + .css + .js đã nối sẵn với nhau
function btw {
    param([string]$BaseName = "web01")
    $BaseName = [System.IO.Path]::GetFileNameWithoutExtension($BaseName)
    $activeDir = Get-ActiveStudyFolder
    $exDir = Join-Path $activeDir "exercises"
    if (-not (Test-Path $exDir)) {
        New-Item -ItemType Directory -Path $exDir -Force | Out-Null
    }

    $htmlPath = Join-Path $exDir "$BaseName.html"
    $cssPath  = Join-Path $exDir "$BaseName.css"
    $jsPath   = Join-Path $exDir "$BaseName.js"

    if (-not (Test-Path $htmlPath)) {
        $htmlContent = @"
<!DOCTYPE html>
<html lang="vi">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bài tập Web: $BaseName</title>
    <link rel="stylesheet" href="$BaseName.css">
</head>
<body>
    <div class="card">
        <h1>🌐 Dự án Web: $BaseName</h1>
        <p>Bấm <b>F3</b> để chuyển nhanh sang sửa <code>$BaseName.css</code> hoặc <code>$BaseName.js</code>!</p>
        <p>Bấm <b>F7</b> để chia đôi màn hình vừa nhìn HTML vừa sửa CSS.</p>
        <p>Bấm <b>F5</b> để mở Live Server tự động tải lại khi lưu (Ctrl+S).</p>
        <button id="nut-bam" onclick="doiTrangThai()">Bấm thử JS</button>
        <p id="thong-bao"></p>
    </div>
    <script src="$BaseName.js"></script>
</body>
</html>
"@
        [System.IO.File]::WriteAllText($htmlPath, $htmlContent, (New-Object System.Text.UTF8Encoding($false)))
    }

    if (-not (Test-Path $cssPath)) {
        $cssContent = @"
/* File giao diện: $BaseName.css (Bấm F3 để chuyển sang $BaseName.js hoặc quay lại .html) */
body {
    font-family: system-ui, sans-serif;
    background: #F6F4F0;
    color: #3D3A36;
    max-width: 640px;
    margin: 40px auto;
    padding: 0 20px;
    line-height: 1.6;
}

.card {
    background: #EDE8E1;
    border: 1px solid #DED6CE;
    border-radius: 12px;
    padding: 24px;
}

h1 {
    color: #9E525E;
    margin-top: 0;
}

button {
    background: #9E525E;
    color: white;
    border: none;
    padding: 10px 18px;
    border-radius: 8px;
    cursor: pointer;
    font-weight: 600;
}
"@
        [System.IO.File]::WriteAllText($cssPath, $cssContent, (New-Object System.Text.UTF8Encoding($false)))
    }

    if (-not (Test-Path $jsPath)) {
        $jsContent = @"
// File xử lý tương tác: $BaseName.js (Bấm F3 để quay về $BaseName.html)
let soLanBam = 0;

function doiTrangThai() {
    soLanBam++;
    const p = document.getElementById("thong-bao");
    p.textContent = "✅ Bạn đã bấm nút " + soLanBam + " lần! (Được xử lý từ file $BaseName.js)";
}
"@
        [System.IO.File]::WriteAllText($jsPath, $jsContent, (New-Object System.Text.UTF8Encoding($false)))
    }

    Set-LastStudyFile $htmlPath
    Push-Location $Global:StudyRoot
    try {
        nvim "$htmlPath" "$cssPath" "$jsPath"
    } finally {
        Pop-Location
    }
}

# Lệnh `xoa` (hoặc `rmf`): Chọn và xóa file Note hoặc Bài tập an toàn
function xoa {
    param([string]$TargetName)
    $activeDir = Get-ActiveStudyFolder
    if ($TargetName) {
        $candidates = @(
            $TargetName,
            (Join-Path (Join-Path $activeDir "notes") $TargetName),
            (Join-Path (Join-Path $activeDir "notes") "$TargetName.md"),
            (Join-Path (Join-Path $activeDir "exercises") $TargetName)
        )
        foreach ($c in $candidates) {
            if (Test-Path $c -PathType Leaf) {
                $ans = Read-Host "⚠️ Bạn có chắc muốn xóa '$c'? (gõ y để xóa)"
                if ($ans -eq "y") {
                    Remove-Item $c -Force
                    Write-Host "🗑️ Đã xóa: $c" -ForegroundColor Green
                }
                return
            }
        }
        Write-Host "Không tìm thấy file '$TargetName'. Đang mở bảng chọn xóa..." -ForegroundColor Yellow
    }

    Push-Location $Global:StudyRoot
    try {
        $files = rg --files -g "**/notes/*" -g "**/exercises/*" -g "!.git/*"
        if (-not $files) {
            Write-Host "Không có file nào trong notes/ hoặc exercises/ để xóa." -ForegroundColor Yellow
            return
        }
        $selected = $files | fzf -m --height=85% --layout=reverse --border `
            --prompt="🗑️ Chọn file muốn XÓA (Tab: chọn nhiều | Enter: xác nhận) > " `
            --header="Tab: Đánh dấu chọn nhiều file | Enter: Xóa | ESC: Hủy" `
            --preview="bat --color=always --style=numbers --line-range=:100 {}" `
            --preview-window="right:60%:wrap"
        if ($selected) {
            Write-Host "`nCác file bạn đã chọn để xóa:" -ForegroundColor Yellow
            foreach ($s in $selected) { Write-Host "  - $s" -ForegroundColor Red }
            $confirm = Read-Host "`nXác nhận xóa vĩnh viễn các file trên? (gõ y để đồng ý)"
            if ($confirm -eq "y") {
                foreach ($s in $selected) {
                    $full = Join-Path $Global:StudyRoot $s
                    if (Test-Path $full) {
                        Remove-Item $full -Force
                        Write-Host "🗑️ Đã xóa: $s" -ForegroundColor Green
                    }
                }
            } else {
                Write-Host "Đã hủy thao tác xóa." -ForegroundColor Cyan
            }
        }
    } finally {
        Pop-Location
    }
}
Set-Alias -Name rmf -Value xoa -Scope Global

# Lệnh `run`: Chạy file Code bài tập vừa mở gần nhất (hoặc truyền tên file)
function run {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$ArgsList
    )
    if ($ArgsList -and $ArgsList.Count -gt 0) {
        $candidate = $ArgsList[0]
        if (-not (Test-Path $candidate)) {
            $inEx = Join-Path (Join-Path (Get-ActiveStudyFolder) "exercises") $candidate
            if (Test-Path $inEx) {
                $ArgsList[0] = $inEx
            }
        }
    }
    python "$Global:RunCodeScript" @ArgsList
}

# Lệnh `play`: Bảng nháp thử code từng dòng trực tiếp
function play {
    param([string]$Lang = "py")
    Write-Host "🎮 Đang mở bảng nháp code ($Lang). Gõ exit() hoặc bấm Ctrl+Z rồi Enter để thoát." -ForegroundColor Cyan
    if ($Lang -in @("js", "node")) {
        node
    } elseif ($Lang -in @("bat", "cmd")) {
        cmd.exe
    } else {
        python
    }
}

# Lệnh `web`: Bật Live Server tự động tải lại trang (giống VS Code Live Server)
function web {
    param([string]$HtmlFile)
    $exDir = Join-Path (Get-ActiveStudyFolder) "exercises"
    if ($HtmlFile) {
        $target = if (Test-Path $HtmlFile) { $HtmlFile } else { Join-Path $exDir $HtmlFile }
        if (Test-Path $target) {
            python "$Global:RunCodeScript" "$target"
            return
        }
    }
    $firstHtml = Get-ChildItem -Path $exDir -Filter "*.html" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($firstHtml) {
        python "$Global:RunCodeScript" "$($firstHtml.FullName)"
    } else {
        Write-Host "Chưa có file .html trong exercises/. Hãy gõ: bt web01.html" -ForegroundColor Yellow
    }
}

# =====================================================================
# LUỒNG 3: TÌM KIẾM, QUẢN LÝ KHÓA HỌC & ĐỒNG BỘ GITHUB
# =====================================================================

# Lệnh `nf`: Tìm tất cả file (cả Note lẫn Bài tập)
function nf {
    Push-Location $Global:StudyRoot
    try {
        $files = rg --files --hidden -g "!.git/*" -g "!.github/*" -g "!.last_study_file" -g "!.last_vibe_project"
        $selected = $files | fzf --height=85% --layout=reverse --border `
            --prompt="🔍 Tìm mọi file (Note + Code) > " `
            --header="Enter: Mở bằng Micro | ESC: Thoát" `
            --preview="bat --color=always --style=numbers --line-range=:200 {}" `
            --preview-window="right:60%:wrap"
        if ($selected) {
            Open-InMicro (Join-Path $Global:StudyRoot $selected)
        }
    } finally {
        Pop-Location
    }
}

# Lệnh `ns`: Tìm chữ bên trong mọi bài ghi chú & bài tập
function ns {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Query
    )
    $q = if ($Query) { ($Query -join " ") } else { "." }
    Push-Location $Global:StudyRoot
    try {
        $results = rg --line-number --no-heading --color=always --smart-case -g "!.git/*" -g "!.last_study_file" -g "!.last_vibe_project" "$q"
        if (-not $results) {
            Write-Host "Không tìm thấy nội dung khớp với: $q" -ForegroundColor Yellow
            return
        }
        $picked = $results | fzf --ansi --height=85% --layout=reverse --border `
            --prompt="🔎 Tìm nội dung > " `
            --header="Enter: Mở đúng dòng trong Micro | ESC: Thoát" `
            --delimiter=":" `
            --preview="bat --color=always --style=numbers --highlight-line {2} {1}" `
            --preview-window="right:60%:wrap:+{2}-10"
        if ($picked) {
            $parts = $picked -split ":"
            $fileRel = $parts[0]
            $lineNo = 0
            if ($parts.Count -ge 2) { [void][int]::TryParse($parts[1], [ref]$lineNo) }
            Open-InMicro (Join-Path $Global:StudyRoot $fileRel) $lineNo
        }
    } finally {
        Pop-Location
    }
}

# Lệnh `nn`: Menu Thêm khóa học mới (tự tạo notes/ + exercises/) hoặc Đổi khóa đang học
function nn {
    Write-Host "`n================ 🎓 QUẢN LÝ KHÓA HỌC & BÀI HỌC ================" -ForegroundColor Cyan
    Write-Host "  [1] 📓 Tạo bài Ghi chú lý thuyết mới (vào thư mục notes/)"
    Write-Host "  [2] 💻 Tạo file Code bài tập mới (vào thư mục exercises/)"
    Write-Host "  [3] 📚 Thêm Sách (Book) hoặc Khóa học (Course) mới vào năm 2026"
    Write-Host "  [4] 🔄 Đổi khóa đang học / Đổi trạng thái (🟥 / 🟧 / 🟨 / 🟩)"
    Write-Host "  [0] Thoát"
    $choice = Read-Host "`nChọn số (1-4)"

    if ($choice -eq "1") {
        $name = Read-Host "Nhập tên bài ghi chú (vd: 02-vong-lap-for)"
        if ($name) { n $name }
    } elseif ($choice -eq "2") {
        $name = Read-Host "Nhập tên file bài tập (vd: ex03-loop.bat hoặc ex03.py)"
        if ($name) { bt $name }
    } elseif ($choice -eq "3") {
        $typeChoice = Read-Host "Chọn loại: [1] Sách (books)  hoặc  [2] Khóa học (courses)"
        $category = if ($typeChoice -eq "1") { "books" } else { "courses" }
        $title = Read-Host "Nhập tên đầy đủ (vd: Learn Python)"
        if (-not $title) { return }
        $slug = ($title.ToLower() -replace "[^a-z0-9]+", "-").Trim("-")
        $folder = Join-Path $Global:StudyRoot "2026\$category\$slug"
        New-Item -ItemType Directory -Path (Join-Path $folder "notes") -Force | Out-Null
        New-Item -ItemType Directory -Path (Join-Path $folder "exercises") -Force | Out-Null
        $studyJson = @{
            title  = $title
            status = "studying"
        } | ConvertTo-Json
        [System.IO.File]::WriteAllText((Join-Path $folder "study.json"), $studyJson, (New-Object System.Text.UTF8Encoding($false)))
        python "$Global:GenReadmeScript"
        Write-Host "✅ Đã tạo '$title' kèm 2 thư mục notes/ và exercises/, và cập nhật README.md!" -ForegroundColor Green
    } elseif ($choice -eq "4") {
        $studyFiles = Get-ChildItem -Path (Join-Path $Global:StudyRoot "2026") -Filter "study.json" -Recurse
        if (-not $studyFiles) { return }
        Write-Host "`nDanh sách các Sách / Khóa học hiện có:" -ForegroundColor Yellow
        for ($i = 0; $i -lt $studyFiles.Count; $i++) {
            $data = Get-Content $studyFiles[$i].FullName -Raw -Encoding UTF8 | ConvertFrom-Json
            Write-Host "  [$($i+1)] $($data.title) (Hiện tại: $($data.status))"
        }
        $idxStr = Read-Host "`nChọn số thứ tự khóa học muốn đổi"
        $idx = 0
        if ([int]::TryParse($idxStr, [ref]$idx) -and $idx -ge 1 -and $idx -le $studyFiles.Count) {
            $selectedFile = $studyFiles[$idx - 1]
            $data = Get-Content $selectedFile.FullName -Raw -Encoding UTF8 | ConvertFrom-Json
            Write-Host "Chọn trạng thái mới: [1] not_started (🟥) | [2] ready (🟧) | [3] studying (🟨) | [4] completed (🟩)"
            $stChoice = Read-Host "Chọn (1-4)"
            $stMap = @{ "1" = "not_started"; "2" = "ready"; "3" = "studying"; "4" = "completed" }
            if ($stMap.ContainsKey($stChoice)) {
                $data.status = $stMap[$stChoice]
                $jsonOut = $data | ConvertTo-Json
                [System.IO.File]::WriteAllText($selectedFile.FullName, $jsonOut, (New-Object System.Text.UTF8Encoding($false)))
                python "$Global:GenReadmeScript"
                Write-Host "✅ Đã cập nhật '$($data.title)' -> $($data.status) và làm mới README.md!" -ForegroundColor Green
            }
        }
    }
}

# Lệnh `ide`: Mở Neovim Terminal IDE ngay trong cửa sổ Terminal hiện tại
function ide {
    param([string]$TargetFile)
    Push-Location $Global:StudyRoot
    try {
        if ($TargetFile -and (Test-Path $TargetFile)) {
            nvim "$TargetFile"
        } else {
            $last = Get-LastStudyFile
            if ($last -and (Test-Path $last)) {
                nvim "$last"
            } else {
                nvim .
            }
        }
    } finally {
        Pop-Location
    }
}

# Lệnh `ai`: Hỏi Trợ lý AI trực tiếp từ Terminal (hoặc mở khung chat AI)
function ai {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Prompt
    )
    $last = Get-LastStudyFile
    if ($Prompt -and $Prompt.Count -gt 0) {
        $q = ($Prompt -join " ")
        if ($last -and (Test-Path $last)) {
            python "$Global:AiHelperScript" "$last" "$q"
        } else {
            python "$Global:AiHelperScript" "$q"
        }
    } else {
        if ($last -and (Test-Path $last)) {
            python "$Global:AiHelperScript" "$last"
        } else {
            python "$Global:AiHelperScript"
        }
    }
}

# Lệnh `sync`: Tự động cập nhật README.md, đồng bộ sang Obsidian và đẩy lên GitHub
function sync {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$Message
    )
    python "$Global:LearnScript" push @Message
}

# =====================================================================
# LUỒNG 4: VIBE CODING (`vibe`), OBSIDIAN (`ob`, `gn`, `day`) & BLOG (`blog`)
# =====================================================================

# Đảm bảo lệnh `code` luôn là VS Code chuẩn (xóa function `code` cũ nếu có trong phiên)
if (Test-Path Function:\global:code) {
    Remove-Item Function:\global:code -Force -ErrorAction SilentlyContinue
}

function Get-VSCodeCommand {
    $cand = Join-Path $env:LOCALAPPDATA "Programs\Microsoft VS Code\bin\code.cmd"
    if (Test-Path -LiteralPath $cand) { return $cand }
    $cmd = Get-Command code -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($cmd) { return $cmd.Source }
    return $null
}

function Set-LastVibeProject([string]$DirPath) {
    if ($DirPath -and (Test-Path -LiteralPath $DirPath -PathType Container)) {
        $resolved = (Resolve-Path -LiteralPath $DirPath).Path
        [System.IO.File]::WriteAllText($Global:LastVibeProjectCache, $resolved, (New-Object System.Text.UTF8Encoding($false)))
    }
}

function Get-LastVibeProject {
    if (Test-Path -LiteralPath $Global:LastVibeProjectCache) {
        $p = (Get-Content -LiteralPath $Global:LastVibeProjectCache -Raw -Encoding UTF8).Trim()
        if ($p -and (Test-Path -LiteralPath $p -PathType Container)) {
            return $p
        }
    }
    return $null
}

function Start-VibeWorkspace {
    param(
        [Parameter(Mandatory)][string]$TargetDir,
        [switch]$NoVSCode,
        [switch]$VSCodeOnly
    )
    if (-not (Test-Path -LiteralPath $TargetDir -PathType Container)) {
        New-Item -ItemType Directory -Path $TargetDir -Force | Out-Null
        Write-Host "✨ Đã tạo thư mục dự án mới: $TargetDir" -ForegroundColor Green
    }

    $fullDir = (Resolve-Path -LiteralPath $TargetDir).Path
    $projName = Split-Path $fullDir -Leaf
    Set-LastVibeProject $fullDir
    Set-Location -LiteralPath $fullDir

    if (-not $NoVSCode) {
        $vsCmd = Get-VSCodeCommand
        if ($vsCmd) {
            & $vsCmd "$fullDir"
        }
    }

    if ($VSCodeOnly) {
        Write-Host "✅ Đã mở VS Code cho dự án: $projName ($fullDir)" -ForegroundColor Green
        return
    }

    Write-Host ""
    Write-Host "╭──────────────────────────────────────────────────────────────────────────╮" -ForegroundColor Cyan
    Write-Host "│  ⚡ VIBE CODING: TERMINAL (AI CLI) + VS CODE (ĐỌC & TINH CHỈNH CODE)     │" -ForegroundColor Cyan
    Write-Host "╰──────────────────────────────────────────────────────────────────────────╯" -ForegroundColor Cyan
    Write-Host "  📂 Dự án đang mở : " -NoNewline; Write-Host $fullDir -ForegroundColor Yellow
    Write-Host "  🖥️  VS Code       : " -NoNewline; Write-Host "Đã mở song song để đọc code & sửa tay nhanh" -ForegroundColor Green
    Write-Host "  🤖 Terminal      : " -NoNewline; Write-Host "Đang khởi chạy AI CLI (agy) tại dự án..." -ForegroundColor Magenta
    Write-Host ""

    $agyCmd = Get-Command agy -ErrorAction SilentlyContinue
    if ($agyCmd) {
        & $agyCmd.Source
    } else {
        Write-Host "⚠️ Không tìm thấy lệnh agy trong PATH." -ForegroundColor Yellow
    }
}

function Select-VibeSubfolder([string]$ParentDir) {
    $parentName = Split-Path $ParentDir -Leaf
    $optOpenHere = "📂 [Mở trực tiếp thư mục này: $parentName]"
    $optCreateSub = "✨ [+ Tạo thư mục con mới bên trong $parentName...]"

    $subDirs = Get-ChildItem -LiteralPath $ParentDir -Directory -ErrorAction SilentlyContinue |
        Where-Object { $_.Name -notmatch '^\.|^node_modules$|^__pycache__$|^venv$|^dist$|^build$' } |
        Sort-Object LastWriteTime -Descending |
        Select-Object -ExpandProperty Name

    $menuItems = @($optOpenHere, $optCreateSub)
    if ($subDirs) { $menuItems += $subDirs }

    Push-Location -LiteralPath $ParentDir
    try {
        $fzfOut = $menuItems | fzf --print-query --height=85% --layout=reverse --border `
            --prompt="📂 Thư mục con trong '$parentName' > " `
            --header="Enter: Mở thư mục | Hoặc gõ tên thư mục con mới rồi bấm Enter để tạo ngay" `
            --preview="if exist `"{}`" (dir /b `"{}`") else (echo Chon de mo hoac tao thu muc con moi trong $parentName)" `
            --preview-window="right:55%:wrap"
    } finally {
        Pop-Location
    }

    if (-not $fzfOut) { return $null }
    $lines = @($fzfOut)
    $query = if ($lines.Count -ge 1) { $lines[0].Trim() } else { "" }
    $selected = if ($lines.Count -ge 2) { $lines[1].Trim() } else { "" }

    if ($selected -eq $optOpenHere) { return $ParentDir }
    if ($selected -eq $optCreateSub) {
        $newSub = if ($query) { $query } else { Read-Host "✨ Nhập tên thư mục con mới trong '$parentName'" }
        if (-not $newSub) { return $null }
        return (Join-Path $ParentDir $newSub.Trim())
    }
    if ($selected) { return (Join-Path $ParentDir $selected) }
    if ($query) { return (Join-Path $ParentDir $query) }
    return $null
}

# Lệnh `vibe` (hoặc `vc`): Mở dự án trong D:\Brain2nd\Code bằng VS Code + chạy AI CLI (agy) ở Terminal
function global:vibe {
    param(
        [Parameter(Position = 0)][string]$ProjectName,
        [Parameter(Position = 1)][string]$SubFolder,
        [switch]$NoVSCode,
        [switch]$VSCodeOnly
    )

    if (-not (Test-Path -LiteralPath $Global:VibeCodingRoot -PathType Container)) {
        New-Item -ItemType Directory -Path $Global:VibeCodingRoot -Force | Out-Null
    }

    if ($ProjectName) {
        if ($ProjectName -eq ".") {
            $target = (Get-Location).Path
            if ($SubFolder) { $target = Join-Path $target $SubFolder }
            Start-VibeWorkspace -TargetDir $target -NoVSCode:$NoVSCode -VSCodeOnly:$VSCodeOnly
            return
        }
        if ($ProjectName -in @("brain", "vault", "obsidian")) {
            Start-VibeWorkspace -TargetDir $Global:BrainRoot -NoVSCode:$NoVSCode -VSCodeOnly:$VSCodeOnly
            return
        }

        if (Test-Path -LiteralPath $ProjectName -PathType Container) {
            $target = (Resolve-Path -LiteralPath $ProjectName).Path
            if ($SubFolder) { $target = Join-Path $target $SubFolder }
            Start-VibeWorkspace -TargetDir $target -NoVSCode:$NoVSCode -VSCodeOnly:$VSCodeOnly
            return
        }

        $candidateInRoot = Join-Path $Global:VibeCodingRoot $ProjectName
        if ($SubFolder) {
            $candidateInRoot = Join-Path $candidateInRoot $SubFolder
            Start-VibeWorkspace -TargetDir $candidateInRoot -NoVSCode:$NoVSCode -VSCodeOnly:$VSCodeOnly
            return
        }

        if (Test-Path -LiteralPath $candidateInRoot -PathType Container) {
            Start-VibeWorkspace -TargetDir $candidateInRoot -NoVSCode:$NoVSCode -VSCodeOnly:$VSCodeOnly
            return
        }

        $level2Match = Get-ChildItem -LiteralPath $Global:VibeCodingRoot -Directory -ErrorAction SilentlyContinue |
            ForEach-Object {
                $cand = Join-Path $_.FullName $ProjectName
                if (Test-Path -LiteralPath $cand -PathType Container) { $cand }
            } | Select-Object -First 1

        if ($level2Match) {
            Start-VibeWorkspace -TargetDir $level2Match -NoVSCode:$NoVSCode -VSCodeOnly:$VSCodeOnly
            return
        }

        Start-VibeWorkspace -TargetDir $candidateInRoot -NoVSCode:$NoVSCode -VSCodeOnly:$VSCodeOnly
        return
    }

    $optCreateNew = "✨ [+ Tạo dự án mới trong D:\Brain2nd\Code...]"
    $skipPattern = '^\.|^node_modules$|^__pycache__$|^venv$|^dist$|^build$|^output$|^assets$|^static$|^archetypes$|^i18n$|^layouts$'

    $level1Dirs = Get-ChildItem -LiteralPath $Global:VibeCodingRoot -Directory -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending

    $items = @($optCreateNew)
    foreach ($d1 in $level1Dirs) { $items += $d1.Name }
    foreach ($d1 in $level1Dirs) {
        $subDirs = Get-ChildItem -LiteralPath $d1.FullName -Directory -ErrorAction SilentlyContinue |
            Where-Object { $_.Name -notmatch $skipPattern } |
            Sort-Object LastWriteTime -Descending
        foreach ($d2 in $subDirs) {
            $items += "$($d1.Name)\$($d2.Name)"
        }
    }

    Push-Location -LiteralPath $Global:VibeCodingRoot
    try {
        $fzfOut = $items | fzf --print-query --expect=tab,ctrl-n --height=85% --layout=reverse --border `
            --prompt="⚡ Vibe Code (D:\Brain2nd\Code) > " `
            --header="Enter: Mở VS Code + AI CLI (agy) | Tab: Chọn thư mục con | Ctrl+N: Tạo dự án mới" `
            --preview="if exist `"{}\README.md`" (bat --color=always --style=plain --line-range=:35 `"{}\README.md`" & echo. & echo --- Thu muc / File ben trong --- & dir /b `"{}`") else if exist `"{}`" (dir /b `"{}`") else (echo Bam Enter hoac Ctrl+N de tao du an Vibe Code moi!)" `
            --preview-window="right:58%:wrap"
    } finally {
        Pop-Location
    }

    if (-not $fzfOut) { return }
    $lines = @($fzfOut)
    $query    = if ($lines.Count -ge 1) { $lines[0].Trim() } else { "" }
    $key      = if ($lines.Count -ge 2) { $lines[1].Trim() } else { "" }
    $selected = if ($lines.Count -ge 3) { $lines[2].Trim() } else { "" }

    $targetDir = $null
    if ($key -eq "ctrl-n" -or $selected -eq $optCreateNew) {
        $defaultHint = if ($query) { $query } else { "" }
        if ($defaultHint) {
            $ans = Read-Host "✨ Nhập tên dự án mới (Enter để tạo '$defaultHint', hoặc nhập tên khác)"
            $newName = if ($ans.Trim()) { $ans.Trim() } else { $defaultHint }
        } else {
            $newName = Read-Host "✨ Nhập tên dự án mới trong D:\Brain2nd\Code"
        }
        if (-not $newName) { return }
        $targetDir = Join-Path $Global:VibeCodingRoot $newName.Trim()
    } elseif ($key -eq "tab") {
        $baseRel = if ($selected -and $selected -ne $optCreateNew) { $selected } elseif ($query) { $query } else { "" }
        if (-not $baseRel) { return }
        $baseFull = Join-Path $Global:VibeCodingRoot $baseRel
        if (-not (Test-Path -LiteralPath $baseFull -PathType Container)) {
            New-Item -ItemType Directory -Path $baseFull -Force | Out-Null
        }
        $targetDir = Select-VibeSubfolder $baseFull
    } elseif ($selected) {
        $targetDir = Join-Path $Global:VibeCodingRoot $selected
    } elseif ($query) {
        $targetDir = Join-Path $Global:VibeCodingRoot $query
    }

    if ($targetDir) {
        Start-VibeWorkspace -TargetDir $targetDir -NoVSCode:$NoVSCode -VSCodeOnly:$VSCodeOnly
    }
}
Set-Alias -Name vc -Value vibe -Scope Global

# Lệnh `ob` (hoặc `brain`): Mở nhanh Obsidian tại D:\Brain2nd (gõ `ob ai` để bật thêm AI CLI cùng hỗ trợ)
function global:ob {
    param([string]$Mode)
    Set-Location -LiteralPath $Global:BrainRoot
    Start-Process "obsidian://open?vault=Brain2nd"
    Write-Host "📓 Đã mở Obsidian Vault: D:\Brain2nd" -ForegroundColor Green
    if ($Mode -in @("ai", "agy", "vibe")) {
        $agyCmd = Get-Command agy -ErrorAction SilentlyContinue
        if ($agyCmd) {
            Write-Host "🤖 Đang bật AI CLI (agy) tại D:\Brain2nd để hỗ trợ ghi chú, tự học & lên kế hoạch..." -ForegroundColor Cyan
            & $agyCmd.Source
        }
    } elseif ($Mode -eq "code") {
        $vsCmd = Get-VSCodeCommand
        if ($vsCmd) { & $vsCmd $Global:BrainRoot }
    }
}
Set-Alias -Name brain -Value ob -Scope Global

# Lệnh `day`: Mở hoặc tạo nhanh Nhật ký hôm nay (D:\Brain2nd\Nhật ký\YYYY-MM-DD.md)
function global:day {
    $today = Get-Date -Format "yyyy-MM-dd"
    $dailyDir = Join-Path $Global:BrainRoot "Nhật ký"
    if (-not (Test-Path -LiteralPath $dailyDir)) {
        New-Item -ItemType Directory -Path $dailyDir -Force | Out-Null
    }
    $dailyFile = Join-Path $dailyDir "$today.md"
    if (-not (Test-Path -LiteralPath $dailyFile)) {
        $tplFile = Join-Path $Global:BrainRoot "Mẫu\Mẫu ghi chú hằng ngày.md"
        $tplContent = if (Test-Path -LiteralPath $tplFile) {
            Get-Content -LiteralPath $tplFile -Raw -Encoding UTF8
        } else {
            "---`r`ntags:`r`n  - hang-ngay`r`n  - ca-nhan`r`n---`r`n## Trọng tâm hôm nay`r`n- [ ] `r`n"
        }
        [System.IO.File]::WriteAllText($dailyFile, $tplContent, (New-Object System.Text.UTF8Encoding($false)))
        Write-Host "✨ Đã tạo Nhật ký hôm nay: $dailyFile" -ForegroundColor Green
    }
    $rel = [uri]::EscapeDataString("Nhật ký/$today.md")
    Start-Process "obsidian://open?vault=Brain2nd&file=$rel"
}

# Lệnh `gn`: Tìm mở hoặc tạo nhanh ghi chú trong D:\Brain2nd\Ghi chú (chuẩn Kepano)
function global:gn {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$NoteTitle
    )
    $notesDir = Join-Path $Global:BrainRoot "Ghi chú"
    if (-not (Test-Path -LiteralPath $notesDir)) {
        New-Item -ItemType Directory -Path $notesDir -Force | Out-Null
    }
    if ($NoteTitle -and $NoteTitle.Count -gt 0) {
        $titleStr = ($NoteTitle -join " ").Trim()
        $safeName = ($titleStr -replace '[<>:"/\\|?*]', '-').Trim()
        if (-not $safeName.EndsWith(".md")) { $safeName = "$safeName.md" }
        $target = Join-Path $notesDir $safeName
        if (-not (Test-Path -LiteralPath $target)) {
            $today = Get-Date -Format "yyyy-MM-dd"
            $content = @"
---
Danh mục: []
Chủ đề: []
Ngày tạo: $today
tags: []
---

"@
            [System.IO.File]::WriteAllText($target, $content, (New-Object System.Text.UTF8Encoding($false)))
            Write-Host "✨ Đã tạo ghi chú mới: $target" -ForegroundColor Green
        }
        $rel = [uri]::EscapeDataString("Ghi chú/$safeName")
        Start-Process "obsidian://open?vault=Brain2nd&file=$rel"
        return
    }

    Push-Location -LiteralPath $Global:BrainRoot
    try {
        $mdFiles = rg --files -g "Ghi chú/*.md" -g "Bài viết/*.md" -g "Tài liệu tham khảo/*.md" -g "Trích đoạn/*.md" -g "Nhật ký/*.md" -g "Danh mục/*.md"
        if (-not $mdFiles) {
            Write-Host "Chưa có ghi chú nào. Gõ: gn `"Tên ghi chú`" để tạo mới." -ForegroundColor Yellow
            return
        }
        $selected = $mdFiles | fzf --height=85% --layout=reverse --border `
            --prompt="📓 Tìm Ghi chú Obsidian (D:\Brain2nd) > " `
            --header="Enter: Mở trong Obsidian | ESC: Thoát | Tạo mới: gn `"Tên ghi chú`"" `
            --preview="bat --color=always --style=plain --line-range=:120 {}" `
            --preview-window="right:60%:wrap"
        if ($selected) {
            $rel = [uri]::EscapeDataString(($selected -replace '\\', '/'))
            Start-Process "obsidian://open?vault=Brain2nd&file=$rel"
        }
    } finally {
        Pop-Location
    }
}

# Lệnh `blog`: Điều khiển Blog Hugo (https://cmduyeen.github.io/) từ bất kỳ đâu trong Terminal
function global:blog {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$BlogArgs
    )
    python "$Global:BlogScript" @BlogArgs
}

# Lệnh `stat` (hoặc `me` / `track` / `kpi`): Bảng theo dõi Năng suất cá nhân trên Terminal (như github.com/cmduyeen)
function global:stat {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$StatArgs
    )
    python "$Global:TrackScript" @StatArgs
}
Set-Alias -Name stats -Value stat -Scope Global
Set-Alias -Name me -Value stat -Scope Global
Set-Alias -Name track -Value stat -Scope Global
Set-Alias -Name kpi -Value stat -Scope Global

# Lệnh `learn` (hoặc `study`): Quản lý kho tự học cmduyeen-self-study bằng VS Code & tự động đẩy lên GitHub
function global:learn {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$LearnArgs
    )
    python "$Global:LearnScript" @LearnArgs
}
Set-Alias -Name study -Value learn -Scope Global

# Lệnh `up` (hoặc `upload`): Đẩy nhanh toàn bộ Note + Bài tập Code lên GitHub (https://github.com/cmduyeen/self-study)
function global:up {
    param(
        [Parameter(ValueFromRemainingArguments = $true)]
        [string[]]$CommitMsg
    )
    python "$Global:LearnScript" push @CommitMsg
}
Set-Alias -Name upload -Value up -Scope Global

# Lệnh `b` (hoặc `nb`): Bảng điều khiển trung tâm tối giản
function global:b {
    $activeDir = Get-ActiveStudyFolder
    $activeName = Split-Path $activeDir -Leaf
    $lastVibe = Get-LastVibeProject
    $lastVibeName = if ($lastVibe) { Split-Path $lastVibe -Leaf } else { "(Chưa có)" }

    Write-Host ""
    Write-Host "╭──────────────────────────────────────────────────────────────────────────╮" -ForegroundColor Cyan
    Write-Host "│  🧠 BRAIN2ND CONTROL CENTER (TERMINAL + VS CODE + OBSIDIAN + BLOG)       │" -ForegroundColor Cyan
    Write-Host "╰──────────────────────────────────────────────────────────────────────────╯" -ForegroundColor Cyan
    Write-Host "  📍 Nguồn duy nhất    : " -NoNewline; Write-Host "D:\Brain2nd" -ForegroundColor Yellow
    Write-Host "  ⚡ Dự án Vibe gần nhất: " -NoNewline; Write-Host $lastVibeName -ForegroundColor Cyan
    Write-Host "  📚 Khóa đang tự học   : " -NoNewline; Write-Host $activeName -ForegroundColor Green
    Write-Host ""
    Write-Host "  0️⃣  THEO DÕI NĂNG SUẤT CÁ NHÂN (NHƯ GITHUB PROFILE cmduyeen):" -ForegroundColor Magenta
    Write-Host "    stat (hoặc me)     : Xem thống kê Repos, Bài Blog, Ghi chú Obsidian & Biểu đồ Commits"
    Write-Host "    stat --all / sync  : Xem đủ Repos (--all) / Cập nhật thẳng lên github.com/cmduyeen (sync)"
    Write-Host ""
    Write-Host "  1️⃣  VIBE CODE (TERMINAL AI CLI + VS CODE):" -ForegroundColor Magenta
    Write-Host "    vibe               : Chọn dự án trong D:\Brain2nd\Code -> Mở VS Code + chạy AI CLI (agy)"
    Write-Host "    vibe <tên-dự-án>   : Mở ngay dự án bằng VS Code kèm AI CLI tại Terminal"
    Write-Host "    code <đường-dẫn>   : Lệnh VS Code nguyên bản để mở nhanh file / thư mục bất kỳ"
    Write-Host ""
    Write-Host "  2️⃣  OBSIDIAN KEPANO VI (GHI CHÚ, LÊN KẾ HOẠCH & TỰ HỌC):" -ForegroundColor Magenta
    Write-Host "    ob                 : Mở Obsidian Vault (D:\Brain2nd)"
    Write-Host "    ob ai              : Mở Obsidian + bật AI CLI (agy) tại D:\Brain2nd để cùng lên kế hoạch / tự học"
    Write-Host "    day                : Mở / tạo ngay Nhật ký hôm nay (Nhật ký\YYYY-MM-DD.md)"
    Write-Host "    gn [tên-ghi-chú]   : Tìm mở nhanh ghi chú bằng fzf hoặc tạo mới trong Ghi chú\"
    Write-Host ""
    Write-Host "  3️⃣  BLOG CÁ NHÂN HUGO (https://cmduyeen.github.io/):" -ForegroundColor Magenta
    Write-Host "    blog new [tên-bài] : Tạo bài viết mới trong D:\Brain2nd\Bài viết gắn sẵn [[Bài viết]]"
    Write-Host "    blog edit [tên-bài]: Chọn & mở sửa bài viết trong Obsidian (thêm --code để mở bằng VS Code)"
    Write-Host "    blog publish       : Chọn bài viết -> Tự đóng gói ảnh & đẩy lên GitHub Pages (hỗ trợ cả blog pulish)"
    Write-Host "    blog del [tên-bài] : Chọn xóa bài nháp hoặc gỡ bài đã đăng khỏi Website GitHub Pages"
    Write-Host "    blog sort          : Tự động gom bài viết về Bài viết\, đồng bộ từ Web & chuẩn hóa thuộc tính"
    Write-Host "    blog preview / list: Xem trước tại http://127.0.0.1:1313 (preview) / Xem danh sách (list)"
    Write-Host ""
    Write-Host "  4️⃣  TỰ HỌC CODE VỚI VS CODE & GITHUB (https://github.com/cmduyeen/self-study):" -ForegroundColor Magenta
    Write-Host "    learn              : Mở bảng điều khiển Tự học (Enter = mở ngay khóa đang học trong VS Code)"
    Write-Host "    learn open / ai    : Mở thẳng khóa đang học trong VS Code (learn ai = kèm thêm AI CLI agy)"
    Write-Host "    learn note [tên]   : Tạo / mở bài Ghi chú lý thuyết (notes/) trong VS Code"
    Write-Host "    learn ex [tên]     : Tạo / mở file Bài tập Code (exercises/) trong VS Code"
    Write-Host "    learn push (hoặc up): Tự động tạo README mục lục & Upload toàn bộ lên GitHub + đồng bộ Obsidian"
    Write-Host "    learn set / new    : Đổi khóa đang học hoặc trạng thái (set) / Thêm Sách & Khóa học mới (new)"
    Write-Host ""
}
Set-Alias -Name nb -Value b -Scope Global
