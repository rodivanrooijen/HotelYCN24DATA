import base64
import datetime
from io import BytesIO
from fastapi import APIRouter, Depends, Query, Request, FastAPI
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from matplotlib import pyplot as plt
import seaborn as sns


from func_scraping import scrape_booking_data

app = FastAPI()
router = APIRouter()
templates = Jinja2Templates(directory="templates")

def get_input_parameters(
    stad: str = Query("Maastricht", description="The city name"),
    checkin_datum: str = Query("2024-01-25", description="Check-in date"),
    num_volwassenen: int = Query(2, description="Number of adults"),
    num_kinderen: int = Query(0, description="Number of children"),
    max_paginas: int = Query(2, description="Maximum pages to scrape"),
):
    return stad, checkin_datum, num_volwassenen, num_kinderen, max_paginas

@app.get("/scrapingresult")
async def scrapingresult(
    request: Request,
    input_params: tuple[str, str, int, int, int] = Depends(get_input_parameters),
):
    global last_execution_time, last_execution_status, hotelgegevens, stad, checkin_datum

    # Extract values from the tuple
    stad, checkin_datum, num_volwassenen, num_kinderen, max_paginas = input_params

    checkin_datum = datetime.strptime(checkin_datum, "%Y-%m-%d")
    checkout_datum = (checkin_datum + datetime.timedelta(days=1))
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