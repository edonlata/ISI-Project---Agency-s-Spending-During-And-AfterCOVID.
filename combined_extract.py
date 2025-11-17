"""
combined_extract.py

Creates two outputs from your project files:
 - matched_covid_rows.csv       (detailed rows from Department Spending.csv where 2nd column contains 'covid response' for matched departments)
 - matched_covid_aggregated.csv (one summary row per matched department: counts, concatenated initiatives, sums of numeric fields)

Usage: run without args from the project folder. The script finds:
 - projectrrr.csv (time-series with agencies as column headers)
 - Department Spending.csv (department rows; 2nd column is searched for 'covid response')

Options (edit variables in script if you want different behavior):
 - include_placeholders: whether to include placeholder rows for departments with no covid rows
 - write_detailed: write detailed matched rows CSV
 - write_aggregated: write aggregated CSV

"""

import pandas as pd
from pathlib import Path
import re
import sys

# ----- Config -----
project_dir = Path(__file__).resolve().parent
file_time = Path(r"C:\Users\Nikol\OneDrive\CSC300\projectrrr.csv")
file_dept = project_dir / 'Department Spending.csv'
write_detailed = False
write_aggregated = True
include_placeholders = False   # exclude rows for departments with no covid response rows
covid_phrase = r'covid response'
# ------------------

if not file_time.exists():
    print(f"Time-series file not found: {file_time}")
    sys.exit(1)
if not file_dept.exists():
    print(f"Department file not found: {file_dept}")
    sys.exit(1)

opts = {'engine': 'python', 'on_bad_lines': 'skip'}

df_time = pd.read_csv(file_time, **opts)
df_dept = pd.read_csv(file_dept, **opts)

df_time.columns = df_time.columns.str.strip()
df_dept.columns = df_dept.columns.str.strip()

# agencies are column headers (except Date)
value_cols = [c for c in df_time.columns if c.lower() != 'date']

# normalization helper
def normalize_name(s):
    s = str(s).lower().strip()
    s = re.sub(r"[^0-9a-z ]+", "", s)
    s = re.sub(r"\s+", " ", s)
    return s

# compute totals and target agencies (>1M)

def to_numeric_series(s):
    cleaned = s.astype(str).str.strip()
    cleaned = cleaned.replace({'-': '0'})
    cleaned = cleaned.str.replace(r"[^0-9.\-]", "", regex=True)
    cleaned = cleaned.replace({'': '0', '-': '0'})
    return pd.to_numeric(cleaned, errors='coerce')

# coerce all value columns in df_time
df_time_clean = df_time.copy()
for c in value_cols:
    df_time_clean[c] = to_numeric_series(df_time_clean[c])

totals = df_time_clean[value_cols].sum(axis=0, skipna=True).reset_index()
totals.columns = ['Agency', 'Total_Spend']
over_1m = totals[totals['Total_Spend'] > 1_000_000]
# normalized agency keys
over_1m = over_1m.copy()
over_1m['Agency_clean'] = over_1m['Agency'].astype(str).map(normalize_name)

target_agency_cleans = list(over_1m['Agency_clean'].unique())

# build map of agency_clean -> original agency header (helpful when placeholders used)
agency_clean_map = {normalize_name(a): a for a in value_cols}

# detect dept name column (prefer 'Department')
dept_col = None
for c in df_dept.columns:
    if c.lower() == 'department':
        dept_col = c
        break
if dept_col is None:
    dept_col = df_dept.columns[0]

# detect second column to search
if len(df_dept.columns) < 2:
    print('Department file has fewer than 2 columns; cannot use 2nd column for searching')
    sys.exit(1)
second_col = df_dept.columns[1]

# cleaned department column
df_dept = df_dept.copy()
df_dept['Department_clean'] = df_dept[dept_col].astype(str).map(normalize_name)

# prepare detailed matched rows
pattern = re.compile(covid_phrase, re.I)
rows = []
missing = []

# For numeric detection in department file (for aggregation later)
numeric_cols = []
for c in df_dept.columns:
    if c in [dept_col, 'Department_clean', second_col]:
        continue
    coerced = pd.to_numeric(df_dept[c].astype(str).str.replace(r"[^0-9.\-]", "", regex=True), errors='coerce')
    if coerced.notna().any():
        numeric_cols.append(c)

