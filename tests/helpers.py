"""Small fake SerpApi answers, so tests never spend real searches."""


def leg(origin, destination, airline="IndiGo", flight_number="6E 1"):
    return {
        "departure_airport": {"id": origin, "time": "2026-11-18 06:00"},
        "arrival_airport": {"id": destination, "time": "2026-11-18 08:00"},
        "airline": airline,
        "flight_number": flight_number,
    }


def itinerary(price, *legs):
    return {"flights": list(legs), "price": price, "total_duration": 120 * len(legs)}


def row(origin, first_stop, final_destination, price, date="2026-11-18", flight="6E 1"):
    """A parsed row, as parse_itineraries would produce."""
    stops = 0 if first_stop == final_destination else 1
    return {
        "date": date,
        "searched_destination": final_destination,
        "origin": origin,
        "first_stop": first_stop,
        "final_destination": final_destination,
        "stops": stops,
        "price": price,
        "airline": "IndiGo",
        "all_airlines": "IndiGo",
        "first_flight": flight,
        "departure_time": f"{date} 06:00",
        "duration_min": 120,
        "section": "best_flights",
    }
