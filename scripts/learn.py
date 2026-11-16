"""Hệ thống quản lý Tự học Code thông minh (VS Code + GitHub Auto-Sync + Obsidian)."""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import unicodedata

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, 'reconfigure'):
        stream.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
BRAIN_ROOT = Path(r'D:\Brain2nd')
OBSIDIAN_REF_DIR = BRAIN_ROOT / 'Tài liệu tham khảo'
GEN_README_SCRIPT = ROOT / 'scripts' / 'generate-readme.py'
LAST_FILE_CACHE = ROOT / '.last_study_file'

STATUS_MAP = {
    'not_started': ('🟥', 'Chưa bắt đầu'),
    'ready':       ('🟧', 'Sẵn sàng'),
    'studying':    ('🟨', 'Đang học'),
    'completed':   ('🟩', 'Hoàn thành'),
}

ACTION_ALIASES = {
    'open': 'open', 'code': 'open', 'vs': 'open', 'vscode': 'open', 'o': 'open',
    'ai': 'ai', 'vibe': 'ai', 'agy': 'ai',
    'note': 'note', 'n': 'note', 'notes': 'note',
    'ex': 'ex', 'bt': 'ex', 'exercise': 'ex', 'exercises': 'ex', 'code-ex': 'ex',
    'web': 'web', 'btw': 'web',
    'push': 'push', 'up': 'push', 'upload': 'push', 'sync': 'push', 'save': 'push', 'p': 'push',
    'new': 'new', 'add': 'new', 'create': 'new',
    'switch': 'switch', 'status': 'switch', 'set': 'switch', 'st': 'switch',
    'list': 'list', 'ls': 'list', 'l': 'list',
}


@dataclass
class StudyItem:
    year: str
    category: str          # 'books' hoặc 'courses'
    slug: str
    title: str
    status: str            # 'not_started', 'ready', 'studying', 'completed'
    folder: Path

    @property
    def badge(self) -> str:
        return STATUS_MAP.get(self.status, ('⬜', self.status))[0]

    @property
    def status_vi(self) -> str:
        return STATUS_MAP.get(self.status, ('⬜', self.status))[1]

    @property
    def category_vi(self) -> str:
        return 'Sách' if self.category == 'books' else 'Khóa học'

    @property
    def notes_dir(self) -> Path:
        return self.folder / 'notes'

    @property
    def exercises_dir(self) -> Path:
        return self.folder / 'exercises'

    def notes(self) -> list[Path]:
        if not self.notes_dir.is_dir():
            return []
        return sorted(p for p in self.notes_dir.glob('*.md') if p.is_file())

    def exercises(self) -> list[Path]:
        if not self.exercises_dir.is_dir():
            return []
        return sorted(p for p in self.exercises_dir.iterdir() if p.is_file())


def slugify(value: str) -> str:
    value = unicodedata.normalize('NFKD', value.lower().replace('đ', 'd'))
    value = value.encode('ascii', 'ignore').decode()
    value = re.sub(r'[^a-z0-9]+', '-', value).strip('-')
    return value or 'study-item'


def load_all_studies() -> list[StudyItem]:
    items: list[StudyItem] = []
    for meta_path in sorted(ROOT.glob('[0-9][0-9][0-9][0-9]/*/*/study.json')):
        try:
            data = json.loads(meta_path.read_text(encoding='utf-8'))
            folder = meta_path.parent
            category = folder.parent.name
            year = folder.parent.parent.name
            items.append(
                StudyItem(
                    year=year,
                    category=category,
                    slug=folder.name,
                    title=data.get('title', folder.name).strip(),
                    status=data.get('status', 'not_started').strip(),
                    folder=folder,
                )
            )
        except Exception:
            continue
    # Sắp xếp ưu tiên: studying (🟨) lên đầu -> ready (🟧) -> not_started (🟥) -> completed (🟩)
    order = {'studying': 0, 'ready': 1, 'not_started': 2, 'completed': 3}
    items.sort(key=lambda x: (order.get(x.status, 9), -int(x.year), x.title.lower()))
    return items


def get_active_study(items: list[StudyItem] | None = None) -> StudyItem:
    if items is None:
        items = load_all_studies()
    if not items:
        raise ValueError('Chưa có khóa học nào. Gõ `learn new` để tạo khóa học đầu tiên.')
    for it in items:
        if it.status == 'studying':
            return it
    return items[0]


