#!/usr/bin/env python3
"""
Smart Code & Markdown Note Runner for Self-Study
Supports:
  - Direct code files: .py, .bat, .cmd, .ps1, .js
  - Markdown study notes (.md): extracts and runs ```python, ```bat/```cmd, ```js, ```powershell blocks
  - Friendly Vietnamese Error Explainer for beginners
  - Optional --save (-s) to append execution output directly into the Markdown note
"""

import argparse
import os
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

# Ensure UTF-8 console output on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

ROOT = Path(__file__).resolve().parent.parent
LAST_FILE_CACHE = ROOT / ".last_study_file"

# Colors for terminal
RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
GRAY = "\033[90m"
MAGENTA = "\033[35m"

ERROR_EXPLANATIONS = [
    (
        r"SyntaxError:\s*unterminated string literal",
        "Bạn mở dấu nháy chuỗi chữ (\" hoặc ') nhưng quên đóng lại ở cuối dòng.",
        "Hãy kiểm tra dòng báo lỗi và thêm dấu \" hoặc ' vào cuối câu chữ.",
    ),
    (
        r"SyntaxError:\s*expected ':'",
        "Bạn thiếu dấu hai chấm (:) ở cuối câu lệnh điều kiện hoặc vòng lặp (if, else, for, while, def).",
        "Hãy thêm dấu ':' vào cuối dòng đó (ví dụ: if tuoi >= 18:).",
    ),
    (
        r"SyntaxError:\s*invalid syntax",
        "Cú pháp câu lệnh chưa đúng quy tắc (có thể dư/thiếu dấu ngoặc, dấu phẩy hoặc viết sai từ khóa).",
        "Hãy nhìn kỹ vị trí dấu mũ (^) chỉ vào trong thông báo lỗi để kiểm tra lại.",
    ),
    (
        r"IndentationError",
        "Lỗi thụt đầu dòng (khoảng trắng đầu dòng không đều nhau).",
        "Trong Python, các dòng nằm trong if/for/def phải thụt vào đều nhau (thường là 4 dấu cách hoặc 1 phím Tab).",
    ),
    (
        r"NameError:\s*name '([^']+)' is not defined",
        "Máy tính không hiểu tên biến hoặc tên hàm '{0}' vì nó chưa được tạo ra trước đó (hoặc bị gõ sai chính tả).",
        "Kiểm tra xem bạn đã gán giá trị cho '{0}' chưa, hoặc có viết hoa/thường lệch nhau không.",
    ),
    (
        r"TypeError:\s*can only concatenate str .* to str",
        "Bạn đang cộng trực tiếp một Chuỗi chữ (str) với một Con số (int/float).",
        "Hãy dùng f-string: f\"Kết quả: {so}\" hoặc đổi số thành chữ bằng str(so).",
    ),
    (
        r"TypeError",
        "Kiểu dữ liệu không khớp nhau (ví dụ lấy chữ chia cho số, hoặc truyền sai số lượng tham số vào hàm).",
        "Kiểm tra lại kiểu dữ liệu của các biến bằng hàm type(ten_bien).",
    ),
    (
        r"ZeroDivisionError",
        "Bạn đang thực hiện phép chia cho số 0 (toán học không cho phép chia cho 0).",
        "Kiểm tra lại biến ở mẫu số xem tại sao nó lại bằng 0.",
    ),
    (
        r"ValueError:\s*invalid literal for int\(\)",
        "Bạn đang ép kiểu int() (số nguyên) cho một chuỗi không phải là số (ví dụ int('abc')).",
        "Hãy chắc chắn chuỗi đưa vào int() chỉ chứa các chữ số.",
    ),
    (
        r"IndexError:\s*list index out of range",
        "Bạn đang lấy phần tử ở vị trí vượt quá độ dài của danh sách (list).",
        "Lưu ý: Danh sách trong lập trình đếm từ vị trí 0 (phần tử đầu tiên là [0]).",
    ),
    (
        r"KeyError:\s*(.+)",
        "Không tìm thấy từ khóa (key) {0} bên trong từ điển (dict).",
        "Hãy dùng .get({0}) hoặc kiểm tra lại tên key xem có gõ đúng không.",
    ),
    (
        r"ModuleNotFoundError:\s*No module named '([^']+)'",
        "Thư viện '{0}' chưa được cài trên máy.",
        "Bạn có thể cài bằng lệnh: pip install {0}",
    ),
    (
        r"FileNotFoundError",
        "Chương trình tìm mở một file nhưng không thấy file đó ở đường dẫn đã chỉ định.",
        "Kiểm tra lại tên file và đường dẫn thư mục hiện tại.",
    ),
    (
        r"'([^']+)' is not recognized as an internal or external command",
        "Lệnh '{0}' trong Batch/CMD không tồn tại hoặc bị gõ sai tên.",
        "Trong Batch Script (.bat), hãy kiểm tra lại chính tả lệnh (ví dụ: echo, set, dir, pause, goto).",
    ),
    (
        r"ReferenceError:\s*([^\s]+) is not defined",
        "Biến hoặc hàm '{0}' trong JavaScript chưa được khai báo.",
        "Hãy khai báo bằng let hoặc const trước khi dùng (ví dụ: let {0} = ...).",
    ),
]