# iterate targets and collect detailed rows
for ac in sorted(target_agency_cleans):
    matches = df_dept[df_dept['Department_clean'] == ac]
    if not matches.empty:
        covid_rows = matches[matches[second_col].astype(str).str.contains(pattern, na=False)]
        if not covid_rows.empty:
            for _, r in covid_rows.iterrows():
                out = r.to_dict()
                out['_Matched_Agency_clean'] = ac
                rows.append(out)
        else:
            # no covid rows for this dept
            missing.append(ac)
            if include_placeholders:
                placeholder = {c: None for c in df_dept.columns}
                placeholder[dept_col] = matches[dept_col].iloc[0]
                placeholder[second_col] = None
                placeholder['_Matched_Agency_clean'] = ac
                rows.append(placeholder)
    else:
        # department not found; placeholder using agency header as display
        missing.append(ac)
        if include_placeholders:
            placeholder = {c: None for c in df_dept.columns}
            placeholder[dept_col] = agency_clean_map.get(ac, ac)
            placeholder[second_col] = None
            placeholder['_Matched_Agency_clean'] = ac
            rows.append(placeholder)

detailed_df = pd.DataFrame(rows)

# write detailed if desired (handle permission errors by falling back to timestamped filename)
if write_detailed:
    out_detailed = project_dir / 'matched_covid_rows.csv'
    try:
        detailed_df.to_csv(out_detailed, index=False)
        print(f'Wrote {len(detailed_df)} detailed rows to {out_detailed}')
    except PermissionError:
        from datetime import datetime
        out_detailed = project_dir / f"matched_covid_rows_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        detailed_df.to_csv(out_detailed, index=False)
        print(f'Permission denied writing default file; wrote to {out_detailed} instead')

# Helper function to format as currency
def format_currency(val):
    if pd.isna(val) or val == 0:
        return '$0.00'
    return f'${val:,.2f}'

# Build a map of agency_clean -> total spend (from over_1m)
total_spend_map = dict(zip(over_1m['Agency_clean'], over_1m['Total_Spend']))

# Now aggregated summary: one row per target agency
aggregated = []
for ac in sorted(target_agency_cleans):
    matches = df_dept[df_dept['Department_clean'] == ac]
    covid_rows = matches[matches[second_col].astype(str).str.contains(pattern, na=False)]
    if covid_rows.empty:
        # skip empty rows (include_placeholders is False, so no placeholders added)
        continue
    else:
        initiatives = covid_rows[second_col].astype(str).map(lambda s: s.strip()).replace('', pd.NA).dropna().unique().tolist()
        init_join = ' | '.join(initiatives)
        sums = {}
        for c in numeric_cols:
            coerced = pd.to_numeric(covid_rows[c].astype(str).str.replace(r"[^0-9.\-]", "", regex=True), errors='coerce')
            # use 0.0 for sum if all NaN
            ssum = coerced.sum(min_count=1)
            sums[f'Sum_{c}'] = ssum if pd.notna(ssum) else 0
        
        # Format numeric columns as currency
        formatted_sums = {k: format_currency(v) for k, v in sums.items()}
        
        # Get total spend from first file
        total_spend = total_spend_map.get(ac, 0)
        row = {
            'Department': matches[dept_col].iloc[0],
            'Total_Spend_From_First_File': format_currency(total_spend),
            'Num_Covid_Rows': len(covid_rows),
            'Covid_Initiatives': init_join,
            **formatted_sums
        }
        aggregated.append(row)

agg_df = pd.DataFrame(aggregated)
if write_aggregated:
    out_agg = project_dir / 'matched_covid_aggregated.csv'
    try:
        agg_df.to_csv(out_agg, index=False)
        print(f'Wrote {len(agg_df)} aggregated rows to {out_agg}')
    except PermissionError:
        from datetime import datetime
        out_agg = project_dir / f"matched_covid_aggregated_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        agg_df.to_csv(out_agg, index=False)
        print(f'Permission denied writing default file; wrote to {out_agg} instead')

# summary
print(f'Target agencies (over $1M): {len(target_agency_cleans)}')
print(f'Departments with covid response data: {len(aggregated)}')

print('\nAggregated Covid Response Summary:')
print(agg_df.to_string(index=False))

print('\nDone.')
