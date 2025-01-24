import pandas as pd

# Specify the file path of your CSV file
file_path = open('./11122024_kingston_db_import_ssd_encoded.csv')  # Replace with the actual file path

# Load the CSV file into a DataFrame
try:
    df = pd.read_csv(file_path, low_memory=False)  # Set low_memory=False to handle large files
except Exception as e:
    print(f"Error reading the CSV file: {e}")
    exit(1)  # Exit if there's an error loading the file

# Assuming 'A' column is for brand names and 'B' column contains model categories
brand_column = 'A'  # Column for brands
model_column = 'B'  # Column for higher-level model categories

# Filter only relevant columns and remove duplicates
brand_model_data = df[[brand_column, model_column]].drop_duplicates()

# Remove rows with missing or invalid model names
brand_model_data = brand_model_data.dropna()

# Group by brand and collect distinct model categories into lists
brand_models = brand_model_data.groupby(brand_column)[model_column].apply(lambda x: ', '.join(sorted(x.unique()))).reset_index()

# Save the cleaned data to a CSV file
output_file = 'brand_model_categories_11122024_kingston.csv'
brand_models.to_csv(output_file, index=False)

# Print the output
for _, row in brand_models.iterrows():
    brand = row[brand_column]
    models = row[model_column]
    print(f"Brand: {brand}")
    print(f"Models: {models}\n")

# Notify where the file is saved
print(f"The cleaned brand and model categories have been saved to '{output_file}'")