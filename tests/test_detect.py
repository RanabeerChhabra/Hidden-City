from hiddencity.detect import find_hidden_city, summarise
from tests.helpers import row


def test_finds_connection_cheaper_than_direct():
    rows = [
        row("DEL", "BOM", "BOM", 7000),  # direct DEL -> BOM
        row("DEL", "BOM", "GOI", 5000),  # DEL -> BOM -> GOI, cheaper
    ]
    [opp] = find_hidden_city(rows)
    assert opp["hub"] == "BOM"
    assert opp["final_destination"] == "GOI"
    assert opp["saving"] == 2000
    assert opp["saving_pct"] == 28.6


def test_ignores_connection_that_costs_more():
    rows = [row("DEL", "BOM", "BOM", 5000), row("DEL", "BOM", "GOI", 6000)]
    assert find_hidden_city(rows) == []


def test_ignores_equal_price():
    rows = [row("DEL", "BOM", "BOM", 5000), row("DEL", "BOM", "GOI", 5000)]
    assert find_hidden_city(rows) == []


def test_compares_against_cheapest_direct():
    rows = [
        row("DEL", "BOM", "BOM", 9000),
        row("DEL", "BOM", "BOM", 6000),
        row("DEL", "BOM", "GOI", 6500),  # beats 9000 but not 6000
    ]
    assert find_hidden_city(rows) == []


def test_needs_a_direct_price_for_the_hub():
    # We never saw a direct DEL -> HYD, so there's nothing to compare with.
    rows = [row("DEL", "HYD", "GOI", 3000)]
    assert find_hidden_city(rows) == []


def test_only_compares_same_date():
    rows = [
        row("DEL", "BOM", "BOM", 7000, date="2026-11-18"),
        row("DEL", "BOM", "GOI", 5000, date="2026-11-19"),
    ]
    assert find_hidden_city(rows) == []


def test_same_flight_price_when_available():
    rows = [
        row("DEL", "BOM", "BOM", 6000, flight="AI 101"),
        row("DEL", "BOM", "BOM", 8000, flight="AI 999"),
        row("DEL", "BOM", "GOI", 5000, flight="AI 101"),
    ]
    [opp] = find_hidden_city(rows)
    assert opp["same_flight_direct_price"] == 6000


def test_sorted_biggest_saving_first():
    rows = [
        row("DEL", "BOM", "BOM", 7000),
        row("DEL", "BOM", "GOI", 6500),
        row("DEL", "BOM", "COK", 4000),
    ]
    savings = [opp["saving"] for opp in find_hidden_city(rows)]
    assert savings == [3000, 500]


def test_summary_counts_routes_not_itineraries():
    rows = [
        row("DEL", "BOM", "BOM", 7000),
        row("DEL", "BOM", "GOI", 5000),
        row("DEL", "BOM", "COK", 6000),
        row("DEL", "BLR", "BLR", 4000),  # a second route, no saving
    ]
    summary = summarise(rows, find_hidden_city(rows))
    assert summary["routes_checked"] == 2
    assert summary["routes_with_saving"] == 1
    assert summary["pct_routes_with_saving"] == 50.0
    assert summary["avg_best_saving"] == 2000
