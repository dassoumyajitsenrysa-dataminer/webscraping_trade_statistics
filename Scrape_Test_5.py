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
URL = (
    "https://www.trademap.org/"
    "Country_SelProductCountry.aspx?"
    "nvpm=1|699||||090111|||6|1|1|1|1||2|1||1"
)
TOTAL_PAGES = 7

COLUMNS = [
    "Exporter",
    "Value imported in 2024 (USD thousand)",
    "Trade balance 2024 (USD thousand)",
    "Share in India's imports (%)",
    "Share of India in partner's exports (%)",
    "Quantity imported in 2024",
    "Quantity unit",
    "Unit value (USD/unit)",
    "Growth in imported value 2020-2024 (% p.a.)",
    "Growth in imported quantity 2020-2024 (% p.a.)",
    "Growth in imported value 2023-2024 (% p.a.)",
    "Ranking in world exports",
    "Share in world exports (%)",
    "Partner exports growth 2020-2024 (% p.a.)",
    "Average distance (km)",
    "Concentration of importing countries",
    "Average tariff applied by India (%)",
    "Tariff link / misc",
    "Untapped potential trade (USD thousand)",
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

# 🔑 Wait for real data rows (not just table)
wait.until(EC.presence_of_element_located((By.CLASS_NAME, "partner_label")))

# --------------------------------------------------
# ROW EXTRACTION (HTML-EXACT)
# --------------------------------------------------
def extract_rows(html):
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id="ctl00_PageContent_MyGridView1")

    rows = []

    for tr in table.find_all("tr"):
        # real data rows always have this
        if not tr.find("a", class_="partner_label"):
            continue

        tds = tr.find_all("td")

        # EXACTLY 20 <td> per your HTML
        if len(tds) != 20:
            continue

        # skip expand/bilateral column (td[0])
        values = [
            td.get_text(strip=True).replace("\xa0", "") or None
            for td in tds[1:]
        ]

        rows.append(values)

    return rows

# --------------------------------------------------
# PAGINATION LOOP
# --------------------------------------------------
all_rows = []

for page in range(1, TOTAL_PAGES + 1):
    print(f"Scraping page {page}")

    page_rows = extract_rows(driver.page_source)
    print(f"  Rows found: {len(page_rows)}")
    all_rows.extend(page_rows)

    if page < TOTAL_PAGES:
        driver.execute_script(
            "__doPostBack('ctl00$PageContent$MyGridView1','Page${}')"
            .format(page + 1)
        )
        wait.until(EC.presence_of_element_located((By.CLASS_NAME, "partner_label")))
        time.sleep(2)

driver.quit()

# --------------------------------------------------
# DATAFRAME
# --------------------------------------------------
df = pd.DataFrame(all_rows, columns=COLUMNS)

# Clean numeric formatting
for col in df.columns:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(",", "", regex=False)
        .replace({"": None, "None": None})
    )

# --------------------------------------------------
# SAVE OUTPUT
# --------------------------------------------------
df.to_csv("trademap_final_correct.csv", index=False)

print("\nSUCCESS")
print("Total rows:", len(df))
print(df.head())
