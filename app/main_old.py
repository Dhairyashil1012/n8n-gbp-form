from typing import List
import logging

from fastapi import FastAPI, Request, Body, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr, Field
import httpx

from app.services.google_places import autocomplete_business
from app.config import N8N_WEBHOOK_URL

# -------------------------
# Logging
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)
logger = logging.getLogger(__name__)

# -------------------------
# App
# -------------------------
app = FastAPI(title="Business Intake Service", version="1.0.0")

# Fix: Correct templates path for Render deployment
templates = Jinja2Templates(directory="app/templates")

# -------------------------
# Models
# -------------------------
class Company(BaseModel):
    name: str = Field(..., min_length=1)
    place_id: str = Field(..., min_length=1)


class SubmissionPayload(BaseModel):
    email: EmailStr
    companies: List[Company]

# -------------------------
# Routes
# -------------------------
@app.get("/", response_class=HTMLResponse)
async def form_page(request: Request):
    """
    Render the business intake form page.
    """
    return templates.TemplateResponse("form.html", {"request": request})


@app.get("/autocomplete")
async def autocomplete(query: str = Query(..., min_length=1)):
    """
    Autocomplete business names using Google Places.
    """
    if len(query) < 2:
        return JSONResponse([])

    try:
        results = autocomplete_business(query)
        return JSONResponse(results)
    except Exception:
        logger.exception("Autocomplete failed")
        raise HTTPException(status_code=500, detail="Autocomplete failed")


@app.post("/submit")
async def submit(data: SubmissionPayload = Body(...)):
    """
    Submit form data to n8n webhook.
    """
    try:
        payload = data.model_dump()
        logger.info("Sending data to n8n")
        logger.info("Webhook URL: %s", N8N_WEBHOOK_URL)
        logger.info("Payload: %s", payload)

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(N8N_WEBHOOK_URL, json=payload)
            resp.raise_for_status()

    except httpx.TimeoutException:
        raise HTTPException(status_code=504, detail="n8n timeout")

    except httpx.HTTPStatusError as exc:
        logger.error("n8n error: %s", exc.response.text)
        raise HTTPException(status_code=502, detail="n8n error")

    except Exception:
        logger.exception("Unexpected error")
        raise HTTPException(status_code=500, detail="Internal error")

    return {"status": "success"}
