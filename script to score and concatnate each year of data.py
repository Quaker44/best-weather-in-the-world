import os
import glob
import csv
import math
import statistics
from collections import defaultdict

# Constants for Weatherscore calculation
WEATHERSCORE_BASE = 75  # Base value for heat index comparison
WEATHERSCORE_HEAT_INDEX_DIFF = 1  # Score increment per degree difference from base
WEATHERSCORE_WDSP_THRESHOLD = 21  # Includes Fresh Breeze gusts 
WEATHERSCORE_WDSP_FACTOR = 1  # Score increment per degree above WDSP_THRESHOLD

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

def calculate_weatherscore(heat_index, wdsp):    
    weatherscore = abs(heat_index - WEATHERSCORE_BASE) * WEATHERSCORE_HEAT_INDEX_DIFF

    if wdsp > WEATHERSCORE_WDSP_THRESHOLD:
        weatherscore += (wdsp - WEATHERSCORE_WDSP_THRESHOLD) * WEATHERSCORE_WDSP_FACTOR

    return weatherscore

    total_scores = 0
    num_rows = 0

    with open(csv_file, mode='r') as file:
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            temperature_f = float(row['MAX'])
            dew_point_f = float(row['DEWP'])
            wdsp = float(row['GUST'])
            mxspd = float(rpw['MXSDP'])

            # Skip rows where temperature or dew point or wind speed is 9999.9
            if temperature_f == 9999.9 or dew_point_f == 9999.9 or mxspd == 999.9:
                continue
            if wdsp == 999.9:
                wdsp = mxspd

            num_rows += 1

            relative_humidity = calculate_relative_humidity(temperature_f, dew_point_f)
            heat_index = calculate_heat_index(temperature_f, relative_humidity)
            wdsp = float(row['GUST'])

            weatherscore = calculate_weatherscore(heat_index, wdsp)
            total_scores += weatherscore

    if num_rows >= 5: #99% confidence interval 10% MOE
        average_weatherscore = total_scores / num_rows
        annual_weatherscore = average_weatherscore
        return annual_weatherscore, num_rows
    else:
        return None, num_rows

    station_metadata = {}
    annual_weatherscore, num_rows = calculate_average_weatherscore(csv_file)

    if annual_weatherscore is None:
        print(f"Skipping file {csv_file} due to having only {num_rows} scores.")
        return False

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

    fieldnames = ['Station ID', 
                    'Latitude', 
                    'Longitude', 
                    'Name', 
                    'Elevation', 
                    'Years', 
                    'Average Weatherscore', 
                    'N'
                ]

    # Append to output_file
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
                'Average Weatherscore': annual_weatherscore,
                'N': num_rows
            })

    print(f"{file_number}th file added to {output_file}")
    return True

def calculate_margin_of_error(scores, confidence=0.99):
    if len(scores) < 2:
        return None  # Not enough data to compute MOE
    
    sample_std_dev = statistics.stdev(scores)
    standard_error = sample_std_dev / math.sqrt(len(scores))
    z_score = 2.576  # 99% confidence level
    return z_score * standard_error

def calculate_average_weatherscore(csv_file):
    total_scores = 0
    num_rows = 0
    scores = []

    with open(csv_file, mode='r') as file:
        csv_reader = csv.DictReader(file)

        for row in csv_reader:
            try:
                temperature_f = float(row['MAX'])
                dew_point_f = float(row['DEWP'])
                wdsp = float(row['GUST'])
                mxspd = float(row['MXSPD'])
                
                if temperature_f == 9999.9 or dew_point_f == 9999.9 or mxspd == 999.9:
                    continue
                if wdsp == 999.9:
                    wdsp = mxspd
                
                num_rows += 1
                relative_humidity = calculate_relative_humidity(temperature_f, dew_point_f)
                heat_index = calculate_heat_index(temperature_f, relative_humidity)
                weatherscore = calculate_weatherscore(heat_index, wdsp)
                total_scores += weatherscore
                scores.append(weatherscore)
            except ValueError:
                continue

    if num_rows >= 5:  # 99% confidence interval threshold
        average_weatherscore = total_scores / num_rows
        margin_of_error = calculate_margin_of_error(scores)
        return average_weatherscore, margin_of_error, num_rows
    else:
        return None, None, num_rows

