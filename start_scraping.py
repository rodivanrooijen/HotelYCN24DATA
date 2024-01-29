#start_scraping.py
from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_input_parameters(
    stad: str = Query("Maastricht", description="The city name"),
    checkin_datum: str = Query("2024-01-29", description="Check-in date"),
    num_volwassenen: int = Query(2, description="Number of adults"),
    num_kinderen: int = Query(0, description="Number of children"),
    max_paginas: int = Query(2, description="Maximum pages to scrape"),
):
    return stad, checkin_datum, num_volwassenen, num_kinderen, max_paginas


@router.get("/", response_class=HTMLResponse)
async def show_form(request: Request):
    return templates.TemplateResponse("startscraping.html", {"request": request})

    