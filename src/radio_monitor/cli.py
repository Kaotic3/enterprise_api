from __future__ import annotations

import argparse
import json
import logging
from dataclasses import asdict
from pathlib import Path

from .orchestrator import run_scan
from .registry import SongRegistry
from .scraper import ScraperConfig, StationScraper

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape a radio station page to collect unique songs."
    )
    parser.add_argument("--station-name", required=True, help="Identifier for the station.")
    parser.add_argument("--url", required=True, help="Page to scrape.")
    parser.add_argument(
        "--combined-selector",
        help="CSS selector for text containing 'Artist - Title' in one element.",
    )
    parser.add_argument("--title-selector", help="CSS selector for the song title.")
    parser.add_argument("--artist-selector", help="CSS selector for the artist name.")
    parser.add_argument(
        "--history-selector",
        help="Optional CSS selector for repeated historical track rows.",
    )
    parser.add_argument(
        "--text-splitter",
        default=" - ",
        help="Separator used in the combined selector text. Defaults to ' - '.",
    )
    parser.add_argument(
        "--registry",
        type=Path,
        default=Path(".cache/radio_songs.json"),
        help="Path to persist discovered songs.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    config = ScraperConfig(
        station_name=args.station_name,
        url=args.url,
        combined_selector=args.combined_selector,
        title_selector=args.title_selector,
        artist_selector=args.artist_selector,
        history_selector=args.history_selector,
        text_splitter=args.text_splitter,
    )
    scraper = StationScraper(config)
    registry = SongRegistry(args.registry)

    result = run_scan(scraper, registry)

    payload = {
        "new_songs": [asdict(song) for song in result.new_songs],
        "existing_songs": [asdict(song) for song in result.seen_songs],
        "registry_size": len(registry),
    }

    print(json.dumps(payload, indent=2))


if __name__ == "__main__":  # pragma: no cover
    main()
