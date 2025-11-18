import pandas as pd
from pathlib import Path
import os

base = Path(__file__).resolve().parent
file1 = Path(r"C:\Users\Nikol\OneDrive\CSC300\projectrrr.csv")
file2 = base / 'Department Spending.csv'

print('file1 exists:', file1.exists())
print('file2 exists:', file2.exists())

opts = {'engine':'python', 'on_bad_lines':'skip'}

df1 = pd.read_csv(file1, **opts)
df2 = pd.read_csv(file2, **opts)

df1.columns = df1.columns.str.strip()
df2.columns = df2.columns.str.strip()

# detect name columns
# projectrrr.csv uses agency names as column headers (all columns except 'Date')
value_cols = [c for c in df1.columns if c.lower() != 'date']
set1 = set([str(c).lower().strip() for c in value_cols])

# Department file likely has a 'Department' or similar column with names as rows
cand2 = None
for c in df2.columns:
    if c.lower() in ('department','dept','agency','agency name','department name'):
        cand2 = c
        break
if cand2 is None:
    cand2 = df2.columns[0]
s2 = df2[cand2].astype(str).str.lower().str.strip().str.replace(r"[^0-9a-z ]", "", regex=True)
set2 = set(s2.dropna().unique())

print('unique1:', len(set1), 'unique2:', len(set2))
inter = set1 & set2
print('intersection:', len(inter))
print('\nSome intersection samples:')
for v in list(inter)[:20]:
    print('-', v)

print('\nSome names in projectrrr not in Department file:')
for v in list(set1 - set2)[:20]:
    print('-', v)

print('\nSome names in Department file not in projectrrr:')
for v in list(set2 - set1)[:20]:
    print('-', v)
