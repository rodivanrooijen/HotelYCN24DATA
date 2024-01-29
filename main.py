# import libraries
from fastapi import FastAPI, Request, Query, Depends, APIRouter
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# import routers
import start_scraping, scraping_result, price_analysis

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# all routers 
app.include_router(start_scraping.router) # endpoint: '/' 
app.include_router(scraping_result.router) # endpoint: '/scraping_result' & '/save_data' & '/load_data'
app.include_router(price_analysis.router)  # endpoint: '/price_analysis' & '/get_prices_by_date'