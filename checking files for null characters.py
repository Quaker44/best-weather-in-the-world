import os
import glob

def check_csv_for_null(directory):
    # Get all CSV files in the specified directory
    csv_files = glob.glob(os.path.join(directory, '*.csv'))

    files_with_null = []

    for csv_file in csv_files:
        with open(csv_file, 'r', encoding='utf-8', errors='replace') as file:
            try:
                file_contents = file.read()
                if '\0' in file_contents:
                    files_with_null.append(csv_file)
            except Exception as e:
                print(f"Error reading file {csv_file}: {e}")

    return files_with_null

# Example usage:
directory = '/Users/Quaker/Desktop/Weather_Station_Project/Raw Data Downloads/2018'
files_with_null = check_csv_for_null(directory)

if files_with_null:
    print("Files with null characters:")
    for file in files_with_null:
        print(file)
else:
    print("No files with null characters found.")
