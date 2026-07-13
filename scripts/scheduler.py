"""Monthly scheduler — runs doc sync on the 1st of each month at 03:00 UTC.

Runs inside an isolated RAG container with no published ports.
Does not touch other Docker stacks (e.g. dashboard on :8787).
"""

import time
from datetime import UTC, datetime

from scripts.sync_docs import run_sync

CHECK_HOUR_UTC = 3
CHECK_INTERVAL_SECONDS = 300


def should_run_now(last_run_month: int | None) -> bool:
    now = datetime.now(UTC)
    return now.day == 1 and now.hour == CHECK_HOUR_UTC and last_run_month != now.month


def main() -> None:
    print("RAG monthly scheduler started (1st of each month, 03:00 UTC)")
    print("No ports exposed — connects only to rag-qdrant on rag-project-net")

    last_run_month: int | None = None

    while True:
        if should_run_now(last_run_month):
            print(f"\n=== Monthly sync triggered at {datetime.now(UTC).isoformat()} ===")
            try:
                run_sync(recreate_collection=True)
                last_run_month = datetime.now(UTC).month
                print("Monthly sync complete.")
            except Exception as exc:
                print(f"Monthly sync failed: {exc}")
        time.sleep(CHECK_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
