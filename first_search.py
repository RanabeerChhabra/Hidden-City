# Week 1, step 1: ask SerpApi for one-way DEL -> BOM flights on one date,
# save the answer to disk, and print what came back.

import json
import os

import requests
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("SERPAPI_KEY")

ORIGIN = "DEL"
DESTINATION = "BOM"
DATE = "2026-11-18"

CACHE_FILE = f"cache/{ORIGIN}-{DESTINATION}-{DATE}.json"


def search_flights():
    """Ask SerpApi for flights. Each call uses 1 of our 250 monthly searches."""
    params = {
        "engine": "google_flights",
        "departure_id": ORIGIN,
        "arrival_id": DESTINATION,
        "outbound_date": DATE,
        "type": "2",  # 2 means one-way
        "currency": "INR",
        "hl": "en",  # language: English
        "gl": "in",  # country: India
        "api_key": API_KEY,
    }
    response = requests.get("https://serpapi.com/search.json", params=params, timeout=60)
    return response.json()


# If we already searched this route and date, reuse the saved copy for free.
if os.path.exists(CACHE_FILE):
    print("Using saved results from", CACHE_FILE)
    with open(CACHE_FILE) as f:
        data = json.load(f)
else:
    print("Searching SerpApi (uses 1 search)...")
    data = search_flights()
    if "error" in data:
        print("SerpApi returned an error:", data["error"])
    else:
        os.makedirs("cache", exist_ok=True)
        with open(CACHE_FILE, "w") as f:
            json.dump(data, f, indent=2)

# Google splits results into "best" and "other" flights. We want all of them.
itineraries = data.get("best_flights", []) + data.get("other_flights", [])
print("Found", len(itineraries), "options for", ORIGIN, "->", DESTINATION, "on", DATE)
print()

direct_prices = []

for itinerary in itineraries:
    price = itinerary.get("price")
    airline = itinerary["flights"][0]["airline"]
    layovers = itinerary.get("layovers", [])

    if len(layovers) == 0:
        route = "direct"
        if price is not None:
            direct_prices.append(price)
    else:
        layover_airports = []
        for layover in layovers:
            layover_airports.append(layover["id"])
        route = "via " + ", ".join(layover_airports)

    print("Rs", price, "|", airline, "|", route)

print()
if len(direct_prices) > 0:
    print("Cheapest direct", ORIGIN, "->", DESTINATION, "price: Rs", min(direct_prices))
else:
    print("No direct flights with a price were found.")
