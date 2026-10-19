import os

os.environ.setdefault("SERPAPI_KEY", "test-key")  # app.py reads the key when imported

import app as webapp  # noqa: E402

webapp.searches_left = lambda: None  # don't call SerpApi during tests
client = webapp.app.test_client()


def test_home_page_loads():
    response = client.get("/")
    assert response.status_code == 200
    assert b"HIDDEN CITY" in response.data


def test_rejects_same_airport():
    response = client.post("/api/search", json={"origin": "DEL", "destination": "DEL", "date": "2099-01-01"})
    assert response.status_code == 400


def test_rejects_unknown_airport():
    response = client.post("/api/search", json={"origin": "XXX", "destination": "BOM", "date": "2099-01-01"})
    assert response.status_code == 400


def test_rejects_past_date():
    response = client.post("/api/search", json={"origin": "DEL", "destination": "BOM", "date": "2020-01-01"})
    assert response.status_code == 400
