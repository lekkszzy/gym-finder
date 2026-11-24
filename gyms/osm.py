"""
Helpers for importing gyms from OpenStreetMap (OSM) via the Overpass API.

Kept free of Django imports so the parsing logic is easy to unit test.
Used by the `import_osm_gyms` management command.
"""
import re
from datetime import time
from urllib.parse import urlparse

# County Dublin bounding box: south, west, north, east (Overpass order)
DEFAULT_BBOX = (53.20, -6.55, 53.64, -6.00)

# Public Overpass servers: if the first is busy, the command tries the next
OVERPASS_URLS = [
    "https://overpass-api.de/api/interpreter",
    "https://overpass.kumi.systems/api/interpreter",
]

# Limits matching the Gym model fields
MAX_NAME = 200
MAX_WEBSITE = 200
MAX_ADDRESS = 400

# First "HH:MM-HH:MM" in an OSM opening_hours value, e.g. "Mo-Fr 06:00-22:00"
TIME_RANGE = re.compile(r"(\d{1,2}):(\d{2})\s*-\s*(\d{1,2}):(\d{2})")


def parse_bbox(text):
    """Turn 'south,west,north,east' into a tuple of 4 floats, or raise ValueError."""
    parts = [float(p) for p in text.split(",")]
    if len(parts) != 4:
        raise ValueError("bbox needs 4 numbers: south,west,north,east")
    south, west, north, east = parts
    if not (-90 <= south < north <= 90 and -180 <= west < east <= 180):
        raise ValueError("bbox values are out of range or in the wrong order")
    return south, west, north, east


def build_query(bbox):
    """
    Overpass QL query for every gym (leisure=fitness_centre) in the bounding box.
    Gyms can be mapped as points (nodes) or building outlines (ways/relations);
    'out center' gives a single centre point for the outlines.
    """
    s, w, n, e = bbox
    area = f"({s},{w},{n},{e})"
    return (
        "[out:json][timeout:60];"
        "("
        f'node["leisure"="fitness_centre"]{area};'
        f'way["leisure"="fitness_centre"]{area};'
        f'relation["leisure"="fitness_centre"]{area};'
        ");"
        "out center tags;"
    )


def parse_opening_hours(value):
    """
    Read an OSM opening_hours string.
    Returns (is_24_hours_open, opening_time, closing_time).
    Only "24/7" and the first simple time range are understood; anything else -> unknown.
    """
    if not value:
        return False, None, None
    if value.strip() == "24/7":
        return True, None, None

    match = TIME_RANGE.search(value)
    if not match:
        return False, None, None

    open_h, open_m, close_h, close_m = (int(g) for g in match.groups())
    if close_h == 24 and close_m == 0:      # OSM uses 24:00 for midnight
        close_h, close_m = 23, 59
    if not (0 <= open_h <= 23 and 0 <= close_h <= 23 and open_m <= 59 and close_m <= 59):
        return False, None, None
    return False, time(open_h, open_m), time(close_h, close_m)


def build_address(tags):
    """Join the OSM addr:* tags into one line, e.g. '12 Main Street, Rathmines, D06 X1Y2'."""
    street = " ".join(p for p in (tags.get("addr:housenumber"), tags.get("addr:street")) if p)
    area = tags.get("addr:suburb") or tags.get("addr:city")
    parts = [p for p in (street, area, tags.get("addr:postcode")) if p]
    return ", ".join(parts)[:MAX_ADDRESS]


def clean_website(tags):
    """Return a valid http(s) URL that fits the model field, or '' if there isn't one."""
    url = (tags.get("website") or tags.get("contact:website") or tags.get("url") or "").strip()
    if not url:
        return ""
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    parsed = urlparse(url)
    if not parsed.netloc or " " in url or len(url) > MAX_WEBSITE:
        return ""
    return url


def parse_element(element):
    """
    Convert one Overpass element into a dict of Gym fields.
    Returns None for gyms we can't use (no name or no coordinates).
    """
    tags = element.get("tags", {})
    name = (tags.get("name") or tags.get("brand") or "").strip()
    if not name:
        return None

    # Nodes have lat/lon directly; ways and relations have a 'center'
    point = element if "lat" in element else element.get("center")
    if not point or "lat" not in point or "lon" not in point:
        return None

    is_24, opening, closing = parse_opening_hours(tags.get("opening_hours"))
    return {
        "osm_ref": f"{element['type']}/{element['id']}",   # e.g. "node/123456", unique in OSM
        "name": name[:MAX_NAME],
        "lat": float(point["lat"]),
        "lon": float(point["lon"]),
        "address": build_address(tags),
        "website": clean_website(tags),
        "is_24_hours_open": is_24,
        "opening_time": opening,
        "closing_time": closing,
    }