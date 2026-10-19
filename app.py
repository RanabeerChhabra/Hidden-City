"""The web app: a search page plus one API endpoint that runs a trip search.

Run it with:  python app.py   then open http://localhost:5050
"""

from datetime import date

from flask import Flask, jsonify, render_template, request

from hiddencity import client, config, trip

app = Flask(__name__)
API_KEY = client.get_api_key()


def suggested_date():
    """The earliest date we already have cached data for, so a first search is free."""
    today = date.today().isoformat()
    dates = sorted({d for _, d in client.cached_searches(config.ORIGIN) if d >= today})
    return dates[0] if dates else today


@app.get("/")
def home():
    airports = sorted(config.AIRPORTS.items(), key=lambda item: item[1])
    return render_template(
        "index.html",
        airports=airports,
        default_date=suggested_date(),
        today=date.today().isoformat(),
    )


@app.post("/api/search")
def search():
    body = request.get_json(silent=True) or {}
    origin = str(body.get("origin", "")).strip().upper()
    destination = str(body.get("destination", "")).strip().upper()
    when = str(body.get("date", "")).strip()
    include_hidden = bool(body.get("include_hidden", True))

    if origin not in config.AIRPORTS or destination not in config.AIRPORTS:
        return jsonify(error="Pick airports from the list."), 400
    if origin == destination:
        return jsonify(error="From and To can't be the same airport."), 400
    try:
        if date.fromisoformat(when) < date.today():
            return jsonify(error="Pick a date in the future."), 400
    except ValueError:
        return jsonify(error="Pick a date."), 400

    result = trip.find_trip(origin, destination, when, API_KEY, include_hidden=include_hidden)
    result["airport_names"] = config.AIRPORTS
    return jsonify(result)


if __name__ == "__main__":
    app.run(port=5050, debug=False)
