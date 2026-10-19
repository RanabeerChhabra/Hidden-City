"""Every Indian airport the trip search supports, with rough coordinates.

Coordinates are approximate (about 1 km). They're only used to work out which
cities lie "beyond" a destination, so they don't need to be exact.
"""

from math import asin, cos, radians, sin, sqrt

# code: (city, latitude, longitude)
AIRPORTS = {
    # Metros and big hubs
    "DEL": ("Delhi", 28.56, 77.10),
    "BOM": ("Mumbai", 19.09, 72.87),
    "NMI": ("Navi Mumbai", 18.99, 73.07),
    "BLR": ("Bengaluru", 13.20, 77.71),
    "HYD": ("Hyderabad", 17.24, 78.43),
    "MAA": ("Chennai", 12.99, 80.17),
    "CCU": ("Kolkata", 22.65, 88.45),
    "AMD": ("Ahmedabad", 23.07, 72.63),
    "PNQ": ("Pune", 18.58, 73.92),
    "COK": ("Kochi", 10.15, 76.40),
    "GOI": ("Goa Dabolim", 15.38, 73.83),
    "GOX": ("Goa Mopa", 15.73, 73.86),
    "GAU": ("Guwahati", 26.11, 91.59),
    # North
    "JAI": ("Jaipur", 26.82, 75.81),
    "LKO": ("Lucknow", 26.76, 80.89),
    "IXC": ("Chandigarh", 30.67, 76.79),
    "SXR": ("Srinagar", 33.99, 74.77),
    "IXJ": ("Jammu", 32.69, 74.84),
    "IXL": ("Leh", 34.14, 77.55),
    "ATQ": ("Amritsar", 31.71, 74.80),
    "DED": ("Dehradun", 30.19, 78.18),
    "VNS": ("Varanasi", 25.45, 82.86),
    "AYJ": ("Ayodhya", 26.75, 82.15),
    "GOP": ("Gorakhpur", 26.74, 83.45),
    "IXD": ("Prayagraj", 25.44, 81.73),
    "KNU": ("Kanpur", 26.40, 80.41),
    "AGR": ("Agra", 27.16, 77.96),
    "GWL": ("Gwalior", 26.29, 78.23),
    "DHM": ("Dharamshala", 32.17, 76.26),
    "KUU": ("Kullu", 31.88, 77.15),
    "SLV": ("Shimla", 31.08, 77.07),
    "PGH": ("Pantnagar", 29.03, 79.47),
    "UDR": ("Udaipur", 24.62, 73.90),
    "JDH": ("Jodhpur", 26.25, 73.05),
    "JSA": ("Jaisalmer", 26.89, 70.86),
    "BKB": ("Bikaner", 28.07, 73.21),
    # East and North-East
    "PAT": ("Patna", 25.59, 85.09),
    "GAY": ("Gaya", 24.74, 84.95),
    "DBR": ("Darbhanga", 26.19, 85.91),
    "IXR": ("Ranchi", 23.31, 85.32),
    "DGH": ("Deoghar", 24.45, 86.71),
    "BBI": ("Bhubaneswar", 20.24, 85.82),
    "JRG": ("Jharsuguda", 21.91, 84.05),
    "IXB": ("Bagdogra", 26.68, 88.33),
    "RDP": ("Durgapur", 23.62, 87.24),
    "IXA": ("Agartala", 23.89, 91.24),
    "IMF": ("Imphal", 24.76, 93.90),
    "IXS": ("Silchar", 24.91, 92.98),
    "DMU": ("Dimapur", 25.88, 93.77),
    "AJL": ("Aizawl", 23.84, 92.62),
    "SHL": ("Shillong", 25.70, 91.98),
    "DIB": ("Dibrugarh", 27.48, 95.02),
    "JRH": ("Jorhat", 26.73, 94.18),
    "IXI": ("Lilabari", 27.29, 94.10),
    "HGI": ("Itanagar", 26.97, 93.64),
    "IXZ": ("Port Blair", 11.64, 92.73),
    # West and Central
    "STV": ("Surat", 21.11, 72.74),
    "BDQ": ("Vadodara", 22.34, 73.23),
    "RAJ": ("Rajkot", 22.38, 71.03),
    "BHJ": ("Bhuj", 23.29, 69.67),
    "JGA": ("Jamnagar", 22.47, 70.01),
    "BHU": ("Bhavnagar", 21.75, 72.19),
    "IXU": ("Aurangabad", 19.86, 75.40),
    "NAG": ("Nagpur", 21.09, 79.05),
    "ISK": ("Nashik", 20.12, 73.91),
    "SAG": ("Shirdi", 19.69, 74.38),
    "KLH": ("Kolhapur", 16.66, 74.29),
    "IDR": ("Indore", 22.72, 75.80),
    "BHO": ("Bhopal", 23.29, 77.34),
    "JLR": ("Jabalpur", 23.18, 80.05),
    "RPR": ("Raipur", 21.18, 81.74),
    # South
    "TRV": ("Thiruvananthapuram", 8.48, 76.92),
    "CCJ": ("Kozhikode", 11.14, 75.95),
    "CNN": ("Kannur", 11.92, 75.55),
    "IXE": ("Mangaluru", 12.96, 74.89),
    "CJB": ("Coimbatore", 11.03, 77.04),
    "IXM": ("Madurai", 9.83, 78.09),
    "TRZ": ("Tiruchirappalli", 10.77, 78.71),
    "TCR": ("Thoothukudi", 8.72, 78.03),
    "MYQ": ("Mysuru", 12.23, 76.66),
    "IXG": ("Belagavi", 15.86, 74.62),
    "HBX": ("Hubballi", 15.36, 75.08),
    "GBI": ("Kalaburagi", 17.31, 76.96),
    "VTZ": ("Visakhapatnam", 17.72, 83.22),
    "VGA": ("Vijayawada", 16.53, 80.80),
    "RJA": ("Rajahmundry", 17.11, 81.82),
    "TIR": ("Tirupati", 13.63, 79.54),
    "AGX": ("Agatti", 10.82, 72.18),
}

