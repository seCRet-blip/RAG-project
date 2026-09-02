"""Extract code-critical slices by symbol keywords (not whole huge files)."""

from __future__ import annotations

import re
from pathlib import Path

from authority.chunkers import _cid
from authority.models import AuthorityChunk


def _module_docstring(text: str) -> str:
    match = re.match(r'(?s)^(\s*"""(.*?)"""|\s*\'\'\'(.*?)\'\'\')', text)
    if not match:
        return ""
    return match.group(0).strip()


def _extract_symbol_blocks(text: str, symbols: list[str]) -> list[tuple[str, str]]:
    """Return (label, block) for defs/classes/assignments matching symbols."""
    lines = text.splitlines()
    found: list[tuple[str, str]] = []
    used: set[int] = set()

    for i, line in enumerate(lines):
        if i in used:
            continue
        # Match assignment or def/class containing any symbol token
        for sym in symbols:
            if sym not in line:
                continue
            if re.match(r"^(def |class |async def )", line) or re.match(
                r"^[A-Z_][A-Z0-9_]*\s*[:=]", line
            ) or re.match(r"^[a-zA-Z_][\w]*\s*=", line):
                # Collect indented block
                block_lines = [line]
                used.add(i)
                j = i + 1
                base_indent = len(line) - len(line.lstrip())
                while j < len(lines):
                    nxt = lines[j]
                    if nxt.strip() == "":
                        block_lines.append(nxt)
                        used.add(j)
                        j += 1
                        continue
                    indent = len(nxt) - len(nxt.lstrip())
                    if indent > base_indent or nxt.lstrip().startswith(("#", "@")):
                        block_lines.append(nxt)
                        used.add(j)
                        j += 1
                        continue
                    break
                found.append((sym, "\n".join(block_lines).rstrip()))
                break
    return found


def extract_code_slices(
    path: Path,
    *,
    relative: str,
    symbols: list[str],
    namespace: str = "code-critical",
    freshness: str = "repo-file",
    asset: str | None = "BOTH",
    max_chars: int = 20000,
) -> list[AuthorityChunk]:
    if not path.is_file():
        return []

    text = path.read_text(encoding="utf-8", errors="replace")
    docstring = _module_docstring(text)
    blocks = _extract_symbol_blocks(text, symbols)

    # Fallback: include lines mentioning any symbol (bounded)
    if not blocks:
        hits: list[str] = []
        for line in text.splitlines():
            if any(s in line for s in symbols):
                hits.append(line)
        if hits:
            snippet = "\n".join(hits[:80])
            blocks = [("mentions", snippet)]

    parts: list[str] = []
    if docstring:
        parts.append(f"# Module docstring\n{docstring}")
    for label, block in blocks:
        parts.append(f"# Slice: {label}\n{block}")

    combined = "\n\n".join(parts).strip()
    if not combined:
        return []
    if len(combined) > max_chars:
        combined = combined[:max_chars] + "\n\n# ... truncated to preserve meaning; see source file ..."

    header = (
        f"CODE-CRITICAL slice from `{relative}`\n"
        f"Asset scope: {asset or 'BOTH'}\n"
        f"Symbols: {', '.join(symbols)}\n\n"
    )
    return [
        AuthorityChunk(
            chunk_id=_cid(namespace, relative, "slices"),
            text=header + combined,
            namespace=namespace,
            source_path=relative,
            freshness=freshness,
            title=Path(relative).name,
            section="code-slice",
            asset=asset,  # type: ignore[arg-type]
            metadata={"symbols": symbols},
        )
    ]
