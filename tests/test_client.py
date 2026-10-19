import json
import os
import time

import pytest
import requests

from hiddencity import client, config

KEY = "secret-test-key"


@pytest.fixture(autouse=True)
def temp_cache(tmp_path, monkeypatch):
    """Point the cache at a temporary folder so tests never touch the real one."""
    monkeypatch.setattr(config, "CACHE_DIR", tmp_path)
    monkeypatch.setattr(config, "SEARCH_LOG", tmp_path / "search_log.jsonl")


class FakeResponse:
    def __init__(self, data):
        self.data = data

    def json(self):
        return self.data


def fake_get(data, calls):
    def get(url, params, timeout):
        calls.append(params)
        return FakeResponse(data)

    return get


def test_saves_answer_and_reuses_it(monkeypatch):
    calls = []
    monkeypatch.setattr(requests, "get", fake_get({"best_flights": []}, calls))

    client.fetch_flights("DEL", "BOM", "2026-11-18", KEY)
    client.fetch_flights("DEL", "BOM", "2026-11-18", KEY)

    assert len(calls) == 1  # the second call came from the cache
    assert client.is_cached("DEL", "BOM", "2026-11-18")
    assert client.searches_in_last_hour() == 1


def test_no_results_is_cached(monkeypatch):
    calls = []
    answer = {"error": "Google Flights hasn't returned any results for this query."}
    monkeypatch.setattr(requests, "get", fake_get(answer, calls))

    client.fetch_flights("DEL", "IXZ", "2026-11-18", KEY)
    assert client.is_cached("DEL", "IXZ", "2026-11-18")


def test_real_error_is_not_cached(monkeypatch):
    calls = []
    monkeypatch.setattr(requests, "get", fake_get({"error": "Invalid API key."}, calls))

    with pytest.raises(client.SearchError):
        client.fetch_flights("DEL", "BOM", "2026-11-18", KEY)
    assert not client.is_cached("DEL", "BOM", "2026-11-18")


def test_network_error_hides_key(monkeypatch):
    def broken_get(url, params, timeout):
        raise requests.ConnectionError(f"failed: /search.json?api_key={params['api_key']}")

    monkeypatch.setattr(requests, "get", broken_get)

    with pytest.raises(client.SearchError) as error:
        client.fetch_flights("DEL", "BOM", "2026-11-18", KEY)
    assert KEY not in str(error.value)


def test_stops_at_hourly_limit(monkeypatch):
    monkeypatch.setattr(config, "HOURLY_LIMIT", 2)
    calls = []
    monkeypatch.setattr(requests, "get", fake_get({"best_flights": []}, calls))

    client.fetch_flights("DEL", "BOM", "2026-11-18", KEY)
    client.fetch_flights("DEL", "GOI", "2026-11-18", KEY)
    with pytest.raises(client.HourlyLimitReached):
        client.fetch_flights("DEL", "COK", "2026-11-18", KEY)
    assert len(calls) == 2


def test_lists_cached_searches(tmp_path):
    for name in ["DEL-BOM-2026-11-18.json", "DEL-GOI-2026-11-19.json"]:
        (tmp_path / name).write_text(json.dumps({}))
    assert client.cached_searches("DEL") == [("BOM", "2026-11-18"), ("GOI", "2026-11-19")]


def make_old(path, hours):
    old = time.time() - hours * 3600
    os.utime(path, (old, old))


def test_research_cache_never_expires(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(requests, "get", fake_get({"best_flights": []}, calls))
    client.fetch_flights("DEL", "BOM", "2026-11-18", KEY)
    make_old(tmp_path / "DEL-BOM-2026-11-18.json", hours=500)

    client.fetch_flights("DEL", "BOM", "2026-11-18", KEY)
    assert len(calls) == 1


def test_website_searches_again_when_saved_answer_is_old(monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(requests, "get", fake_get({"best_flights": []}, calls))
    client.fetch_flights("DEL", "BOM", "2026-11-18", KEY)  # research snapshot
    make_old(tmp_path / "DEL-BOM-2026-11-18.json", hours=config.LIVE_MAX_AGE_HOURS + 1)

    client.fetch_flights("DEL", "BOM", "2026-11-18", KEY, live=True)
    assert len(calls) == 2
    # The fresh answer goes to cache/live/, the research file is left alone.
    assert (tmp_path / "live" / "DEL-BOM-2026-11-18.json").exists()
    assert client.age_hours(tmp_path / "DEL-BOM-2026-11-18.json") > config.LIVE_MAX_AGE_HOURS


def test_website_reuses_recent_answer(monkeypatch):
    calls = []
    monkeypatch.setattr(requests, "get", fake_get({"best_flights": []}, calls))
    client.fetch_flights("DEL", "BOM", "2026-11-18", KEY, live=True)
    client.fetch_flights("DEL", "BOM", "2026-11-18", KEY, live=True)
    assert len(calls) == 1


def test_website_can_use_searches_the_scan_leaves_free(monkeypatch):
    monkeypatch.setattr(config, "HOURLY_LIMIT", 1)
    monkeypatch.setattr(config, "LIVE_HOURLY_LIMIT", 2)
    calls = []
    monkeypatch.setattr(requests, "get", fake_get({"best_flights": []}, calls))

    client.fetch_flights("DEL", "BOM", "2026-11-18", KEY)  # scan uses its share
    with pytest.raises(client.HourlyLimitReached):
        client.fetch_flights("DEL", "GOI", "2026-11-18", KEY)
    client.fetch_flights("DEL", "COK", "2026-11-18", KEY, live=True)  # website still can
    assert len(calls) == 2
