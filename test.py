import pandas as pd
import os
from pathlib import Path

# --- Read spending time-series (projectrrr.csv) ---
# The CSV lives at C:\Users\Nikol\OneDrive\CSC300\projectrrr.csv on your machine
file_path = r"C:\Users\Nikol\OneDrive\CSC300\projectrrr.csv"

if not os.path.exists(file_path):
    raise FileNotFoundError(f"CSV file not found: {file_path}")

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


# --- Read Department file (relative to project script) ---
new_file_path = Path(__file__).resolve().parent / 'Department Spending.csv'
if not new_file_path.exists():
    raise FileNotFoundError(f"CSV file not found: {new_file_path}")

df_new = pd.read_csv(new_file_path, engine="python", on_bad_lines="skip")
df_new.columns = df_new.columns.str.strip()
df_covid = pd.read_csv(new_file_path, engine="python", on_bad_lines="skip")
df_covid.columns = df_covid.columns.str.strip()

# If the Department column isn't present, try to detect a likely candidate
if 'Department' not in df_new.columns:
    candidates = [c for c in df_new.columns if 'dept' in c.lower() or 'department' in c.lower() or 'agency' in c.lower()]
    if candidates:
        df_new['Department'] = df_new[candidates[0]]
    else:
        df_new['Department'] = ''
df_new['Department'] = df_new['Department'].astype(str)

#--- Standardize text for better matching ---
over_1m['Agency_clean'] = over_1m['Agency'].astype(str).str.lower().str.strip().str.replace(r"[^0-9a-z ]", "", regex=True)
df_new['Department_clean'] = df_new['Department'].astype(str).str.lower().str.strip().str.replace(r"[^0-9a-z ]", "", regex=True)

# --- Merge based on cleaned names ---
merged = pd.merge(
    df_new,
    over_1m,
    left_on="Department_clean",
    right_on="Agency_clean",
    how="inner"  # only matching departments
)

# --- Display matching departments ---
print("\n🟦 Departments matching agencies over $1M spend:\n")
if merged.empty:
    print("(none) - no exact name matches after cleaning.\n")
else:
    print(merged[['Department', 'Total_Spend']].to_string(index=False))

print(f"\n✅ Found {len(merged)} matching departments.\n")

#after finding the matching departments, you can further analyze or export the results as needed.
#on the second file, find the colomn named 'Initiative Category' and filter to only those rows where the value is 'COVID-19 Response'
# --- FILTER to only Initiative Category = "COVID Response" ---
covid_only = df_covid[df_covid["Initiative Category"].str.strip().str.lower() == "covid response"]

# Standardize agency name in COVID dataset
covid_only["Agency_clean"] = covid_only["Agency"].str.lower().str.strip()
# Merge with over_1m on cleaned names
merged_covid = pd.merge(
    covid_only,
    over_1m,
    left_on="Agency_clean",
    right_on="Agency_clean",
    how="inner"
)
print("\n🟧 Agencies over $1M spend involved in COVID-19 Response:\n")
if merged_covid.empty:
    print("(none) - no exact name matches after cleaning.\n")
else:
    print(merged_covid[["Agency_x", "Total_Spend"]].to_string(index=False))
print(f"\n✅ Found {len(merged_covid)} matching agencies involved in COVID-19 Response.\n")







# Helpful suggestion: if you still see 0 matches, consider fuzzy matching or a manual mapping between agency and department names.

