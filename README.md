Manufacturer Part Number Validation
This script validates the mfr_part_no (Manufacturer Part Number) column in a given CSV file. It checks whether each part number follows a specific format and logs the results (both valid and invalid values) to a text file. The script uses regular expressions to ensure that the part numbers conform to the expected pattern.

Features
Validates the mfr_part_no column in the input CSV file using a predefined pattern.
Separates valid and invalid part numbers.
Logs the results of the validation to a text file (test_results.txt), including details of invalid rows.
Fails the test if any invalid part numbers are found.

Requirements
Python 3.x
pandas library
pytest library
re module (comes with Python)
To install the required libraries, run:

bash
Copy
pip install pandas pytest
How to Use
Place your CSV file in the same directory as this script, or update the path to your CSV file in the file_path variable within the script.

The CSV file should contain a column named mfr_part_no that holds the manufacturer part numbers for validation.

Run the test using pytest:

bash
Copy
pytest script_name.py
The test will:
Validate each part number in the mfr_part_no column against the specified pattern.
Save the results to a file called test_results.txt.
Example of CSV Input Format
csv
Copy
mfr_part_no,product_name
ABCD-1234,Product 1
XYZ-B21,Product 2
12345,Product 3
A1B2C3-D21,Product 4
Example of Test Results (test_results.txt)
sql
Copy
===== TEST RESULTS FOR mfr_part_no =====

VALID mfr_part_no VALUES:
XYZ-B21
ABCD-1234
A1B2C3-D21

INVALID mfr_part_no VALUES:
Row 2: 12345
Validation Pattern
The mfr_part_no field is validated using the following regular expression pattern:

regex
Copy
^[a-zA-Z0-9]{4,6}(-B21|-H21|-K21|-S01|-L22|-S21|-L21|-001|-B22)?$
This pattern ensures that:

The part number is between 4 to 6 alphanumeric characters.
Optionally, the part number can end with one of the following suffixes: -B21, -H21, -K21, -S01, -L22, -S21, -L21, -001, -B22.

Error Handling
If the mfr_part_no column is missing from the CSV file, the test will fail with an assertion error.
If there are any invalid part numbers, the test will fail, and the details will be logged to the test_results.txt file.
==========================================================================================================================================

