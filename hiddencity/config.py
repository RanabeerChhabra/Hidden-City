"""Settings for the whole project: where we fly from, where to, and where files go."""

import os
from pathlib import Path

# The project folder (one level above this file).
ROOT = Path(__file__).resolve().parent.parent

# Raw SerpApi answers, one JSON file per search. On Vercel the project folder is
# read-only, so answers go to /tmp there (and last only as long as the server).
if os.environ.get("VERCEL"):
    CACHE_DIR = Path("/tmp/hiddencity-cache")
else:
    CACHE_DIR = ROOT / "cache"
SEARCH_LOG = CACHE_DIR / "search_log.jsonl"  # one line per search we paid for
DATA_DIR = ROOT / "data"  # cleaned results (SQLite database and CSV files)

ORIGIN = "DEL"

# Every city we search DEL -> city for. One search to a city tells us two things:
#   1. the direct price DEL -> city
#   2. connecting flights DEL -> hub -> city, which are the hidden-city candidates
#      for every hub they stop at.
# So searching N cities covers every hub among them, not just one route.
DESTINATIONS = {
    "BOM": "Mumbai",
    "NMI": "Navi Mumbai",
    "BLR": "Bengaluru",
    "HYD": "Hyderabad",
    "MAA": "Chennai",
    "CCU": "Kolkata",
    "GOI": "Goa (Dabolim)",
    "GOX": "Goa (Mopa)",
    "COK": "Kochi",
    "AMD": "Ahmedabad",
    "PNQ": "Pune",
    "JAI": "Jaipur",
    "LKO": "Lucknow",
    "GAU": "Guwahati",
    "PAT": "Patna",
    "BBI": "Bhubaneswar",
    "IXC": "Chandigarh",
    "SXR": "Srinagar",
    "IXB": "Bagdogra",
    "TRV": "Thiruvananthapuram",
    "IXE": "Mangaluru",
    "IXM": "Madurai",
    "VNS": "Varanasi",
    "NAG": "Nagpur",
    "IDR": "Indore",
    "BHO": "Bhopal",
    "RPR": "Raipur",
    "IXR": "Ranchi",
    "CJB": "Coimbatore",
    "IXZ": "Port Blair",
    "ATQ": "Amritsar",
    "UDR": "Udaipur",
    "IXJ": "Jammu",
    "IXL": "Leh",
    "VTZ": "Visakhapatnam",
    "VGA": "Vijayawada",
    "IXA": "Agartala",
    "DIB": "Dibrugarh",
    "DED": "Dehradun",
    "JDH": "Jodhpur",
    "STV": "Surat",
}

# For a trip search, how many cities beyond the destination to search for
# hidden-city tickets. Each one costs a search unless it's already cached.
# Small airports rarely have connections through them, so we try fewer.
MAX_BEYOND_SEARCHES = 6
MAX_BEYOND_SEARCHES_SMALL_AIRPORT = 2

# The website re-searches saved answers older than this, so prices stay current.
# (The research scan never expires: it's a snapshot on purpose.)
LIVE_MAX_AGE_HOURS = 6

# Protecting the monthly budget once the site is public:
# each visitor can trigger at most this many paid searches a day...
VISITOR_DAILY_SEARCHES = 15
# ...and the site stops making new searches when the account gets this low.
BUDGET_RESERVE = 10

# SerpApi's free plan allows 50 searches an hour. The research scan stops at 45,
# which keeps the last 5 free for people searching on the website.
HOURLY_LIMIT = 45
LIVE_HOURLY_LIMIT = 50

# Seconds to wait between searches, to be polite to the API.
PAUSE_BETWEEN_SEARCHES = 1
