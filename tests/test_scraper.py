from radio_monitor.scraper import ScraperConfig, StationScraper


def test_parse_current_song_with_combined_selector():
    html = """
    <html><body>
    <div id="now-playing">Artist Name - Track Title</div>
    </body></html>
    """
    config = ScraperConfig(
        station_name="Test FM", url="http://example.com", combined_selector="#now-playing"
    )
    scraper = StationScraper(config)

    song = scraper.parse_current_song(html)
    assert song.title == "Track Title"
    assert song.artist == "Artist Name"
    assert song.station == "Test FM"


def test_parse_current_song_with_split_selectors():
    html = """
    <div class="title">Lonely Boy</div>
    <div class="artist">The Black Keys</div>
    """
    config = ScraperConfig(
        station_name="Test FM",
        url="http://example.com",
        title_selector=".title",
        artist_selector=".artist",
    )
    scraper = StationScraper(config)

    song = scraper.parse_current_song(html)
    assert song.title == "Lonely Boy"
    assert song.artist == "The Black Keys"
    assert song.station == "Test FM"


def test_parse_history_rows():
    html = """
    <div class="history">
      <div class="row"><span class="title">Song A</span> - <span class="artist">Artist A</span></div>
      <div class="row"><span class="title">Song B</span> - <span class="artist">Artist B</span></div>
    </div>
    """
    config = ScraperConfig(
        station_name="Test FM",
        url="http://example.com",
        title_selector=".title",
        artist_selector=".artist",
        history_selector=".row",
    )
    scraper = StationScraper(config)

    songs = list(scraper.parse_history(html))
    assert len(songs) == 2
    assert songs[0].title == "Song A"
    assert songs[0].artist == "Artist A"
    assert songs[1].title == "Song B"
    assert songs[1].artist == "Artist B"
