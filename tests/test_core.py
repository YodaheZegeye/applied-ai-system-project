"""
Tests for the actual application code:
  - _extract_json()   in src/agent.py    — parses Gemini responses robustly
  - get_client()      in src/agent.py    — raises clearly when API key is missing
  - _parse_itunes_results() in src/itunes.py — cleans raw iTunes API responses
"""

import pytest
from src.agent import _extract_json, get_client
from src.itunes import _parse_itunes_results


# ---------------------------------------------------------------------------
# _extract_json — the function that pulls JSON out of Gemini responses
# ---------------------------------------------------------------------------

def test_extract_json_clean_string():
    result = _extract_json('{"genre": "pop", "mood": "happy"}')
    assert result == {"genre": "pop", "mood": "happy"}


def test_extract_json_wrapped_in_code_block():
    text = '```json\n{"genre": "lofi", "mood": "chill"}\n```'
    result = _extract_json(text)
    assert result["genre"] == "lofi"


def test_extract_json_embedded_in_prose():
    text = 'Here is my answer: {"genre": "rock", "mood": "intense"} as requested.'
    result = _extract_json(text)
    assert result["genre"] == "rock"


def test_extract_json_parses_array():
    text = '[{"index": 1, "reason": "great song"}, {"index": 2, "reason": "fits well"}]'
    result = _extract_json(text)
    assert isinstance(result, list)
    assert len(result) == 2
    assert result[0]["index"] == 1


def test_extract_json_raises_on_garbage_input():
    with pytest.raises(ValueError):
        _extract_json("this is definitely not json at all")


def test_extract_json_handles_extra_whitespace():
    result = _extract_json('   \n  {"key": "value"}  \n  ')
    assert result == {"key": "value"}


# ---------------------------------------------------------------------------
# get_client — must raise clearly when GEMINI_API_KEY is not set
# ---------------------------------------------------------------------------

def test_get_client_raises_without_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="GEMINI_API_KEY"):
        get_client()


# ---------------------------------------------------------------------------
# _parse_itunes_results — cleans and structures raw iTunes API responses
# ---------------------------------------------------------------------------

def _make_itunes_song(**overrides):
    base = {
        "kind": "song",
        "trackName": "Test Song",
        "artistName": "Test Artist",
        "primaryGenreName": "Pop",
        "collectionName": "Test Album",
        "artworkUrl100": "https://example.com/100x100bb.jpg",
        "previewUrl": "https://example.com/preview.m4a",
        "trackViewUrl": "https://music.apple.com/track/1",
    }
    base.update(overrides)
    return base


def test_parse_itunes_returns_songs():
    result = _parse_itunes_results([_make_itunes_song()])
    assert len(result) == 1
    assert result[0]["title"] == "Test Song"
    assert result[0]["artist"] == "Test Artist"


def test_parse_itunes_filters_out_non_songs():
    raw = [
        _make_itunes_song(),
        _make_itunes_song(kind="music-video", trackName="A Video"),
        _make_itunes_song(kind="podcast", trackName="A Podcast"),
    ]
    result = _parse_itunes_results(raw)
    assert len(result) == 1
    assert result[0]["title"] == "Test Song"


def test_parse_itunes_upgrades_artwork_resolution():
    raw = [_make_itunes_song(artworkUrl100="https://example.com/100x100bb.jpg")]
    result = _parse_itunes_results(raw)
    assert "300x300bb" in result[0]["artwork_url"]
    assert "100x100bb" not in result[0]["artwork_url"]


def test_parse_itunes_handles_missing_fields_gracefully():
    result = _parse_itunes_results([{"kind": "song"}])
    assert result[0]["title"] == "Unknown"
    assert result[0]["artist"] == "Unknown"
    assert result[0]["genre"] == "Unknown"
    assert result[0]["artwork_url"] == ""
    assert result[0]["preview_url"] == ""


def test_parse_itunes_empty_list_returns_empty():
    assert _parse_itunes_results([]) == []


def test_parse_itunes_no_artwork_upgrade_when_blank():
    result = _parse_itunes_results([_make_itunes_song(artworkUrl100="")])
    assert result[0]["artwork_url"] == ""