def explain_error(stderr_text: str) -> str:
    if not stderr_text or not stderr_text.strip():
        return ""
    hints = []
    # Find line number if present
    line_match = re.search(r"line (\d+)", stderr_text, re.IGNORECASE)
    line_info = f" (Dòng {line_match.group(1)})" if line_match else ""

    for pattern, meaning, fix in ERROR_EXPLANATIONS:
        m = re.search(pattern, stderr_text)
        if m:
            groups = m.groups()
            formatted_meaning = meaning.format(*groups) if groups else meaning
            formatted_fix = fix.format(*groups) if groups else fix
            hints.append(
                f"{YELLOW}{BOLD}💡 Giải thích lỗi tiếng Việt{line_info}:{RESET}\n"
                f"   • {BOLD}Nguyên nhân:{RESET} {formatted_meaning}\n"
                f"   • {BOLD}Cách sửa:{RESET}    {formatted_fix}"
            )
            break

    if not hints and ("Error" in stderr_text or "Exception" in stderr_text):
        hints.append(
            f"{YELLOW}{BOLD}💡 Gợi ý kiểm tra lỗi{line_info}:{RESET}\n"
            f"   • Hãy xem dòng cuối cùng của thông báo lỗi phía trên và kiểm tra lại cú pháp tại{line_info or ' dòng vừa viết'}."
        )
    return "\n".join(hints)


