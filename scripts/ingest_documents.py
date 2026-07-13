"""CLI: ingest processed chunks from data/processed/ into Qdrant."""

import argparse

from retriever.chunk_loader import ingest_processed_chunks


def main() -> None:
    parser = argparse.ArgumentParser(description="Index processed chunks into Qdrant")
    parser.add_argument(
        "--source",
        choices=["kubernetes", "docker", "all"],
        default="all",
        help="Which chunk file(s) to index",
    )
    args = parser.parse_args()

    source = None if args.source == "all" else args.source
    total = ingest_processed_chunks(source=source)
    print(f"\nDone. Indexed {total} chunks total.")


if __name__ == "__main__":
    main()
