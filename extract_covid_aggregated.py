import pandas as pd
from pathlib import Path
import re

project_dir = Path(__file__).resolve().parent
file_time = Path(r"C:\Users\Nikol\OneDrive\CSC300\projectrrr.csv")
file_dept = project_dir / 'Department Spending.csv'

if not file_time.exists():
    raise FileNotFoundError(file_time)
if not file_dept.exists():
    raise FileNotFoundError(file_dept)

opts = {'engine': 'python', 'on_bad_lines': 'skip'}

df_time = pd.read_csv(file_time, **opts)
df_dept = pd.read_csv(file_dept, **opts)

# normalize headers/columns
df_time.columns = df_time.columns.str.strip()
df_dept.columns = df_dept.columns.str.strip()

# agencies are the column headers in projectrrr.csv (except 'Date')
agency_cols = [c for c in df_time.columns if c.lower() != 'date']

# normalize agency names for matching
def normalize_name(s):
    s = str(s).lower().strip()
    s = re.sub(r"[^0-9a-z ]+", "", s)
    s = re.sub(r"\s+", " ", s)
    return s

agency_clean_map = {normalize_name(a): a for a in agency_cols}

# detect dept name column
dept_col = None
for c in df_dept.columns:
    if c.lower() == 'department':
        dept_col = c
        break
if dept_col is None:
    dept_col = df_dept.columns[0]

# second column index 1
if len(df_dept.columns) < 2:
    raise ValueError('Department file has fewer than 2 columns; cannot use 2nd column.')
second_col = df_dept.columns[1]

# cleaned department
df_dept['Department_clean'] = df_dept[dept_col].astype(str).map(normalize_name)

# compute >1M agencies

def to_numeric_series(s):
    cleaned = s.astype(str).str.strip()
    cleaned = cleaned.replace({'-': '0'})
    cleaned = cleaned.str.replace(r"[^0-9.\-]", "", regex=True)
    cleaned = cleaned.replace({'': '0', '-': '0'})
    return pd.to_numeric(cleaned, errors='coerce')

value_cols = [c for c in df_time.columns if c.lower() != 'date']
df_time_clean = df_time.copy()
for c in value_cols:
    df_time_clean[c] = to_numeric_series(df_time_clean[c])

totals = df_time_clean[value_cols].sum(axis=0, skipna=True).reset_index()
totals.columns = ['Agency', 'Total_Spend']

over_1m = totals[totals['Total_Spend'] > 1_000_000]
over_1m['Agency_clean'] = over_1m['Agency'].astype(str).map(normalize_name)

target_agency_cleans = list(over_1m['Agency_clean'].unique())

# prepare aggregation
pattern = re.compile(r'covid response', re.I)
aggregated = []

# determine numeric columns in df_dept for summing (attempt to coerce)
numeric_cols = []
for c in df_dept.columns:
    # skip department text columns
    if c in [dept_col, 'Department_clean', second_col]:
        continue
    coerced = pd.to_numeric(df_dept[c].astype(str).str.replace(r"[^0-9.\-]", "", regex=True), errors='coerce')
    if coerced.notna().any():
        numeric_cols.append(c)

for ac in target_agency_cleans:
    matches = df_dept[df_dept['Department_clean'] == ac]
    # rows where second_col contains covid response
    covid_rows = matches[matches[second_col].astype(str).str.contains(r'covid response', case=False, na=False)]
    if covid_rows.empty:
        # create aggregated row with zero counts
        aggregated.append({
            'Matched_Agency_clean': ac,
            'Department_display': agency_clean_map.get(ac, ''),
            'Num_Covid_Rows': 0,
            'Covid_Initiatives': '',
            **{f'Sum_{c}': 0 for c in numeric_cols}
        })
    else:
        # concatenate unique initiative descriptions
        initiatives = covid_rows[second_col].astype(str).map(lambda s: s.strip()).replace('', pd.NA).dropna().unique().tolist()
        init_join = ' | '.join(initiatives)
        # sum numeric cols
        sums = {}
        for c in numeric_cols:
            coerced = pd.to_numeric(covid_rows[c].astype(str).str.replace(r"[^0-9.\-]", "", regex=True), errors='coerce')
            sums[f'Sum_{c}'] = coerced.sum(min_count=1)
        aggregated.append({
            'Matched_Agency_clean': ac,
            'Department_display': matches[dept_col].iloc[0] if not matches.empty else agency_clean_map.get(ac, ''),
            'Num_Covid_Rows': len(covid_rows),
            'Covid_Initiatives': init_join,
            **sums
        })

out_df = pd.DataFrame(aggregated)
# restore nicer department column name
out_path = project_dir / 'matched_covid_aggregated.csv'
out_df.to_csv(out_path, index=False)
print(f'Wrote {len(out_df)} aggregated rows to {out_path}')
print(out_df.head(20).to_string(index=False))
