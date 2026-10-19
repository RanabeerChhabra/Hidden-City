"""Settings for the whole project: where we fly from, where to, and where files go."""

from pathlib import Path

# The project folder (one level above this file).
ROOT = Path(__file__).resolve().parent.parent

CACHE_DIR = ROOT / "cache"  # raw SerpApi answers, one JSON file per search
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

# SerpApi's free plan allows 50 searches an hour. We stop a little below that.
HOURLY_LIMIT = 45

# Seconds to wait between searches, to be polite to the API.
PAUSE_BETWEEN_SEARCHES = 1
