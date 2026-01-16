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

# ---------------- DRIVER ----------------
options = Options()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 40)
driver.get(URL)

wait.until(EC.presence_of_element_located(
    (By.ID, "ctl00_PageContent_MyGridView1")
))


# ---------------- HS8 PARSER ----------------
def parse_hs8(html, country):
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id="ctl00_PageContent_MyGridView1")

    rows = table.find_all("tr")[2:]
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


# ---------------- MAIN LOOP ----------------
hs8_rows = []
page = 1

while True:
    print(f"Page {page}")
    time.sleep(2)

    # find all country rows (skip World)
    rows = driver.find_elements(
        By.XPATH,
        "//table[@id='ctl00_PageContent_MyGridView1']//tr[td/a[@class='partner_label']]"
    )

    for row in rows:
        country = row.find_element(By.CLASS_NAME, "partner_label").text
        if country == "World":
            continue

        try:
            plus_btn = row.find_element(By.XPATH, ".//input[contains(@class,'breakdown')]")

            print(f"  ➕ Clicking HS8 for {country}")
            driver.execute_script("arguments[0].click();", plus_btn)

            wait.until(EC.presence_of_element_located(
                (By.XPATH, "//th[contains(text(),'Product code')]")
            ))
            time.sleep(2)

            hs8_rows.extend(parse_hs8(driver.page_source, country))

            driver.back()
            wait.until(EC.presence_of_element_located(
                (By.ID, "ctl00_PageContent_MyGridView1")
            ))

        except Exception as e:
            print(f"Failed {country}: {e}")
            continue

    # pagination
    try:
        driver.find_element(By.LINK_TEXT, str(page + 1)).click()
        page += 1
    except:
        break


driver.quit()


# ---------------- SAVE ----------------
df_hs8 = pd.DataFrame(hs8_rows)

for c in df_hs8.columns:
    df_hs8[c] = (
        df_hs8[c].astype(str)
        .str.replace(",", "", regex=False)
        .replace({"": None, "-": None})
    )

df_hs8.to_csv("hs8_country_level.csv", index=False)

print("✅ HS8 extraction COMPLETE")
