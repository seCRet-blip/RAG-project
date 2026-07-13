"""CLI: inspect processed chunks — useful for learning what the pipeline produced."""

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser(description="Preview chunks from the processing pipeline")
    parser.add_argument("--source", choices=["kubernetes", "docker"], default="docker")
    parser.add_argument("--limit", type=int, default=3, help="Number of chunks to preview")
    parser.add_argument("--search", type=str, default=None, help="Filter chunks containing text")
    args = parser.parse_args()

    chunks_path = Path(f"data/processed/chunks/{args.source}/chunks.jsonl")
    if not chunks_path.exists():
        print(f"No chunks found at {chunks_path}")
        print("Run: python -m scripts.crawl_docs && python -m scripts.process_docs")
        return

    shown = 0
    with chunks_path.open(encoding="utf-8") as f:
        for line in f:
            chunk = json.loads(line)
            if args.search and args.search.lower() not in chunk["text"].lower():
                continue

            print("-" * 72)
            print(f"ID:      {chunk['chunk_id']}")
            print(f"Title:   {chunk['title']}")
            print(f"Section: {chunk['section']}")
            print(f"URL:     {chunk['url']}")
            print(f"Chars:   {chunk['char_count']}")
            preview = chunk["text"][:400].replace("\n", " ")
            print(f"Text:    {preview}...")

            shown += 1
            if shown >= args.limit:
                break

    if shown == 0:
        print("No matching chunks found.")
    else:
        print(f"\nShowed {shown} chunk(s) from {chunks_path}")


if __name__ == "__main__":
    main()
