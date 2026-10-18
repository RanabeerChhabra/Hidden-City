from hiddencity.parse import parse_itineraries
from tests.helpers import itinerary, leg


def test_direct_flight_has_zero_stops():
    data = {"best_flights": [itinerary(5000, leg("DEL", "BOM"))]}
    [row] = parse_itineraries(data, "BOM", "2026-11-18")
    assert row["stops"] == 0
    assert row["first_stop"] == "BOM"
    assert row["final_destination"] == "BOM"


def test_connection_records_first_stop_as_hub():
    data = {"other_flights": [itinerary(4000, leg("DEL", "BOM"), leg("BOM", "GOI"))]}
    [row] = parse_itineraries(data, "GOI", "2026-11-18")
    assert row["stops"] == 1
    assert row["first_stop"] == "BOM"
    assert row["final_destination"] == "GOI"
    assert row["section"] == "other_flights"


def test_reads_both_sections():
    data = {
        "best_flights": [itinerary(5000, leg("DEL", "BOM"))],
        "other_flights": [itinerary(6000, leg("DEL", "BOM"))],
    }
    assert len(parse_itineraries(data, "BOM", "2026-11-18")) == 2


def test_skips_itinerary_without_price():
    data = {"best_flights": [{"flights": [leg("DEL", "BOM")]}]}
    assert parse_itineraries(data, "BOM", "2026-11-18") == []


def test_lists_each_airline_once():
    data = {
        "best_flights": [
            itinerary(
                4000,
                leg("DEL", "BOM", airline="Air India"),
                leg("BOM", "GOI", airline="Air India"),
            )
        ]
    }
    [row] = parse_itineraries(data, "GOI", "2026-11-18")
    assert row["all_airlines"] == "Air India"


def test_empty_answer_gives_no_rows():
    no_results = {"error": "Google Flights hasn't returned any results for this query."}
    assert parse_itineraries(no_results, "BOM", "2026-11-18") == []
