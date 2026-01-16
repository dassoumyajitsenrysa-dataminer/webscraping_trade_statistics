import time
import pandas as pd
from bs4 import BeautifulSoup

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager


# ================= CONFIG =================
USERNAME = "YOUR_EMAIL"
PASSWORD = "YOUR_PASSWORD"

HS6_CODE = "090111"
REPORTER = "India"
YEAR = 2024

START_URL = "https://www.trademap.org/Index.aspx"


# ================= DRIVER =================
options = Options()
options.add_argument("--start-maximized")

driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

wait = WebDriverWait(driver, 40)
driver.get(START_URL)


# ================= LOGIN CHECK =================
def ensure_login():
    try:
        login_label = driver.find_element(By.ID, "ctl00_MenuControl_Label_Login")
        if login_label.text.strip().lower() == "login":
            print("🔐 Login required")
            driver.find_element(By.ID, "ctl00_MenuControl_marmenu_login").click()

            wait.until(EC.presence_of_element_located((By.ID, "txtUserName")))
            driver.find_element(By.ID, "txtUserName").send_keys(USERNAME)
            driver.find_element(By.ID, "txtPassword").send_keys(PASSWORD)
            driver.find_element(By.ID, "btnLogin").click()

            wait.until(EC.presence_of_element_located(
                (By.ID, "ctl00_PageContent_RadComboBox_Product_Input")
            ))
            print("✅ Logged in successfully")
    except:
        print("✅ Already logged in")


ensure_login()


# ================= SEARCH HS6 =================
product_box = wait.until(EC.element_to_be_clickable(
    (By.ID, "ctl00_PageContent_RadComboBox_Product_Input")
))
product_box.clear()
product_box.send_keys(HS6_CODE)
time.sleep(1)
product_box.send_keys(Keys.ENTER)


# ================= SELECT INDIA =================
country_box = wait.until(EC.element_to_be_clickable(
    (By.ID, "ctl00_PageContent_RadComboBox_Country_Input")
))
country_box.clear()
country_box.send_keys(REPORTER)
time.sleep(1)
country_box.send_keys(Keys.ENTER)


# ================= OPEN TRADE INDICATORS =================
ti_button = wait.until(EC.element_to_be_clickable(
    (By.ID, "ctl00_PageContent_Button_TradeIndicators")
))
ti_button.click()

wait.until(EC.presence_of_element_located(
    (By.ID, "ctl00_PageContent_MyGridView1")
))


# ================= PARSERS =================
def parse_table(html, level, country):
    soup = BeautifulSoup(html, "lxml")
    table = soup.find("table", id="ctl00_PageContent_MyGridView1")

    rows = table.find_all("tr")[2:]
    out = []

    for tr in rows:
        tds = tr.find_all("td")
        if len(tds) < 9:
            continue

        code = tds[0].get_text(strip=True)
        if not code.isdigit():
            continue

        row = {
            "reporter": country,
            "year": YEAR,
            "hs6_code": HS6_CODE if level == "HS8" else code,
            "hs8_code": code if level == "HS8" else None,
            "product_label": tds[1].get_text(strip=True),
            "value_country_2022": tds[2].get_text(strip=True),
            "value_country_2023": tds[3].get_text(strip=True),
            "value_country_2024": tds[4].get_text(strip=True),
            "unit": tds[6].get_text(strip=True),
            "world_share": tds[12].get_text(strip=True)
        }
        out.append(row)

    return out


# ================= SCRAPE HS6 =================
hs6_data = parse_table(driver.page_source, "HS6", REPORTER)


# ================= SCRAPE HS8 =================
hs8_data = []

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
        driver.execute_script("arguments[0].click();", plus_btn)

        wait.until(EC.presence_of_element_located(
            (By.XPATH, "//th[contains(text(),'Product code')]")
        ))
        time.sleep(2)

        hs8_data.extend(parse_table(driver.page_source, "HS8", country))

        driver.back()
        wait.until(EC.presence_of_element_located(
            (By.ID, "ctl00_PageContent_MyGridView1")
        ))

    except Exception as e:
        print(f"HS8 failed for {country}: {e}")


driver.quit()


# ================= SAVE =================
df_hs6 = pd.DataFrame(hs6_data)
df_hs8 = pd.DataFrame(hs8_data)

for df in (df_hs6, df_hs8):
    for c in df.columns:
        df[c] = (
            df[c].astype(str)
            .str.replace(",", "", regex=False)
            .replace({"": None, "-": None})
        )

df_hs6.to_csv("hs6_india.csv", index=False)
df_hs8.to_csv("hs8_india.csv", index=False)

print("✅ DONE: HS6 & HS8 extracted successfully")