def ensure_live_server(port: int = 5500) -> str:
    """Ensure background Live Server is running on http://127.0.0.1:5500 serving ROOT."""
    import urllib.request
    base_url = f"http://127.0.0.1:{port}"
    try:
        with urllib.request.urlopen(f"{base_url}/__live_info", timeout=0.3) as resp:
            if resp.status == 200:
                return base_url
    except Exception:
        pass

    live_script = ROOT / "scripts" / "live-server.py"
    if sys.platform == "win32":
        # Use PowerShell Start-Process -WindowStyle Hidden so the server outlives Micro's subshell
        ps_cmd = (
            f"Start-Process -FilePath '{sys.executable}' "
            f"-ArgumentList '\"{live_script}\" -d \"{ROOT}\" -p {port}' "
            f"-WorkingDirectory '{ROOT}' -WindowStyle Hidden"
        )
        subprocess.run(["powershell.exe", "-NoProfile", "-Command", ps_cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        subprocess.Popen(
            [sys.executable, str(live_script), "-d", str(ROOT), "-p", str(port)],
            cwd=str(ROOT),
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            stdin=subprocess.DEVNULL,
            start_new_session=True,
        )
    for _ in range(20):
        time.sleep(0.1)
        try:
            with urllib.request.urlopen(f"{base_url}/__live_info", timeout=0.2) as resp:
                if resp.status == 200:
                    break
        except Exception:
            pass
    return base_url


def open_in_live_server(target_html: Path) -> int:
    from urllib.parse import quote
    base_url = ensure_live_server(5500)
    try:
        rel = target_html.resolve().relative_to(ROOT.resolve()).as_posix()
        url = f"{base_url}/{quote(rel, safe='/-._')}"
    except ValueError:
        url = target_html.as_uri()

    print(f"{GREEN}{BOLD}⚡ Live Server đang hoạt động:{RESET} {CYAN}{url}{RESET}")
    print(f"{YELLOW}💡 Giống VS Code Live Server: Bạn chỉ cần sửa code trong Micro rồi bấm Ctrl+S, trình duyệt sẽ TỰ ĐỘNG tải lại ngay!{RESET}")
    if sys.platform == "win32":
        subprocess.run(["cmd.exe", "/c", "start", "", url], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        import webbrowser
        webbrowser.open(url)
    return 0


def save_last_file(path: Path) -> None:
    try:
        LAST_FILE_CACHE.write_text(str(path.resolve()), encoding="utf-8")
    except Exception:
        pass


def get_last_file() -> Path | None:
    if LAST_FILE_CACHE.exists():
        try:
            p = Path(LAST_FILE_CACHE.read_text(encoding="utf-8").strip())
            if p.exists():
                return p
        except Exception:
            pass
    return None


def run_single_command(cmd: list[str], cwd: Path) -> tuple[int, str, str, float]:
    start = time.perf_counter()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"
    # Run interactively if stdin is needed, while capturing stderr for explanation when non-interactive
    proc = subprocess.run(
        cmd,
        cwd=str(cwd),
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env=env,
    )
    elapsed = time.perf_counter() - start
    return proc.returncode, proc.stdout, proc.stderr, elapsed


def run_interactive_file(file_path: Path) -> int:
    ext = file_path.suffix.lower()
    cwd = file_path.parent
    print(f"{CYAN}{BOLD}▶ Đang chạy:{RESET} {file_path.name} {GRAY}({cwd}){RESET}")
    print(f"{GRAY}{'─' * 56}{RESET}")

    if ext == ".py":
        cmd = [sys.executable, str(file_path)]
    elif ext in (".bat", ".cmd"):
        # Ensure UTF-8 without BOM and CRLF line endings so cmd.exe parses Vietnamese lines cleanly
        try:
            raw_text = file_path.read_text(encoding="utf-8-sig")
            normalized = raw_text.replace("\r\n", "\n").replace("\n", "\r\n")
            file_path.write_bytes(normalized.encode("utf-8"))
        except Exception:
            pass
        cmd = ["cmd.exe", "/c", file_path.name]
    elif ext == ".ps1":
        cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(file_path)]
    elif ext == ".js":
        cmd = ["node", str(file_path)]
    elif ext in (".html", ".htm"):
        return open_in_live_server(file_path)
    elif ext == ".css":
        html_files = sorted(cwd.glob("*.html"))
        if html_files:
            return open_in_live_server(html_files[0])
        print(f"{YELLOW}Đây là file giao diện CSS ({file_path.name}). Hãy tạo thêm 1 file .html cùng thư mục để xem trên Live Server nhé!{RESET}")
        return 0
    else:
        print(f"{RED}Không hỗ trợ chạy trực tiếp đuôi file '{ext}'. Hãy dùng .py, .bat, .cmd, .ps1, .js, .html hoặc .md{RESET}")
        return 1

    # Check if the file asks for interactive input (input(), set /p, Read-Host)
    content = ""
    try:
        content = file_path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        pass

    needs_stdin = bool(
        re.search(r"\binput\s*\(|\bset\s+/p\b|\bRead-Host\b|\bpause\b", content, re.IGNORECASE)
    )

    start = time.perf_counter()
    env = os.environ.copy()
    env["PYTHONIOENCODING"] = "utf-8"

    if needs_stdin:
        # Let user type directly in terminal, capture stderr to temp file for Vietnamese explanation
        with tempfile.NamedTemporaryFile(mode="w+", encoding="utf-8", delete=False, suffix=".err") as err_file:
            err_path = Path(err_file.name)
        try:
            with open(err_path, "w", encoding="utf-8") as ef:
                proc = subprocess.run(cmd, cwd=str(cwd), stderr=ef, env=env)
            elapsed = time.perf_counter() - start
            stderr_text = err_path.read_text(encoding="utf-8", errors="replace")
        finally:
            err_path.unlink(missing_ok=True)

        if stderr_text:
            print(f"\n{RED}{stderr_text.rstrip()}{RESET}")
            hint = explain_error(stderr_text)
            if hint:
                print(f"\n{hint}")
        rc = proc.returncode
    else:
        rc, out, err, elapsed = run_single_command(cmd, cwd)
        if out:
            print(out.rstrip())
        if err:
            print(f"{RED}{err.rstrip()}{RESET}")
            hint = explain_error(err)
            if hint:
                print(f"\n{hint}")

    print(f"{GRAY}{'─' * 56}{RESET}")
    status_str = f"{GREEN}✔ Hoàn tất ({elapsed:.2f}s){RESET}" if rc == 0 else f"{RED}✖ Kết thúc với mã lỗi {rc} ({elapsed:.2f}s){RESET}"
    print(status_str)
    return rc


CODE_BLOCK_RE = re.compile(
    r"```(python|py|bat|batch|cmd|js|javascript|powershell|ps1)\s*\r?\n(.*?)```",
    re.DOTALL | re.IGNORECASE,
)


def run_markdown_note(md_path: Path, block_index: int | None = None, save_output: bool = False) -> int:
    text = md_path.read_text(encoding="utf-8", errors="replace")
    matches = list(CODE_BLOCK_RE.finditer(text))

    if not matches:
        print(f"{YELLOW}📄 Bài Note '{md_path.name}' chưa có khối code nào để chạy.{RESET}")
        print(
            f"{GRAY}Gợi ý: Hãy chèn khối code vào bài Note theo mẫu:\n"
            f"```python\nprint('Xin chào!')\n```\n"
            f"hoặc ```bat cho Batch Script.{RESET}"
        )
        return 0

    print(
        f"{CYAN}{BOLD}📓 Sổ tay học Code:{RESET} {md_path.name} "
        f"{GRAY}(Tìm thấy {len(matches)} khối code){RESET}"
    )

    if block_index is not None and (block_index < 1 or block_index > len(matches)):
        print(f"{RED}Chỉ có {len(matches)} khối code trong bài này (bạn chọn #{block_index}).{RESET}")
        return 1

    overall_rc = 0
    outputs_by_index: dict[int, str] = {}
    accumulated_py_code: list[str] = []

    for idx, match in enumerate(matches, start=1):
        lang = match.group(1).lower()
        code = match.group(2).strip("\r\n")
        if not code.strip():
            continue

        is_selected = (block_index is None) or (block_index == idx)
        if not is_selected:
            if lang in ("python", "py"):
                accumulated_py_code.append(code)
            continue

        print(f"\n{MAGENTA}{BOLD}▶ [Khối #{idx} - {lang}]{RESET}")
        for line_no, line in enumerate(code.splitlines(), start=1):
            print(f"{GRAY}  {line_no:2d} │ {line}{RESET}")
        print(f"{GRAY}  ───┴────────────────────────────{RESET}")

        suffix_map = {
            "python": ".py",
            "py": ".py",
            "bat": ".bat",
            "batch": ".bat",
            "cmd": ".cmd",
            "js": ".js",
            "javascript": ".js",
            "powershell": ".ps1",
            "ps1": ".ps1",
        }
        suffix = suffix_map[lang]

        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", suffix=suffix, dir=str(md_path.parent), delete=False
        ) as tmp:
            if suffix in (".bat", ".cmd") and not code.lstrip().lower().startswith("@echo"):
                tmp.write("@echo off\r\nchcp 65001 >nul\r\n" + code.replace("\n", "\r\n") + "\r\n")
            elif suffix == ".py" and accumulated_py_code:
                # Run previous blocks silently so shared variables/functions work across blocks
                prelude = "\n\n".join(accumulated_py_code)
                wrapper = (
                    "import io as _io, sys as _sys\n"
                    "_old_out = _sys.stdout\n"
                    "_sys.stdout = _io.StringIO()\n"
                    "try:\n"
                    + "\n".join("    " + l for l in prelude.splitlines())
                    + "\nfinally:\n"
                    "    _sys.stdout = _old_out\n"
                    + code
                    + "\n"
                )
                tmp.write(wrapper)
            else:
                tmp.write(code + "\n")
            tmp_path = Path(tmp.name)

        try:
            if suffix == ".py":
                cmd = [sys.executable, str(tmp_path)]
            elif suffix in (".bat", ".cmd"):
                cmd = ["cmd.exe", "/c", str(tmp_path)]
            elif suffix == ".ps1":
                cmd = ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(tmp_path)]
            else:
                cmd = ["node", str(tmp_path)]

            rc, out, err, elapsed = run_single_command(cmd, md_path.parent)
            if out:
                print(out.rstrip())
                outputs_by_index[idx] = out.rstrip()
            if err:
                print(f"{RED}{err.rstrip()}{RESET}")
                hint = explain_error(err)
                if hint:
                    print(f"\n{hint}")
                overall_rc = rc or 1
            else:
                print(f"{GREEN}✔ Khối #{idx} chạy xong ({elapsed:.2f}s){RESET}")
                if suffix == ".py":
                    accumulated_py_code.append(code)
        finally:
            tmp_path.unlink(missing_ok=True)

    if save_output and outputs_by_index:
        # Insert or update "> 📤 **Kết quả chạy:**" right below each executed block
        new_text = text
        for idx, match in reversed(list(enumerate(matches, start=1))):
            if idx not in outputs_by_index:
                continue
            out_lines = "\n".join(f"> `{line}`" for line in outputs_by_index[idx].splitlines())
            result_block = f"\n> 📤 **Kết quả chạy (Khối #{idx}):**\n{out_lines}\n"
            end_pos = match.end()
            # Remove existing result block if immediately following
            after = new_text[end_pos:]
            existing_re = re.match(r"^\r?\n> 📤 \*\*Kết quả chạy.*?(?=\r?\n\r?\n|\Z)", after, re.DOTALL)
            if existing_re:
                new_text = new_text[:end_pos] + result_block + after[existing_re.end():]
            else:
                new_text = new_text[:end_pos] + result_block + after
        md_path.write_text(new_text, encoding="utf-8")
        print(f"\n{GREEN}💾 Đã lưu kết quả chạy trực tiếp vào bài Note: {md_path.name}{RESET}")

    return overall_rc


