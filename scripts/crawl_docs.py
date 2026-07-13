"""CLI: crawl Kubernetes and Docker documentation."""

import argparse
from dataclasses import replace

from crawler.config import SOURCES, CrawlSettings
from crawler.crawl import crawl_source


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Crawl free public docs (Kubernetes + Docker) into data/raw/"
    )
    parser.add_argument(
        "--source",
        choices=["kubernetes", "docker", "all"],
        default="all",
        help="Which documentation source to crawl",
    )
    parser.add_argument(
        "--max-pages",
        type=int,
        default=None,
        help="Override max pages per source (default: 100)",
    )
    args = parser.parse_args()

    settings = CrawlSettings()
    names = list(SOURCES) if args.source == "all" else [args.source]

    for name in names:
        source = SOURCES[name]
        if args.max_pages is not None:
            source = replace(source, max_pages=args.max_pages)

        print(f"\n=== Crawling {name} (max {source.max_pages} pages) ===")
        manifest = crawl_source(source, settings)
        print(f"Saved {manifest['page_count']} pages to data/raw/html/{name}/")
        print(f"Manifest: data/raw/{name}_manifest.json")

    if args.source == "all":
        print("\nCrawled both kubernetes and docker.")
    print("Next: py -m scripts.process_docs --source all")


if __name__ == "__main__":
    main()
