import os
import sys

def has_tmax_field(filepath):
    """
    Check if a file contains the string "TMAX".
    Returns True if found, False otherwise.
    """
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            return "TMAX" in content
    except Exception as e:
        print(f"Error reading {filepath}: {e}")
        return False

def delete_files_without_tmax(directory):
    """
    Delete all files in the directory that don't contain "TMAX".
    """
    if not os.path.isdir(directory):
        print(f"Error: {directory} is not a valid directory")
        return
    
    deleted_count = 0
    kept_count = 0
    
    # Walk through all files in the directory
    for root, dirs, files in os.walk(directory):
        for filename in files:
            filepath = os.path.join(root, filename)
            
            if has_tmax_field(filepath):
                print(f"✓ Keeping: {filepath}")
                kept_count += 1
            else:
                try:
                    os.remove(filepath)
                    print(f"✗ Deleted: {filepath}")
                    deleted_count += 1
                except Exception as e:
                    print(f"Error deleting {filepath}: {e}")
    
    print(f"\nSummary:")
    print(f"Files kept: {kept_count}")
    print(f"Files deleted: {deleted_count}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <directory_path>")
        sys.exit(1)
    
    directory = sys.argv[1]
    
    # Confirm before deleting
    response = input(f"This will delete all files in '{directory}' that don't contain 'TMAX'. Continue? (yes/no): ")
    if response.lower() == 'yes':
        delete_files_without_tmax(directory)
    else:
        print("Operation cancelled.")