# Super TCG OCR

Super TCG OCR is a Python script for recognizing and renaming Magic the Gathering card images using OCR (Optical Character Recognition) and the Scryfall API. The script processes images in nested directories, renames them based on the identified card name, and organizes the files into `Processed` and `Error` folders.

## Dependencies

- Python 3.6+
- easyocr
- opencv-python
- requests
- colorama

## Usage

1. Prepare your images:
   - Place your card images in the `Import` folder. Ensure the `Import` folder exists in the root directory of the script.

2. Run the script:

`python super_tcg_ocr.py`

3. Follow the on-screen instructions:

- The script will display progress messages and notify you of any errors.
- Successfully processed files will be moved to the Processed folder within each subdirectory.
- Files that encountered errors will be moved to the Error folder within each subdirectory.

4. Check the Log.txt file in the Import folder for detailed logs and error information.

### License
This project is licensed under the MIT License.

### Contributing
Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.