def find_vscode_exe() -> str:
    for var in ('LOCALAPPDATA', 'ProgramFiles', 'ProgramFiles(x86)'):
        base = os.environ.get(var)
        if base:
            for rel in ('Programs/Microsoft VS Code/Code.exe', 'Microsoft VS Code/Code.exe', 'Programs/Microsoft VS Code/bin/code.cmd'):
                cand = Path(base) / rel
                if cand.is_file():
                    return str(cand)
    cmd = shutil.which('code') or shutil.which('Code.exe')
    if cmd:
        return cmd
    raise ValueError('Không tìm thấy VS Code. Hãy kiểm tra cài đặt VS Code.')


def open_in_vscode(folder: Path, *files_to_open: Path):
    exe = find_vscode_exe()
    args = [exe, str(folder)]
    for f in files_to_open:
        if f and f.is_file():
            args.append(str(f))
    subprocess.Popen(args)


def generate_course_readme(item: StudyItem):
    """Tạo file README.md bên trong từng khóa học/sách để hiển thị mục lục Notes & Exercises trên GitHub."""
    item.notes_dir.mkdir(parents=True, exist_ok=True)
    item.exercises_dir.mkdir(parents=True, exist_ok=True)
    notes = item.notes()
    exercises = item.exercises()

    lines = [
        f'# {item.badge} {item.title}',
        '',
        f'- **Phân loại:** {item.category_vi} (`{item.year}`)',
        f'- **Trạng thái:** {item.badge} {item.status_vi}',
        f'- **Thống kê:** `{len(notes)}` bài ghi chú lý thuyết · `{len(exercises)}` file bài tập thực hành',
        '',
        '## 📓 Ghi chú lý thuyết (`notes/`)',
        '',
    ]
    if notes:
        for n in notes:
            lines.append(f'- [{n.name}](notes/{n.name})')
    else:
        lines.append('*Chưa có ghi chú.*')

    lines.extend([
        '',
        '## 💻 Bài tập thực hành (`exercises/`)',
        '',
    ])
    if exercises:
        for ex in exercises:
            lines.append(f'- [{ex.name}](exercises/{ex.name})')
    else:
        lines.append('*Chưa có bài tập.*')

    lines.append('')
    readme_file = item.folder / 'README.md'
    readme_file.write_text('\n'.join(lines), encoding='utf-8', newline='\n')


def sync_to_obsidian_reference(items: list[StudyItem]):
    """Đồng bộ danh sách Sách & Khóa học sang D:\\Brain2nd\\Tài liệu tham khảo\\ của Obsidian."""
    OBSIDIAN_REF_DIR.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    for it in items:
        safe_title = re.sub(r'[<>:"/\\|?*]', '-', it.title).strip()
        obs_path = OBSIDIAN_REF_DIR / f'{safe_title}.md'
        cat_link = '[[Sách]]' if it.category == 'books' else '[[Khóa học]]'
        tag_type = 'sach' if it.category == 'books' else 'khoa-hoc'
        gh_url = f'https://github.com/cmduyeen/self-study/tree/main/{it.year}/{it.category}/{it.slug}'

        notes_links = '\n'.join(f'- `{n.name}`' for n in it.notes()) or '- *(Chưa có ghi chú)*'
        ex_links = '\n'.join(f'- `{e.name}`' for e in it.exercises()) or '- *(Chưa có bài tập)*'

        content = f"""---
Danh mục:
  - "{cat_link}"
Chủ đề:
  - Tự học Code
Nguồn: "{gh_url}"
Đường dẫn: "{it.folder.as_posix()}"
Trạng thái: {it.status_vi}
Năm: {it.year}
Ngày tạo: {today}
Lần gần nhất: {today}
tags:
  - {tag_type}
  - tu-hoc
---
# {it.badge} {it.title}

- **Thư mục Code & Note:** `{it.folder}`
- **GitHub:** [{gh_url}]({gh_url})
- **Mở nhanh ở Terminal:** `learn` (hoặc `learn open`)

## 📓 Danh sách Ghi chú (`notes/`)
{notes_links}

## 💻 Danh sách Bài tập (`exercises/`)
{ex_links}
"""
        obs_path.write_text(content, encoding='utf-8')


def update_all_readmes():
    items = load_all_studies()
    for it in items:
        generate_course_readme(it)
    subprocess.run([sys.executable, str(GEN_README_SCRIPT)], cwd=ROOT, check=True)
    sync_to_obsidian_reference(items)


