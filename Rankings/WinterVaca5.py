import os
import glob
import csv
import math

# Constants for Weatherscore calculation
WEATHERSCORE_BASE = 80  # Base value for heat index comparison
WEATHERSCORE_HEAT_INDEX_DIFF = 1  # Score increment per degree difference from base
WEATHERSCORE_WDSP_THRESHOLD = 12  # Wind speed threshold for additional score
WEATHERSCORE_WDSP_FACTOR = 2  # Score increment per degree above WDSP_THRESHOLD
WEATHERSCORE_FRSHTT_RULES = {
    1: 10,   # Effect for the first digit being 1
    2: 20,  # Effect for the second digit being 1
    3: -25, # Effect for the third digit being 1
    4: 20,  # Effect for the fourth digit being 1
    5: 10,  # Effect for the fifth digit being 1
    6: 50   # Effect for the sixth digit being 1
}

def fahrenheit_to_celsius(fahrenheit):
    return (fahrenheit - 32) * 5.0 / 9.0

def celsius_to_fahrenheit(celsius):
    return (celsius * 9.0 / 5.0) + 32

def calculate_relative_humidity(temperature_f, dew_point_f):
    # Convert temperatures from Fahrenheit to Celsius
    temperature_c = fahrenheit_to_celsius(temperature_f)
    dew_point_c = fahrenheit_to_celsius(dew_point_f)

    # Calculate saturation vapor pressure for the temperature
    e_s = 6.11 * math.exp(17.625 * temperature_c / (243.04 + temperature_c))

    # Calculate actual vapor pressure for the dew point
    e_d = 6.11 * math.exp(17.625 * dew_point_c / (243.04 + dew_point_c))

    # Calculate relative humidity
    relative_humidity = (e_d / e_s) * 100

    return relative_humidity

def simple_heat_index(temperature, humidity):
    return 0.5 * (
        temperature + 61.0 + ((temperature - 68.0) * 1.2) + (humidity * 0.094)
    )

def calculate_heat_index(temperature, humidity):
    # Constants for the heat index equation
    c1 = -42.379
    c2 = 2.04901523
    c3 = 10.14333127
    c4 = -0.22475541
    c5 = -6.83783 * (10 ** -3)
    c6 = -5.481717 * (10 ** -2)
    c7 = 1.22874 * (10 ** -3)
    c8 = 8.5282 * (10 ** -4)
    c9 = -1.99 * (10 ** -6)

    # Determine whether to use the heat index equation with adjustments
    simple_hi = simple_heat_index(temperature, humidity)
    if simple_hi < 80:
        return temperature

    # Calculate the initial heat index using the NOAA formula
    heat_index = (
        c1
        + (c2 * temperature)
        + (c3 * humidity)
        + (c4 * temperature * humidity)
        + (c5 * temperature ** 2)
        + (c6 * humidity ** 2)
        + (c7 * temperature ** 2 * humidity)
        + (c8 * temperature * humidity ** 2)
        + (c9 * temperature ** 2 * humidity ** 2)
    )

    # Check conditions for applying the first adjustment
    if humidity < 13 and 80 <= temperature <= 112:
        adjustment = ((13 - humidity) / 4) * math.sqrt(
            (17 - abs(temperature - 95)) / 17
        )
        heat_index -= adjustment

    # Check conditions for applying the second adjustment
    if humidity > 85 and 80 <= temperature <= 87:
        adjustment = ((humidity - 85) / 10) * ((87 - temperature) / 5)
        heat_index += adjustment

    return heat_index

def calculate_weatherscore(heat_index, wdsp, frshtt):
    weatherscore = abs(heat_index - WEATHERSCORE_BASE) * WEATHERSCORE_HEAT_INDEX_DIFF

    if wdsp > WEATHERSCORE_WDSP_THRESHOLD:
        weatherscore += (wdsp - WEATHERSCORE_WDSP_THRESHOLD) * WEATHERSCORE_WDSP_FACTOR

    frshtt = int(frshtt)  # Convert FRSHTT to integer for processing
    for i in range(1, 7):
        if frshtt % 10 == 1:
            if i in WEATHERSCORE_FRSHTT_RULES:
                weatherscore += WEATHERSCORE_FRSHTT_RULES[i]
        frshtt //= 10

    return weatherscore

