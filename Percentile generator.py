import pandas as pd
from scipy.stats import rankdata

# Load the existing CSV file
file_path = '/home/sam/Projects/best-weather-in-the-world/2024rankings77(21).csv'
df = pd.read_csv(file_path)

# Calculate the rank for each "Annual Average Weatherscore" (higher is better)
df['Rank'] = rankdata(-df['Adjusted Average Weatherscore'], method='min')

# Calculate the percentile for each rank
df['Percentile'] = (df['Rank'] - 1) / (len(df['Adjusted Average Weatherscore']) - 1) * 100

# Overwrite the existing CSV file with updated data
df.to_csv(file_path, index=False)

print("Percentiles have been added to the existing file")
