from fastapi import APIRouter, Depends
from typing import List
from fastapi import Depends, HTTPException
from sqlalchemy.orm import Session


from supporting_scripts.db_connection import (
    get_db,
    LocationRating,
    LocationRatingCreate,
)

router = APIRouter()


@router.get("/locationrating/all", response_model=List[LocationRatingCreate])
def get_location_ratings(db: Session = Depends(get_db)):
    return db.query(LocationRating).all()


@router.get("/locationrating/{locationrating_id}", response_model=LocationRatingCreate)
def get_LocationRating(location_rating_id: int, db: Session = Depends(get_db)):
    location_rating = (
        db.query(LocationRating).filter(LocationRating.ID == location_rating_id).first()
    )
    if location_rating is None:
        raise HTTPException(status_code=404, detail="LocationRating not found")
    return location_rating


@router.post("/locationrating", response_model=LocationRatingCreate)
def create_LocationRating(
    location_rating: LocationRatingCreate, db: Session = Depends(get_db)
):
    db_location_rating = LocationRating(
        Nuts2Code=location_rating.nuts_2_code,
        Country=location_rating.country,
        LocationName=location_rating.location_name,
        NumAccoms=location_rating.num_accoms,
        NetOccupancyRate=location_rating.net_ccupancy_rate,
        ArrivalsAccommodation=location_rating.arrivals_accommodation,
        ExpenditureAccomodation=location_rating.expenditure_accomodation,
        ExpenditureTrip=location_rating.expenditure_trip,
        HicpCountry=location_rating.hicp_country,
        LastUpdated=location_rating.last_updated,
    )
    db.add(db_location_rating)
    db.commit()
    db.refresh(db_location_rating)
    return db_location_rating
