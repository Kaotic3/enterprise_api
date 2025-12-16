from radio_monitor.models import Song
from radio_monitor.orchestrator import run_scan
from radio_monitor.registry import SongRegistry
from radio_monitor.scraper import ScraperConfig, StationScraper


class DummyScraper(StationScraper):
    def __init__(self):
        config = ScraperConfig(
            station_name="Test FM",
            url="http://example.com",
            combined_selector="#unused",
        )
        config.validate()
        self.config = config
        self.parsed = False

    def fetch_page(self) -> str:
        return "<html></html>"

    def parse_current_song(self, html: str) -> Song:  # type: ignore[override]
        self.parsed = True
        return Song(title="Song One", artist="Artist", station="Test FM")

    def parse_history(self, html: str):  # type: ignore[override]
        return [Song(title="Song Two", artist="Artist", station="Test FM")]


def test_run_scan_collects_new_songs():
    scraper = DummyScraper()
    registry = SongRegistry()

    result = run_scan(scraper, registry)

    assert scraper.parsed is True
    assert len(result.new_songs) == 2
    assert registry.songs == set(result.new_songs)

    # Running again should mark as seen
    result2 = run_scan(scraper, registry)
    assert len(result2.new_songs) == 0
    assert len(result2.seen_songs) == 2
