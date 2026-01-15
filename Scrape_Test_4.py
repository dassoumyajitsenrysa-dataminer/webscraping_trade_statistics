import time
import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# --------------------------------------------------
# CONFIG
# --------------------------------------------------
URL = "https://www.trademap.org/Country_SelProductCountry.aspx?nvpm=1|699||||090111|||6|1|1|1|1||2|1||1"
TOTAL_PAGES = 7

COLUMNS = [
    "Exporter",
    "Value imported (USD thousand)",
    "Trade balance (USD thousand)",
    "Share in India's imports (%)",
    "Quantity",
    "Quantity unit",
    "Unit value (USD/unit)",
    "Growth value 2020-2024",
    "Growth quantity 2020-2024",
    "Growth value 2023-2024",
    "World export rank",
    "Share in world exports (%)",
    "Partner export growth",
    "Average distance (km)",
    "Market concentration",
    "Average tariff (%)",
]

# --------------------------------------------------
# SELENIUM SETUP
# --------------------------------------------------
options = Options()
options.add_argument("--disable-blink-features=AutomationControlled")
options.add_argument("--start-maximized")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 40)
driver.get(URL)

# 🔑 HARD WAIT UNTIL REAL DATA ROW EXISTS
wait.until(EC.presence_of_element_located((By.CLASS_NAME, "partner_label")))

# --------------------------------------------------
# ROW EXTRACTION (STRICT)
# --------------------------------------------------
def extract_page_rows(html):
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id="ctl00_PageContent_MyGridView1")
    rows = []

    for tr in table.find_all("tr"):
        partner = tr.find("a", class_="partner_label")
        tds = tr.find_all("td")

        # STRICT RULES
        if not partner:
            continue
        if len(tds) < 17:
            continue

        values = [
            td.get_text(strip=True).replace("\xa0", "") or None
            for td in tds[1:18]   # skip expand icon column
        ]

        rows.append(values)

    return rows

# --------------------------------------------------
# PAGINATION LOOP
# --------------------------------------------------
all_rows = []

for page in range(1, TOTAL_PAGES + 1):
    print(f"Scraping page {page}")

    html = driver.page_source
    page_rows = extract_page_rows(html)

    print(f"  Rows found: {len(page_rows)}")
    all_rows.extend(page_rows)

    if page < TOTAL_PAGES:
        driver.execute_script(
            "__doPostBack('ctl00$PageContent$MyGridView1','Page${}')"
            .format(page + 1)
        )

        # 🔑 WAIT AGAIN FOR DATA BINDING
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "partner_label")))
        time.sleep(2)

driver.quit()

# --------------------------------------------------
# DATAFRAME
# --------------------------------------------------
df = pd.DataFrame(all_rows, columns=COLUMNS)

# CLEAN NUMBERS
for col in df.columns:
    df[col] = (
        df[col].astype(str)
        .str.replace(",", "", regex=False)
        .replace({"": None, "None": None})
    )

df.to_csv("trademap_all_pages.csv", index=False)

print("\nSUCCESS")
print("Total rows:", len(df))
print(df.head())
