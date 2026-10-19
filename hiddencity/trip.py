"""Trip search: for one trip (e.g. DEL -> BOM on a date), find the best normal
ticket and the best hidden-city ticket.

How:
  1. Search origin -> destination. That gives every normal ticket.
  2. Search origin -> a few cities *beyond* the destination. Any of those tickets
     whose first stop is our destination is a hidden-city ticket: you get off there.
  3. Put them side by side.
"""

from concurrent.futures import ThreadPoolExecutor

from hiddencity import airports, client, config, parse


def choose_beyond_cities(origin, destination, limit):
    """Pick the cities most likely to have connections through `destination`.

    First, cities where our cache has already seen a ticket from this origin
    stopping at the destination (most often first). Then cities that lie
    geographically beyond the destination.
    """
    seen_count = {}
    for city, date in client.cached_searches(origin):
        if city == destination:
            continue
        data = client.load_cached(origin, city, date)
        for row in parse.parse_itineraries(data, city, date):
            if row["stops"] > 0 and row["first_stop"] == destination:
                seen_count[city] = seen_count.get(city, 0) + 1

    ranked = sorted(seen_count, key=seen_count.get, reverse=True)
    for city in airports.beyond(origin, destination):
        if city not in ranked:
            ranked.append(city)

    chosen = [c for c in ranked if c not in (origin, destination) and c in airports.AIRPORTS]
    return chosen[:limit]


def default_beyond_limit(destination):
    if destination in airports.HUBS:
        return config.MAX_BEYOND_SEARCHES
    return config.MAX_BEYOND_SEARCHES_SMALL_AIRPORT


def split_tickets(rows, destination):
    """Sort tickets into normal ones (that end at the destination) and hidden-city ones."""
    normal = []
    hidden = []
    for row in rows:
        if row["final_destination"] == destination:
            normal.append(row)
        elif row["stops"] > 0 and row["first_stop"] == destination:
            hidden.append(row)
    normal.sort(key=lambda r: r["price"])
    hidden.sort(key=lambda r: r["price"])
    return normal, hidden


def compare(normal, hidden):
    """The headline: best of each, and how much hidden-city saves (if anything)."""
    best_normal = normal[0] if normal else None
    best_hidden = hidden[0] if hidden else None

    saving = None
    if best_normal and best_hidden and best_hidden["price"] < best_normal["price"]:
        saving = best_normal["price"] - best_hidden["price"]

    if best_hidden and (best_normal is None or best_hidden["price"] < best_normal["price"]):
        best_overall = "hidden"
    elif best_normal:
        best_overall = "normal"
    else:
        best_overall = None

    return {
        "best_normal": best_normal,
        "best_hidden": best_hidden,
        "best_overall": best_overall,
        "saving": saving,
        "saving_pct": round(100 * saving / best_normal["price"], 1) if saving else None,
    }


def find_trip(origin, destination, date, api_key, include_hidden=True, max_beyond=None):
    """Run the whole trip search. Returns a dict ready to show on the page.

    Prices are kept current: saved answers older than LIVE_MAX_AGE_HOURS are
    searched again.
    """
    if max_beyond is None:
        max_beyond = default_beyond_limit(destination)

    cities = [destination]
    if include_hidden:
        cities += choose_beyond_cities(origin, destination, max_beyond)

    already_cached = [c for c in cities if client.fresh_copy(origin, c, date, live=True)]

    def fetch(city):
        try:
            return city, client.fetch_flights(origin, city, date, api_key, live=True), None
        except (client.SearchError, client.HourlyLimitReached) as e:
            return city, None, str(e)

    # Run the searches side by side, so 7 searches take a few seconds, not a minute.
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(fetch, cities))

    rows = []
    problems = []
    for city, data, error in results:
        if error:
            problems.append(f"{origin}->{city}: {error}")
        else:
            rows.extend(parse.parse_itineraries(data, city, date))

    # How old is the oldest price we're showing? (0 for brand-new searches.)
    ages = []
    for city in cities:
        path = client.fresh_copy(origin, city, date, live=True)
        if path:
            ages.append(client.age_hours(path))

    normal, hidden = split_tickets(rows, destination)
    return {
        "origin": origin,
        "destination": destination,
        "date": date,
        "cities_searched": cities,
        "live_searches": len(cities) - len(already_cached) - len(problems),
        "cached_searches": len(already_cached),
        "problems": problems,
        "prices_age_minutes": round(max(ages) * 60) if ages else None,
        "normal": normal,
        "hidden": hidden,
        **compare(normal, hidden),
    }
