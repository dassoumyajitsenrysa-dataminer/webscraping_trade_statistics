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

# ----------------------------------------------------
# Fixed schema (verified from HTML)
# ----------------------------------------------------
COLUMNS = [
    "Exporters",
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
    "Untapped potential trade (USD thousand)",
]

# ----------------------------------------------------
# Selenium setup
# ----------------------------------------------------
options = Options()
options.add_argument("--start-maximized")
options.add_argument("--disable-blink-features=AutomationControlled")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 40)

URL = (
    "https://www.trademap.org/"
    "Country_SelProductCountry.aspx?"
    "nvpm=1|699||||090111|||6|1|1|1|1||2|1||1"
)

driver.get(URL)

# 🔑 WAIT FOR REAL DATA, NOT JUST TABLE
wait.until(
    EC.presence_of_element_located(
        (By.CLASS_NAME, "partner_label")
    )
)

# ----------------------------------------------------
# Extract rows (HTML-accurate)
# ----------------------------------------------------
def extract_rows(html):
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id="ctl00_PageContent_MyGridView1")

    rows = []

    for tr in table.find_all("tr"):
        if not tr.find("a", class_="partner_label"):
            continue

        tds = tr.find_all("td")
        if len(tds) != 19:
            continue

        values = [
            td.get_text(strip=True).replace("\xa0", "") or None
            for td in tds[1:]  # skip expand icon
        ]

        rows.append(values)

    return rows

# ----------------------------------------------------
# Pagination loop
# ----------------------------------------------------
ALL_ROWS = []
TOTAL_PAGES = 7

for page in range(1, TOTAL_PAGES + 1):
    print(f"Scraping page {page}...")

    ALL_ROWS.extend(extract_rows(driver.page_source))

    if page < TOTAL_PAGES:
        driver.execute_script(
            "__doPostBack('ctl00$PageContent$MyGridView1','Page${}')"
            .format(page + 1)
        )

        # 🔑 WAIT AGAIN FOR DATA ROWS AFTER POSTBACK
        wait.until(
            EC.presence_of_element_located(
                (By.CLASS_NAME, "partner_label")
            )
        )

        time.sleep(2)

driver.quit()

# ----------------------------------------------------
# Build DataFrame
# ----------------------------------------------------
df = pd.DataFrame(ALL_ROWS, columns=COLUMNS)

# ----------------------------------------------------
# Clean numeric artifacts
# ----------------------------------------------------
for col in df.columns:
    df[col] = (
        df[col]
        .astype(str)
        .str.replace(",", "", regex=False)
        .replace({"": None, "None": None})
    )

# ----------------------------------------------------
# Save
# ----------------------------------------------------
df.to_csv("trademap_090111_all_pages.csv", index=False)

print("SUCCESS")
print("Rows:", len(df))
print("Columns:", df.columns.tolist())
