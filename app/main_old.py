from typing import List
import logging
import os

from fastapi import FastAPI, Request, HTTPException, Query
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
# Fix Template Path (IMPORTANT)
# -------------------------
# BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# templates = Jinja2Templates(directory=os.path.join(BASE_DIR, "templates"))
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

templates = Jinja2Templates(
    directory=os.path.join(BASE_DIR,"app", "templates")
)
# -------------------------
# App
# -------------------------
app = FastAPI()

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
    return templates.TemplateResponse(
        request,                 # ✅ FIRST argument
        "form.html",             # ✅ template name
        {"request": request}     # ✅ context
    )

@app.get("/autocomplete")
async def autocomplete(query: str = Query(..., min_length=2)):
    try:
        results = await autocomplete_business(query)
        return JSONResponse(results)

    except Exception:
        logger.exception("Autocomplete failed")
        raise HTTPException(status_code=500, detail="Autocomplete failed")


@app.post("/submit")
async def submit(data: SubmissionPayload):
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
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
