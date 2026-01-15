from bs4 import BeautifulSoup
import pandas as pd

# -----------------------------
# 1. Load HTML
# -----------------------------
with open("table.html", "r", encoding="utf-8") as f:
    html = f.read()

soup = BeautifulSoup(html, "lxml")

# -----------------------------
# 2. Locate the table
# -----------------------------
table = soup.find("table", id="ctl00_PageContent_MyGridView1")

if not table:
    raise ValueError("Table not found")

# -----------------------------
# 3. Extract headers
# -----------------------------
headers = []

# The second header row contains actual column names
header_rows = table.find_all("tr")

for tr in header_rows:
    ths = tr.find_all("th")
    if ths:
        for th in ths:
            header_text = th.get_text(strip=True)
            if header_text:
                headers.append(header_text)

# Optional: remove duplicated or unwanted headers
headers = list(dict.fromkeys(headers))

# -----------------------------
# 4. Extract data rows
# -----------------------------
data = []

for tr in table.find_all("tr"):
    tds = tr.find_all("td")
    if not tds:
        continue

    row = []
    for td in tds:
        text = td.get_text(" ", strip=True)
        row.append(text if text else None)

    # Filter out pager rows
    if len(row) > 5:
        data.append(row)

# -----------------------------
# 5. Normalize row length
# -----------------------------
max_cols = max(len(r) for r in data)

normalized_data = [
    r + [None] * (max_cols - len(r))
    for r in data
]

# -----------------------------
# 6. Create DataFrame
# -----------------------------
df = pd.DataFrame(normalized_data)

# Assign headers if counts match
if len(headers) <= df.shape[1]:
    df.columns = headers + [f"extra_{i}" for i in range(df.shape[1] - len(headers))]

# -----------------------------
# 7. Clean numeric columns
# -----------------------------
for col in df.columns:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(",", "", regex=False)
        .replace({"None": None})
    )

# -----------------------------
# 8. Save output
# -----------------------------
df.to_csv("parsed_trade_data.csv", index=False)

print("Parsing complete. Rows:", len(df))
