import pandas as pd
import simplekml

# Read the CSV file
csv_file =r'C:\Users\samuel.purinton\Downloads\final_ranking_temps75_with_percentiles.csv'
data = pd.read_csv(csv_file)

# Filter the data based on the percentile column
filtered_data = data[data['Percentile'] < 1]

# Create a KML object
kml = simplekml.Kml()

# Iterate over the filtered data and add placemarks to the KML file
for _, row in filtered_data.iterrows():
    kml.newpoint(
        name=row['Name'],
        coords=[(row['Longitude'], row['Latitude'])],
        description=f"Percentile: {row['Percentile']}"
    )

# Save the KML file
kml.save("filtered_locations.kml")

print("KML file 'filtered_locations.kml' created successfully.")