def main() -> int:
    parser = argparse.ArgumentParser(description="Chạy file Code hoặc khối Code trong bài Note (.md)")
    parser.add_argument("target", nargs="?", help="Đường dẫn file .py, .bat, .cmd, .js, .ps1, hoặc .md")
    parser.add_argument("-b", "--block", type=int, help="Chỉ chạy khối code thứ N trong bài Note .md")
    parser.add_argument("-s", "--save", action="store_true", help="Lưu kết quả chạy vào bên dưới khối code trong bài Note .md")
    parser.add_argument("--pause", action="store_true", help="Dừng màn hình chờ bấm Enter (dùng khi gọi từ phím F5 trong Micro)")
    args = parser.parse_args()

    target_path: Path | None = None
    if args.target:
        candidate = Path(args.target)
        if not candidate.exists():
            # Try relative to ROOT
            alt = ROOT / args.target
            if alt.exists():
                candidate = alt
        target_path = candidate
    else:
        target_path = get_last_file()

    if not target_path or not target_path.exists():
        print(f"{YELLOW}Chưa chọn file để chạy.{RESET} Hãy gõ: {BOLD}run <tên_file>{RESET} hoặc mở file bằng {BOLD}learn{RESET} / {BOLD}nf{RESET}.")
        return 1

    save_last_file(target_path)

    if target_path.suffix.lower() == ".md":
        rc = run_markdown_note(target_path, block_index=args.block, save_output=args.save)
    else:
        rc = run_interactive_file(target_path)

    if args.pause and target_path.suffix.lower() not in (".html", ".htm", ".css"):
        print(f"\n{CYAN}Nhấn [Enter] để quay lại trình soạn thảo...{RESET}", end="", flush=True)
        try:
            input()
        except EOFError:
            pass

    return rc


if __name__ == "__main__":
    sys.exit(main())
