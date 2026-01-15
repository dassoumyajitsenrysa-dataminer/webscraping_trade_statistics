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

# ----------------------------------------
# 1. Selenium Setup
# ----------------------------------------
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

# ----------------------------------------
# 2. Target URL
# ----------------------------------------
URL = (
    "https://www.trademap.org/"
    "Country_SelProductCountry.aspx?"
    "nvpm=1|699||||090111|||6|1|1|1|1||2|1||1"
)

driver.get(URL)

wait = WebDriverWait(driver, 30)

# Wait for table to load
wait.until(
    EC.presence_of_element_located(
        (By.ID, "ctl00_PageContent_MyGridView1")
    )
)

# ----------------------------------------
# 3. Helper: Extract table from page
# ----------------------------------------
def extract_table(html):
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id="ctl00_PageContent_MyGridView1")

    rows = []
    for tr in table.find_all("tr"):
        tds = tr.find_all("td")
        if len(tds) < 5:
            continue
        row = [td.get_text(" ", strip=True) or None for td in tds]
        rows.append(row)

    return rows


# ----------------------------------------
# 4. Extract Headers (Once)
# ----------------------------------------
page_source = driver.page_source
soup = BeautifulSoup(page_source, "lxml")
table = soup.find("table", id="ctl00_PageContent_MyGridView1")

headers = []
for tr in table.find_all("tr"):
    ths = tr.find_all("th")
    if ths:
        for th in ths:
            text = th.get_text(strip=True)
            if text:
                headers.append(text)

headers = list(dict.fromkeys(headers))

# ----------------------------------------
# 5. Pagination Loop
# ----------------------------------------
all_rows = []

TOTAL_PAGES = 7

for page in range(1, TOTAL_PAGES + 1):
    print(f"Scraping page {page}...")

    html = driver.page_source
    rows = extract_table(html)
    all_rows.extend(rows)

    if page < TOTAL_PAGES:
        driver.execute_script(
            "__doPostBack('ctl00$PageContent$MyGridView1','Page${}')".format(page + 1)
        )
        time.sleep(4)  # HUMAN delay
        wait.until(
            EC.presence_of_element_located(
                (By.ID, "ctl00_PageContent_MyGridView1")
            )
        )

# ----------------------------------------
# 6. Close Browser
# ----------------------------------------
driver.quit()

# ----------------------------------------
# 7. Normalize & Build DataFrame
# ----------------------------------------
max_len = max(len(r) for r in all_rows)
all_rows = [r + [None] * (max_len - len(r)) for r in all_rows]

df = pd.DataFrame(all_rows)

if len(headers) <= df.shape[1]:
    df.columns = headers + [
        f"extra_{i}" for i in range(df.shape[1] - len(headers))
    ]

# ----------------------------------------
# 8. Clean Numbers
# ----------------------------------------
for col in df.columns:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(",", "", regex=False)
        .replace({"None": None})
    )

# ----------------------------------------
# 9. Save Output
# ----------------------------------------
df.to_csv("trademap_all_pages_090111.csv", index=False)

print(f"Done. Total rows scraped: {len(df)}")