def save_annual_weatherscore(csv_file, output_file, file_number):
    station_metadata = {}
    annual_weatherscore, margin_of_error, num_rows = calculate_average_weatherscore(csv_file)
    
    if annual_weatherscore is None:
        print(f"Skipping file {csv_file} due to insufficient data ({num_rows} rows).")
        return False
    
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

    fieldnames = ['Station ID', 'Latitude', 'Longitude', 'Name', 'Elevation', 'Years', 'Average Weatherscore', 'Margin of Error', 'N']
    
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
                'Average Weatherscore': annual_weatherscore,
                'Margin of Error': margin_of_error,
                'N': num_rows
            })

    print(f"{file_number}th file added to {output_file}")
    return True

def process_directory(directory, output_file):
    # Initialize output file with headers if it doesn't exist
    if not os.path.exists(output_file):
        with open(output_file, mode='w', newline='') as csvfile:
            fieldnames = ['Station ID', 'Latitude', 'Longitude', 'Name', 'Elevation', 'Years', 'Average Weatherscore', 'Margin of Error', 'N']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()

    skipped_files_count = 0

    # Get all CSV files
    csv_files = glob.glob(os.path.join(directory, '2024', '*.csv'), recursive=True)
    
    #one year at a time
    #csv_files = glob.glob(os.path.join(directory, '*.csv'))


    for idx, csv_file in enumerate(csv_files, start=1):
        if not save_annual_weatherscore(csv_file, output_file, idx):
            skipped_files_count += 1

    print(f"All annual average Weatherscores with station metadata appended to {output_file}")
    print(f"Skipped {skipped_files_count} files.")

# Example usage to process all CSV files in a directory and append results to a single CSV file
directory = '/home/sam/Documents/ISD_Data/'
output_file = '/home/sam/Projects/best-weather-in-the-world/2024rankings60(21).csv'
process_directory(directory, output_file)

