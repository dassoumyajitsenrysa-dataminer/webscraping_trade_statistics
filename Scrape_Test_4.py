import time
import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# ------------------------------------------------
# 1. Selenium Setup
# ------------------------------------------------
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

# ------------------------------------------------
# 2. Extract Headers (CORRECT WAY)
# ------------------------------------------------
soup = BeautifulSoup(driver.page_source, "lxml")
table = soup.find("table", id="ctl00_PageContent_MyGridView1")

header_rows = table.find_all("tr")

# Second header row contains numeric headers
second_header = header_rows[2]

headers = ["Exporters"]  # THIS IS A TD COLUMN, NOT TH

for th in second_header.find_all("th"):
    headers.append(th.get_text(strip=True))

# ------------------------------------------------
# 3. Extract ALL country rows (NO SLICING)
# ------------------------------------------------
def extract_rows(html):
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id="ctl00_PageContent_MyGridView1")

    rows = []

    for tr in table.find_all("tr"):
        country_tag = tr.find("a", class_="partner_label")
        if not country_tag:
            continue

        tds = tr.find_all("td")
        if len(tds) < len(headers) + 1:
            continue

        # Skip expand-icon td, keep EVERYTHING else
        row = [td.get_text(" ", strip=True) or None for td in tds[1:]]

        rows.append(row)

    return rows

# ------------------------------------------------
# 4. Pagination Loop
# ------------------------------------------------
all_rows = []
TOTAL_PAGES = 7

for page in range(1, TOTAL_PAGES + 1):
    print(f"Scraping page {page}...")
    all_rows.extend(extract_rows(driver.page_source))

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

# ------------------------------------------------
# 5. DataFrame
# ------------------------------------------------
df = pd.DataFrame(all_rows, columns=headers)

# ------------------------------------------------
# 6. Cleaning
# ------------------------------------------------
for col in df.columns:
    df[col] = (
        df[col]
        .replace({"": None, "\xa0": None})
        .astype(str)
        .str.replace(",", "", regex=False)
        .replace({"None": None})
    )

# ------------------------------------------------
# 7. Save
# ------------------------------------------------
df.to_csv("trademap_090111_all_pages.csv", index=False)

print("SUCCESS")
print("Rows:", len(df))
print("Columns:", df.columns.tolist())
