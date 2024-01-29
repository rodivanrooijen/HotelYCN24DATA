
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.session import Session

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