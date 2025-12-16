from pathlib import Path

from radio_monitor.models import Song
from radio_monitor.registry import SongRegistry


def test_registry_adds_unique_and_persists(tmp_path: Path):
    storage = tmp_path / "songs.json"
    registry = SongRegistry(storage)

    first = Song(title="Track", artist="Artist", station="Station A")
    assert registry.add(first) is True
    assert len(registry) == 1

    # Duplicate should not increase size
    assert registry.add(Song(title="track", artist="artist", station="Station A")) is False
    assert len(registry) == 1

    # Persistence check
    registry2 = SongRegistry(storage)
    assert len(registry2) == 1
    assert first in registry2
