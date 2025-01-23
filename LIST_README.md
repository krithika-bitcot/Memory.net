Group Unique Products by Brand
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
