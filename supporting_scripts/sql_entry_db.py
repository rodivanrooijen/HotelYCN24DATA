import mysql.connector
from datetime import date, timedelta
import random

# Connect to MySQL
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    passwd="",
    database="scraping"
)

# Create a cursor
cursor = conn.cursor()

# Define the hotel and kamertypes
hotel = 'Test Hotel'
kamertypes = ['een_persoons_kamer', 'twee_persoons_kamer', 'Familiekamer']

# Define date range
start_date = date(2024, 1, 1)
end_date = date(2024, 12, 31)

# Insert data into the database
current_date = start_date
while current_date <= end_date:
    for kamertype in kamertypes:
        if kamertype == 'een_persoons_kamer':
            prijs = 55  # Updated price for een_persoons_kamer
        elif kamertype == 'twee_persoons_kamer':
            prijs = 66
        elif kamertype == 'Familiekamer':
            prijs = 77
        query = "INSERT INTO prijzen (hotel, kamertype, prijs, datum) VALUES (%s, %s, %s, %s)"
        values = (hotel, kamertype, prijs, current_date)
        cursor.execute(query, values)

    current_date += timedelta(days=1)

# Commit changes and close connection
conn.commit()
cursor.close()
conn.close()
