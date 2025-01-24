import pandas as pd

# Specify the file path of your CSV file
file_path = 'kingston.csv'  # Replace with the actual CSV file path

# Load the CSV file into a DataFrame
try:
    df = pd.read_csv(file_path)
except Exception as e:
    print(f"Error reading the CSV file: {e}")
    exit(1)  # Exit if there's an error loading the file

# Print the column names to inspect the structure of your data
print("Columns in the CSV file:", df.columns)

# Display the first few rows of the dataframe (to check the structure)
print(df.head())

# Assuming the first column is for brand names and the second column is for product names
brand_column = df.columns[0]  # The first column might be the brand column
product_column = df.columns[1]  # Assuming the second column contains product names

# Check if the columns exist in the dataframe
if brand_column not in df.columns or product_column not in df.columns:
    print(f"Error: Columns '{brand_column}' or '{product_column}' not found in the data.")
    exit(1)

# Remove duplicate product names (keep only the first occurrence of each product per brand)
df_unique = df.drop_duplicates(subset=[brand_column, product_column])

# Group products by brand
grouped = df_unique.groupby(brand_column)[product_column].apply(list).reset_index()

# Save the grouped data to a new CSV file
output_file = 'unique_products_by_brand.csv'
grouped.to_csv(output_file, index=False)

# Print the grouped data by brand
for _, row in grouped.iterrows():
    brand = row[brand_column]
    products = row[product_column]
    print(f"Brand: {brand}")
    print(f"Products: {', '.join(products)}\n")

# Optionally, display the result file location
print(f"The grouped unique product names by brand have been saved to '{output_file}'")