# Dictionary mapping country codes to country names
countries = {
    'AA': 'ARUBA',
    'AC': 'ANTIGUA AND BARBUDA',
    'AF': 'AFGHANISTAN',
    'AG': 'ALGERIA',
    'AI': 'ASCENSION ISLAND',
    'AJ': 'AZERBAIJAN',
    'AL': 'ALBANIA',
    'AM': 'ARMENIA',
    'AN': 'ANDORRA',
    'AO': 'ANGOLA',
    'AQ': 'AMERICAN SAMOA',
    'AR': 'ARGENTINA',
    'AS': 'AUSTRALIA',
    'AT': 'ASHMORE AND CARTIER ISLANDS',
    'AU': 'AUSTRIA',
    'AV': 'ANGUILLA',
    'AX': 'ANTIGUA, ST. KITTS, NEVIS, BARBUDA',
    'AY': 'ANTARCTICA',
    'AZ': 'AZORES',
    'BA': 'BAHRAIN',
    'BB': 'BARBADOS',
    'BC': 'BOTSWANA',
    'BD': 'BERMUDA',
    'BE': 'BELGIUM',
    'BF': 'BAHAMAS THE',
    'BG': 'BANGLADESH',
    'BH': 'BELIZE',
    'BI': 'BURUNDI',
    'BK': 'BOSNIA AND HERZEGOVINA',
    'BL': 'BOLIVIA',
    'BM': 'BURMA',
    'BN': 'BENIN',
    'BO': 'BELARUS',
    'BP': 'SOLOMON ISLANDS',
    'BQ': 'NAVASSA ISLAND',
    'BR': 'BRAZIL',
    'BS': 'BASSAS DA INDIA',
    'BT': 'BHUTAN',
    'BU': 'BULGARIA',
    'BV': 'BOUVET ISLAND',
    'BX': 'BRUNEI',
    'BY': 'BURUNDI',
    'BZ': 'BELGIUM AND LUXEMBOURG',
    'CA': 'CANADA',
    'CB': 'CAMBODIA',
    'CC': 'CEUTA AND MELILLA',
    'CD': 'CHAD',
    'CE': 'SRI LANKA',
    'CF': 'CONGO',
    'CG': 'ZAIRE',
    'CH': 'CHINA',
    'CI': 'CHILE',
    'CJ': 'CAYMAN ISLANDS',
    'CK': 'COCOS (KEELING) ISLANDS',
    'CL': 'CAROLINE ISLANDS',
    'CM': 'CAMEROON',
    'CN': 'COMOROS',
    'CO': 'COLOMBIA',
    'CP': 'CANARY ISLANDS',
    'CQ': 'NORTHERN MARIANA ISLANDS',
    'CR': 'CORAL SEA ISLANDS',
    'CS': 'COSTA RICA',
    'CT': 'CENTRAL AFRICAN REPUBLIC',
    'CU': 'CUBA',
    'CV': 'CAPE VERDE',
    'CW': 'COOK ISLANDS',
    'CY': 'CYPRUS',
    'CZ': 'CANTON ISLAND',
    'DA': 'DENMARK',
    'DJ': 'DJIBOUTI',
    'DO': 'DOMINICA',
    'DQ': 'JARVIS ISLAND',
    'DR': 'DOMINICAN REPUBLIC',
    'DY': 'DEMOCRATIC YEMEN',
    'EC': 'ECUADOR',
    'EG': 'EGYPT',
    'EI': 'IRELAND',
    'EK': 'EQUATORIAL GUINEA',
    'EN': 'ESTONIA',
    'ER': 'ERITREA',
    'ES': 'EL SALVADOR',
    'ET': 'ETHIOPIA',
    'EU': 'EUROPA ISLAND',
    'EZ': 'CZECH REPUBLIC',
    'FG': 'FRENCH GUIANA',
    'FI': 'FINLAND',
    'FJ': 'FIJI',
    'FK': 'FALKLAND ISLANDS (ISLAS MALVINAS)',
    'FM': 'MICRONESIA, FEDERATED STATES OF',
    'FO': 'FAROE ISLANDS',
    'FP': 'FRENCH POLYNESIA',
    'FQ': 'BAKER ISLAND',
    'FR': 'FRANCE',
    'FS': 'FRENCH SOUTHERN AND ANTARCTIC LANDS',
    'GA': 'GAMBIA  THE',
    'GB': 'GABON',
    'GG': 'GEORGIA',
    'GH': 'GHANA',
    'GI': 'GIBRALTAR',
    'GJ': 'GRENADA',
    'GK': 'GUERNSEY',
    'GL': 'GREENLAND',
    'GM': 'GERMANY',
    'GO': 'GLORIOSO ISLANDS',
    'GP': 'GUADELOUPE',
    'GQ': 'GUAM',
    'GR': 'GREECE',
    'GT': 'GUATEMALA',
    'GV': 'GUINEA',
    'GY': 'GUYANA',
    'GZ': 'GAZA STRIP',
    'HA': 'HAITI',
    'HK': 'HONG KONG',
    'HM': 'HEARD ISLAND AND MCDONALD ISLANDS',
    'HO': 'HONDURAS',
    'HQ': 'HOWLAND ISLAND',
    'HR': 'CROATIA',
    'HU': 'HUNGARY',
    'IC': 'ICELAND',
    'ID': 'INDONESIA',
    'IM': 'MAN  ISLE OF',
    'IN': 'INDIA',
    'IO': 'BRITISH INDIAN OCEAN TERRITORY',
    'IP': 'CLIPPERTON ISLAND',
    'IR': 'IRAN',
    'IS': 'ISRAEL',
    'IT': 'ITALY',
    'IV': 'COTE D\'IVOIRE',
    'IW': 'ISRAEL-JORDAN DMZ',
    'IZ': 'IRAQ',
    'JA': 'JAPAN',
    'JE': 'JERSEY',
    'JM': 'JAMAICA',
    'JN': 'JAN MAYEN',
    'JO': 'JORDAN',
    'JQ': 'JOHNSTON ATOLL',
    'JU': 'JUAN DE NOVA ISLAND',
    'KE': 'KENYA',
    'KG': 'KYRGYZSTAN',
    'KN': 'KOREA, NORTH',
    'KQ': 'KINGMAN REEF',
    'KR': 'KIRIBATI',
    'KS': 'KOREA, SOUTH',
    'KT': 'CHRISTMAS ISLAND',
    'KU': 'KUWAIT',
    'KV': 'KOSOVO',
    'KZ': 'KAZAKHSTAN',
    'LA': 'LAOS',
    'LC': 'ST. LUCIA AND ST. VINCENT',
    'LE': 'LEBANON',
    'LG': 'LATVIA',
    'LH': 'LITHUANIA',
    'LI': 'LIBERIA',
    'LN': 'SOUTHERN LINE ISLANDS',
    'LO': 'SLOVAKIA',
    'LQ': 'PALMYRA ATOLL',
    'LS': 'LIECHTENSTEIN',
    'LT': 'LESOTHO',
    'LU': 'LUXEMBOURG',
    'LY': 'LIBYA',
    'MA': 'MADAGASCAR',
    'MB': 'MARTINIQUE',
    'MC': 'MACAU',
    'MD': 'MOLDOVA',
    'ME': 'MADEIRA',
    'MF': 'MAYOTTE',
    'MG': 'MONGOLIA',
    'MH': 'MONTSERRAT',
    'MI': 'MALAWI',
    'MJ': 'MONTENEGRO',
    'MK': 'MACEDONIA',
    'ML': 'MALI',
    'MM': 'BURMA (MYANMAR)',
    'MN': 'MONACO',
    'MO': 'MOROCCO',
    'MP': 'MAURITIUS',
    'MQ': 'MIDWAY ISLANDS',
    'MR': 'MAURITANIA',
    'MT': 'MALTA',
    'MU': 'OMAN',
    'MV': 'MALDIVES',
    'MW': 'MONTENEGRO',
    'MX': 'MEXICO',
    'MY': 'MALAYSIA',
    'MZ': 'MOZAMBIQUE',
    'NC': 'NEW CALEDONIA',
    'NE': 'NIUE',
    'NF': 'NORFOLK ISLAND',
    'NG': 'NIGER',
    'NH': 'VANUATU',
    'NI': 'NIGERIA',
    'NL': 'NETHERLANDS',
    'NO': 'NORWAY',
    'NP': 'NEPAL',
    'NR': 'NAURU',
    'NS': 'SURINAME',
    'NT': 'NETHERLANDS ANTILLES',
    'NU': 'NICARAGUA',
    'NZ': 'NEW ZEALAND',
    'OD': 'SOUTH SUDAN',
    'OW': 'OCEAN WEATHER STATIONS',
    'PA': 'PARAGUAY',
    'PC': 'PITCAIRN ISLANDS',
    'PE': 'PERU',
    'PF': 'PARACEL ISLANDS',
    'PG': 'SPRATLY ISLANDS',
    'PI': 'PHOENIX ISLANDS',
    'PK': 'PAKISTAN',
    'PL': 'POLAND',
    'PM': 'PANAMA',
    'PN': 'NORTH PACIFIC ISLANDS',
    'PO': 'PORTUGAL',
    'PP': 'PAPUA NEW GUINEA',
    'PS': 'PALAU - TRUST TERRITORY OF THE PACIFIC ISLANDS',
    'PU': 'GUINEA-BISSAU',
    'PZ': 'SOUTH PACIFIC ISLANDS',
    'QA': 'QATAR',
    'RE': 'REUNION AND ASSOCIATED ISLANDS',
    'RI': 'SERBIA',
    'RM': 'MARSHALL ISLANDS',
    'RO': 'ROMANIA',
    'RP': 'PHILIPPINES',
    'RQ': 'PUERTO RICO',
    'RS': 'RUSSIA',
    'RW': 'RWANDA',
    'SA': 'SAUDI ARABIA',
    'SB': 'ST. PIERRE AND MIQUELON',
    'SC': 'ST. KITTS AND NEVIS',
    'SE': 'SEYCHELLES',
    'SF': 'SOUTH AFRICA',
    'SG': 'SENEGAL',
    'SH': 'ST. HELENA',
    'SI': 'SLOVENIA',
    'SK': 'SARAWAK AND SABA',
    'SL': 'SIERRA LEONE',
    'SM': 'SAN MARINO',
    'SN': 'SINGAPORE',
    'SO': 'SOMALIA',
    'SP': 'SPAIN',
    'SR': 'SERBIA',
    'SS': 'ST. MAARTEN',
    'ST': 'ST. LUCIA',
    'SU': 'SUDAN',
    'SV': 'SVALBARD',
    'SW': 'SWEDEN',
    'SX': 'SOUTH GEORGIA AND THE SOUTH SANDWICH ISLANDS',
    'SY': 'SYRIA',
    'SZ': 'SWITZERLAND',
    'TC': 'UNITED ARAB EMIRATES',
    'TD': 'TRINIDAD AND TOBAGO',
    'TE': 'TROMELIN ISLAND',
    'TH': 'THAILAND',
    'TI': 'TAJIKISTAN',
    'TK': 'TURKS AND CAICOS ISLANDS',
    'TL': 'TOKELAU',
    'TN': 'TONGA',
    'TO': 'TOGO',
    'TP': 'SAO TOME AND PRINCIPE',
    'TS': 'TUNISIA',
    'TU': 'TURKEY',
    'TV': 'TUVALU',
    'TW': 'TAIWAN',
    'TX': 'TURKMENISTAN',
    'TZ': 'TANZANIA',
    'UA': 'FORMER USSR (ASIA)',
    'UE': 'FORMER USSR (EUROPE)',
    'UG': 'UGANDA',
    'UK': 'UNITED KINGDOM',
    'UP': 'UKRAINE',
    'US': 'UNITED STATES',
    'UV': 'BURKINA FASO',
    'UY': 'URUGUAY',
    'UZ': 'UZBEKISTAN',
    'VC': 'ST. VINCENT AND THE GRENADINES',
    'VE': 'VENEZUELA',
    'VI': 'VIRGIN ISLANDS (BRITISH)',
    'VM': 'VIETNAM',
    'VQ': 'VIRGIN ISLANDS (U.S.)',
    'VT': 'VATICAN CITY',
    'WA': 'NAMIBIA',
    'WE': 'WEST BANK',
    'WF': 'WALLIS AND FUTUNA',
    'WI': 'WESTERN SAHARA',
    'WQ': 'WAKE ISLAND',
    'WS': 'WESTERN SAMOA',
    'WZ': 'SWAZILAND',
    'YM': 'YEMEN',
    'YU': 'YUGOSLAVIA (& FORMER TERRITORY)',
    'YY': 'ST. MARTEEN, ST. EUSTATIUS, AND SABA',
    'ZA': 'ZAMBIA',
    'ZI': 'ZIMBABWE',
    'ZM': 'SAMOA',
    'ZZ': 'ST. MARTIN AND ST. BARTHOLOMEW'
}

