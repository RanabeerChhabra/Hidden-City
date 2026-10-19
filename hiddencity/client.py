"""Talks to SerpApi.

Every answer is saved to disk (the cache) and every paid search is logged,
so we never pay twice for the same search and always know how many we've used.
"""

import json
import os
import time
from datetime import datetime, timedelta, timezone

import requests
from dotenv import load_dotenv

from hiddencity import config

SEARCH_URL = "https://serpapi.com/search.json"
ACCOUNT_URL = "https://serpapi.com/account.json"

# SerpApi sends this as an "error" when a route simply has no flights.
# That is a real answer, so we cache it instead of searching again.
NO_RESULTS_MESSAGE = "hasn't returned any results"


class SearchError(Exception):
    """A search failed (network problem, bad key, ...). Safe to retry later."""


class HourlyLimitReached(Exception):
    """We've used our hourly allowance. Run again later; the cache keeps our progress."""


def get_api_key():
    load_dotenv(config.ROOT / ".env")
    key = os.getenv("SERPAPI_KEY")
    if not key:
        raise SystemExit("SERPAPI_KEY is missing. Copy .env.example to .env and add your key.")
    return key


def cache_path(origin, destination, date, folder=None):
    folder = folder or config.CACHE_DIR
    return folder / f"{origin}-{destination}-{date}.json"


def live_folder():
    """Where website searches are saved, apart from the research snapshot."""
    return config.CACHE_DIR / "live"


def is_cached(origin, destination, date):
    return cache_path(origin, destination, date).exists()


def load_cached(origin, destination, date):
    path = cache_path(origin, destination, date)
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def age_hours(path):
    return (time.time() - path.stat().st_mtime) / 3600


def fresh_copy(origin, destination, date, live):
    """Path to a saved answer we're allowed to reuse, or None.

    Research (live=False): any saved answer, however old. The scan is a snapshot.
    Website (live=True): only answers younger than LIVE_MAX_AGE_HOURS, because
    people expect today's prices. Checks the website's own folder and the
    research cache, so a scan from this morning still saves searches.
    """
    if not live:
        path = cache_path(origin, destination, date)
        return path if path.exists() else None
    for folder in (live_folder(), config.CACHE_DIR):
        path = cache_path(origin, destination, date, folder)
        if path.exists() and age_hours(path) < config.LIVE_MAX_AGE_HOURS:
            return path
    return None


def log_search(origin, destination, date, status):
    """Append one line to the search log so we can count what we've used."""
    config.CACHE_DIR.mkdir(exist_ok=True)
    entry = {
        "time": datetime.now(timezone.utc).isoformat(),
        "origin": origin,
        "destination": destination,
        "date": date,
        "status": status,
    }
    with open(config.SEARCH_LOG, "a") as f:
        f.write(json.dumps(entry) + "\n")


def searches_in_last_hour():
    if not config.SEARCH_LOG.exists():
        return 0
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)
    count = 0
    with open(config.SEARCH_LOG) as f:
        for line in f:
            entry = json.loads(line)
            if datetime.fromisoformat(entry["time"]) > one_hour_ago:
                count += 1
    return count


def hide_key(text, api_key):
    """Error messages from `requests` can contain the full URL, key included."""
    return text.replace(api_key, "***")


def fetch_flights(origin, destination, date, api_key, live=False):
    """Return SerpApi's answer for a one-way search. Uses a saved answer when it can.

    live=True is for the website: old answers are searched again, and new ones are
    saved in cache/live/ so the research snapshot is never overwritten.
    """
    saved = fresh_copy(origin, destination, date, live)
    if saved is not None:
        with open(saved) as f:
            return json.load(f)

    limit = config.LIVE_HOURLY_LIMIT if live else config.HOURLY_LIMIT
    if searches_in_last_hour() >= limit:
        raise HourlyLimitReached(f"{limit} searches used in the last hour.")

    params = {
        "engine": "google_flights",
        "departure_id": origin,
        "arrival_id": destination,
        "outbound_date": date,
        "type": "2",  # one-way
        "currency": "INR",
        "hl": "en",
        "gl": "in",
        "api_key": api_key,
    }
    try:
        response = requests.get(SEARCH_URL, params=params, timeout=60)
        data = response.json()
    except (requests.RequestException, ValueError) as e:
        log_search(origin, destination, date, "failed")
        raise SearchError(hide_key(str(e), api_key)) from None

    error = data.get("error")
    if error and NO_RESULTS_MESSAGE not in error:
        log_search(origin, destination, date, "error")
        raise SearchError(error)

    folder = live_folder() if live else config.CACHE_DIR
    folder.mkdir(parents=True, exist_ok=True)
    with open(cache_path(origin, destination, date, folder), "w") as f:
        json.dump(data, f, indent=2)
    log_search(origin, destination, date, "ok")
    return data


def account_status(api_key):
    """Plan name and searches left this month. Checking this is free."""
    response = requests.get(ACCOUNT_URL, params={"api_key": api_key}, timeout=30)
    return response.json()


def cached_searches(origin):
    """Every (destination, date) we have a saved answer for, from this origin."""
    found = []
    for path in sorted(config.CACHE_DIR.glob(f"{origin}-*.json")):
        # File names look like DEL-BOM-2026-11-18.json
        _, destination, date = path.stem.split("-", 2)
        found.append((destination, date))
    return found
