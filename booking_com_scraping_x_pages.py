import pandas as pd
from func_scraping import scrape_booking_data
import seaborn as sns
import mplcursors
import matplotlib.pyplot as plt

# Specificeer invoerparameters en het maximale aantal pagina's om te scrapen
stad = 'Maastricht'
checkin_datum = '2024-01-23'
checkout_datum = '2024-01-24'
num_volwassenen = 2
num_kinderen = 0
max_paginas = 2  # Maximaal aantal paginas om te scrapen // Houd rekening met een vertraging van 5 seconden tussen pagina's

# Roep de functie aan om gegevens van meerdere pagina's te scrapen
hotelgegevens = scrape_booking_data(stad, checkin_datum, checkout_datum, num_volwassenen, num_kinderen, max_paginas)

# Sla de gegevens op in een CSV-bestand
#hotelgegevens.to_csv(f'C:/Users/rodiv/Desktop/YCN/Git/0. YCN_Public/0. Python/booking_com/hotels_{stad}_{checkin_datum}_{checkout_datum}_{num_volwassenen}_{num_kinderen}.csv', header=True, index=False)

# Zet de kolommen 'naam' en 'locatie' om naar het type 'string' (object blijft hetzelfde)
hotelgegevens['naam'] = hotelgegevens['naam'].astype(str)
hotelgegevens['locatie'] = hotelgegevens['locatie'].astype(str)

# Zet de kolom 'prijs' om naar het type 'integer' (als het mogelijk is)
hotelgegevens['prijs'] = pd.to_numeric(hotelgegevens['prijs'], errors='coerce').astype(pd.Int64Dtype())

# Zet de kolom 'beoordeling' om naar het type 'float' (als het mogelijk is)
hotelgegevens['beoordeling'] = hotelgegevens['beoordeling'].str.replace(',', '.').astype(float)

# Create a color palette based on unique locations
unique_locations = hotelgegevens['locatie'].unique()
color_palette = sns.color_palette('Set1', n_colors=len(unique_locations))

# Plot distributie van prijzen, beoordelingen en locaties van hotels
plt.figure(figsize=(12, 8))
for i, location in enumerate(unique_locations):
    subset = hotelgegevens[hotelgegevens['locatie'] == location]
    scatter = plt.scatter(subset['prijs'], subset['beoordeling'], color=color_palette[i], alpha=0.7, label=location)
    c = mplcursors.cursor(scatter, hover=False)  # Disable hover
    @c.connect("add")
    def _(sel):
        sel.annotation.get_bbox_patch().set(fc="white")
        sel.annotation.arrow_patch.set(arrowstyle="simple", fc="white", alpha=.5)
        sel.annotation.set_text(hotelgegevens.loc[sel.target.index]['naam'])
        sel.annotation.set_visible(True)  # Show annotation on click

plt.xlabel('Prijs', fontsize=12)
plt.ylabel('Beoordeling', fontsize=12)
plt.title('Verdeling van de Prijzen, Beoordelingen en Locaties van Hotels', fontsize=14)
plt.legend(fontsize=10)
plt.grid(True, linestyle='--', alpha=0.5)
plt.xticks(fontsize=10)
plt.yticks(fontsize=10)
plt.tight_layout()
plt.show()

# Calculate the average price per night based on location
average_price_per_location = hotelgegevens.groupby('locatie')['prijs'].mean()
modus_price_per_location = hotelgegevens.groupby('locatie')['prijs'].agg(pd.Series.mode)
median_price_per_location = hotelgegevens.groupby('locatie')['prijs'].median()

print(average_price_per_location)
print(modus_price_per_location)
print(median_price_per_location)

# Calculate the average price per night based on location
average_price = hotelgegevens['prijs'].mean()
modus_price = hotelgegevens['prijs'].agg(pd.Series.mode)
median_price = hotelgegevens['prijs'].median()

print("gemiddelde prijs: ", average_price)
print("modus: ", modus_price)
print("mediaan: ", median_price)

# Make a recommendation for your own hotel price based on location
#your_hotel_location = 'Maastricht'  # Replace with your own hotel location
#your_hotel_price = average_price_per_location[your_hotel_location] * 1.2  # Adjust the multiplier as needed

#print(f"Recommended price for your hotel in {your_hotel_location}: {your_hotel_price}")
