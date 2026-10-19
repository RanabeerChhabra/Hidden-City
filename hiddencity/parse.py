"""Turns SerpApi's nested JSON into flat rows: one row per itinerary."""


def parse_itineraries(data, searched_destination, date):
    """Return a list of dicts, one per bookable itinerary in a SerpApi answer.

    An itinerary is one ticket. It has one leg (a direct flight) or several legs
    (a connection). The first leg's arrival airport is where a hidden-city
    traveller would get off.
    """
    # A link to the same search on Google Flights, so people can check and book there.
    search_url = data.get("search_metadata", {}).get("google_flights_url")

    rows = []
    for section in ("best_flights", "other_flights"):
        for itinerary in data.get(section, []):
            legs = itinerary.get("flights", [])
            price = itinerary.get("price")
            if not legs or price is None:
                continue  # can't compare an itinerary with no legs or no price

            first_leg = legs[0]
            last_leg = legs[-1]

            airlines = []
            for leg in legs:
                if leg.get("airline") not in airlines:
                    airlines.append(leg.get("airline"))

            rows.append(
                {
                    "date": date,
                    "searched_destination": searched_destination,
                    "origin": first_leg["departure_airport"]["id"],
                    "first_stop": first_leg["arrival_airport"]["id"],
                    "final_destination": last_leg["arrival_airport"]["id"],
                    "stops": len(legs) - 1,
                    "price": price,
                    "airline": first_leg.get("airline"),
                    "all_airlines": " / ".join(str(a) for a in airlines),
                    "first_flight": first_leg.get("flight_number"),
                    "flight_numbers": " + ".join(str(leg.get("flight_number")) for leg in legs),
                    "departure_time": first_leg["departure_airport"].get("time"),
                    "first_stop_arrival_time": first_leg["arrival_airport"].get("time"),
                    "final_arrival_time": last_leg["arrival_airport"].get("time"),
                    "first_leg_duration_min": first_leg.get("duration"),
                    "duration_min": itinerary.get("total_duration"),
                    "airline_logo": itinerary.get("airline_logo") or first_leg.get("airline_logo"),
                    "search_url": search_url,
                    "section": section,
                }
            )
    return rows
