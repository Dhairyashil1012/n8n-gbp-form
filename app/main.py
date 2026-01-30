from typing import List

import logging

from fastapi import FastAPI, Request, Body, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr, Field
import httpx

from app.services.google_places import autocomplete_business
from app.config import N8N_WEBHOOK_URL
# app/main.py (top of file)



# -------------------------
# Logging configuration
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# -------------------------
# App initialization
# -------------------------
app = FastAPI(
    title="Business Submission Service",
    version="1.0.0",
)

templates = Jinja2Templates(directory="app/templates")


# -------------------------
# Pydantic models (validation only)
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
    Render main HTML form.
    """
    return templates.TemplateResponse(
        "form.html",
        {"request": request},
    )


@app.get("/autocomplete")
async def autocomplete(
    query: str = Query(..., min_length=1),
):
    """
    Google Places autocomplete endpoint.
    """
    if len(query) < 2:
        return JSONResponse([])

    try:
        results = autocomplete_business(query)
        return JSONResponse(results)

    except Exception as exc:
        logger.exception("Autocomplete failed")
        raise HTTPException(
            status_code=500,
            detail="Autocomplete service unavailable",
        ) from exc


@app.post("/submit")
async def submit(
    data: SubmissionPayload = Body(...),
):
    """
    Expected payload:
    {
      "email": "...",
      "companies": [
        { "name": "...", "place_id": "..." }
      ]
    }
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.post(
                N8N_WEBHOOK_URL,
                json=data.model_dump(),
            )
            response.raise_for_status()

    except httpx.TimeoutException:
        logger.error("n8n webhook timeout")
        raise HTTPException(
            status_code=504,
            detail="Upstream service timeout",
        )

    except httpx.HTTPStatusError as exc:
        logger.error(
            "n8n webhook failed | status=%s | body=%s",
            exc.response.status_code,
            exc.response.text,
        )
        raise HTTPException(
            status_code=502,
            detail="Upstream service error",
        )

    except Exception as exc:
        logger.exception("Unexpected submit error")
        raise HTTPException(
            status_code=500,
            detail="Internal server error",
        ) from exc

    return {"status": "success"}
