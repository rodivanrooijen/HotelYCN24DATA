# main.py

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from func_scraping import scrape_booking_data
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import numpy as np
import base64
from io import BytesIO

app = FastAPI()
templates = Jinja2Templates(directory="templates")

@app.get("/")
async def root(request: Request):
    stad = 'Maastricht'
    checkin_datum = '2024-01-24'
    checkout_datum = '2024-01-25'
    num_volwassenen = 2
    num_kinderen = 0
    max_paginas = 2

    hotelgegevens = scrape_booking_data(stad, checkin_datum, checkout_datum, num_volwassenen, num_kinderen, max_paginas)

    hotelgegevens['naam'] = hotelgegevens['naam'].astype(str)
    hotelgegevens['locatie'] = hotelgegevens['locatie'].astype(str)
    hotelgegevens['prijs'] = pd.to_numeric(hotelgegevens['prijs'], errors='coerce').astype(pd.Int64Dtype())
    hotelgegevens['beoordeling'] = hotelgegevens['beoordeling'].str.replace(',', '.').astype(float)

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

    average_price = hotelgegevens['prijs'].mean()
    modus_price = hotelgegevens['prijs'].agg(pd.Series.mode)
    median_price = hotelgegevens['prijs'].median()

    return templates.TemplateResponse("result.html", {"request": request, "gemiddelde_prijs": average_price,
                                                      "modus_prijs": modus_price, "mediaan_prijs": median_price,
                                                      "plot_base64": plot_base64})
