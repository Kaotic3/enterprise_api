# enterprise_api

Initial scaffolding for a radio-station scraping utility that will feed missing
tracks into Lidarr.

## Quickstart

Run a one-off scan using CSS selectors from the target site:
```bash
python -m radio_monitor.cli \
  --station-name "My Station" \
  --url "https://example.com/now-playing" \
  --combined-selector "#now-playing"
```

The command prints JSON describing which songs were newly discovered and
persists the registry to `.cache/radio_songs.json` by default. Use
`--title-selector` and `--artist-selector` if the site exposes separate fields
instead of a combined "Artist - Title" element. You can also supply a
`--history-selector` to harvest any recent track list shown on the page.
