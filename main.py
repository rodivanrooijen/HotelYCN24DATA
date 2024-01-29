from fastapi import FastAPI
from src.hotel_cancelation import model
from src.best_location import main
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# import routers
from endpoints import start_scraping, scraping_result, price_analysis

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# all routers
app.include_router(start_scraping.router)  # endpoint: '/' & '/start_scraping'
app.include_router(
    scraping_result.router
)  # endpoint: '/scraping_result' & '/save_data' & '/load_data'
app.include_router(
    price_analysis.router
)  # endpoint: '/price_analysis' & '/get_prices_by_date'


@app.get("/model")
async def read_item():
    return model()


@app.get("/best_location")
async def location():
    best_location_list = main()
    return best_location_list
