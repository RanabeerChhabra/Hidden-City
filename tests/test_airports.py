from hiddencity import airports


def test_delhi_mumbai_distance_is_about_1150_km():
    assert 1100 < airports.distance_km("DEL", "BOM") < 1200


def test_beyond_mumbai_from_delhi_includes_goa_and_kochi():
    cities = airports.beyond("DEL", "BOM")
    assert "GOI" in cities[:5]
    assert "COK" in cities[:5]


def test_beyond_skips_second_airport_in_same_city():
    assert "NMI" not in airports.beyond("DEL", "BOM")


def test_beyond_only_lists_cities_further_away():
    for city in airports.beyond("DEL", "BOM"):
        assert airports.distance_km("DEL", city) > airports.distance_km("DEL", "BOM")
