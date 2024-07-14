import os
import glob

def detect_null_characters(file_path):
    with open(file_path, 'rb') as file:
        for chunk in iter(lambda: file.read(4096), b''):
            if b'\x00' in chunk:
                return True
    return False

def delete_files_with_null_characters(directory):
    # Get all files in the specified directory
    files_to_delete = []

    for file_path in glob.glob(os.path.join(directory, '*.*')):
        if detect_null_characters(file_path):
            files_to_delete.append(file_path)

    if files_to_delete:
        print(f"Found {len(files_to_delete)} file(s) with null characters. Deleting...")

        for file_path in files_to_delete:
            try:
                os.remove(file_path)
                print(f"Deleted: {file_path}")
            except Exception as e:
                print(f"Failed to delete {file_path}: {e}")
    else:
        print("No files with null characters found.")

# Example usage: Specify the directory containing the files to check and delete
directory = '/Users/Quaker/Desktop/Weather_Station_Project/Raw Data Downloads/2018'
delete_files_with_null_characters(directory)

