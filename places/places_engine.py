import os
import requests
from urllib.parse import quote

GOOGLE_PLACES_API_KEY = os.getenv("GOOGLE_PLACES_API_KEY")

BASE_SEARCH_URL = "https://maps.googleapis.com/maps/api/place/textsearch/json"
BASE_DETAIL_URL = "https://maps.googleapis.com/maps/api/place/details/json"


def _maps_url(name: str, place_id: str) -> str:
    """Return a clickable Google Maps URL for Telegram."""
    n = (name or "place").strip()
    pid = (place_id or "").strip()
    q = quote(n)
    # Use query + query_place_id for best match
    return f"https://www.google.com/maps/search/?api=1&query={q}&query_place_id={pid}"


def places_search(query: str, limit: int = 5):
    """
    Búsqueda simple de lugares por texto.
    Devuelve:
      - lista de dicts con name, address, rating, types, place_id
      - o dict {"error": "..."} si algo falla
    """
    if not GOOGLE_PLACES_API_KEY:
        return {"error": "GOOGLE_PLACES_API_KEY not set"}

    params = {
        "query": query,
        "key": GOOGLE_PLACES_API_KEY,
    }

    try:
        r = requests.get(BASE_SEARCH_URL, params=params, timeout=10)
    except Exception as e:
        return {"error": f"request failed: {e!r}"}

    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}"}

    data = r.json()

    status = data.get("status")
    if status != "OK":
        # Puede ser ZERO_RESULTS, OVER_QUERY_LIMIT, etc.
        return {"error": status or "UNKNOWN_STATUS", "data": data}

    results = data.get("results", [])[:limit]

    output = []
    for item in results:
        output.append(
            {
                "name": item.get("name"),
                "address": item.get("formatted_address"),
                "rating": item.get("rating"),
                "types": item.get("types"),
                "place_id": item.get("place_id"),
                "maps_url": _maps_url(item.get("name"), item.get("place_id")),
            }
        )

    return output


def place_details(place_id: str):
    """
    Detalle de un lugar por place_id.
    Devuelve:
      - dict con name, address, phone, opening_hours, rating, website
      - o dict {"error": "..."} si algo falla
    """
    if not GOOGLE_PLACES_API_KEY:
        return {"error": "GOOGLE_PLACES_API_KEY not set"}

    params = {
        "place_id": place_id,
        "key": GOOGLE_PLACES_API_KEY,
        "fields": (
            "name,formatted_address,formatted_phone_number,"
            "opening_hours,rating,website"
        ),
    }

    try:
        r = requests.get(BASE_DETAIL_URL, params=params, timeout=10)
    except Exception as e:
        return {"error": f"request failed: {e!r}"}

    if r.status_code != 200:
        return {"error": f"HTTP {r.status_code}"}

    data = r.json()
    status = data.get("status")
    if status != "OK":
        return {"error": status or "UNKNOWN_STATUS", "data": data}

    result = data.get("result", {}) or {}

    return {
        "name": result.get("name"),
        "address": result.get("formatted_address"),
        "phone": result.get("formatted_phone_number"),
        "opening_hours": result.get("opening_hours"),
        "rating": result.get("rating"),
        "website": result.get("website"),
        "maps_url": _maps_url(result.get("name"), place_id),
    }
