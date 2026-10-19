"""The web app: a search page plus one API endpoint that runs a trip search.

Run it with:  python app.py   then open http://localhost:5050
"""

from datetime import date

import requests
from flask import Flask, jsonify, render_template, request

from hiddencity import airports, client, config, trip

app = Flask(__name__)
API_KEY = client.get_api_key()
CITY_NAMES = {code: info[0] for code, info in airports.AIRPORTS.items()}


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


@app.get("/")
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


@app.post("/api/search")
def search():
    body = request.get_json(silent=True) or {}
    origin = str(body.get("origin", "")).strip().upper()
    destination = str(body.get("destination", "")).strip().upper()
    when = str(body.get("date", "")).strip()
    include_hidden = bool(body.get("include_hidden", True))

    if origin not in CITY_NAMES or destination not in CITY_NAMES:
        return jsonify(error="Pick airports from the list."), 400
    if origin == destination:
        return jsonify(error="From and To can't be the same airport."), 400
    try:
        if date.fromisoformat(when) < date.today():
            return jsonify(error="Pick a date in the future."), 400
    except ValueError:
        return jsonify(error="Pick a date."), 400

    result = trip.find_trip(origin, destination, when, API_KEY, include_hidden=include_hidden)
    result["airport_names"] = CITY_NAMES
    result["searches_left"] = searches_left()
    return jsonify(result)


if __name__ == "__main__":
    app.run(port=5050, debug=False)
