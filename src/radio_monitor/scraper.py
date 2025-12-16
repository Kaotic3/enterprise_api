from __future__ import annotations

import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Callable, Iterable, Optional

from .models import Song


def _clean_text(text: str | None) -> str:
    return text.strip() if text else ""


class _Node:
    def __init__(self, tag: str, attrs: dict[str, str]):
        self.tag = tag
        self.attrs = attrs
        self.children: list["_Node"] = []
        self._text_fragments: list[str] = []

    def add_child(self, child: "_Node") -> None:
        self.children.append(child)

    def add_text(self, text: str) -> None:
        if text:
            self._text_fragments.append(text)

    def all_text(self) -> str:
        parts = list(self._text_fragments)
        for child in self.children:
            parts.append(child.all_text())
        return "".join(parts)


class _DOMBuilder(HTMLParser):
    def __init__(self):
        super().__init__()
        self.root = _Node("document", {})
        self._stack: list[_Node] = [self.root]

    def handle_starttag(self, tag: str, attrs) -> None:  # type: ignore[override]
        node = _Node(tag, {key: value for key, value in attrs})
        self._stack[-1].add_child(node)
        self._stack.append(node)

    def handle_startendtag(self, tag: str, attrs) -> None:  # type: ignore[override]
        node = _Node(tag, {key: value for key, value in attrs})
        self._stack[-1].add_child(node)

    def handle_endtag(self, tag: str) -> None:  # type: ignore[override]
        # Pop until we find the matching tag or reach the root.
        for idx in range(len(self._stack) - 1, 0, -1):
            if self._stack[idx].tag == tag:
                del self._stack[idx:]
                break

    def handle_data(self, data: str) -> None:  # type: ignore[override]
        self._stack[-1].add_text(data)


def _matches_selector(node: _Node, selector: str) -> bool:
    if selector.startswith("#"):
        return node.attrs.get("id") == selector[1:]
    if selector.startswith("."):
        classes = node.attrs.get("class", "").split()
        return selector[1:] in classes
    return node.tag == selector


def _find_first(node: _Node, selector: str) -> _Node | None:
    if _matches_selector(node, selector):
        return node
    for child in node.children:
        found = _find_first(child, selector)
        if found:
            return found
    return None


def _find_all(node: _Node, selector: str) -> list[_Node]:
    results: list[_Node] = []
    if _matches_selector(node, selector):
        results.append(node)
    for child in node.children:
        results.extend(_find_all(child, selector))
    return results


def _parse_html(html: str) -> _Node:
    parser = _DOMBuilder()
    parser.feed(html)
    parser.close()
    return parser.root


@dataclass(slots=True)
class ScraperConfig:
    """
    Configuration for extracting song information from a station page.

    The configuration supports either a combined selector (e.g. "Artist - Title")
    or separate selectors for artist and title content. Selectors support simple
    CSS-style syntax: tag names (`div`), class names (`.class-name`), or IDs
    (`#element-id`).
    """

    station_name: str
    url: str
    combined_selector: str | None = None
    title_selector: str | None = None
    artist_selector: str | None = None
    history_selector: str | None = None
    text_splitter: str = " - "
    postprocess: Optional[Callable[[Song], Song]] = None

    def validate(self) -> None:
        if not (self.combined_selector or (self.title_selector and self.artist_selector)):
            raise ValueError(
                "Provide either 'combined_selector' or both 'title_selector' and 'artist_selector'."
            )


class StationScraper:
    """Fetch and parse a station now-playing page using simple selectors."""

    def __init__(
        self,
        config: ScraperConfig,
        fetcher: Callable[[str], str] | None = None,
    ) -> None:
        config.validate()
        self.config = config
        self._fetcher = fetcher or self._default_fetcher

    def _default_fetcher(self, url: str) -> str:
        with urllib.request.urlopen(url, timeout=15) as response:  # noqa: S310 - intentional external call
            encoding = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(encoding, errors="replace")

    def fetch_page(self) -> str:
        return self._fetcher(self.config.url)

    def parse_current_song(self, html: str) -> Song:
        root = _parse_html(html)
        title, artist = self._extract_title_artist(root)
        song = Song(title=title, artist=artist, station=self.config.station_name)
        if self.config.postprocess:
            song = self.config.postprocess(song)
        return song

    def parse_history(self, html: str) -> Iterable[Song]:
        if not self.config.history_selector:
            return []

        root = _parse_html(html)
        entries: list[Song] = []
        for row in _find_all(root, self.config.history_selector):
            title, artist = self._extract_title_artist(row)
            song = Song(title=title, artist=artist, station=self.config.station_name)
            if self.config.postprocess:
                song = self.config.postprocess(song)
            entries.append(song)
        return entries

    def _extract_title_artist(self, node: _Node) -> tuple[str, str]:
        config = self.config

        if config.combined_selector:
            target = _find_first(node, config.combined_selector)
            if not target:
                raise ValueError(f"Could not find combined selector '{config.combined_selector}'")

            combined_text = _clean_text(target.all_text())
            if config.text_splitter in combined_text:
                artist, title = [
                    part.strip() for part in combined_text.split(config.text_splitter, 1)
                ]
                return title, artist

            raise ValueError(
                f"Combined selector text did not include separator '{config.text_splitter}': "
                f"'{combined_text}'"
            )

        title_el = _find_first(node, config.title_selector or "")
        artist_el = _find_first(node, config.artist_selector or "")

        if not title_el or not artist_el:
            missing = []
            if not title_el:
                missing.append(config.title_selector)
            if not artist_el:
                missing.append(config.artist_selector)
            missing_text = ", ".join(selector or "<empty>" for selector in missing)
            raise ValueError(f"Could not find selector(s): {missing_text}")

        return _clean_text(title_el.all_text()), _clean_text(artist_el.all_text())