def default_ext_for_study(item: StudyItem) -> str:
    combined = (item.slug + ' ' + item.title).lower()
    if any(k in combined for k in ('batch', 'cmd', 'dos')):
        return '.bat'
    if any(k in combined for k in ('js', 'javascript', 'node', 'react', 'frontend')):
        return '.js'
    if any(k in combined for k in ('html', 'css', 'web')):
        return '.html'
    if any(k in combined for k in ('powershell', 'ps1')):
        return '.ps1'
    return '.py'


def create_or_open_note(name: str | None = None, open_editor: bool = True) -> Path:
    active = get_active_study()
    active.notes_dir.mkdir(parents=True, exist_ok=True)
    existing = active.notes()

    if not name:
        print(f'\n📓 Danh sách Ghi chú trong [{active.title}]:')
        for idx, p in enumerate(existing, 1):
            print(f'  [{idx}] {p.name}')
        print(f'  [N] + Tạo bài ghi chú mới')
        ans = input('Chọn số để mở hoặc nhập tên bài mới (Enter để mở bài mới nhất): ').strip()
        if not ans and existing:
            target = existing[-1]
            if open_editor:
                open_in_vscode(active.folder, target)
            return target
        if ans.isdigit() and 1 <= int(ans) <= len(existing):
            target = existing[int(ans) - 1]
            if open_editor:
                open_in_vscode(active.folder, target)
            return target
        if ans.lower() == 'n' or not ans:
            name = input('Nhập tên bài ghi chú mới (vd: vong-lap-for): ').strip()
        else:
            name = ans

    if not name:
        raise ValueError('Cần nhập tên bài ghi chú.')

    clean_name = name.strip()
    if clean_name.endswith('.md'):
        clean_name = clean_name[:-3]
    slug_name = slugify(clean_name)

    # Nếu chưa có số thứ tự ở đầu (vd: 01-, 02-), tự động đánh số tiếp theo
    if not re.match(r'^\d{2}-', slug_name):
        next_num = len(existing) + 1
        file_name = f'{next_num:02d}-{slug_name}.md'
    else:
        file_name = f'{slug_name}.md'

    target = active.notes_dir / file_name
    if not target.exists():
        today = dt.date.today().isoformat()
        content = f"""# 📓 {clean_name}

> 📅 **Ngày học:** {today}  
> 📚 **Khóa học / Sách:** {active.title}

## 1. Khái niệm & Kiến thức cốt lõi
- 

## 2. Cú pháp & Ví dụ minh họa
```
```

## 3. Ghi nhớ thực tế
- 
"""
        target.write_text(content, encoding='utf-8')
        print(f'✨ Đã tạo bài ghi chú mới: {target.relative_to(ROOT)}')
    else:
        print(f'📓 Đang mở bài ghi chú: {target.relative_to(ROOT)}')

    update_all_readmes()
    if open_editor:
        open_in_vscode(active.folder, target)
    return target


