from __future__ import annotations

import re


START = "<!-- research-kb:managed:start -->"
END = "<!-- research-kb:managed:end -->"


def merge_managed_content(existing: str, managed: str) -> str:
    """Insert or replace only the machine-managed block."""
    block = f"{START}\n{managed.strip()}\n{END}"
    pattern = re.compile(re.escape(START) + r".*?" + re.escape(END), re.S)
    if pattern.search(existing):
        return pattern.sub(block, existing, count=1)
    researcher_heading = re.search(r"(?m)^## 研究者笔记\s*$", existing)
    if researcher_heading:
        index = researcher_heading.start()
        return existing[:index].rstrip() + "\n\n" + block + "\n\n" + existing[index:]
    return existing.rstrip() + "\n\n" + block + "\n"
