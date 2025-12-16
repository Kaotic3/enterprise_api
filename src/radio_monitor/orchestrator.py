from __future__ import annotations

import logging
from typing import Iterable, Sequence

from .models import Song
from .registry import SongRegistry
from .scraper import StationScraper

logger = logging.getLogger(__name__)


class ScanResult:
    def __init__(self, new_songs: Sequence[Song], seen_songs: Sequence[Song]) -> None:
        self.new_songs = list(new_songs)
        self.seen_songs = list(seen_songs)


def run_scan(scraper: StationScraper, registry: SongRegistry) -> ScanResult:
    """
    Fetch the station page, parse current and historical songs, and store unique entries.
    """
    html = scraper.fetch_page()
    discovered: list[Song] = []

    try:
        discovered.append(scraper.parse_current_song(html))
    except Exception as exc:  # noqa: BLE001 - top-level diagnostic
        logger.error("Failed to parse current song: %s", exc)

    for song in scraper.parse_history(html):
        discovered.append(song)

    new: list[Song] = []
    existing: list[Song] = []
    for song in discovered:
        if registry.add(song):
            new.append(song)
        else:
            existing.append(song)

    return ScanResult(new_songs=new, seen_songs=existing)
