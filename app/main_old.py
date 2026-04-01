from typing import List
import logging

from fastapi import FastAPI, Request, Body, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr, Field
import httpx

from app.services.google_places import autocomplete_business
from app.config import N8N_WEBHOOK_URL
# main.py
from typing import List
import logging
import os

from fastapi import FastAPI, Request, Body, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr, Field
import httpx

# -------------------------
# Config
# -------------------------
N8N_WEBHOOK_URL = os.getenv("N8N_WEBHOOK_URL", "https://socioadminz.app.n8n.cloud/webhook/company-intake")

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

# Templates folder
BASE_DIR = os.path.dirname(__file__)
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
templates = Jinja2Templates(directory=TEMPLATES_DIR)

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
    template_path = os.path.join(TEMPLATES_DIR, "form.html")
    if not os.path.exists(template_path):
        logger.error("Template not found: %s", template_path)
        raise HTTPException(status_code=500, detail="Template not found")
    return templates.TemplateResponse("form.html", {"request": request})

@app.get("/autocomplete")
async def autocomplete(query: str = Query(..., min_length=1)):
    if len(query) < 2:
        return JSONResponse([])

    try:
        # Your actual autocomplete function
        from app.services.google_places import autocomplete_business
        results = autocomplete_business(query)
        return JSONResponse(results)
    except Exception:
        logger.exception("Autocomplete failed, returning fallback data")
        # Dummy fallback to prevent frontend crash
        return JSONResponse([
            {"name": "Test Business 1", "place_id": "dummy_1"},
            {"name": "Test Business 2", "place_id": "dummy_2"},
        ])

@app.post("/submit")
async def submit(data: SubmissionPayload = Body(...)):
    try:
        payload = data.model_dump()
        logger.info("Sending data to n8n: %s", payload)
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
