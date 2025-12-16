from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Song:
    """Represents a song identified from a station page."""

    title: str
    artist: str
    station: str

    def normalized(self) -> "Song":
        """Return a lowercased version useful for comparisons."""
        return Song(title=self.title.lower(), artist=self.artist.lower(), station=self.station)
