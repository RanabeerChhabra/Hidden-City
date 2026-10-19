import os

import pytest

os.environ.setdefault("SERPAPI_KEY", "test-key")  # app.py reads the key when imported

import app as webapp  # noqa: E402
from hiddencity import config, trip  # noqa: E402

client = webapp.app.test_client()
TRIP = {"origin": "DEL", "destination": "BOM", "date": "2099-01-01"}


@pytest.fixture(autouse=True)
def no_real_api(monkeypatch):
    """Never call SerpApi from tests, and start every test with a clean slate."""
    monkeypatch.setattr(webapp, "searches_left", lambda: 200)
    monkeypatch.setattr(trip, "live_searches_needed", lambda *args, **kwargs: 1)
    monkeypatch.setattr(trip, "find_trip", fake_find_trip)
    webapp.visitor_usage.clear()


def fake_find_trip(origin, destination, date, api_key, include_hidden=True):
    return {"live_searches": 1, "normal": [], "hidden": []}


def test_root_redirects_to_hiddencity():
    response = client.get("/")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/hiddencity/")


def test_home_page_loads():
    response = client.get("/hiddencity/")
    assert response.status_code == 200
    assert b"HIDDEN CITY" in response.data
    assert b"/hiddencity/static/style.css" in response.data


def test_static_files_served_under_prefix():
    assert client.get("/hiddencity/static/style.css").status_code == 200


def test_rejects_same_airport():
    response = client.post("/hiddencity/api/search", json={**TRIP, "destination": "DEL"})
    assert response.status_code == 400


def test_rejects_unknown_airport():
    response = client.post("/hiddencity/api/search", json={**TRIP, "origin": "XXX"})
    assert response.status_code == 400


def test_rejects_past_date():
    response = client.post("/hiddencity/api/search", json={**TRIP, "date": "2020-01-01"})
    assert response.status_code == 400


def test_search_works():
    response = client.post("/hiddencity/api/search", json=TRIP)
    assert response.status_code == 200
    assert response.get_json()["visitor_searches_left"] == config.VISITOR_DAILY_SEARCHES - 1


def test_visitor_daily_limit(monkeypatch):
    monkeypatch.setattr(config, "VISITOR_DAILY_SEARCHES", 2)
    assert client.post("/hiddencity/api/search", json=TRIP).status_code == 200
    assert client.post("/hiddencity/api/search", json=TRIP).status_code == 200
    assert client.post("/hiddencity/api/search", json=TRIP).status_code == 429


def test_stops_when_monthly_budget_is_low(monkeypatch):
    monkeypatch.setattr(webapp, "searches_left", lambda: config.BUDGET_RESERVE)
    assert client.post("/hiddencity/api/search", json=TRIP).status_code == 503


def test_saved_searches_still_work_when_budget_is_low(monkeypatch):
    monkeypatch.setattr(webapp, "searches_left", lambda: 0)
    monkeypatch.setattr(trip, "live_searches_needed", lambda *args, **kwargs: 0)
    assert client.post("/hiddencity/api/search", json=TRIP).status_code == 200