def calculate_average_weatherscore(csv_file, target_month):
    total_scores = 0
    num_rows = 0

    with open(csv_file, mode='r') as file:
        csv_reader = csv.DictReader(file)
        all_frshtt_zero = True

        for row in csv_reader:
            date = row['DATE']
            # Extract month from date and check if it matches the target month
            month = date[5:7]  # Extract month as 'MM'
            if month != target_month:
                continue

            temperature_f = float(row['MAX'])
            dew_point_f = float(row['DEWP'])

            # Check if all FRSHTT values are '000000'
            if any(row['FRSHTT'][i] != '0' for i in range(6)):
                all_frshtt_zero = False

            # Skip rows where temperature or dew point is 9999.9
            if temperature_f == 9999.9 or dew_point_f == 9999.9:
                continue

            num_rows += 1

            relative_humidity = calculate_relative_humidity(temperature_f, dew_point_f)
            heat_index = calculate_heat_index(temperature_f, relative_humidity)
            wdsp = float(row['WDSP'])
            frshtt = row['FRSHTT']

            weatherscore = calculate_weatherscore(heat_index, wdsp, frshtt)
            total_scores += weatherscore

        # Check conditions to skip the file
        if all_frshtt_zero or num_rows < 27:
            return None

    if num_rows > 0:
        average_weatherscore = total_scores / num_rows
        return average_weatherscore
    else:
        return None

def save_average_weatherscore(csv_file, output_file, file_number, target_month):
    station_metadata = {}
    average_weatherscore = calculate_average_weatherscore(csv_file, target_month)

    if average_weatherscore is None:
        print(f"Skipping file {csv_file} due to all FRSHTT values being '000000' or fewer than 27 valid scores.")
        return

    with open(csv_file, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            station_id = row['STATION']
            if station_id not in station_metadata:
                station_metadata[station_id] = {
                    'latitude': row['LATITUDE'],
                    'longitude': row['LONGITUDE'],
                    'name': row['NAME'],
                    'elevation': row['ELEVATION'],
                    'years': []
                }
            year = row['DATE'][:4]
            if year not in station_metadata[station_id]['years']:
                station_metadata[station_id]['years'].append(year)

    fieldnames = ['Station ID', 'Latitude', 'Longitude', 'Name', 'Elevation', 'Years', 'Month', 'Average Weatherscore']

    # Append to output_file instead of creating a new one each time
    with open(output_file, mode='a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        for station_id, metadata in station_metadata.items():
            writer.writerow({
                'Station ID': station_id,
                'Latitude': metadata['latitude'],
                'Longitude': metadata['longitude'],
                'Name': metadata['name'],
                'Elevation': metadata['elevation'],
                'Years': ', '.join(metadata['years']),
                'Month': target_month,
                'Average Weatherscore': average_weatherscore
            })

    print(f"{file_number}th file average Weatherscore for month {target_month} added to {output_file}")

def process_directory(directory, output_file, target_month):
    # Initialize output file with headers if it doesn't exist
    if not os.path.exists(output_file):
        with open(output_file, mode='w', newline='') as csvfile:
            fieldnames = ['Station ID', 'Latitude', 'Longitude', 'Name', 'Elevation', 'Years', 'Month', 'Average Weatherscore']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

    # Get all CSV files in the specified directory
    csv_files = glob.glob(os.path.join(directory, '*.csv'))

    for idx, csv_file in enumerate(csv_files, start=1):
        save_average_weatherscore(csv_file, output_file, idx, target_month)

    print(f"All average Weatherscores with station metadata for month {target_month} appended to {output_file}")

# Example usage to process all CSV files in a directory and append results to a single CSV file
directory = '/home/sam/Documents/ISD_Data/1994'
output_file = '/home/sam/PycharmProjects/best-weather-in-the-world/WinterVaca/JanVacaRankings(3).csv'
target_month = '01'  # Specify the month you are interested in (e.g., '01' for January)
process_directory(directory, output_file, target_month)
