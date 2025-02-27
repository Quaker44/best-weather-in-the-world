import csv
from collections import defaultdict

# Function to retrieve the weight for a given year
def get_weight_for_year(year):
    weights = {
 2024: 1.0, 2023: 0.96666667, 2022: 0.93333333, 2021: 0.9, 
 2020: 0.86666667, 2019: 0.83333333, 2018: 0.8, 2017: 0.76666667,
 2016: 0.73333333, 2015: 0.7, 2014: 0.66666667, 2013: 0.63333333,
 2012: 0.6, 2011: 0.56666667, 2010: 0.53333333,  2009: 0.5,
 2008: 0.46666667, 2007: 0.43333333,  2006: 0.4, 2005: 0.36666667,
 2004: 0.33333333, 2003: 0.3, 2002: 0.26666667, 2001: 0.23333333,
 2000: 0.2, 1999: 0.16666667, 1998: 0.13333333, 1997: 0.1,
 1996: 0.06666667, 1995: 0.03333333, 1994: 0,
    }
    return weights.get(year, 0)  # Default to 0 if year not found in weights dictionary

# Function to calculate weighted averages across all years for each Station ID
def calculate_weighted_averages(input_csv):
    # Dictionary to hold the weighted sums and sum of weights for each Station ID
    weighted_sums = defaultdict(float)
    sum_of_weights = defaultdict(float)

    # Dictionary to store station details
    station_details = {}

    # Read data from the input CSV file
    with open(input_csv, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            station_id = row['Station ID']
            year = int(row['Years'])  # Assuming 'Years' is the column name for year
            weatherscore = float(row['Adjusted Average Weatherscore'])
            latitude = row['Latitude']
            longitude = row['Longitude']
            name = row['Name']
            elevation = row['Elevation']

            # Store station details if not already stored
            if station_id not in station_details:
                station_details[station_id] = {
                    'Latitude': latitude,
                    'Longitude': longitude,
                    'Name': name,
                    'Elevation': elevation
                }

            # Calculate weighted value for this entry
            weight = get_weight_for_year(year)
            weighted_value = weatherscore * weight

            # Accumulate weighted sums and sum of weights for this Station ID
            weighted_sums[station_id] += weighted_value
            sum_of_weights[station_id] += weight

    # Calculate the weighted average for each Station ID, skipping stations with <18 years of data

return weighted_average, station_details

# Function to save the weighted averages and station details to a CSV file
def save_weighted_averages_to_csv(weighted_average, station_details, output_csv):
    # Prepare data to write to the output CSV file
    output_data = []
    for station_id, avg in weighted_average.items():
        station_info = station_details.get(station_id, {})
        new_row = {
            'Station ID': station_id,
            'Latitude': station_info.get('Latitude', ''),
            'Longitude': station_info.get('Longitude', ''),
            'Name': station_info.get('Name', ''),
            'Elevation': station_info.get('Elevation', ''),
            'Weighted Average Weatherscore': avg
        }
        output_data.append(new_row)

    # Write the output data to the CSV file
    with open(output_csv, mode='w', newline='') as file:
        fieldnames = ['Station ID', 'Latitude', 'Longitude', 'Name', 'Elevation', 'Weighted Average Weatherscore']
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(output_data)

    print(f"Weighted averages and station details saved to {output_csv}")

# Input and Output locations:
input_csv = '/home/sam/Projects/best-weather-in-the-world/rankings75(21).csv'
output_csv = '/home/sam/Projects/best-weather-in-the-world/rankings75(21)(1).csv'  # Specify the output file name here

# Calculate weighted averages and station details
weighted_average, station_details = calculate_weighted_averages(input_csv)

# Save the weighted averages and station details to the specified CSV file
save_weighted_averages_to_csv(weighted_average, station_details, output_csv)
