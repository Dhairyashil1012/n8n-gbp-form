import httpx
from app.config import GOOGLE_API_KEY

GOOGLE_AUTOCOMPLETE_URL = "https://maps.googleapis.com/maps/api/place/autocomplete/json"


async def autocomplete_business(query: str):
    params = {
        "input": query,
        "key": GOOGLE_API_KEY,
        "types": "establishment",
    }

    async with httpx.AsyncClient(timeout=5.0) as client:
        response = await client.get(GOOGLE_AUTOCOMPLETE_URL, params=params)
        response.raise_for_status()

    data = response.json()

    return [
        {
            "name": item["description"],
            "place_id": item["place_id"],
        }
        for item in data.get("predictions", [])
    ]
