import os
import cv2
import easyocr
import requests
import logging
import re
import unicodedata
import shutil
import colorama
from pathlib import Path
from colorama import Fore, Style

# Initialize EasyOCR reader
reader = easyocr.Reader(['en'])

# Initialize colorama
colorama.init()

# Set up logging
import_folder = 'Import'
log_file_path = os.path.join(import_folder, 'Log.txt')

# Configure logging to output to both console and log file
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

# Create handlers
file_handler = logging.FileHandler(log_file_path)
console_handler = logging.StreamHandler()

# Set level for handlers
file_handler.setLevel(logging.INFO)
console_handler.setLevel(logging.WARNING)

# Create formatters and add them to handlers
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# Add handlers to the logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

def sanitize_filename(name):
    # Normalize the name to NFD (decompose characters with diacritics)
    nfkd_form = unicodedata.normalize('NFD', name)
    # Remove diacritics
    sanitized_name = ''.join([c for c in nfkd_form if not unicodedata.combining(c)])
    # Remove any remaining character that is not alphanumeric or a space
    sanitized_name = re.sub(r'[^a-zA-Z0-9 ]', '', sanitized_name)
    # Replace spaces with underscores
    sanitized_name = sanitized_name.replace(' ', '_')
    return sanitized_name

def preprocess_file_names(directory):
    for root, _, files in os.walk(directory):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                original_path = os.path.join(root, file)
                directory = os.path.dirname(original_path)
                file_extension = os.path.splitext(original_path)[1]
                sanitized_name = sanitize_filename(os.path.splitext(file)[0])
                new_file_name = f"{sanitized_name}{file_extension}"
                new_file_path = os.path.join(directory, new_file_name)
                
                counter = 1
                while os.path.exists(new_file_path):
                    new_file_name = f"{sanitized_name}_{counter}{file_extension}"
                    new_file_path = os.path.join(directory, new_file_name)
                    counter += 1
                
                if original_path != new_file_path:
                    os.rename(original_path, new_file_path)
                    logging.info(f"Preprocessed {original_path} to {new_file_path}")

def get_card_name(image_path):
    try:
        # Read image using OpenCV
        image = cv2.imread(image_path)
        if image is None:
            raise ValueError(f"Could not read image: {image_path}")
        
        # Use EasyOCR to extract text from image
        result = reader.readtext(image, detail=0)
        
        # Extract only the first line of text
        card_text = result[0] if result else ''
        
        logging.debug(f"Extracted text from {image_path}: {card_text}")
        
        # Use Scryfall API to identify the card
        response = requests.get(f'https://api.scryfall.com/cards/named?fuzzy={card_text}')
        
        if response.status_code == 200:
            card_data = response.json()
            card_name = card_data['name']
            logging.info(f"Identified card '{card_name}' for image {image_path}")
            return card_name
        else:
            logging.warning(f"Card not found for text: {card_text} in image {image_path}")
            return None
    except Exception as e:
        logging.error(f"Error processing image {image_path}: {e}")
        return None

def rename_card_image(image_path, card_name):
    try:
        # Sanitize the card name
        sanitized_card_name = sanitize_filename(card_name)
        
        # Get the directory and file extension
        directory = os.path.dirname(image_path)
        file_extension = os.path.splitext(image_path)[1]
        
        # Create the new file name
        new_file_name = f"{sanitized_card_name}{file_extension}"
        new_file_path = os.path.join(directory, new_file_name)
        
        # Check if the file already exists and append a number if it does
        counter = 1
        while os.path.exists(new_file_path):
            new_file_name = f"{sanitized_card_name}_{counter}{file_extension}"
            new_file_path = os.path.join(directory, new_file_name)
            counter += 1
        
        # Rename the original file
        os.rename(image_path, new_file_path)
        logging.info(f"Renamed {image_path} to {new_file_path}")
        
        return new_file_path
    except Exception as e:
        logging.error(f"Error renaming image {image_path} to {new_file_name}: {e}")
        return None

def move_file(file_path, destination_folder):
    try:
        if not os.path.exists(destination_folder):
            os.makedirs(destination_folder)
        
        destination_path = os.path.join(destination_folder, os.path.basename(file_path))
        
        # Handle duplicate file names by appending a counter
        counter = 1
        while os.path.exists(destination_path):
            base, ext = os.path.splitext(os.path.basename(file_path))
            destination_path = os.path.join(destination_folder, f"{base}_{counter}{ext}")
            counter += 1
        
        shutil.move(file_path, destination_path)
        logging.info(f"Moved {file_path} to {destination_path}")
    except Exception as e:
        logging.error(f"Error moving file {file_path} to {destination_folder}: {e}")

def process_directory(directory):
    for root, dirs, files in os.walk(directory):
        # Remove 'Processed' and 'Error' from dirs to exclude them from the walk
        dirs[:] = [d for d in dirs if d not in ['Processed', 'Error']]
        
        if root == directory:
            continue  # Skip the root import directory
        print(f"Now processing {root}")
        logging.info(f"Now processing {root}")
        processed_folder = os.path.join(root, 'Processed')
        error_folder = os.path.join(root, 'Error')
        
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png')):
                try:
                    image_path = os.path.join(root, file)
                    logging.debug(f"Processing {image_path}")
                    
                    card_name = get_card_name(image_path)
                    
                    if card_name:
                        new_file_path = rename_card_image(image_path, card_name)
                        if new_file_path:
                            move_file(new_file_path, processed_folder)
                        else:
                            move_file(image_path, error_folder)
                    else:
                        move_file(image_path, error_folder)
                except Exception as e:
                    logging.error(f"Error processing file {file}: {e}")
                    print(Fore.RED + "Error: Please check Log.txt for details" + Style.RESET_ALL)
                    move_file(os.path.join(root, file), error_folder)
        print("Complete!")

def main():
    print("Super TCG OCR is starting up...")
    
    # Define the import folder
    import_folder = 'Import'
    
    # Check if the import folder exists
    if not os.path.exists(import_folder):
        logging.error(f"The import folder '{import_folder}' does not exist. Please create it and add the card images.")
        return
    
    print("Super TCG OCR is pre-processing file names...")
    logging.info(f"Starting preprocessing of file names in folder '{import_folder}'")
    preprocess_file_names(import_folder)
    print("Complete!")
    
    print(f"Super TCG OCR is processing images in folder '{import_folder}'")
    logging.info(f"Starting processing of images in folder '{import_folder}'")
    process_directory(import_folder)
    
    print("Complete!")
    print("Super TCG OCR has finished! Press Enter to end.")
    input()  # Wait for Enter key to be pressed before exiting

if __name__ == "__main__":
    main()
