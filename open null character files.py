import os
import glob
import subprocess

def detect_null_characters(file_path):
    with open(file_path, 'rb') as file:
        for chunk in iter(lambda: file.read(4096), b''):
            if b'\x00' in chunk:
                return True
    return False

def open_files_in_excel(directory):
    files_to_open = []

    for file_path in glob.glob(os.path.join(directory, '*.*')):
        if detect_null_characters(file_path):
            files_to_open.append(file_path)

    if files_to_open:
        for file_path in files_to_open:
            print(f"Opening file with null characters in Excel: {file_path}")
            subprocess.Popen(['open', file_path])
    else:
        print("No files with null characters found.")

# Example usage: Specify the directory containing the files to check and open in Excel
directory = '/Users/Quaker/Desktop/Weather_Station_Project/Raw Data Downloads/2018'
open_files_in_excel(directory)
