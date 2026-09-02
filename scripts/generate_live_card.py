"""CLI: regenerate state-live rag_live_card.md from bot repo."""

from __future__ import annotations

import argparse
from pathlib import Path

from authority.live_card import write_live_card
from authority.manifest import resolve_bot_root


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate sniper-bot live card")
    parser.add_argument("--bot-repo", default=None)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/authority/rag_live_card.md"),
    )
    args = parser.parse_args()
    bot = resolve_bot_root(args.bot_repo)
    path = write_live_card(bot, args.out)
    print(f"Wrote {path}")


if __name__ == "__main__":
    main()
