from typing import List
import logging

from fastapi import FastAPI, Request, Body, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr, Field
import httpx

from app.services.google_places import autocomplete_business
from app.config import N8N_WEBHOOK_URL

from typing import List
import logging

from fastapi import FastAPI, Request, Body, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr, Field
import httpx
import os

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

# ✅ Correct template directory for Render
TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")
logger.info("Templates directory: %s", TEMPLATES_DIR)
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
    # Confirm template exists
    template_path = os.path.join(TEMPLATES_DIR, "form.html")
    if not os.path.exists(template_path):
        logger.error("Template not found: %s", template_path)
        raise HTTPException(status_code=500, detail="Template not found")
    return templates.TemplateResponse("form.html", {"request": request})


@app.get("/autocomplete")
async def autocomplete(query: str = Query(..., min_length=1)):
    # For now return dummy data to avoid Google Places errors
    if len(query) < 2:
        return JSONResponse([])
    try:
        from app.services.google_places import autocomplete_business
        results = autocomplete_business(query)
        return JSONResponse(results)
    except Exception:
        logger.exception("Autocomplete failed, returning dummy data")
        return JSONResponse([{"name": "Test Business", "place_id": "123"}])


@app.post("/submit")
async def submit(data: SubmissionPayload = Body(...)):
    from app.config import N8N_WEBHOOK_URL
    try:
        logger.info("Sending data to n8n")
        logger.info("Webhook URL: %s", N8N_WEBHOOK_URL)
        logger.info("Payload: %s", data.model_dump())

        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(N8N_WEBHOOK_URL, json=data.model_dump())
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
