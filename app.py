"""The web app: a search page plus one API endpoint that runs a trip search.

Everything lives under /hiddencity, so it can sit at rana.beer/hiddencity.

Run it locally with:  python app.py   then open http://localhost:5050/hiddencity/
"""

from datetime import date

import requests
from flask import Blueprint, Flask, jsonify, redirect, render_template, request

from hiddencity import airports, client, config, trip

PREFIX = "/hiddencity"

# Static files live in public/ because Vercel serves that folder straight from
# its CDN. Locally, Flask serves the same folder at the same address.
app = Flask(
    __name__,
    static_folder="public/hiddencity/static",
    static_url_path=f"{PREFIX}/static",
)
site = Blueprint("site", __name__, url_prefix=PREFIX)

API_KEY = client.get_api_key()
CITY_NAMES = {code: info[0] for code, info in airports.AIRPORTS.items()}

# How many paid searches each visitor has used today: {ip: (date, count)}.
# Kept in memory, so it resets when the server restarts. Good enough to stop
# one person accidentally using up the month; not a security barrier.
visitor_usage = {}


def suggested_date():
    """The earliest date we already have cached data for, so a first search is free."""
    today = date.today().isoformat()
    dates = sorted({d for _, d in client.cached_searches(config.ORIGIN) if d >= today})
    return dates[0] if dates else today


def searches_left():
    try:
        return client.account_status(API_KEY).get("total_searches_left")
    except requests.RequestException:
        return None


def visitor_ip():
    # Behind Vercel the visitor's address is the first one in X-Forwarded-For.
    forwarded = request.headers.get("X-Forwarded-For", "")
    return forwarded.split(",")[0].strip() or request.remote_addr or "unknown"


def used_today(ip):
    day, count = visitor_usage.get(ip, (None, 0))
    return count if day == date.today() else 0


def record_usage(ip, searches):
    visitor_usage[ip] = (date.today(), used_today(ip) + searches)


@app.get("/")
def root():
    return redirect(f"{PREFIX}/")


@site.get("/")
def home():
    airport_list = [{"code": code, "city": name} for code, name in CITY_NAMES.items()]
    airport_list.sort(key=lambda a: a["city"])
    return render_template(
        "index.html",
        airports=airport_list,
        default_date=suggested_date(),
        today=date.today().isoformat(),
        searches_left=searches_left(),
    )


@site.post("/api/search")
def search():
    body = request.get_json(silent=True) or {}
    origin = str(body.get("origin", "")).strip().upper()
    destination = str(body.get("destination", "")).strip().upper()
    when = str(body.get("date", "")).strip()
    include_hidden = bool(body.get("include_hidden", False))

    if origin not in CITY_NAMES or destination not in CITY_NAMES:
        return jsonify(error="Pick airports from the list."), 400
    if origin == destination:
        return jsonify(error="From and To can't be the same airport."), 400
    try:
        if date.fromisoformat(when) < date.today():
            return jsonify(error="Pick a date in the future."), 400
    except ValueError:
        return jsonify(error="Pick a date."), 400

    # Budget checks, before spending anything.
    needed = trip.live_searches_needed(origin, destination, when, include_hidden)
    ip = visitor_ip()
    left = None
    if needed:
        if used_today(ip) + needed > config.VISITOR_DAILY_SEARCHES:
            return jsonify(
                error="You've reached today's search limit. This is a free research project; please come back tomorrow."
            ), 429
        left = searches_left()
        if left is not None and left - needed < config.BUDGET_RESERVE:
            return jsonify(
                error="This month's flight searches are used up. Searches that were run recently still work."
            ), 503

    result = trip.find_trip(origin, destination, when, API_KEY, include_hidden=include_hidden)
    record_usage(ip, result["live_searches"])

    result["airport_names"] = CITY_NAMES
    result["searches_left"] = left - result["live_searches"] if left is not None else None
    result["visitor_searches_left"] = config.VISITOR_DAILY_SEARCHES - used_today(ip)
    result["hidden_cost"] = (
        0 if include_hidden else trip.live_searches_needed(origin, destination, when, True)
    )
    return jsonify(result)


app.register_blueprint(site)

if __name__ == "__main__":
    app.run(port=5050, debug=False)
