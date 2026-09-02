"""Load and resolve ingest_manifest.yaml."""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_MANIFEST = ROOT / "ingest_manifest.yaml"


def resolve_bot_root(explicit: str | Path | None = None) -> Path:
    raw = explicit or os.getenv("BOT_REPO_ROOT") or ""
    if not raw:
        try:
            from backend.core.config import Settings

            raw = Settings().bot_repo_root
        except Exception:
            raw = ""
    if not raw:
        raise ValueError(
            "BOT_REPO_ROOT is not set. Add it to .env or pass --bot-repo."
        )
    path = Path(raw).expanduser().resolve()
    if not path.is_dir():
        raise FileNotFoundError(f"Bot repo not found: {path}")
    return path


def load_manifest(path: Path | None = None) -> dict[str, Any]:
    manifest_path = path or DEFAULT_MANIFEST
    text = manifest_path.read_text(encoding="utf-8")
    # Allow ${ENV} substitution
    text = re.sub(
        r"\$\{([A-Z0-9_]+)\}",
        lambda m: os.getenv(m.group(1), m.group(0)),
        text,
    )
    data = yaml.safe_load(text)
    if not isinstance(data, dict):
        raise ValueError("Manifest must be a YAML mapping")
    return data
