Manufacturer Part Number Validation
==============================

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

Alphabetic Validation for CSV Columns
==================================
This script validates specified columns in a CSV file to ensure that they contain only alphabetic values (i.e., letters without numbers or special characters). It checks multiple columns, logs the results, and reports any invalid values found. If any invalid data is detected, the script fails the test and logs the details in a text file.

Features
Validates columns for alphabetic values (letters only).
Tests multiple columns specified in the script.
Logs the validation results in a text file (test_results_1.txt), including both valid and invalid values.
Fails the test if any invalid values are found in the specified columns.
Requirements
Python 3.x
pandas library
pytest library
To install the required libraries, run:

bash
Copy
pip install pandas pytest
How to Use
Place your CSV file in the same directory as this script, or update the path to your CSV file in the file_path variable within the script.

The CSV file should contain columns that need to be validated for alphabetic values. You can customize which columns to validate in the columns_to_test list.

Run the test using pytest:

bash
Copy
pytest script_name.py
The script will:
Check the specified columns to ensure they contain only alphabetic values.
Save the results to a file called test_results_1.txt.
Example of CSV Input Format
csv
Copy
store,A,B
Store1,Apple,Orange
Store2,Banana,1234
Store3,Cherry,Pear
Example of Test Results (test_results_1.txt)
sql
Copy
===== TEST RESULTS FOR ALPHABET VALIDATION =====

Results for column 'store':
VALID VALUES:
Store1
Store2
Store3

INVALID VALUES:
No invalid values found.

Results for column 'A':
VALID VALUES:
Apple
Banana
Cherry

INVALID VALUES:
No invalid values found.

Results for column 'B':
VALID VALUES:
Orange
Pear

INVALID VALUES:
Row 1: 1234
Validation Criteria
The is_valid_alphabet function checks whether a value is a string containing only alphabetic characters (i.e., no numbers or special characters). This is done using Python's str.isalpha() method.

Error Handling
If the specified columns are missing from the CSV file, the test will fail with an assertion error.
If any values in the specified columns are not alphabetic, the test will fail, and the details will be logged in test_results_1.txt.

========================================================================================================================

Group Unique Products by Brand
==============================

This script processes a CSV file containing product data and groups the products by their respective brands, ensuring that only unique products per brand are included. It removes any duplicate product entries for each brand and saves the results to a new CSV file.

Features
Loads a CSV file containing brand and product data.
Removes duplicate product names for each brand.
Groups products by brand.
Saves the resulting grouped data to a new CSV file.
Prints the unique products grouped by brand to the console.
Requirements
Python 3.x
pandas library
To install the required library, run:

bash
Copy
pip install pandas
How to Use
Place your CSV file with brand and product data in the same directory as this script, or specify the path to the CSV file.

The CSV file should contain at least two columns:

The first column should represent the brand names.
The second column should represent the product names.
Run the script using Python:

bash
Copy
python script_name.py
The script will process the data, remove duplicates, and group the products by brand.
The output will be saved in a new file called unique_products_by_brand.csv.
Example of CSV Input Format
csv
Copy
Brand,Product
BrandA,Product1
BrandA,Product2
BrandA,Product1
BrandB,Product3
BrandB,Product4
BrandB,Product3
Example of CSV Output Format
csv
Copy
Brand,Product
BrandA,"['Product1', 'Product2']"
BrandB,"['Product3', 'Product4']"
Error Handling
If the specified CSV file can't be read or doesn't exist, the script will print an error message and exit.
If the expected columns for brand and product names are missing, the script will display an error and exit.

=====================================================================================================================================
