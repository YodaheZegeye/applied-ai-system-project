"""
iTunes Search API client.
Searches Apple's worldwide music catalog — no API key required.
"""

import json
import logging
import urllib.parse
import urllib.request
from typing import List, Dict

logger = logging.getLogger(__name__)

_SEARCH_URL = "https://itunes.apple.com/search"


def search_songs(query: str, limit: int = 30) -> List[Dict]:
    """
    Search the iTunes worldwide catalog.
    Returns a list of song dicts with title, artist, genre, artwork, preview URL.
    """
    params = urllib.parse.urlencode({
        "term": query,
        "media": "music",
        "entity": "song",
        "limit": limit,
    })
    url = f"{_SEARCH_URL}?{params}"
    logger.info(f"iTunes search | query='{query}' limit={limit}")

    req = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.URLError as e:
        raise RuntimeError(f"iTunes API unreachable: {e}") from e
    except json.JSONDecodeError as e:
        raise RuntimeError(f"iTunes returned unexpected response: {e}") from e

    raw = [r for r in data.get("results", []) if r.get("kind") == "song"]
    logger.info(f"iTunes returned {len(raw)} songs")

    return _parse_itunes_results(raw)


def _parse_itunes_results(raw: list) -> List[Dict]:
    """Convert raw iTunes API result dicts into clean song dicts."""
    songs = []
    for item in raw:
        if item.get("kind") != "song":
            continue
        artwork = item.get("artworkUrl100", "")
        if artwork:
            artwork = artwork.replace("100x100bb", "300x300bb")
        songs.append({
            "title":       item.get("trackName", "Unknown"),
            "artist":      item.get("artistName", "Unknown"),
            "genre":       item.get("primaryGenreName", "Unknown"),
            "album":       item.get("collectionName", ""),
            "artwork_url": artwork,
            "preview_url": item.get("previewUrl", ""),
            "track_url":   item.get("trackViewUrl", ""),
        })
    return songs
