"""CLI: run extract → clean → chunk on crawled data."""

import argparse
from pathlib import Path

from processing.pipeline import DataPipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Process crawled HTML through extract, clean, and chunk stages"
    )
    parser.add_argument(
        "--source",
        choices=["kubernetes", "docker", "all"],
        default="all",
        help="Which source to process",
    )
    parser.add_argument(
        "--stage",
        choices=["extract", "clean", "chunk", "all"],
        default="all",
        help="Run a single stage or the full pipeline",
    )
    args = parser.parse_args()

    pipeline = DataPipeline()
    names = ["kubernetes", "docker"] if args.source == "all" else [args.source]

    for name in names:
        print(f"\n=== Processing {name} (stage={args.stage}) ===")
        result = pipeline.run(source_name=name, stage=args.stage)
        print(f"  extracted: {result.extracted_count} docs")
        print(f"  cleaned:   {result.cleaned_count} docs")
        print(f"  chunks:    {result.chunk_count} chunks")
        print(f"  output:    data/processed/chunks/{name}/chunks.jsonl")


if __name__ == "__main__":
    main()
