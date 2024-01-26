# import libraries
from fastapi import FastAPI, Request, Query, Depends, APIRouter
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import StreamingResponse, JSONResponse, HTMLResponse
from func_scraping import scrape_booking_data
import pandas as pd
import matplotlib.pyplot as plt
import base64
from io import BytesIO
from datetime import datetime, timedelta, date
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
import os
import calendar as cal_module
from typing import Optional

import start_scraping, scraping_result

# Connect to MySQL database
DATABASE_URL = "mysql+mysqlconnector://root:@localhost/scraping"

# Database setup using SQLite (you can replace it with your preferred database)
engine = create_engine(DATABASE_URL)
Base = declarative_base()

class HotelData(Base):
    __tablename__ = "hotel_data"

    id = Column(Integer, primary_key=True, index=True)
    stad = Column(String(255), index=True)
    checkin_datum = Column(String(20))  # Specify the length here (adjust as needed)
    checkout_datum = Column(String(20))  # Specify the length here (adjust as needed)
    num_volwassenen = Column(Integer)
    num_kinderen = Column(Integer)
    naam = Column(String(255))  # Add columns for name, location, price, and rating
    locatie = Column(String(255))
    prijs = Column(Float)
    beoordeling = Column(Float)
    last_execution_time = Column(DateTime)

class Prijzen(Base):
    __tablename__ = "prijzen"

    id = Column(Integer, primary_key=True, index=True)
    hotel = Column(String(255), index=True)
    kamertype = Column(String(255))
    prijs = Column(Float)
    datum = Column(DateTime)

Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global variables
hotelgegevens = None
last_execution_time = None
last_execution_status = None
stad = None
checkin_datum = None
checkout_datum = None
num_volwassenen = None
num_kinderen = None
max_paginas = None

# Helper function to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_input_parameters(
    stad: str = Query("Maastricht", description="The city name"),
    checkin_datum: str = Query("2024-01-25", description="Check-in date"),
    num_volwassenen: int = Query(2, description="Number of adults"),
    num_kinderen: int = Query(0, description="Number of children"),
    max_paginas: int = Query(2, description="Maximum pages to scrape"),
):
    return stad, checkin_datum, num_volwassenen, num_kinderen, max_paginas

app.include_router(start_scraping.router)
app.include_router(scraping_result.router)    


@app.post("/save_data")
async def save_data():
    global hotelgegevens

    if hotelgegevens is not None and not hotelgegevens.empty:
        # Voeg inputparameters toe aan DataFrame
        hotelgegevens["Stad"] = stad
        hotelgegevens["Checkin_datum"] = checkin_datum
        hotelgegevens["Checkout_datum"] = checkout_datum
        hotelgegevens["Num_volwassenen"] = num_volwassenen
        hotelgegevens["Num_kinderen"] = num_kinderen

        # Voeg een datum/tijdstempelkolom toe
        hotelgegevens["Datum_tijd_stempel"] = datetime.now()

        # Specify the directory where you want to save the CSV file
        save_directory = "csv_data"  # Replace with your folder path

        # Ensure the directory exists, create it if not
        os.makedirs(save_directory, exist_ok=True)

        # Generate the full path for the CSV file
        filename = f"hotel_data_{stad}_{datetime.now().strftime('%Y%m%d%H%M%S')}.csv"
        filepath = os.path.join(save_directory, filename)

        # Sla de gegevens op als CSV-bestand
        hotelgegevens.to_csv(filepath, index=False)

        # Stuur het CSV-bestand als download naar de gebruiker
        content = hotelgegevens.to_csv(index=False)
        response = StreamingResponse(iter([content]), media_type="text/csv")
        response.headers["Content-Disposition"] = f"attachment; filename={filename}"
        return response
    else:
        return {"message": "Geen data beschikbaar om op te slaan."}
    
@app.post("/load_data")
async def load_data(
    input_params: tuple[str, str, int, int, int] = Depends(get_input_parameters),
    db: Session = Depends(get_db)
):
    global hotelgegevens

    # Extract values from the tuple
    stad, checkin_datum, num_volwassenen, num_kinderen, max_paginas = input_params

    if hotelgegevens is not None and not hotelgegevens.empty:
        for _, row in hotelgegevens.iterrows():
            # Check if a matching row exists in the database
            existing_hotel = db.query(HotelData).filter_by(
                naam=row['naam'],
                checkout_datum=checkout_datum,
                checkin_datum=checkin_datum,
                num_volwassenen=num_volwassenen,
                num_kinderen=num_kinderen
            ).first()

            if existing_hotel:
                # Update the 'prijs' and 'beoordeling' of the existing row
                existing_hotel.prijs = row['prijs']
                existing_hotel.beoordeling = row['beoordeling']
                existing_hotel.last_execution_time = datetime.now()
            else:
                # Insert a new row
                db_data = HotelData(
                    stad=stad,
                    checkin_datum=checkin_datum,
                    checkout_datum=checkout_datum,
                    num_volwassenen=num_volwassenen,
                    num_kinderen=num_kinderen,
                    last_execution_time=datetime.now(),
                    naam=row['naam'],
                    locatie=row['locatie'],
                    prijs=row['prijs'],
                    beoordeling=row['beoordeling']
                )
                db.add(db_data)

        db.commit()
        return JSONResponse(content={"message": "Data successfully loaded into the database."})
    else:
        return JSONResponse(content={"message": "No data available to load into the database."})
    
@app.get("/price_analysis", response_class=HTMLResponse)
async def price_analysis(request: Request, db: Session = Depends(get_db)):
    # Ophalen van unieke waarden voor hotels en kamertypes uit de tabel "prijzen"
    hotels = db.query(Prijzen.hotel).distinct().all()
    kamertypes = db.query(Prijzen.kamertype).distinct().all()

    hotels = [hotel[0] for hotel in hotels]
    kamertypes = [kamertype[0] for kamertype in kamertypes]

    # Fetch prices from the database
    prices = db.query(Prijzen.hotel, Prijzen.kamertype, Prijzen.prijs, Prijzen.datum).all()

    # Organize prices by hotel and room type
    prices_by_hotel_and_room = {}
    for price in prices:
        hotel = price[0]
        kamertype = price[1]
        prijs = price[2]
        datum = price[3].strftime("%Y-%m-%d")

        if hotel not in prices_by_hotel_and_room:
            prices_by_hotel_and_room[hotel] = {}

        if kamertype not in prices_by_hotel_and_room[hotel]:
            prices_by_hotel_and_room[hotel][kamertype] = {}

        prices_by_hotel_and_room[hotel][kamertype][datum] = prijs

    return templates.TemplateResponse(
        "price_analysis.html",
        {"request": request, "hotels": hotels, "kamertypes": kamertypes, "prices_by_date": prices_by_hotel_and_room},
    )

router = APIRouter()

# Define the new endpoint
@router.get("/get_prices_by_date")
async def get_prices_by_date(hotel: str, kamertype: str, db: Session = Depends(get_db)):
    """
    Endpoint to fetch prices based on the selected hotel and kamertype.

    Parameters:
    - hotel: The selected hotel from the dropdown.
    - kamertype: The selected kamertype from the dropdown.

    Returns:
    - A JSON response containing prices by date.
    """
    prices_by_date = {}

    # Query the database to get prices based on the selected hotel and kamertype
    prices = db.query(Prijzen.datum, Prijzen.prijs).filter_by(hotel=hotel, kamertype=kamertype).all()

    for date, price in prices:
        # Format the date if needed
        formatted_date = date.strftime("%Y-%m-%d")
        prices_by_date[formatted_date] = price

    return prices_by_date

app.include_router(router)