# Airports where lots of connections change planes. Hidden-city fares only
# exist when a destination is somewhere people connect through.
HUBS = {"DEL", "BOM", "BLR", "HYD", "MAA", "CCU", "AMD", "PNQ", "COK", "GOI", "GAU", "NMI"}


def city(code):
    return AIRPORTS[code][0]


def distance_km(a, b):
    """Great-circle distance between two airports (the haversine formula)."""
    _, lat1, lon1 = AIRPORTS[a]
    _, lat2, lon2 = AIRPORTS[b]
    lat1, lon1, lat2, lon2 = map(radians, (lat1, lon1, lat2, lon2))
    h = sin((lat2 - lat1) / 2) ** 2 + cos(lat1) * cos(lat2) * sin((lon2 - lon1) / 2) ** 2
    return 2 * 6371 * asin(sqrt(h))


def beyond(origin, destination):
    """Airports further on from `destination`, best guesses first.

    A city C is "beyond" destination D if flying origin -> D -> C is not much
    longer than flying origin -> C directly, i.e. D is roughly on the way.
    """
    direct = distance_km(origin, destination)
    candidates = []
    for code in AIRPORTS:
        if code in (origin, destination):
            continue
        if distance_km(destination, code) < 60:
            continue  # a second airport in the same city (e.g. BOM and NMI)
        to_city = distance_km(origin, code)
        if to_city <= direct:
            continue  # not further away than the destination
        detour = (direct + distance_km(destination, code) - to_city) / to_city
        if detour > 0.35:
            continue  # too far out of the way to route through the destination
        if code in HUBS:
            detour -= 0.1  # big airports have more flights, so try them first
        candidates.append((detour, code))
    candidates.sort()
    return [code for _, code in candidates]
