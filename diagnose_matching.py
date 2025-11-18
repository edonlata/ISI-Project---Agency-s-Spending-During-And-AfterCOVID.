import pandas as pd
import os
from pathlib import Path

base = Path(r"C:\Users\Nikol\OneDrive\CSC300")
file1 = base / 'projectrrr.csv'
file2 = base / 'Department Spending.csv'

print('File1:', file1, 'exists=', file1.exists())
print('File2:', file2, 'exists=', file2.exists())

# read with same options as test.py
opts = {'engine': 'python', 'on_bad_lines': 'skip'}

if not file1.exists() or not file2.exists():
    print('\nOne or both files missing. Listing directory contents for troubleshooting:')
    for p in base.glob('*'):
        print(' -', p.name)
    raise SystemExit(1)


df1 = pd.read_csv(file1, **opts)
df2 = pd.read_csv(file2, **opts)

df1.columns = df1.columns.str.strip()
df2.columns = df2.columns.str.strip()

print('\nfile1 columns:', list(df1.columns))
print('file2 columns:', list(df2.columns))

# Determine which column is intended to be the Agency/Department name
cand1 = None
cand2 = None
for c in df1.columns:
    if c.lower() in ('agency', 'department', 'dept', 'department name', 'agency name'):
        cand1 = c
        break
for c in df2.columns:
    if c.lower() in ('department', 'dept', 'department name', 'agency', 'agency name'):
        cand2 = c
        break

print('\nDetected name columns:')
print(' - in projectrrr.csv:', cand1)
print(' - in Department Spending.csv:', cand2)

if cand1 is None or cand2 is None:
    print('\nCould not auto-detect name columns. Showing first few rows of each file:')
    print('\nprojectrrr.csv sample:')
    print(df1.head(5).to_string(index=False))
    print('\nDepartment Spending.csv sample:')
    print(df2.head(5).to_string(index=False))
    raise SystemExit(1)

# create cleaned columns
s1 = df1[cand1].astype(str).str.lower().str.strip()
s2 = df2[cand2].astype(str).str.lower().str.strip()

# remove excessive punctuation/spaces
import re

def normalize(s):
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"[^0-9a-z ]", "", s)
    s = s.strip()
    return s

s1n = s1.map(normalize)
s2n = s2.map(normalize)

set1 = set(s1n.dropna().unique())
set2 = set(s2n.dropna().unique())

print('\nCounts:')
print(' - projectrrr unique names:', len(set1))
print(' - Department Spending unique names:', len(set2))

inter = set1 & set2
print(' - exact intersection size:', len(inter))

print('\nSample matches (up to 20):')
for i, v in enumerate(list(inter)[:20], 1):
    print(f"{i}. {v}")

# show some unmatched examples from the large side
unmatched_from_1 = list(set1 - set2)[:20]
unmatched_from_2 = list(set2 - set1)[:20]

print('\nSample names in projectrrr but not in Department Spending (20):')
for v in unmatched_from_1:
    print(' -', v)

print('\nSample names in Department Spending but not in projectrrr (20):')
for v in unmatched_from_2:
    print(' -', v)

# show top agency totals file used in test.py approach if relevant
try:
    # attempt to replicate totals and top few
    def to_numeric_series(s):
        cleaned = s.astype(str).str.strip()
        cleaned = cleaned.replace({'-': '0'})
        cleaned = cleaned.str.replace(r"[^0-9.\-]", "", regex=True)
        cleaned = cleaned.replace({'': '0', '-': '0'})
        return pd.to_numeric(cleaned, errors='coerce')

    value_cols = [c for c in df1.columns if c.lower() != 'date']
    df1_clean = df1.copy()
    for c in value_cols:
        df1_clean[c] = to_numeric_series(df1_clean[c])
    totals = df1_clean[value_cols].sum(axis=0, skipna=True).reset_index()
    totals.columns = ['Agency', 'Total_Spend']
    over_1m = totals[totals['Total_Spend'] > 1_000_000]
    print('\nTop agencies from projectrrr.csv (replicated):')
    print(over_1m.sort_values('Total_Spend', ascending=False).head(10).to_string(index=False))
except Exception as e:
    print('Could not replicate totals:', e)

print('\nDiagnostic script finished.')
