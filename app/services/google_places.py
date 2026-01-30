import requests
from app.config import GOOGLE_API_KEY

GOOGLE_AUTOCOMPLETE_URL = (
    "https://maps.googleapis.com/maps/api/place/autocomplete/json"
)

def autocomplete_business(query: str):
    params = {
        "input": query,
        "types": "establishment",
        "key": GOOGLE_API_KEY
    }

    response = requests.get(GOOGLE_AUTOCOMPLETE_URL, params=params, timeout=5)
    response.raise_for_status()

    data = response.json()

    return [
        {
            "name": p["description"],
            "place_id": p["place_id"]
        }
        for p in data.get("predictions", [])
    ]
