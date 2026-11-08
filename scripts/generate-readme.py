import json
import re
import sys
from pathlib import Path
from urllib.parse import quote


ROOT = Path(__file__).resolve().parent.parent
README = ROOT / "README.md"
START = "<!-- STUDY-LIST:START -->"
END = "<!-- STUDY-LIST:END -->"
STATUS = {
    "not_started": "🟥",
    "ready": "🟧",
    "studying": "🟨",
    "completed": "🟩",
}
CATEGORIES = {"books": "book", "courses": "course"}
METADATA_PATTERN = re.compile(r"(?P<year>\d{4})/(?P<category>books|courses)/[^/]+/study\.json$")


def load_studies():
    studies = []
    for metadata_path in ROOT.glob("[0-9][0-9][0-9][0-9]/*/*/study.json"):
        relative = metadata_path.relative_to(ROOT).as_posix()
        match = METADATA_PATTERN.fullmatch(relative)
        if not match:
            raise ValueError(f"Unexpected study metadata path: {relative}")

        data = json.loads(metadata_path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            raise ValueError(f"{relative}: metadata must be a JSON object")
        title = data.get("title")
        status = data.get("status")
        if not isinstance(title, str) or not title.strip():
            raise ValueError(f"{relative}: 'title' must be a non-empty string")
        if not isinstance(status, str) or status not in STATUS:
            valid = ", ".join(STATUS)
            raise ValueError(f"{relative}: 'status' must be one of: {valid}")

        category = match.group("category")
        target = quote(metadata_path.parent.relative_to(ROOT).as_posix(), safe="/-._")
        studies.append(
            (match.group("year"), category, title.strip(), STATUS[status], target)
        )

    studies.sort(key=lambda item: (item[0], item[1] != "books", item[2].casefold()))
    return studies


def render_list(studies):
    lines = []
    current_year = None
    for year, category, title, marker, target in studies:
        if year != current_year:
            if lines:
                lines.append("")
            lines.extend((f"## {year}", ""))
            current_year = year
        safe_title = title.replace("\\", "\\\\").replace("[", "\\[").replace("]", "\\]")
        lines.append(f"- {marker} {CATEGORIES[category]} - [{safe_title}]({target}/)")
    return "\n".join(lines)


def update_readme():
    content = README.read_text(encoding="utf-8-sig")
    if content.count(START) != 1 or content.count(END) != 1:
        raise ValueError("README must contain exactly one study-list marker pair")

    start = content.index(START) + len(START)
    end = content.index(END)
    if start > end:
        raise ValueError("README study-list markers are out of order")

    generated = render_list(load_studies())
    updated = content[:start] + "\n" + generated + "\n" + content[end:]
    if updated != content:
        README.write_text(updated, encoding="utf-8", newline="\n")


if __name__ == "__main__":
    try:
        update_readme()
    except (OSError, ValueError, json.JSONDecodeError) as error:
        print(f"README generation failed: {error}", file=sys.stderr)
        sys.exit(1)
