import numpy as np
import csv
from collections import defaultdict

# Function to generate linearly decaying weights
def generate_weights(start_year, end_year, start_weight=1.0, end_weight=0.0):
    years = list(range(start_year, end_year + 1))
    weights = np.linspace(start_weight, end_weight, len(years))
    return dict(zip(years, weights))

# Function to retrieve the weight for a given year
def get_weight_for_year(year, weights):
    return weights.get(year, 0)  # Default to 0 if year not found

# Function to calculate weighted averages across all years for each Station ID
def calculate_weighted_averages(input_csv, weights):
    weighted_sums = defaultdict(float)
    sum_of_weights = defaultdict(float)
    station_details = {}

    with open(input_csv, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            station_id = row['Station ID']
            year = int(row['Years'])
            weatherscore = float(row['Average Weatherscore'])
            latitude = row['Latitude']
            longitude = row['Longitude']
            name = row['Name']
            elevation = row['Elevation']

            if station_id not in station_details:
                station_details[station_id] = {
                    'Latitude': latitude,
                    'Longitude': longitude,
                    'Name': name,
                    'Elevation': elevation
                }

            weight = get_weight_for_year(year, weights)
            weighted_value = weatherscore * weight
            weighted_sums[station_id] += weighted_value
            sum_of_weights[station_id] += weight

    weighted_average = {station_id: weighted_sums[station_id] / sum_of_weights[station_id] for station_id in weighted_sums}
    return weighted_average, station_details

# Function to save the results
def save_weighted_averages_to_csv(weighted_average, station_details, output_csv):
    output_data = []
    for station_id, avg in weighted_average.items():
        station_info = station_details.get(station_id, {})
        output_data.append({
            'Station ID': station_id,
            'Latitude': station_info.get('Latitude', ''),
            'Longitude': station_info.get('Longitude', ''),
            'Name': station_info.get('Name', ''),
            'Elevation': station_info.get('Elevation', ''),
            'Weighted Average Weatherscore': avg
        })

    with open(output_csv, mode='w', newline='') as file:
        fieldnames = ['Station ID', 'Latitude', 'Longitude', 'Name', 'Elevation', 'Weighted Average Weatherscore']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_data)

    print(f"Weighted averages and station details saved to {output_csv}")

# Parameters
start_year = 1993
end_year = 2024
input_csv = 'input_data.csv'  # Replace with actual path
output_csv = 'output_data.csv'  # Replace with actual path

# Generate weights and process the data
weights = generate_weights(start_year, end_year, start_weight=0.0, end_weight=1.0)
weighted_average, station_details = calculate_weighted_averages(input_csv, weights)
save_weighted_averages_to_csv(weighted_average, station_details, output_csv)
