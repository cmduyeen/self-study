#!/usr/bin/env python3
"""
Live Markdown Note Watcher for Windows Terminal Split Pane
Watches a .md file (or the latest edited note) and automatically re-renders it
with `glow` whenever you press Ctrl+S in Micro!
"""

import os
import subprocess
import sys
import time
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass


def get_system_theme() -> str:
    if sys.platform == "win32":
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize",
            )
            val, _ = winreg.QueryValueEx(key, "AppsUseLightTheme")
            winreg.CloseKey(key)
            return "light" if val == 1 else "dark"
        except Exception:
            pass
    return "dark"


def render_note(md_path: Path) -> None:
    os.system("cls" if os.name == "nt" else "clear")
    theme = get_system_theme()
    print(f"\033[36m\033[1m📖 LIVE NOTE PREVIEW:\033[0m {md_path.name} \033[90m(Tự cập nhật khi bấm Ctrl+S | Nhấn Ctrl+C để đóng khung)\033[0m")
    print("\033[90m" + "─" * 64 + "\033[0m")
    env = os.environ.copy()
    winget_links = os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links")
    if winget_links not in env.get("PATH", ""):
        env["PATH"] = env.get("PATH", "") + ";" + winget_links

    subprocess.run(["glow", "-s", theme, str(md_path)], env=env)


def main():
    if len(sys.argv) < 2:
        print("Hãy truyền đường dẫn file .md cần theo dõi.")
        return 1

    md_path = Path(sys.argv[1]).resolve()
    if not md_path.exists():
        print(f"Không tìm thấy file: {md_path}")
        return 1

    last_mtime = 0
    last_theme = ""
    try:
        while True:
            if md_path.exists():
                mtime = md_path.stat().st_mtime_ns
                theme = get_system_theme()
                if mtime != last_mtime or theme != last_theme:
                    last_mtime = mtime
                    last_theme = theme
                    render_note(md_path)
            time.sleep(0.3)
    except KeyboardInterrupt:
        pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
