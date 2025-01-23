Alphabetic Validation for CSV Columns
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
