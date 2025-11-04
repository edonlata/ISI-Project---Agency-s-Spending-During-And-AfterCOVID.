import pandas as pd

import os

# Define the file path (use raw string to avoid backslash escape issues)
file_path = r"C:\Users\Nikol\OneDrive\CSC300\projectrrr.csv"

# Ensure file exists before attempting to read
if not os.path.exists(file_path):
    raise FileNotFoundError(f"CSV file not found: {file_path}")

# Read CSV safely with a fallback if the python engine raises an unexpected error
try:
    df = pd.read_csv(file_path, engine="python", on_bad_lines="skip")
except Exception:
    df = pd.read_csv(file_path)
df.columns = df.columns.str.strip()

# Identify value columns (all except Date)
value_cols = [c for c in df.columns if c.lower() != "date"]

# Function to clean numeric columns
def to_numeric_series(s):
    cleaned = s.astype(str).str.strip()
    cleaned = cleaned.replace({'-': '0'})  # Treat dash as zero
    cleaned = cleaned.str.replace(r"[^0-9.\-]", "", regex=True)
    cleaned = cleaned.replace({'': '0', '-': '0'})
    return pd.to_numeric(cleaned, errors="coerce")

# Clean up numeric values
df_clean = df.copy()
for c in value_cols:
    df_clean[c] = to_numeric_series(df_clean[c])

# Sum spending per agency across all dates
totals = df_clean[value_cols].sum(axis=0, skipna=True).reset_index()
totals.columns = ["Agency", "Total_Spend"]

# Filter agencies with spend > $1,000,000
over_1m = totals[totals["Total_Spend"] > 1_000_000].sort_values("Total_Spend", ascending=False)

# --- Paginated display in terminal ---
chunk_size = 15  # how many rows to show at once
num_rows = len(over_1m)

for start in range(0, num_rows, chunk_size):
    end = min(start + chunk_size, num_rows)
    print(f"\n🟩 Showing agencies {start + 1} to {end} of {num_rows}\n")
    print(over_1m.iloc[start:end].to_string(index=False))
    
    if end < num_rows:
        input("\nPress Enter to see more...\n")

print("\n✅ Finished displaying all agencies over $1M.\n")




# new_file_path = r"C:\Users\Nikol\OneDrive\CSC300\Department Spending.csv"
# if not os.path.exists(new_file_path):
#     raise FileNotFoundError(f"CSV file not found: {new_file_path}")

# df_new = pd.read_csv(new_file_path, engine="python", on_bad_lines="skip")
# df_new.columns = df_new.columns.str.strip()

# #--- Standardize text for better matching ---
# over_1m['Agency_clean'] = over_1m['Agency'].str.lower().str.strip()
# df_new['Department_clean'] = df_new['Agency'].str.lower().str.strip()

# # --- Merge based on cleaned names ---
# merged = pd.merge(
#     df_new,
#     over_1m,
#     left_on="Department_clean",
#     right_on="Agency_clean",
#     how="inner"  # only matching departments
# )

# # --- Display matching departments ---
# print("\n🟦 Departments matching agencies over $1M spend:\n")
# print(merged[['Department', 'Total_Spend']].to_string(index=False))

# print(f"\n✅ Found {len(merged)} matching departments.\n")


#make the project read another file called Department Spending.csv
# # Define the new file path
# #new_file_path = r"C:\Users\Nikol\OneDrive\CSC300\Department Spending.csv"
# # Ensure new file exists before attempting to read  
# #if not os.path.exists(new_file_path):
# #    raise FileNotFoundError(f"CSV file not found: {new_file_path}")
# # Read new CSV safely
# #try:
# #    df_new = pd.read_csv(new_file_path, engine="python", on_bad_lines="skip")
# #except Exception:
# #    df_new = pd.read_csv(new_file_path)
# #df_new.columns = df_new.columns.str.strip() 
# # Display the only the department names that match those in the previous file
# matching_departments = df_new[df_new['Department'].isin(over_1m['Agency'])]
# print("\n🟦 Departments matching agencies over $1M spend:\n")
# print(matching_departments['Department'].to_string(index=False))
# # how to make this whole code in a comment

