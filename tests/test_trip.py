import json

import pytest

from hiddencity import config, trip
from tests.helpers import itinerary, leg, row


def test_split_tickets():
    rows = [
        row("DEL", "BOM", "BOM", 7000),  # normal, direct
        row("DEL", "AMD", "BOM", 6500),  # normal, connecting
        row("DEL", "BOM", "GOI", 5000),  # hidden city: get off at BOM
        row("DEL", "HYD", "GOI", 4000),  # irrelevant: stops at HYD
    ]
    normal, hidden = trip.split_tickets(rows, "BOM")
    assert [r["price"] for r in normal] == [6500, 7000]
    assert [r["price"] for r in hidden] == [5000]


def test_compare_hidden_wins():
    result = trip.compare([row("DEL", "BOM", "BOM", 7000)], [row("DEL", "BOM", "GOI", 5000)])
    assert result["best_overall"] == "hidden"
    assert result["saving"] == 2000
    assert result["saving_pct"] == 28.6


def test_compare_normal_wins():
    result = trip.compare([row("DEL", "BOM", "BOM", 5000)], [row("DEL", "BOM", "GOI", 6000)])
    assert result["best_overall"] == "normal"
    assert result["saving"] is None


def test_compare_nothing_found():
    result = trip.compare([], [])
    assert result["best_overall"] is None


@pytest.fixture
def temp_cache(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "SEARCH_LOG", tmp_path / "search_log.jsonl")
    return tmp_path


def test_choose_beyond_prefers_cities_seen_routing_through_hub(temp_cache):
    goa = {"best_flights": [itinerary(9000, leg("DEL", "BOM"), leg("BOM", "GOI"))]}
    (temp_cache / "DEL-GOI-2026-11-18.json").write_text(json.dumps(goa))

    chosen = trip.choose_beyond_cities("DEL", "BOM", 3)
    assert chosen[0] == "GOI"
    assert "BOM" not in chosen and "DEL" not in chosen
    assert len(chosen) == 3


def test_find_trip_uses_cache_only(temp_cache):
    bom = {"best_flights": [itinerary(7000, leg("DEL", "BOM"))]}
    goa = {"best_flights": [itinerary(5000, leg("DEL", "BOM"), leg("BOM", "GOI"))]}
    (temp_cache / "DEL-BOM-2026-11-18.json").write_text(json.dumps(bom))
    (temp_cache / "DEL-GOI-2026-11-18.json").write_text(json.dumps(goa))

    result = trip.find_trip("DEL", "BOM", "2026-11-18", "key", max_beyond=1)
    assert result["cities_searched"] == ["BOM", "GOI"]
    assert result["live_searches"] == 0
    assert result["best_overall"] == "hidden"
    assert result["saving"] == 2000
