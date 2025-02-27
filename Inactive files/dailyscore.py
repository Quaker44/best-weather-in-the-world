import pandas as pd

# Input the CSV file path
input_file = '/home/sam/Downloads/75.csv'  # Replace with your input CSV file path
output_file = '/home/sam/Downloads/75.csv'  # Replace with your desired output CSV file path

# Load the CSV into a DataFrame
df = pd.read_csv(input_file)

# Ensure the necessary column exists in the DataFrame
if 'Weatherscore' in df.columns:
    # Add the 'Daily score' column
    df['Daily score'] = df['Weatherscore'] / 365.25

    # Save the updated DataFrame back to a CSV file
    df.to_csv(output_file, index=False)

    print(f"Updated CSV has been saved to {output_file}")
else:
    print("Error: The column 'Weighted average weatherscore' does not exist in the input CSV.")
