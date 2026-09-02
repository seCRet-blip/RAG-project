"""Format answers for clean HTML display."""

from __future__ import annotations

import re


def plain_text_answer(text: str) -> str:
    if not text:
        return ""

    cleaned = text.strip()
    cleaned = re.sub(r"```\w*\n?", "", cleaned)
    cleaned = cleaned.replace("```", "")
    cleaned = re.sub(r"`([^`]+)`", r"\1", cleaned)
    cleaned = re.sub(r"\*\*(.+?)\*\*", r"\1", cleaned)
    cleaned = re.sub(r"__(.+?)__", r"\1", cleaned)
    cleaned = re.sub(r"(?<!\*)\*(?!\*)(.+?)(?<!\*)\*(?!\*)", r"\1", cleaned)
    cleaned = re.sub(r"^#{1,6}\s+", "", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"^\s*[-*•]\s+", "• ", cleaned, flags=re.MULTILINE)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def answer_lines(text: str) -> list[str]:
    cleaned = plain_text_answer(text)
    if not cleaned:
        return []

    lines: list[str] = []
    for block in cleaned.split("\n\n"):
        block = block.strip()
        if not block:
            continue
        if "\n" in block:
            for line in block.split("\n"):
                if line.strip():
                    lines.append(line.rstrip())
            lines.append("")
        else:
            lines.append(block)
    while lines and lines[-1] == "":
        lines.pop()
    return lines


def line_kind(line: str) -> str:
    stripped = line.strip()
    if not stripped:
        return "spacer"
    if stripped.startswith("• ") or stripped.startswith("- "):
        return "bullet"
    if re.match(r"^\d+[.)]\s+\S", stripped):
        return "section"
    if re.match(r"^[A-Z][A-Z0-9 _/-]{2,24}:\s*$", stripped):
        return "section"
    return "body"
