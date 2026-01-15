import time
import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ---------------------------------------
# 1. Selenium Setup
# ---------------------------------------
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 30)

URL = (
    "https://www.trademap.org/"
    "Country_SelProductCountry.aspx?"
    "nvpm=1|699||||090111|||6|1|1|1|1||2|1||1"
)

driver.get(URL)

wait.until(EC.presence_of_element_located(
    (By.ID, "ctl00_PageContent_MyGridView1")
))

# ---------------------------------------
# 2. Extract Headers (ONCE)
# ---------------------------------------
soup = BeautifulSoup(driver.page_source, "lxml")
table = soup.find("table", id="ctl00_PageContent_MyGridView1")

header_row = table.find_all("tr")[2]   # second header line
headers = [
    th.get_text(strip=True)
    for th in header_row.find_all("th")
]

# Remove the first column (expand icon)
headers = headers[1:]

# ---------------------------------------
# 3. Row Extractor (NO JUNK)
# ---------------------------------------
def extract_country_rows(html):
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id="ctl00_PageContent_MyGridView1")

    rows = []
    for tr in table.find_all("tr"):
        country = tr.find("a", class_="partner_label")
        if not country:
            continue

        tds = tr.find_all("td")
        if len(tds) < 19:
            continue

        row = []
        for td in tds[1:]:  # skip expand icon column
            text = td.get_text(" ", strip=True)
            row.append(text if text else None)

        rows.append(row)

    return rows


# ---------------------------------------
# 4. Pagination Loop
# ---------------------------------------
ALL_ROWS = []
TOTAL_PAGES = 7

for page in range(1, TOTAL_PAGES + 1):
    print(f"Scraping page {page}...")

    html = driver.page_source
    rows = extract_country_rows(html)
    ALL_ROWS.extend(rows)

    if page < TOTAL_PAGES:
        driver.execute_script(
            "__doPostBack('ctl00$PageContent$MyGridView1','Page${}')"
            .format(page + 1)
        )
        time.sleep(4)
        wait.until(EC.presence_of_element_located(
            (By.ID, "ctl00_PageContent_MyGridView1")
        ))

driver.quit()

# ---------------------------------------
# 5. DataFrame
# ---------------------------------------
df = pd.DataFrame(ALL_ROWS, columns=headers)

# ---------------------------------------
# 6. Cleaning
# ---------------------------------------
for col in df.columns:
    df[col] = (
        df[col]
        .replace({"": None, "\xa0": None})
        .astype(str)
        .str.replace(",", "", regex=False)
        .replace({"None": None})
    )

# ---------------------------------------
# 7. Save
# ---------------------------------------
df.to_csv("HSN_090111_all_pages_clean.csv", index=False)

print("DONE")
print("Rows:", len(df))
print("Columns:", list(df.columns))
