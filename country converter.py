import csv

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
filename = '/home/sam/Projects/best-weather-in-the-world/rankings76(21).csv'  # Replace with your actual CSV file name
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

# Example usage:
adjust_weatherscore(filename)

