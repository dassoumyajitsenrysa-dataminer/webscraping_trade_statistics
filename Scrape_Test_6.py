import time
import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


URL = (
    "https://www.trademap.org/"
    "Country_SelProductCountry.aspx?"
    "nvpm=1|699||||090111|||6|1|1|1|1||2|1||1"
)

YEAR = 2024
HS6_CODE = "090111"


# -------------------- DRIVER --------------------
options = Options()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 40)
driver.get(URL)

wait.until(EC.presence_of_element_located((By.ID, "ctl00_PageContent_MyGridView1")))


# -------------------- HS8 PARSER --------------------
def parse_hs8(html, country):
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id="ctl00_PageContent_MyGridView1")

    rows = table.find_all("tr")[2:]  # skip headers
    data = []

    for tr in rows:
        tds = tr.find_all("td")
        if len(tds) < 9:
            continue

        hs8 = tds[0].get_text(strip=True)
        if not hs8.isdigit():
            continue

        data.append({
            "country": country,
            "hs6_code": HS6_CODE,
            "hs8_code": hs8,
            "year": YEAR,
            "product_label": tds[1].get_text(strip=True),
            "value_2022_country": tds[2].get_text(strip=True),
            "value_2023_country": tds[3].get_text(strip=True),
            "value_2024_country": tds[4].get_text(strip=True),
            "value_2022_world": tds[6].get_text(strip=True),
            "value_2023_world": tds[7].get_text(strip=True),
            "value_2024_world": tds[8].get_text(strip=True),
        })

    return data


# -------------------- HS6 PARSER --------------------
def parse_hs6(html):
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id="ctl00_PageContent_MyGridView1")

    rows = table.find_all("tr")
    data = []

    for tr in rows:
        tds = tr.find_all("td")
        if len(tds) != 17:
            continue

        country = tds[1].get_text(strip=True)
        if not country:
            continue

        data.append({
            "country": country,
            "hs6_code": HS6_CODE,
            "year": YEAR,
            "value_imported_usd_k": tds[2].get_text(strip=True),
            "trade_balance_usd_k": tds[3].get_text(strip=True),
            "share_india_imports_pct": tds[4].get_text(strip=True),
            "quantity": tds[5].get_text(strip=True),
            "quantity_unit": tds[6].get_text(strip=True),
            "unit_value": tds[7].get_text(strip=True),
            "growth_value_2020_24": tds[8].get_text(strip=True),
            "growth_quantity_2020_24": tds[9].get_text(strip=True),
            "growth_value_2023_24": tds[10].get_text(strip=True),
            "partner_rank": tds[11].get_text(strip=True),
            "partner_world_share": tds[12].get_text(strip=True),
            "partner_export_growth": tds[13].get_text(strip=True),
            "avg_distance_km": tds[14].get_text(strip=True),
            "concentration_index": tds[15].get_text(strip=True),
            "tariff_pct": tds[16].get_text(strip=True),
        })

    return data


# -------------------- MAIN LOOP --------------------
hs8_rows = []
hs6_rows = []

page = 1

while True:
    print(f"Processing page {page}")
    time.sleep(2)

    soup = BeautifulSoup(driver.page_source, "lxml")
    country_links = soup.select("a.partner_label")

    for link in country_links:
        country = link.get_text(strip=True)
        if country == "World":
            continue

        try:
            print(f"  ➕ Expanding {country}")
            elem = driver.find_element(By.LINK_TEXT, country)
            elem.click()

            wait.until(EC.presence_of_element_located(
                (By.ID, "ctl00_PageContent_MyGridView1")
            ))
            time.sleep(2)

            hs8_rows.extend(parse_hs8(driver.page_source, country))

            driver.back()
            wait.until(EC.presence_of_element_located(
                (By.ID, "ctl00_PageContent_MyGridView1")
            ))

        except Exception:
            continue

    # pagination
    try:
        next_page = driver.find_element(By.LINK_TEXT, str(page + 1))
        next_page.click()
        page += 1
    except:
        break


# collect HS6 after HS8 is complete
hs6_rows = parse_hs6(driver.page_source)

driver.quit()


# -------------------- CLEAN & SAVE --------------------
def clean(df):
    for c in df.columns:
        df[c] = (
            df[c].astype(str)
            .str.replace(",", "", regex=False)
            .replace({"": None, "-": None})
        )
    return df


df_hs8 = clean(pd.DataFrame(hs8_rows))
df_hs6 = clean(pd.DataFrame(hs6_rows))

df_hs8.to_csv("hs8_country_level.csv", index=False)
df_hs6.to_csv("hs6_country_level.csv", index=False)

print("✔ SCRAPING COMPLETE")
