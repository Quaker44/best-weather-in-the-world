import csv
from collections import defaultdict

# Function to retrieve the weight for a given year
def get_weight_for_year(year):
    weights = {
        1994: 0.1000, 1995: 0.1083, 1996: 0.1172, 1997: 0.1269, 1998: 0.1374,
        1999: 0.1487, 2000: 0.1610, 2001: 0.1743, 2002: 0.1887, 2003: 0.2043,
        2004: 0.2212, 2005: 0.2395, 2006: 0.2593, 2007: 0.2807, 2008: 0.3039,
        2009: 0.3290, 2010: 0.3562, 2011: 0.3857, 2012: 0.4175, 2013: 0.4520,
        2014: 0.4894, 2015: 0.5298, 2016: 0.5736, 2017: 0.6210, 2018: 0.6723,
        2019: 0.7279, 2020: 0.7880, 2021: 0.8532, 2022: 0.9237, 2023: 1.0000
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
            weatherscore = float(row['Average Weatherscore'])
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

    # Calculate the weighted average for each Station ID
    weighted_average = {}
    for station_id in weighted_sums:
        weighted_average[station_id] = weighted_sums[station_id] / sum_of_weights[station_id]

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
input_csv = '/home/sam/PycharmProjects/best-weather-in-the-world/WinterVaca/JanVacaRankings(3).csv'
output_csv = '/home/sam/PycharmProjects/best-weather-in-the-world/WinterVaca/JanVacaRankings(4).csv'  # Specify the output file name here

# Calculate weighted averages and station details
weighted_average, station_details = calculate_weighted_averages(input_csv)

# Save the weighted averages and station details to the specified CSV file
save_weighted_averages_to_csv(weighted_average, station_details, output_csv)