def create_or_open_exercise(name: str | None = None, open_editor: bool = True) -> Path:
    active = get_active_study()
    active.exercises_dir.mkdir(parents=True, exist_ok=True)
    existing = active.exercises()

    if not name:
        print(f'\n💻 Danh sách Bài tập trong [{active.title}]:')
        for idx, p in enumerate(existing, 1):
            print(f'  [{idx}] {p.name}')
        print(f'  [N] + Tạo file bài tập mới')
        ans = input('Chọn số để mở hoặc nhập tên file mới (Enter để mở bài mới nhất): ').strip()
        if not ans and existing:
            target = existing[-1]
            LAST_FILE_CACHE.write_text(str(target), encoding='utf-8')
            if open_editor:
                open_in_vscode(active.folder, target)
            return target
        if ans.isdigit() and 1 <= int(ans) <= len(existing):
            target = existing[int(ans) - 1]
            LAST_FILE_CACHE.write_text(str(target), encoding='utf-8')
            if open_editor:
                open_in_vscode(active.folder, target)
            return target
        if ans.lower() == 'n' or not ans:
            name = input('Nhập tên file bài tập mới (vd: ex05-loop.py hoặc loop): ').strip()
        else:
            name = ans

    if not name:
        raise ValueError('Cần nhập tên file bài tập.')

    raw_path = Path(name.strip())
    ext = raw_path.suffix.lower() or default_ext_for_study(active)
    stem = slugify(raw_path.stem)

    if not re.match(r'^(ex\d+|web\d+|\d{2}-)', stem):
        next_num = len(existing) + 1
        file_name = f'ex{next_num:02d}-{stem}{ext}'
    else:
        file_name = f'{stem}{ext}'

    target = active.exercises_dir / file_name
    if not target.exists():
        if ext in {'.bat', '.cmd'}:
            tpl = f"@echo off\nchcp 65001 >nul\nREM Bài tập: {file_name} ({active.title})\n\necho Xin chào từ {file_name}!\n"
        elif ext == '.py':
            tpl = f"# Bài tập: {file_name} ({active.title})\n\ndef main():\n    print('Xin chào từ {file_name}!')\n\nif __name__ == '__main__':\n    main()\n"
        elif ext == '.js':
            tpl = f"// Bài tập: {file_name} ({active.title})\n\nconsole.log('Xin chào từ {file_name}!');\n"
        elif ext in {'.html', '.htm'}:
            tpl = f"<!DOCTYPE html>\n<html lang=\"vi\">\n<head>\n  <meta charset=\"UTF-8\">\n  <title>{file_name}</title>\n</head>\n<body>\n  <h1>Bài tập: {file_name}</h1>\n</body>\n</html>\n"
        else:
            tpl = ''
        target.write_text(tpl, encoding='utf-8')
        print(f'✨ Đã tạo bài tập mới: {target.relative_to(ROOT)}')
    else:
        print(f'💻 Đang mở bài tập: {target.relative_to(ROOT)}')

    LAST_FILE_CACHE.write_text(str(target), encoding='utf-8')
    update_all_readmes()
    if open_editor:
        open_in_vscode(active.folder, target)
    return target


def open_active_in_vscode(with_ai: bool = False):
    active = get_active_study()
    active.notes_dir.mkdir(parents=True, exist_ok=True)
    active.exercises_dir.mkdir(parents=True, exist_ok=True)
    update_all_readmes()

    files_to_focus = []
    notes = active.notes()
    exercises = active.exercises()
    if notes:
        files_to_focus.append(notes[-1])
    if exercises:
        files_to_focus.append(exercises[-1])
    if not files_to_focus:
        files_to_focus.append(active.folder / 'README.md')

    open_in_vscode(active.folder, *files_to_focus)
    print(f'\n🖥️  Đã mở VS Code cho khóa đang học: {active.badge} {active.title}')
    print(f'   📂 Thư mục : {active.folder}')
    print(f'   📓 Ghi chú : {len(notes)} bài (notes/)  ·  💻 Bài tập: {len(exercises)} file (exercises/)')
    print(f'   🚀 Khi học xong, gõ `learn push` (hoặc `up`) để tự động lưu & đẩy lên GitHub!\n')

    if with_ai:
        agy = shutil.which('agy')
        if agy:
            os.chdir(active.folder)
            subprocess.run([agy])


