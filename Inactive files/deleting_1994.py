import pandas as pd

def remove_rows_by_year(csv_file, year_to_remove=1994):
    # Read the CSV file
    df = pd.read_csv(csv_file)
    
    # Filter out rows where the 'Years' column is equal to the specified year
    df_filtered = df[df['Years'] != year_to_remove]
    
    # Save the filtered data back to the same CSV file
    df_filtered.to_csv(csv_file, index=False)
    print(f"Filtered CSV saved as {csv_file}")

# Example usage
remove_rows_by_year('/home/sam/Projects/best-weather-in-the-world/rankings75(21).csv')
