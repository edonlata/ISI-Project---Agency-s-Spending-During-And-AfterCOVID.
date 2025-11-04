import pandas as pd

# Define the file path to the CSV file
file_path = "Independent_Budget_Office__NYC_COVID_19_Spending_by_Date_-_Citywide_and_by_Agency_20251020 .csv"

# Read the CSV file safely, skipping bad lines
df = pd.read_csv(file_path, engine="python", on_bad_lines="skip")
df.columns = df.columns.str.strip()  # Strip whitespace from column names

# Identify value columns (all columns except "Date")
value_cols = [c for c in df.columns if c.lower() != "date"]

# Function to clean numeric columns
def to_numeric_series(s):
    cleaned = s.astype(str).str.strip()  # Convert to string and strip whitespace
    cleaned = cleaned.replace({'-': '0'})  # Treat dash as zero
    cleaned = cleaned.str.replace(r"[^0-9.\-]", "", regex=True)  # Remove non-numeric characters
    cleaned = cleaned.replace({'': '0', '-': '0'})  # Replace empty strings and dashes with zero
    return pd.to_numeric(cleaned, errors="coerce")  # Convert to numeric, coercing errors to NaN

# Create a copy of the DataFrame and clean up numeric values
df_clean = df.copy()
for c in value_cols:
    df_clean[c] = to_numeric_series(df_clean[c])  # Apply cleaning function to each value column

# Sum spending per agency across all dates
totals = df_clean[value_cols].sum(axis=0, skipna=True).reset_index()  # Sum values for each agency
totals.columns = ["Agency", "Total_Spend"]  # Rename columns for clarity

# Filter agencies with spending greater than $1,000,000
over_1m = totals[totals["Total_Spend"] > 1_000_000].sort_values("Total_Spend", ascending=False)

# --- Paginated display in terminal ---
chunk_size = 15  # Number of rows to display at once
num_rows = len(over_1m)  # Total number of rows in the filtered DataFrame

# Loop through the filtered DataFrame in chunks
for start in range(0, num_rows, chunk_size):
    end = min(start + chunk_size, num_rows)  # Calculate the end index for the current chunk
    print(f"\n🟩 Showing agencies {start + 1} to {end} of {num_rows}\n")
    print(over_1m.iloc[start:end].to_string(index=False))  # Display the current chunk of rows
    
    if end < num_rows:  # If there are more rows to display, prompt the user to continue
        input("\nPress Enter to see more...\n")

# Indicate that all rows have been displayed
print("\n✅ Finished displaying all agencies over $1M.\n")