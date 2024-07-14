import csv

def create_csv_with_headers(output_file):
    fieldnames = ['Station ID', 'Latitude', 'Longitude', 'Name', 'Elevation', 'Years', 'Annual Average Weatherscore']

    with open(output_file, mode='w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

    print(f"CSV file '{output_file}' with headers created successfully.")

# Example usage to create a new CSV file with headers
output_file = 'annual_weatherscore_output(7).csv'
create_csv_with_headers(output_file)

