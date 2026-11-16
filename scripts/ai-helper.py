#!/usr/bin/env python3
"""
AI Study Assistant for Neovim Terminal IDE & CLI
- Automatically reads the current file you are editing in Neovim
- Uses your existing GitHub login (`gh auth token` -> GitHub Models API) or GEMINI_API_KEY / OPENAI_API_KEY
- Can explain code, fix bugs, generate exercises, or summarize study notes in Vietnamese!
"""

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

RESET = "\033[0m"
BOLD = "\033[1m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
GRAY = "\033[90m"


def get_github_token() -> str:
    token = os.environ.get("GITHUB_TOKEN", "").strip()
    if token:
        return token
    try:
        res = subprocess.run(
            ["gh", "auth", "token"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            timeout=3,
        )
        if res.returncode == 0 and res.stdout.strip():
            return res.stdout.strip()
    except Exception:
        pass
    return ""


def ask_ai(prompt: str, context_file: Path | None = None, history: list[dict] | None = None) -> str:
    system_msg = (
        "Bạn là Trợ lý AI kèm cặp 1-1 cho người tự học lập trình và ghi chú (Self-Study). "
        "Hãy trả lời bằng tiếng Việt ngắn gọn, rõ ràng, dễ hiểu cho người non-tech mới học code, "
        "có ví dụ cụ thể."
    )
    if context_file and context_file.exists() and context_file.is_file():
        try:
            content = context_file.read_text(encoding="utf-8", errors="replace")[:6000]
            system_msg += f"\n\nNgười học đang mở file `{context_file.name}` với nội dung:\n```\n{content}\n```"
        except Exception:
            pass

    messages = [{"role": "system", "content": system_msg}]
    if history:
        messages.extend(history[-6:])
    messages.append({"role": "user", "content": prompt})

    # 1. Try GitHub Models API using existing `gh auth token`
    gh_token = get_github_token()
    if gh_token:
        url = "https://models.inference.ai.azure.com/chat/completions"
        payload = json.dumps({
            "model": "gpt-4o-mini",
            "messages": messages,
            "temperature": 0.4,
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {gh_token}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            pass
        except Exception:
            pass

    # 2. Try Gemini API Key if configured
    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    if gemini_key:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={gemini_key}"
        payload = json.dumps({
            "contents": [{"parts": [{"text": f"{system_msg}\n\nCâu hỏi: {prompt}"}]}]
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return data["candidates"][0]["content"]["parts"][0]["text"].strip()
        except Exception:
            pass

    # 3. Zero-config instant AI fallback (works out-of-the-box with no API key required)
    try:
        url = "https://text.pollinations.ai/openai"
        payload = json.dumps({
            "model": "openai",
            "messages": messages,
            "temperature": 0.4,
        }).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=payload,
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"].strip()
    except Exception:
        pass

    return (
        "⚠️ Không kết nối được mạng tới máy chủ AI.\n"
        "💡 Hãy kiểm tra kết nối Internet hoặc gõ `:Copilot setup` trong Neovim."
    )


def main():
    context_file: Path | None = None
    args = sys.argv[1:]
    if args and Path(args[0]).exists():
        context_file = Path(args[0]).resolve()
        args = args[1:]

    # One-shot question from CLI (`ai "giải thích lệnh set /a"`)
    if args:
        question = " ".join(args)
        print(f"{CYAN}{BOLD}🤖 Đang hỏi AI...{RESET}")
        ans = ask_ai(question, context_file)
        print(f"\n{ans}\n")
        return 0

    # Interactive Side-Panel inside Neovim (F8 / Alt+A)
    print(f"{CYAN}{BOLD}╭────────────────────────────────────────────────────╮{RESET}")
    print(f"{CYAN}{BOLD}│  🤖 TRỢ LÝ AI HỌC CODE & NOTE (NEOVIM SIDE PANEL)  │{RESET}")
    print(f"{CYAN}{BOLD}╰────────────────────────────────────────────────────╯{RESET}")
    if context_file:
        print(f"📄 Đang đọc file: {GREEN}{BOLD}{context_file.name}{RESET}")
    print(f"{GRAY}Gợi ý nhanh: Gõ 1 (Giải thích bài này) | 2 (Kiểm tra lỗi & tối ưu) | 3 (Cho bài tập tương tự) | q (Thoát){RESET}")
    print(f"{GRAY}{'─' * 54}{RESET}")

    history: list[dict] = []
    shortcuts = {
        "1": "Hãy giải thích chi tiết từng dòng code hoặc nội dung trong file đang mở một cách dễ hiểu nhất cho người mới.",
        "2": "Hãy kiểm tra xem file đang mở có lỗi nào không và gợi ý cách viết tốt hơn.",
        "3": "Hãy ra cho tôi 1 bài tập nhỏ tương tự với file đang mở (kèm gợi ý cách giải) để tôi tự luyện tập.",
    }

    while True:
        try:
            user_in = input(f"\n{MAGENTA}{BOLD}Bạn hỏi AI > {RESET}").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if not user_in:
            continue
        if user_in.lower() in ("q", "exit", "quit", "thoat"):
            break

        prompt = shortcuts.get(user_in, user_in)
        print(f"{GRAY}⏳ AI đang suy nghĩ...{RESET}")
        reply = ask_ai(prompt, context_file, history)
        print(f"\n{GREEN}{BOLD}🤖 AI:{RESET}\n{reply}")
        history.append({"role": "user", "content": prompt})
        history.append({"role": "assistant", "content": reply})

    return 0


if __name__ == "__main__":
    sys.exit(main())