def convert_country_code(code):
    # Check if the code exists in the dictionary
    if code in countries:
        return countries[code]
    else:
        return code  # Return the original code if not found

# Function to process CSV file
def process_csv(filename):
    rows = []
    with open(filename, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            name = row['Name']
            # Assuming 'Name' column contains values like 'MERU, KE'
            if ',' in name:
                parts = name.split(', ')
                if len(parts) == 2:
                    country_code = parts[1].strip()
                    country_name = convert_country_code(country_code)
                    # Modify the 'Name' column with the updated country name
                    row['Name'] = f"{parts[0]}, {country_name}"
                    print(f"Original Name: {name}, Updated Name: {row['Name']}")
                else:
                    print(f"Invalid format: {name}")
            rows.append(row)

    # Write the updated data back to the CSV file
    with open(filename, mode='w', newline='') as file:
        fieldnames = reader.fieldnames
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

# Example usage:
filename = output_file
process_csv(filename)

def adjust_weatherscore(filename):
    with open(filename, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        fieldnames = reader.fieldnames + ['Adjusted Average Weatherscore']
        
        rows = []
        for row in reader:
            try:
                avg_score = float(row['Average Weatherscore'])
                margin_of_error = float(row['Margin of Error'])
                row['Adjusted Average Weatherscore'] = avg_score + margin_of_error
                print('Weatherscore adjusted')
            except ValueError:
                row['Adjusted Average Weatherscore'] = ''  # Handle missing or invalid values
                print('Error!')
            rows.append(row)
        
    with open(filename, mode='w', newline='') as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Adjusted weatherscore added and saved to {file}")
adjust_weatherscore(filename)
