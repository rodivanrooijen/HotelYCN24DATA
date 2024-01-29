import base64
import datetime
from io import BytesIO
from fastapi import APIRouter, Depends, Query, Request, FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from matplotlib import pyplot as plt
import seaborn as sns
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session
from start_scraping import get_input_parameters
from datetime import datetime, timedelta
import pandas as pd
import os


from func_scraping import scrape_booking_data

router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_input_parameters(
    stad: str = Query("Maastricht", description="The city name"),
    checkin_datum: str = Query("2024-01-30", description="Check-in date"),
    num_volwassenen: int = Query(2, description="Number of adults"),
    num_kinderen: int = Query(0, description="Number of children"),
    max_paginas: int = Query(2, description="Maximum pages to scrape"),
):
    return stad, checkin_datum, num_volwassenen, num_kinderen, max_paginas

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

# Helper function to get database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/scrapingresult")
async def scrapingresult(
    request: Request,
    input_params: tuple[str, str, int, int, int] = Depends(get_input_parameters),
):
    global last_execution_time, last_execution_status, hotelgegevens, stad, checkin_datum, checkout_datum, num_volwassenen, num_kinderen, max_paginas

    # Extract values from the tuple
    stad, checkin_datum, num_volwassenen, num_kinderen, max_paginas = input_params

    checkin_datum = datetime.strptime(checkin_datum, "%Y-%m-%d")
    checkout_datum = (checkin_datum + timedelta(days=1))
    checkin_datum = checkin_datum.strftime("%Y-%m-%d")
    checkout_datum = checkout_datum.strftime("%Y-%m-%d")
    # max_paginas = 2

    # Use the user-provided values
    stad = stad
    checkin_datum = checkin_datum
    checkout_datum = checkout_datum
    num_volwassenen = num_volwassenen
    num_kinderen = num_kinderen
    max_paginas = max_paginas

    hotelgegevens = scrape_booking_data(stad, checkin_datum, checkout_datum, num_volwassenen, num_kinderen, max_paginas)

    hotelgegevens['naam'] = hotelgegevens['naam'].astype(str)
    hotelgegevens['locatie'] = hotelgegevens['locatie'].astype(str)
    hotelgegevens['prijs'] = pd.to_numeric(hotelgegevens['prijs'], errors='coerce').astype(pd.Int64Dtype())
    hotelgegevens['beoordeling'] = hotelgegevens['beoordeling'].str.replace(',', '.').astype(float)

    last_execution_time = datetime.now().strftime("%d/%m/%Y %H:%M:%S")

    # Bijwerken van de uitvoeringsstatus
    if hotelgegevens.empty:
        last_execution_status = "Old data from data archive"
    else:
        last_execution_status = "Live"

    unique_locations = hotelgegevens['locatie'].unique()
    color_palette = sns.color_palette('Set1', n_colors=len(unique_locations))

    plt.figure(figsize=(8, 6))
    for i, location in enumerate(unique_locations):
        subset = hotelgegevens[hotelgegevens['locatie'] == location]
        scatter = plt.scatter(subset['prijs'], subset['beoordeling'], color=color_palette[i], alpha=0.7, label=location)

    plt.xlabel('Prijs', fontsize=12)
    plt.ylabel('Beoordeling', fontsize=12)
    plt.title('Verdeling van de Prijzen, Beoordelingen en Locaties van Hotels', fontsize=14)
    plt.legend(fontsize=10)
    plt.grid(True, linestyle='--', alpha=0.5)
    plt.xticks(fontsize=10)
    plt.yticks(fontsize=10)
    plt.tight_layout()

    # Save the plot to an in-memory buffer
    buffer = BytesIO()
    plt.savefig(buffer, format="png")
    buffer.seek(0)
    plot_base64 = base64.b64encode(buffer.getvalue()).decode("utf-8")


    #Bereken gemiddelde, modus en mediaan van de prijzen
    average_price = hotelgegevens['prijs'].mean()
    modus_price = hotelgegevens['prijs'].agg(pd.Series.mode)
    modus_price = modus_price[0]
    median_price = hotelgegevens['prijs'].median()

    # Plot a bar chart for price distribution
    plt.figure(figsize=(8, 6))
    sns.histplot(hotelgegevens['prijs'], bins=40, kde=False, color="skyblue")
    plt.title("Price Distribution")
    plt.xlabel("Price")
    plt.ylabel("Frequency")

    # Add text annotations for average_price and median_price
    plt.axvline(x=average_price, color='red', linestyle='--', linewidth=2, label=f'Average Price: €{average_price:.2f}')
    plt.axvline(x=median_price, color='green', linestyle='--', linewidth=2, label=f'Median: €{median_price:.2f}')
    plt.axvline(x=modus_price, color='blue', linestyle='--', linewidth=2, label=f'Modus: €{modus_price:.2f}')

    plt.legend()  # Show legend with annotations

    # Save the plot to a BytesIO object
    image_stream = BytesIO()
    plt.savefig(image_stream, format="png")
    image_stream.seek(0)

    # Encode the image to base64 for embedding in HTML
    image_base64 = base64.b64encode(image_stream.read()).decode("utf-8")

    # Close the plot to release resources
    plt.close()

    return templates.TemplateResponse("result.html", {"request": request, 
                                                      "stad" : stad,
                                                      "checkin_datum": checkin_datum,
                                                      "checkout_datum": checkout_datum,
                                                      "num_volwassenen": num_volwassenen,
                                                      "num_kinderen": num_kinderen,
                                                      "max_paginas": max_paginas,
                                                      "gemiddelde_prijs": average_price,
                                                      "modus_prijs": modus_price, 
                                                      "mediaan_prijs": median_price,
                                                      "plot_base64": plot_base64,
                                                      "image_base64": image_base64,
                                                      "last_execution_time": last_execution_time,
                                                      "last_execution_status": last_execution_status})

@router.post("/save_data")
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
    
@router.post("/load_data")
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
    