def push_to_github(custom_msg: str | None = None):
    print('🔄 1/3: Đang cập nhật mục lục README.md và đồng bộ sang Obsidian...')
    update_all_readmes()

    # Kiểm tra trạng thái Git
    status_out = subprocess.run(
        ['git', 'status', '--porcelain'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', check=True
    ).stdout.strip()

    ahead_out = subprocess.run(
        ['git', 'rev-list', '--count', 'origin/main..HEAD'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', check=False
    ).stdout.strip()
    ahead = int(ahead_out) if ahead_out.isdigit() else 0

    if not status_out and ahead == 0:
        print('✨ Toàn bộ ghi chú và bài tập đã được lưu đồng bộ trên https://github.com/cmduyeen/self-study !')
        return

    active = get_active_study()
    if status_out:
        changed_lines = [line.strip() for line in status_out.splitlines() if line.strip()]
        print(f'📦 2/3: Đang đóng gói {len(changed_lines)} file thay đổi...')
        for line in changed_lines[:8]:
            print(f'   • {line}')
        if len(changed_lines) > 8:
            print(f'   • ... và {len(changed_lines) - 8} file khác')

        subprocess.run(['git', 'add', '-A'], cwd=ROOT, check=True)
        now_str = dt.datetime.now().strftime('%Y-%m-%d %H:%M')
        msg = custom_msg or f'study({active.slug}): update notes & exercises ({now_str})'
        subprocess.run(['git', 'commit', '-m', msg], cwd=ROOT, check=True)

    print('☁️  3/3: Đang đồng bộ và đẩy lên https://github.com/cmduyeen/self-study ...')
    subprocess.run(['git', 'pull', '--rebase', '--autostash', 'origin', 'main'], cwd=ROOT, check=True)
    subprocess.run(['git', 'push', 'origin', 'main'], cwd=ROOT, check=True)
    print(f'✅ ĐÃ LƯU LÊN GITHUB THÀNH CÔNG! Xem tại: https://github.com/cmduyeen/self-study')


def add_new_study():
    print('\n➕ THÊM SÁCH HOẶC KHÓA HỌC MỚI VÀO SELF-STUDY')
    cat_choice = input('Chọn loại: [1] 📚 Sách (books)   [2] 🎓 Khóa học (courses) [mặc định: 2]: ').strip()
    category = 'books' if cat_choice == '1' else 'courses'
    title = input('Nhập tên đầy đủ của Sách / Khóa học: ').strip()
    if not title:
        print('Đã hủy.')
        return

    st_choice = input('Chọn trạng thái: [1] 🟨 Đang học (mặc định)  [2] 🟧 Sẵn sàng  [3] 🟥 Chưa bắt đầu: ').strip()
    status = {'1': 'studying', '2': 'ready', '3': 'not_started'}.get(st_choice, 'studying')

    year = str(dt.date.today().year)
    slug = slugify(title)
    folder = ROOT / year / category / slug
    (folder / 'notes').mkdir(parents=True, exist_ok=True)
    (folder / 'exercises').mkdir(parents=True, exist_ok=True)

    # Nếu đặt khóa mới là studying (🟨), có thể chuyển các khóa studying cũ sang ready hoặc giữ nguyên tùy ý
    meta = {'title': title, 'status': status}
    (folder / 'study.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    update_all_readmes()
    print(f'✅ Đã tạo [{title}] tại {folder.relative_to(ROOT)} và đồng bộ sang Obsidian!')
    open_in_vscode(folder, folder / 'README.md')


def switch_study_status():
    items = load_all_studies()
    if not items:
        print('Chưa có khóa học nào.')
        return
    print('\n🔄 DANH SÁCH SÁCH & KHÓA HỌC HIỆN CÓ:')
    for idx, it in enumerate(items, 1):
        print(f'  [{idx}] {it.badge} {it.title} ({it.category_vi} · {len(it.notes())} notes · {len(it.exercises())} bài tập)')

    raw = input('\nChọn số thứ tự khóa học muốn đổi trạng thái / chọn làm khóa đang học (0 để thoát): ').strip()
    if not raw.isdigit() or not (1 <= int(raw) <= len(items)):
        return
    target = items[int(raw) - 1]
    print(f'\nĐổi trạng thái cho "{target.title}":')
    print('  [1] 🟨 studying    (Đang học — Mở mặc định khi gõ `learn`)')
    print('  [2] 🟩 completed   (Đã hoàn thành)')
    print('  [3] 🟧 ready       (Sẵn sàng học)')
    print('  [4] 🟥 not_started (Chưa bắt đầu)')
    st_ch = input('Chọn (1-4) [mặc định: 1]: ').strip() or '1'
    new_status = {'1': 'studying', '2': 'completed', '3': 'ready', '4': 'not_started'}.get(st_ch)
    if not new_status:
        return

    # Nếu chọn 1 khóa làm studying (🟨), hỏi xem có muốn chuyển khóa studying cũ về ready (🟧) để chỉ tập trung 1 khóa không
    if new_status == 'studying':
        for other in items:
            if other.folder != target.folder and other.status == 'studying':
                other_meta = {'title': other.title, 'status': 'ready'}
                (other.folder / 'study.json').write_text(json.dumps(other_meta, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    meta = {'title': target.title, 'status': new_status}
    (target.folder / 'study.json').write_text(json.dumps(meta, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    update_all_readmes()
    print(f'✅ Đã cập nhật "{target.title}" -> {STATUS_MAP[new_status][0]} {STATUS_MAP[new_status][1]}!')
    if new_status == 'studying':
        open_active_in_vscode()


def list_studies():
    items = load_all_studies()
    active = get_active_study(items) if items else None
    print('\n╭────────────────────────────────────────────────────────────────────────────╮')
    print('│  🎓 KHO TỰ HỌC CODE (D:\\Brain2nd\\Code\\cmduyeen-self-study)                 │')
    print('╰────────────────────────────────────────────────────────────────────────────╯')
    for idx, it in enumerate(items, 1):
        active_tag = '  👈 [ĐANG HỌC MẶC ĐỊNH]' if (active and it.folder == active.folder) else ''
        print(f'  {idx}. {it.badge} [{it.category_vi}] {it.title}{active_tag}')
        print(f'     📓 {len(it.notes())} ghi chú (notes/)  ·  💻 {len(it.exercises())} bài tập (exercises/)  ·  📂 {it.folder.relative_to(ROOT).as_posix()}')
    print('')


def interactive_menu():
    active = get_active_study()
    print('\n╭─────────────── 🎓 SELF-STUDY CLI (VS CODE + GITHUB AUTO-SAVE) ───────────────╮')
    print(f'│  📚 Đang học : {active.badge} {active.title:<58} │')
    print(f'│  📊 Tiến độ  : {len(active.notes())} bài ghi chú (notes/) · {len(active.exercises())} bài tập code (exercises/)           │')
    print('├──────────────────────────────────────────────────────────────────────────────┤')
    print('│  [1] learn open : Mở khóa đang học trong VS Code (viết Note + làm Bài tập)   │')
    print('│  [2] learn note : Tạo / mở bài Ghi chú lý thuyết (notes/) bằng VS Code       │')
    print('│  [3] learn ex   : Tạo / mở file Bài tập Code (exercises/) bằng VS Code       │')
    print('│  [4] learn push : Tự động cập nhật README & Upload toàn bộ lên GitHub (up)   │')
    print('│  [5] learn set  : Đổi khóa đang học / Đổi trạng thái (🟥 🟧 🟨 🟩)            │')
    print('│  [6] learn new  : Thêm Sách (Book) hoặc Khóa học (Course) mới                │')
    print('│  [7] learn ai   : Mở VS Code + bật AI CLI (agy) kèm cặp ngay tại khóa học    │')
    print('│  [0] Thoát                                                                   │')
    print('╰──────────────────────────────────────────────────────────────────────────────╯')
    ch = input('Chọn thao tác [Enter = 1 Mở VS Code ngay, hoặc 0-7]: ').strip() or '1'
    if ch == '0':
        return
    elif ch == '1':
        open_active_in_vscode(with_ai=False)
    elif ch == '2':
        create_or_open_note()
    elif ch == '3':
        create_or_open_exercise()
    elif ch == '4':
        push_to_github()
    elif ch == '5':
        switch_study_status()
    elif ch == '6':
        add_new_study()
    elif ch == '7':
        open_active_in_vscode(with_ai=True)


def main():
    parser = argparse.ArgumentParser(description='Quản lý kho tự học cmduyeen-self-study bằng VS Code & GitHub')
    parser.add_argument('action', nargs='?', help='open | note | ex | push (up) | new | set | list | ai')
    parser.add_argument('name', nargs='*', help='Tên bài ghi chú, tên bài tập hoặc lời nhắn commit')
    args = parser.parse_args()

    if not args.action:
        interactive_menu()
        return

    raw = args.action.lower().strip()
    action = ACTION_ALIASES.get(raw)
    rest_str = ' '.join(args.name).strip() if args.name else None

    if not action:
        # Nếu người dùng gõ `learn ten-bai` thì hiểu là tìm/mở khóa học hoặc tạo nhanh
        raise ValueError(
            f'Lệnh "{args.action}" không hợp lệ. Hỗ trợ: '
            'learn, learn open, learn note, learn ex, learn push (hoặc up), learn set, learn new, learn list, learn ai.'
        )

    if action == 'open':
        open_active_in_vscode(with_ai=False)
    elif action == 'ai':
        open_active_in_vscode(with_ai=True)
    elif action == 'note':
        create_or_open_note(rest_str)
    elif action == 'ex':
        create_or_open_exercise(rest_str)
    elif action == 'push':
        push_to_github(rest_str)
    elif action == 'new':
        add_new_study()
    elif action == 'switch':
        switch_study_status()
    elif action == 'list':
        list_studies()


if __name__ == '__main__':
    try:
        main()
    except (ValueError, OSError, subprocess.CalledProcessError) as error:
        print('❌ Lỗi: ' + str(error))
        sys.exit(1)
    except (KeyboardInterrupt, EOFError):
        print('\nĐã dừng.')
