"""Terminal Productivity Tracker cho Dyn (https://github.com/cmduyeen & D:\\Brain2nd)."""
from __future__ import annotations

import argparse
import calendar
from collections import Counter
import datetime as dt
import json
from pathlib import Path
import re
import subprocess
import sys
import urllib.error
import urllib.request

for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, 'reconfigure'):
        stream.reconfigure(encoding='utf-8')

BRAIN_ROOT = Path(r'D:\Brain2nd')
CODE_ROOT = BRAIN_ROOT / 'Code'
BLOG_REPO = CODE_ROOT / 'cmduyeen-github-page'
PROFILE_REPO = CODE_ROOT / 'cmduyeen-github-profile'
STUDY_REPO = CODE_ROOT / 'cmduyeen-self-study'
CACHE_FILE = STUDY_REPO / '.github_profile_cache.json'
GITHUB_USER = 'cmduyeen'

# Mã màu ANSI tối giản, hài hòa với Serein Theme
RESET = '\033[0m'
BOLD = '\033[1m'
DIM = '\033[2m'
CYAN = '\033[36m'
GREEN = '\033[32m'
YELLOW = '\033[33m'
MAGENTA = '\033[35m'
BLUE = '\033[34m'


def fetch_github_repos(force_refresh: bool = False) -> list[dict]:
    """Lấy danh sách public repos từ GitHub API (có cache 30 phút để chạy tức thì)."""
    if not force_refresh and CACHE_FILE.is_file():
        try:
            age = dt.datetime.now().timestamp() - CACHE_FILE.stat().st_mtime
            if age < 1800:
                return json.loads(CACHE_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass

    url = f'https://api.github.com/users/{GITHUB_USER}/repos?type=public&sort=created&direction=desc&per_page=100'
    req = urllib.request.Request(
        url,
        headers={
            'Accept': 'application/vnd.github+json',
            'User-Agent': 'dyn-brain2nd-cli',
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=6) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            if isinstance(data, list):
                CACHE_FILE.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
                return data
    except Exception:
        pass

    if CACHE_FILE.is_file():
        try:
            return json.loads(CACHE_FILE.read_text(encoding='utf-8'))
        except Exception:
            pass
    return []


def collect_local_git_commits_by_month(months: list[dt.date]) -> Counter:
    """Đếm tổng số commit của Dyn trên toàn bộ các repo trong D:\\Brain2nd\\Code trong 12 tháng qua."""
    start_date = months[0].isoformat()
    counts: Counter = Counter()
    seen_hashes: set[str] = set()

    if not CODE_ROOT.is_dir():
        return counts

    for repo_dir in CODE_ROOT.iterdir():
        if not (repo_dir / '.git').exists():
            continue
        try:
            res = subprocess.run(
                ['git', '-C', str(repo_dir), 'log', '--all', f'--since={start_date}', '--format=%H|%ad', '--date=short'],
                capture_output=True, text=True, encoding='utf-8', timeout=4, check=False
            )
            for line in res.stdout.splitlines():
                parts = line.strip().split('|')
                if len(parts) == 2:
                    commit_hash, date_str = parts
                    if commit_hash not in seen_hashes and len(date_str) >= 7:
                        seen_hashes.add(commit_hash)
                        y, m = int(date_str[:4]), int(date_str[5:7])
                        counts[dt.date(y, m, 1)] += 1
        except Exception:
            continue
    return counts


def collect_blog_stats() -> tuple[list[dict], int, Counter]:
    """Thu thập danh sách bài blog đã đăng, số bài nháp và thống kê theo tháng."""
    published_posts = []
    draft_count = 0
    month_counts: Counter = Counter()

    blog_dir = BRAIN_ROOT / 'Bài viết'
    if blog_dir.is_dir():
        for md in sorted(blog_dir.glob('*.md')):
            try:
                text = md.read_text(encoding='utf-8-sig')
            except OSError:
                continue
            m = re.match(r'\A---\r?\n(.*?)\r?\n---', text, re.S)
            header = m.group(1) if m else ''
            status = ''
            pub_date = ''
            slug = ''
            category = ''
            for line in header.splitlines():
                if line.startswith('Trạng thái:'):
                    status = line.split(':', 1)[1].strip().strip('"\'')
                elif line.startswith('Ngày xuất bản:'):
                    pub_date = line.split(':', 1)[1].strip().strip('"\'')[:10]
                elif line.startswith('Ngày tạo:') and not pub_date:
                    pub_date = line.split(':', 1)[1].strip().strip('"\'')[:10]
                elif line.startswith('Slug:'):
                    slug = line.split(':', 1)[1].strip().strip('"\'')
                elif line.startswith('Chuyên mục:'):
                    category = line.split(':', 1)[1].strip().strip('"\'')

            if status == 'Đã đăng':
                published_posts.append({
                    'title': md.stem,
                    'date': pub_date or '2026-01-01',
                    'slug': slug,
                    'category': category,
                })
                if re.match(r'^\d{4}-\d{2}', pub_date):
                    month_counts[dt.date(int(pub_date[:4]), int(pub_date[5:7]), 1)] += 1
            else:
                draft_count += 1

    published_posts.sort(key=lambda x: x['date'], reverse=True)
    return published_posts, draft_count, month_counts


def collect_obsidian_stats() -> dict[str, int]:
    def count_md(folder_name: str) -> int:
        p = BRAIN_ROOT / folder_name
        return sum(1 for _ in p.glob('*.md')) if p.is_dir() else 0

    return {
        'bai_viet': count_md('Bài viết'),
        'ghi_chu': count_md('Ghi chú'),
        'nhat_ky': count_md('Nhật ký'),
        'trich_doan': count_md('Trích đoạn'),
        'tham_khao': count_md('Tài liệu tham khảo'),
    }


def collect_study_stats() -> dict[str, int]:
    studying = 0
    completed = 0
    total_courses = 0
    notes_count = 0
    ex_count = 0

    if STUDY_REPO.is_dir():
        for sj in STUDY_REPO.rglob('study.json'):
            total_courses += 1
            try:
                data = json.loads(sj.read_text(encoding='utf-8'))
                st = data.get('status', '')
                if st == 'studying':
                    studying += 1
                elif st == 'completed':
                    completed += 1
            except Exception:
                pass
            notes_dir = sj.parent / 'notes'
            ex_dir = sj.parent / 'exercises'
            if notes_dir.is_dir():
                notes_count += sum(1 for _ in notes_dir.glob('*.md'))
            if ex_dir.is_dir():
                ex_count += sum(1 for f in ex_dir.iterdir() if f.is_file())

    return {
        'total': total_courses,
        'studying': studying,
        'completed': completed,
        'notes': notes_count,
        'exercises': ex_count,
    }


def last_n_months(n: int = 6) -> list[dt.date]:
    today = dt.date.today().replace(day=1)
    months = []
    for offset in range(n - 1, -1, -1):
        idx = today.year * 12 + today.month - 1 - offset
        y, m0 = divmod(idx, 12)
        months.append(dt.date(y, m0 + 1, 1))
    return months


def render_bar(value: int, max_val: int, width: int = 18, color: str = GREEN) -> str:
    if max_val <= 0 or value <= 0:
        return f'{DIM}{"·" * width}{RESET}'
    filled = max(1, int(round((value / max_val) * width)))
    empty = max(0, width - filled)
    return f'{color}{"█" * filled}{RESET}{DIM}{"·" * empty}{RESET}'


def display_dashboard(force_refresh: bool = False, show_all_repos: bool = False):
    gh_repos = fetch_github_repos(force_refresh=force_refresh)
    visible_gh_repos = [
        r for r in gh_repos
        if not r.get('private') and r.get('name', '').lower() != GITHUB_USER.lower()
    ]
    local_code_dirs = [
        d for d in (CODE_ROOT.iterdir() if CODE_ROOT.is_dir() else [])
        if d.is_dir() and not d.name.startswith('.')
    ]

    pub_posts, draft_posts, blog_by_month = collect_blog_stats()
    obs = collect_obsidian_stats()
    study = collect_study_stats()

    # Thống kê Repo theo năm & theo tháng (giống 2026-16R, 2025-3R trên github.com/cmduyeen)
    repos_by_year: dict[int, list[tuple[dt.datetime, dict]]] = {}
    repo_by_month: Counter = Counter()
    for r in visible_gh_repos:
        raw_created = r.get('created_at', '')
        if raw_created:
            dt_obj = dt.datetime.fromisoformat(raw_created.replace('Z', '+00:00'))
            repos_by_year.setdefault(dt_obj.year, []).append((dt_obj, r))
            repo_by_month[dt.date(dt_obj.year, dt_obj.month, 1)] += 1

    months = last_n_months(6)
    commits_by_month = collect_local_git_commits_by_month(months)
    total_commits_6m = sum(commits_by_month.values())

    print('')
    print(f'{CYAN}╭──────────────────────────────────────────────────────────────────────────────────╮{RESET}')
    print(f'{CYAN}│{RESET}  {BOLD}📊 BẢNG THEO DÕI NĂNG SUẤT CÁ NHÂN — DYN (@cmduyeen){RESET}                            {CYAN}│{RESET}')
    print(f'{CYAN}│{RESET}  {DIM}GitHub: https://github.com/cmduyeen  ·  Blog: https://cmduyeen.github.io/{RESET}       {CYAN}│{RESET}')
    print(f'{CYAN}╰──────────────────────────────────────────────────────────────────────────────────╯{RESET}')

    # 1. 4 KHỐI KPI TỔNG QUAN
    year_badges = ' · '.join(
        f'{y}-{len(items)}R' for y, items in sorted(repos_by_year.items(), reverse=True)
    ) or 'Local'
    print(f'\n  {BOLD}⚡ CHỈ SỐ NĂNG SUẤT CỐT LÕI (SINGLE SOURCE: D:\\Brain2nd){RESET}')
    print(f'  ├─ 📦 {BOLD}GitHub Repos :{RESET} {GREEN}{len(visible_gh_repos)} public repos{RESET} ({year_badges})  ·  📂 {len(local_code_dirs)} dự án trong Code\\')
    print(f'  ├─ 🌐 {BOLD}Blog Hugo    :{RESET} {YELLOW}{len(pub_posts)} bài đã đăng{RESET}  ·  📝 {draft_posts} bản nháp (D:\\Brain2nd\\Bài viết)')
    print(f'  ├─ 🧠 {BOLD}Obsidian     :{RESET} {CYAN}{obs["ghi_chu"]} ghi chú{RESET}  ·  📅 {obs["nhat_ky"]} nhật ký  ·  🔖 {obs["trich_doan"]} trích đoạn web')
    print(f'  └─ 🎓 {BOLD}Tự học Code  :{RESET} {MAGENTA}{study["studying"]} đang học (🟨){RESET} · {study["completed"]} hoàn thành (🟩) · {study["notes"]} notes · {study["exercises"]} bài tập')

    # 2. BIỂU ĐỒ PRODUCTIVITY 6 THÁNG GẦN NHẤT (COMMITS + REPOS + BLOG POSTS)
    max_commits = max(commits_by_month.values(), default=1)
    print(f'\n  {BOLD}📈 PRODUCTIVITY (6 THÁNG GẦN NHẤT — {total_commits_6m} COMMITS){RESET}')
    print(f'  {DIM}Tháng     Commits                  Số lượng   Repos mới (R)   Bài Blog (B){RESET}')
    for m in months:
        m_label = f"{calendar.month_abbr[m.month].upper()} '{m.year % 100:02d}"
        c_val = commits_by_month.get(m, 0)
        r_val = repo_by_month.get(m, 0)
        b_val = blog_by_month.get(m, 0)
        bar = render_bar(c_val, max_commits, width=20, color=GREEN)
        r_str = f'{BLUE}+{r_val}R{RESET}' if r_val else f'{DIM} 0R{RESET}'
        b_str = f'{YELLOW}+{b_val}B{RESET}' if b_val else f'{DIM} 0B{RESET}'
        print(f'  {m_label:<8}  {bar}  {c_val:>4} commits      {r_str:<14}  {b_str}')

    # 3. # MY STUFF (GIỐNG TRANG GITHUB PROFILE https://github.com/cmduyeen)
    print(f'\n  {BOLD}🗂️  MY STUFF (REPOSITORIES THEO NĂM){RESET}')
    for year in sorted(repos_by_year.keys(), reverse=True):
        entries = sorted(repos_by_year[year], key=lambda item: (-item[0].timestamp(), item[1]['name'].lower()))
        limit = len(entries) if show_all_repos else min(6, len(entries))
        print(f'  {CYAN}▾ {year}-{len(entries)}R{RESET}')
        for dt_obj, repo in entries[:limit]:
            date_tag = f'{calendar.month_abbr[dt_obj.month].upper()}-{dt_obj.day:02d}'
            r_name = repo['name']
            local_exists = (CODE_ROOT / r_name).is_dir()
            local_badge = f'{GREEN}[Local ✓]{RESET}' if local_exists else ''
            print(f'    • {DIM}{date_tag}{RESET} -> {BOLD}{r_name}{RESET} {local_badge}')
        if len(entries) > limit:
            print(f'    {DIM}... và {len(entries) - limit} repo khác trong năm {year} (gõ `stat --all` để xem hết){RESET}')

    # 4. # BLOG POSTS MỚI NHẤT
    print(f'\n  {BOLD}✍️  BLOG POSTS MỚI NHẤT (https://cmduyeen.github.io/){RESET}')
    for post in pub_posts[:5]:
        cat_tag = f'[{post["category"]}] ' if post['category'] else ''
        print(f'    • {DIM}{post["date"]}{RESET} : {YELLOW}{cat_tag}{RESET}{post["title"]}')
    if len(pub_posts) > 5:
        print(f'    {DIM}... xem toàn bộ {len(pub_posts)} bài bằng lệnh `blog list`{RESET}')

    print(f'\n  {DIM}💡 Mẹo: Gõ `stat --all` xem đủ 33 Repo · `stat -r` làm mới API · `stat sync` cập nhật lên github.com/cmduyeen{RESET}\n')


def sync_github_profile():
    """Cập nhật trực tiếp README.md của cmduyeen-github-profile và đẩy lên GitHub."""
    readme_path = PROFILE_REPO / 'README.md'
    if not readme_path.is_file():
        print('❌ Không tìm thấy repo cmduyeen-github-profile.')
        return

    gh_repos = fetch_github_repos(force_refresh=True)
    visible = [
        r for r in gh_repos
        if not r.get('private') and r.get('name', '').lower() != GITHUB_USER.lower()
    ]
    pub_posts, _, _ = collect_blog_stats()

    # 1. Render MY-STUFF
    grouped: dict[int, list[tuple[dt.datetime, dict]]] = {}
    for r in visible:
        raw_created = r.get('created_at', '')
        if raw_created:
            dt_obj = dt.datetime.fromisoformat(raw_created.replace('Z', '+00:00'))
            grouped.setdefault(dt_obj.year, []).append((dt_obj, r))

    sections = []
    for year in sorted(grouped.keys(), reverse=True):
        entries = []
        for created, r in sorted(grouped[year], key=lambda item: (-item[0].timestamp(), item[1]['name'].lower())):
            label = f'{calendar.month_abbr[created.month].upper()}-{created.day:02d}'
            name = r['name']
            url = r['html_url']
            entries.append(f'<li><code>{label}</code> -&gt; <a href="{url}">{name}</a></li>')
        sections.append(
            f'<details>\n<summary>{year}-{len(grouped[year])}R</summary>\n\n<ol>\n'
            + '\n'.join(entries)
            + '\n</ol>\n</details>'
        )
    my_stuff_block = '\n\n'.join(sections)

    # 2. Render BLOG-POST-LIST
    blog_lines = []
    for p in pub_posts[:5]:
        url = f'https://cmduyeen.github.io/posts/{p["slug"]}/'
        blog_lines.append(f'- {p["date"]}: <a href="{url}">{p["title"]}</a>')
    blog_block = '\n'.join(blog_lines)

    content = readme_path.read_text(encoding='utf-8')
    for marker, val in [('MY-STUFF', my_stuff_block), ('BLOG-POST-LIST', blog_block)]:
        s_tag = f'<!-- {marker}:START -->'
        e_tag = f'<!-- {marker}:END -->'
        s_idx = content.find(s_tag)
        e_idx = content.find(e_tag)
        if 0 <= s_idx < e_idx:
            content = content[:s_idx + len(s_tag)] + '\n' + val + '\n' + content[e_idx:]

    readme_path.write_text(content, encoding='utf-8', newline='\n')
    subprocess.run(['git', '-C', str(PROFILE_REPO), 'add', 'README.md'], check=False)
    diff = subprocess.run(
        ['git', '-C', str(PROFILE_REPO), 'diff', '--cached', '--name-only'],
        capture_output=True, text=True, check=False
    ).stdout.strip()
    if diff:
        subprocess.run(['git', '-C', str(PROFILE_REPO), 'commit', '-m', 'Update profile README from Brain2nd CLI'], check=True)
        subprocess.run(['git', '-C', str(PROFILE_REPO), 'push', 'origin', 'main'], check=True)
        print('✅ Đã cập nhật và đẩy danh sách Repo & Blog mới nhất lên https://github.com/cmduyeen !')
    else:
        print('✨ Trang https://github.com/cmduyeen đã ở trạng thái mới nhất!')


def main():
    parser = argparse.ArgumentParser(description='Bảng theo dõi năng suất cá nhân trên Terminal')
    parser.add_argument('action', nargs='?', help='sync (tùy chọn cập nhật lên github.com/cmduyeen)')
    parser.add_argument('--refresh', '-r', action='store_true', help='Làm mới dữ liệu trực tiếp từ GitHub API')
    parser.add_argument('--all', '-a', action='store_true', help='Hiển thị toàn bộ danh sách repo không rút gọn')
    args = parser.parse_args()
    if args.action and args.action.lower() == 'sync':
        sync_github_profile()
        display_dashboard(force_refresh=False, show_all_repos=args.all)
    else:
        display_dashboard(force_refresh=args.refresh, show_all_repos=args.all)


if __name__ == '__main__':
    main()
