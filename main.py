from fastapi import FastAPI
from hotel_cancelation import model
from best_location import main
app = FastAPI()


@app.get("/model")
async def read_item():
    return model()

@app.get("/best_location")
async def location():
    best_location_list = main()
    return best_location_list

