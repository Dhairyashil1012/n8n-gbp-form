import requests
from app.config import GOOGLE_API_KEY

GOOGLE_AUTOCOMPLETE_URL = "https://maps.googleapis.com/maps/api/place/autocomplete/json"


def autocomplete_business(query: str):
    params = {
        "input": query,
        "key": GOOGLE_API_KEY,
        "types": "establishment",
    }

    response = requests.get(GOOGLE_AUTOCOMPLETE_URL, params=params, timeout=5)
    response.raise_for_status()

    data = response.json()

    results = []
    for item in data.get("predictions", []):
        results.append({
            "name": item["description"],
            "place_id": item["place_id"],
        })

    return results
