"""Finds hidden-city fares: a connecting ticket A -> hub -> C that costs less
than flying A -> hub directly on the same day."""


def cheapest_direct_prices(rows):
    """{(origin, airport, date): lowest direct price} from every direct itinerary."""
    cheapest = {}
    for row in rows:
        if row["stops"] != 0:
            continue
        key = (row["origin"], row["final_destination"], row["date"])
        if key not in cheapest or row["price"] < cheapest[key]:
            cheapest[key] = row["price"]
    return cheapest


def direct_price_by_flight(rows):
    """{(date, flight number): lowest price when that flight is sold on its own}."""
    prices = {}
    for row in rows:
        if row["stops"] != 0 or not row["first_flight"]:
            continue
        key = (row["date"], row["first_flight"])
        if key not in prices or row["price"] < prices[key]:
            prices[key] = row["price"]
    return prices


def find_hidden_city(rows):
    """Return one dict per connecting itinerary that beats the direct fare to its first stop."""
    direct = cheapest_direct_prices(rows)
    by_flight = direct_price_by_flight(rows)

    found = []
    for row in rows:
        if row["stops"] == 0:
            continue
        hub = row["first_stop"]
        if hub == row["final_destination"]:
            continue  # first stop is the destination itself, nothing hidden
        direct_price = direct.get((row["origin"], hub, row["date"]))
        if direct_price is None:
            continue  # we never searched (or found) a direct flight to this hub
        if row["price"] >= direct_price:
            continue

        saving = direct_price - row["price"]
        found.append(
            {
                "date": row["date"],
                "origin": row["origin"],
                "hub": hub,
                "final_destination": row["final_destination"],
                "airline": row["airline"],
                "first_flight": row["first_flight"],
                "departure_time": row["departure_time"],
                "hidden_city_price": row["price"],
                "cheapest_direct_price": direct_price,
                # The same plane, sold alone as a direct ticket (if Google showed it).
                "same_flight_direct_price": by_flight.get((row["date"], row["first_flight"])),
                "saving": saving,
                "saving_pct": round(100 * saving / direct_price, 1),
            }
        )
    found.sort(key=lambda r: r["saving"], reverse=True)
    return found


def summarise(rows, opportunities):
    """Headline numbers: how many hub routes had at least one hidden-city saving."""
    direct = cheapest_direct_prices(rows)
    # A route here is (origin, hub, date) where we know the direct price.
    routes_checked = set(direct)
    routes_with_saving = set()
    for opp in opportunities:
        routes_with_saving.add((opp["origin"], opp["hub"], opp["date"]))

    best_saving_per_route = {}
    for opp in opportunities:
        key = (opp["origin"], opp["hub"], opp["date"])
        best_saving_per_route[key] = max(best_saving_per_route.get(key, 0), opp["saving"])

    savings = list(best_saving_per_route.values())
    return {
        "routes_checked": len(routes_checked),
        "routes_with_saving": len(routes_with_saving),
        "pct_routes_with_saving": round(100 * len(routes_with_saving) / len(routes_checked), 1)
        if routes_checked
        else 0.0,
        "avg_best_saving": round(sum(savings) / len(savings)) if savings else 0,
        "max_saving": max(savings) if savings else 0,
    }
