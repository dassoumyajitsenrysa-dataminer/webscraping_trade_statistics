import requests
from bs4 import BeautifulSoup
import pandas as pd

# ----------------------------------
# 1. URL
# ----------------------------------
URL = "https://www.trademap.org/Country_SelProductCountry.aspx?nvpm=1|699||||090111|||6|1|1|1|1||2|1||1"

# ----------------------------------
# 2. Session + Headers (CRITICAL)
# ----------------------------------
session = requests.Session()

headers = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.trademap.org/",
}

# ----------------------------------
# 3. Fetch Page
# ----------------------------------
response = session.get(URL, headers=headers, timeout=30)
response.raise_for_status()

html = response.text

# ----------------------------------
# 4. Parse HTML
# ----------------------------------
soup = BeautifulSoup(html, "lxml")

table = soup.find("table", id="ctl00_PageContent_MyGridView1")

if not table:
    raise RuntimeError("Trade table not found — page structure may have changed.")

# ----------------------------------
# 5. Extract Headers
# ----------------------------------
headers = []
for tr in table.find_all("tr"):
    ths = tr.find_all("th")
    if ths:
        for th in ths:
            text = th.get_text(strip=True)
            if text:
                headers.append(text)

headers = list(dict.fromkeys(headers))

# ----------------------------------
# 6. Extract Data Rows
# ----------------------------------
rows = []

for tr in table.find_all("tr"):
    tds = tr.find_all("td")
    if len(tds) < 5:
        continue

    row = [td.get_text(" ", strip=True) or None for td in tds]
    rows.append(row)

# ----------------------------------
# 7. Normalize Rows
# ----------------------------------
max_len = max(len(r) for r in rows)
rows = [r + [None] * (max_len - len(r)) for r in rows]

# ----------------------------------
# 8. DataFrame
# ----------------------------------
df = pd.DataFrame(rows)

if len(headers) <= df.shape[1]:
    df.columns = headers + [
        f"extra_{i}" for i in range(df.shape[1] - len(headers))
    ]

# ----------------------------------
# 9. Clean Numbers
# ----------------------------------
for col in df.columns:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(",", "", regex=False)
        .replace({"None": None})
    )

# ----------------------------------
# 10. Save
# ----------------------------------
df.to_csv("trademap_imports_090111.csv", index=False)

print(f"Scraped {len(df)} rows successfully.")
