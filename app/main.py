from typing import List
import logging

from fastapi import FastAPI, Request, Body, HTTPException, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, EmailStr, Field
import httpx

from services.google_places import autocomplete_business
from config import N8N_WEBHOOK_URL

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
templates = Jinja2Templates(directory="templates")

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
    return templates.TemplateResponse("form.html", {"request": request})


@app.get("/autocomplete")
<<<<<<< HEAD
async def autocomplete(query: str = Query(..., min_length=2)):
    try:
        results = autocomplete_business(query)
        return JSONResponse(results)
=======
async def autocomplete(query: str = Query(..., min_length=1)):
    if len(query) < 2:
        return JSONResponse([])

    try:
        return JSONResponse(autocomplete_business(query))
>>>>>>> 3a63f1bb408dea3f920db3e9c311ba417b7d77a2
    except Exception:
        logger.exception("Autocomplete failed")
        raise HTTPException(status_code=500, detail="Autocomplete failed")


@app.post("/submit")
async def submit(data: SubmissionPayload = Body(...)):
    try:
<<<<<<< HEAD
        logger.info("Sending to n8n: %s", data.model_dump())

        async with httpx.AsyncClient(timeout=10.0) as client:
=======
        logger.info("Sending data to n8n")
        logger.info("Webhook URL: %s", N8N_WEBHOOK_URL)
        logger.info("Payload: %s", data.model_dump())

        async with httpx.AsyncClient(timeout=5.0) as client:
>>>>>>> 3a63f1bb408dea3f920db3e9c311ba417b7d77a2
            resp = await client.post(
                N8N_WEBHOOK_URL,
                json=data.model_dump(),
            )
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