from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path
from typing import Iterable, Set

from .models import Song


class SongRegistry:
    """
    Tracks unique songs that have been scraped from the station.

    The registry keeps both the original values and a normalized set to make
    comparisons case-insensitive.
    """

    def __init__(self, storage_path: Path | str | None = None) -> None:
        self._songs: Set[Song] = set()
        self._normalized: Set[Song] = set()
        self._storage_path = Path(storage_path) if storage_path else None

        if self._storage_path and self._storage_path.exists():
            self._load(self._storage_path)

    def add(self, song: Song) -> bool:
        """
        Add a song to the registry.

        Returns True if the song was not previously present, False otherwise.
        """
        normalized = song.normalized()
        if normalized in self._normalized:
            return False

        self._songs.add(song)
        self._normalized.add(normalized)
        self._persist()
        return True

    def extend(self, songs: Iterable[Song]) -> int:
        """Add multiple songs and return the count of new entries."""
        new_count = 0
        for song in songs:
            if self.add(song):
                new_count += 1
        return new_count

    def __contains__(self, song: Song) -> bool:  # pragma: no cover - simple delegation
        return song.normalized() in self._normalized

    def __len__(self) -> int:  # pragma: no cover - simple delegation
        return len(self._songs)

    def _persist(self) -> None:
        if not self._storage_path:
            return
        payload = [asdict(song) for song in self._songs]
        self._storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._storage_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def _load(self, path: Path) -> None:
        content = json.loads(path.read_text(encoding="utf-8"))
        for entry in content:
            song = Song(**entry)
            self._songs.add(song)
            self._normalized.add(song.normalized())

    @property
    def songs(self) -> Set[Song]:
        return set(self._songs)
